"""AttachmentService -- bytes to SharePoint Online, metadata to SQL.

SQL never stores file content. The durable pointer is (GraphDriveId, GraphItemId);
StorageUrl is retained for human navigation and audit exports only.
"""
import hashlib
import os
import re
from ..extensions import db
from ..models import Attachment, Submission
from ..constants import AuditAction
from ..models.base import utcnow
from .audit_service import AuditService
from .graph_client import GraphClient, GraphError

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._\- ]+")


class AttachmentError(Exception):
    pass


class AttachmentService:
    def __init__(self, config: dict, graph: GraphClient | None = None):
        self.config = config
        self.graph = graph or GraphClient(
            tenant_id=config["ENTRA_TENANT_ID"],
            client_id=config["ENTRA_CLIENT_ID"],
            client_secret=config["ENTRA_CLIENT_SECRET"],
            base_url=config["GRAPH_BASE_URL"],
        )
        self.drive_id = config.get("SPO_DRIVE_ID")
        self.root = config.get("SPO_ATTACHMENT_ROOT", "ComplianceEvidence")
        self.large_threshold = config.get("SPO_LARGE_FILE_THRESHOLD", 4 * 1024 * 1024)
        self.chunk = config.get("SPO_UPLOAD_CHUNK_BYTES", 5 * 320 * 1024)
        self.allowed = config.get("ALLOWED_UPLOAD_EXTENSIONS", set())

    # ---- Path convention: /{root}/{QuarterLabel}/{SubmissionId}/{filename} ----
    def build_folder_path(self, submission: Submission) -> str:
        quarter = (submission.period.QuarterLabel if submission.period else "Unassigned")
        return f"{self.root}/{self._safe(quarter)}/{submission.SubmissionId}"

    @staticmethod
    def _safe(name: str) -> str:
        return _SAFE_NAME.sub("_", (name or "").strip()) or "file"

    def validate_file(self, filename: str, size_bytes: int) -> None:
        ext = os.path.splitext(filename)[1].lower()
        if self.allowed and ext not in self.allowed:
            raise AttachmentError(f"File type '{ext}' is not permitted.")
        max_bytes = self.config.get("MAX_CONTENT_LENGTH", 25 * 1024 * 1024)
        if size_bytes > max_bytes:
            raise AttachmentError(f"File exceeds the {max_bytes // (1024*1024)} MB limit.")

    # ---- Upload ----
    def upload(self, submission: Submission, file_stream, filename: str,
               content_type: str | None, actor_upn: str,
               attestation_id: int | None = None,
               field_code: str | None = None) -> Attachment:
        data = file_stream.read()
        self.validate_file(filename, len(data))

        safe_name = self._safe(filename)
        target = f"{self.build_folder_path(submission)}/{safe_name}"
        digest = hashlib.sha256(data).hexdigest()

        try:
            if len(data) < self.large_threshold:
                item = self._simple_upload(target, data, content_type)
            else:
                item = self._chunked_upload(target, data)
        except GraphError as exc:
            raise AttachmentError(f"Upload to SharePoint failed: {exc}") from exc

        attachment = Attachment(
            SubmissionId=submission.SubmissionId,
            AttestationId=attestation_id,
            FieldCode=field_code,
            OriginalFileName=filename,
            ContentType=content_type,
            GraphDriveId=item.get("parentReference", {}).get("driveId", self.drive_id),
            GraphItemId=item.get("id"),
            StorageUrl=item.get("webUrl", ""),
            FileSizeBytes=len(data),
            Sha256=digest,
            UploadedBy=actor_upn,
            UploadedUtc=utcnow(),
        )
        db.session.add(attachment)
        db.session.commit()

        AuditService.record("Attachment", attachment.AttachmentId,
                            AuditAction.ATTACHMENT_UPLOAD, actor=actor_upn,
                            details={"submissionId": submission.SubmissionId,
                                     "fileName": filename, "sizeBytes": len(data),
                                     "sha256": digest})
        return attachment

    def _simple_upload(self, target_path: str, data: bytes, content_type: str | None) -> dict:
        path = f"/drives/{self.drive_id}/root:/{target_path}:/content"
        headers = {"Content-Type": content_type or "application/octet-stream"}
        return self.graph.request("PUT", path, data=data, headers=headers).json()

    def _chunked_upload(self, target_path: str, data: bytes) -> dict:
        session_path = f"/drives/{self.drive_id}/root:/{target_path}:/createUploadSession"
        upload_url = self.graph.request(
            "POST", session_path,
            json={"item": {"@microsoft.graph.conflictBehavior": "rename"}}
        ).json()["uploadUrl"]

        total = len(data)
        for start in range(0, total, self.chunk):
            end = min(start + self.chunk, total) - 1
            headers = {"Content-Length": str(end - start + 1),
                       "Content-Range": f"bytes {start}-{end}/{total}"}
            response = self.graph.request("PUT", upload_url, data=data[start:end + 1],
                                          headers=headers)
            if response.status_code in (200, 201):
                return response.json()
        raise AttachmentError("Chunked upload completed without a final item response.")

    # ---- Download ----
    def download_url(self, attachment: Attachment) -> str:
        """Short-lived pre-authenticated URL. Never expose the raw drive path."""
        data = self.graph.get_json(
            f"/drives/{attachment.GraphDriveId}/items/{attachment.GraphItemId}"
            "?select=id,name,@microsoft.graph.downloadUrl")
        url = data.get("@microsoft.graph.downloadUrl")
        if not url:
            raise AttachmentError("SharePoint did not return a download URL.")
        return url

    def soft_delete(self, attachment: Attachment, actor_upn: str) -> None:
        """Metadata is retained for audit; only the SPO item is removed."""
        attachment.IsDeleted = True
        db.session.commit()
        AuditService.record("Attachment", attachment.AttachmentId,
                            AuditAction.ATTACHMENT_DELETE, actor=actor_upn,
                            details={"graphItemId": attachment.GraphItemId})

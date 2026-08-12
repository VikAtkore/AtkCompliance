"""MigrationService -- legacy InfoPath XML and Vlookup import.

Nothing in SharePoint 2013 is modified. Raw XML is preserved in staging so
every migrated record can be reconciled field-by-field against its source.
"""
import base64
import hashlib
import logging
from xml.etree import ElementTree as ET
from ..extensions import db
from ..models import (LegacyXmlSubmissionStage, LegacyVlookupStage,
                      LegacyAttachmentStage, LegacyReminderStage,
                      EntityMaster, Submission, QuestionnaireResponse)
from ..constants import QUESTION_CATALOG, AuditAction, SubmissionStatus
from .audit_service import AuditService

log = logging.getLogger(__name__)

# Legacy InfoPath field name -> target column. Names preserve the original
# spellings found in myschema.xsd, including 'businesssgement'.
FIELD_MAP = {
    "quarter": "QuarterLabel",
    "Yourname": "EmployeeName",
    "region": "Region",
    "businesssgement": "BusinessSegment",
    "BusinessUnit": "BusinessUnit",
    "location": "Location",
    "preparersrole": "PreparerRole",
}

QUESTION_FIELD_MAP = {code: code for code, _, _ in QUESTION_CATALOG}


class MigrationService:
    @staticmethod
    def stage_xml(file_name: str, raw_xml: str, source_library: str,
                  source_path: str | None = None) -> LegacyXmlSubmissionStage:
        row = LegacyXmlSubmissionStage(
            SourceLibrary=source_library, SourceFileName=file_name,
            SourcePath=source_path, RawXml=raw_xml, ParseStatus="Pending")
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def parse_staged(stage_row: LegacyXmlSubmissionStage) -> dict:
        """Returns a normalized dict; does not write Submission rows."""
        try:
            root = ET.fromstring(stage_row.RawXml)
        except ET.ParseError as exc:
            stage_row.ParseStatus = "Failed"
            stage_row.ParseError = str(exc)
            db.session.commit()
            raise

        values, questions, attachments = {}, {}, []
        for element in root.iter():
            tag = element.tag.split("}")[-1]
            text = (element.text or "").strip()
            if tag in FIELD_MAP:
                values[FIELD_MAP[tag]] = text
            elif tag in QUESTION_FIELD_MAP:
                questions[tag] = text
            elif text and len(text) > 512 and MigrationService._looks_base64(text):
                attachments.append({"field": tag, "data": text})

        stage_row.ParseStatus = "Parsed"
        db.session.commit()
        return {"values": values, "questions": questions,
                "attachmentFields": [a["field"] for a in attachments],
                "_attachments": attachments}

    @staticmethod
    def _looks_base64(text: str) -> bool:
        sample = text[:120].replace("\n", "").replace("\r", "")
        return all(c.isalnum() or c in "+/=" for c in sample)

    @staticmethod
    def decode_infopath_attachment(encoded: str) -> tuple[str, bytes]:
        """InfoPath base64Binary fields carry a header with the file name."""
        blob = base64.b64decode(encoded)
        if len(blob) < 24:
            raise ValueError("Attachment payload is too short to contain a header.")
        name_length = int.from_bytes(blob[20:24], "little")
        name_bytes = blob[24:24 + name_length * 2]
        file_name = name_bytes.decode("utf-16-le").rstrip("\x00")
        content = blob[24 + name_length * 2:]
        return file_name, content

    @staticmethod
    def merge_vlookup() -> dict:
        """Upsert staged Vlookup rows into EntityMaster, keyed on EntityNumber."""
        summary = {"inserted": 0, "updated": 0, "skipped": 0}
        rows = db.session.query(LegacyVlookupStage).filter(
            LegacyVlookupStage.MergeStatus == "Pending").all()
        for row in rows:
            if not (row.Title or row.EntityNumber):
                row.MergeStatus = "Skipped"
                summary["skipped"] += 1
                continue
            entity = db.session.query(EntityMaster).filter(
                EntityMaster.EntityNumber == row.EntityNumber).first() if row.EntityNumber else None
            if entity is None:
                entity = EntityMaster(Title=row.Title or row.EntityNumber)
                db.session.add(entity)
                summary["inserted"] += 1
            else:
                summary["updated"] += 1
            entity.Title = row.Title or entity.Title
            entity.EntityNumber = row.EntityNumber or entity.EntityNumber
            entity.PullName = row.PullName
            entity.SubmitName = row.SubmitName
            entity.SubmittedCode = row.SubmittedCode
            entity.LegacyListItemId = row.LegacyListItemId
            db.session.flush()
            row.MergedEntityId = entity.EntityId
            row.MergeStatus = "Merged"
        db.session.commit()
        AuditService.record("Migration", "Vlookup", AuditAction.MIGRATION_IMPORT,
                            details=summary)
        return summary

    @staticmethod
    def reconcile(period_id: int) -> dict:
        """Record-count reconciliation used in the Phase 4 parallel run."""
        staged = db.session.query(LegacyXmlSubmissionStage).count()
        parsed = db.session.query(LegacyXmlSubmissionStage).filter(
            LegacyXmlSubmissionStage.ParseStatus == "Parsed").count()
        loaded = db.session.query(Submission).filter(
            Submission.PeriodId == period_id,
            Submission.LegacyXmlFileName.isnot(None)).count()
        return {"stagedXml": staged, "parsedXml": parsed, "loadedSubmissions": loaded,
                "unreconciled": parsed - loaded}

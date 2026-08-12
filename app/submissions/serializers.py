"""JSON shapes returned by the API. Phase 2 templates consume the same shapes."""


def attachment_to_dict(a) -> dict:
    return {
        "attachmentId": a.AttachmentId,
        "fileName": a.OriginalFileName,
        "contentType": a.ContentType,
        "sizeBytes": a.FileSizeBytes,
        "uploadedBy": a.UploadedBy,
        "uploadedUtc": a.UploadedUtc.isoformat() if a.UploadedUtc else None,
        "fieldCode": a.FieldCode,
        "attestationId": a.AttestationId,
    }


def attestation_to_dict(a) -> dict:
    return {
        "attestationId": a.AttestationId,
        "type": a.AttestationType,
        "selected": a.Selected,
        "acknowledged": a.Acknowledged,
        "acknowledgedUtc": a.AcknowledgedUtc.isoformat() if a.AcknowledgedUtc else None,
        "referenceDocumentUrl": a.ReferenceDocumentUrl,
        "exceptionText": a.ExceptionText,
    }


def response_to_dict(r) -> dict:
    return {
        "responseId": r.ResponseId,
        "questionCode": r.QuestionCode,
        "questionText": r.QuestionText,
        "answer": r.Answer,
        "explanation": r.Explanation,
        "requiresExplanationWhenYes": r.RequiresExplanationWhenYes,
        "displayOrder": r.DisplayOrder,
    }


def submission_to_dict(s, summary: bool = False) -> dict:
    data = {
        "submissionId": s.SubmissionId,
        "periodId": s.PeriodId,
        "quarterLabel": s.period.QuarterLabel if s.period else None,
        "entityId": s.EntityId,
        "entityTitle": s.entity.Title if s.entity else None,
        "employeeName": s.EmployeeName,
        "employeeUpn": s.EmployeeUserPrincipalName,
        "region": s.Region,
        "businessSegment": s.BusinessSegment,
        "businessUnit": s.BusinessUnit,
        "location": s.Location,
        "preparerRole": s.PreparerRole,
        "group1Entity": s.Group1Entity,
        "group2Entity": s.Group2Entity,
        "status": s.Status,
        "submittedUtc": s.SubmittedUtc.isoformat() if s.SubmittedUtc else None,
        "isEditable": s.is_editable,
        "hasException": s.has_exception,
        "attachmentCount": len([a for a in s.attachments if not a.IsDeleted]),
        "legacyXmlFileName": s.LegacyXmlFileName,
        "lastSavedUtc": (s.ModifiedUtc or s.CreatedUtc).isoformat() if (s.ModifiedUtc or s.CreatedUtc) else None,
    }
    if summary:
        return data
    data["attestations"] = [attestation_to_dict(a) for a in s.attestations]
    data["responses"] = [response_to_dict(r) for r in
                         sorted(s.responses, key=lambda x: x.DisplayOrder)]
    data["attachments"] = [attachment_to_dict(a) for a in s.attachments if not a.IsDeleted]
    data["representatives"] = [{"name": r.RepresentativeName, "title": r.RepresentativeTitle}
                               for r in s.representatives]
    return data

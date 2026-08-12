# Entity Relationship Diagram

## Logical model

```mermaid
erDiagram
    CertificationPeriod ||--o{ Submission : "governs"
    CertificationPeriod ||--o{ ReferenceDocument : "publishes"
    CertificationPeriod ||--o{ ReminderMilestone : "schedules"
    EntityMaster        ||--o{ Submission : "certified by"
    EntityMaster        ||--o{ ReminderRecipient : "notifies for"
    EntityMaster        ||--o{ UserRole : "scopes"

    Submission ||--o{ QuestionnaireResponse : "answers"
    Submission ||--o{ Attestation : "selects"
    Submission ||--o{ Attachment : "evidences"
    Submission ||--o{ SubmissionRepresentative : "names"
    Submission ||--o{ ReminderRunLog : "chased by"
    Attestation ||--o{ Attachment : "supports"

    AppUser ||--o{ UserRole : "granted"
    Role    ||--o{ UserRole : "defines"

    ReminderTemplate  ||--o{ ReminderMilestone : "renders"
    ReminderMilestone ||--o{ ReminderRecipient : "targets"
    ReminderMilestone ||--o{ ReminderRunLog : "records"

    CertificationPeriod {
        int  PeriodId PK
        nvarchar QuarterLabel
        int  FiscalYear
        int  QuarterNumber
        date StartDate
        date DueDate
        bit  IsOpen
        bit  Enable404
        bit  IsArchived
    }

    EntityMaster {
        int  EntityId PK
        nvarchar Title
        nvarchar EntityNumber
        nvarchar PullName
        nvarchar SubmitName
        nvarchar SubmittedCode
        nvarchar Region
        nvarchar BusinessSegment
        nvarchar BusinessUnit
        nvarchar Location
        bit  IsGroup1
        bit  IsGroup2
        bit  IsActive
        int  LegacyListItemId
    }

    Submission {
        bigint SubmissionId PK
        int    PeriodId FK
        int    EntityId FK
        nvarchar EmployeeName
        nvarchar EmployeeUserPrincipalName
        nvarchar Region
        nvarchar BusinessSegment
        nvarchar BusinessUnit
        nvarchar Location
        nvarchar PreparerRole
        bit      Group1Entity
        bit      Group2Entity
        decimal  ExceptionAmount
        nvarchar Status
        nvarchar LegacyXmlFileName
        nvarchar LegacyXmlPath
        datetime2 SubmittedUtc
        datetime2 ArchivedUtc
        int      RowVersion
    }

    QuestionnaireResponse {
        bigint ResponseId PK
        bigint SubmissionId FK
        nvarchar QuestionCode
        nvarchar QuestionText
        bit      Answer
        nvarchar Explanation
        bit      RequiresExplanationWhenYes
        int      DisplayOrder
    }

    Attestation {
        bigint AttestationId PK
        bigint SubmissionId FK
        nvarchar AttestationType
        bit      Selected
        bit      Acknowledged
        nvarchar AcknowledgedBy
        datetime2 AcknowledgedUtc
        nvarchar ReferenceDocumentUrl
        nvarchar ExceptionText
    }

    Attachment {
        bigint AttachmentId PK
        bigint SubmissionId FK
        bigint AttestationId FK
        nvarchar OriginalFileName
        nvarchar GraphDriveId
        nvarchar GraphItemId
        nvarchar StorageUrl
        bigint   FileSizeBytes
        nvarchar Sha256
        bit      IsDeleted
    }

    AppUser {
        int UserId PK
        nvarchar ObjectId
        nvarchar UserPrincipalName
        nvarchar DisplayName
        bit IsActive
        datetime2 LastLoginUtc
    }

    UserRole {
        int UserRoleId PK
        int UserId FK
        int RoleId FK
        nvarchar ScopeRegion
        nvarchar ScopeBusinessUnit
        int      ScopeEntityId FK
        bit      IsActive
    }

    AuditLog {
        bigint AuditLogId PK
        nvarchar EntityName
        nvarchar EntityKey
        nvarchar Action
        nvarchar Actor
        datetime2 EventUtc
        nvarchar BeforeJson
        nvarchar AfterJson
    }
```

## Migration staging (isolated — no FK to the operational schema)

```mermaid
erDiagram
    LegacyXmlSubmissionStage ||--o{ LegacyAttachmentStage : "yields"
    LegacyVlookupStage  }o--|| EntityMaster : "merges into"
    LegacyReminderStage }o--|| ReminderMilestone : "maps to"
    LegacyXmlSubmissionStage }o--|| Submission : "loads into"

    LegacyXmlSubmissionStage {
        bigint StageId PK
        nvarchar SourceLibrary
        nvarchar SourceFileName
        nvarchar SourcePath
        nvarchar RawXml
        nvarchar ParseStatus
        nvarchar ParseError
        bigint   MappedSubmissionId
    }
    LegacyVlookupStage {
        int StageId PK
        nvarchar Title
        nvarchar EntityNumber
        nvarchar MergeStatus
        int MergedEntityId
    }
    LegacyAttachmentStage {
        bigint StageId PK
        bigint XmlStageId
        nvarchar FieldName
        nvarchar DecodedFileName
        nvarchar ExtractStatus
        nvarchar GraphItemId
    }
    LegacyReminderStage {
        int StageId PK
        nvarchar Title
        datetime2 ReminderDate
        nvarchar MapStatus
        int MappedMilestoneId
    }
```

## Cardinality notes

| Relationship | Rule |
|---|---|
| CertificationPeriod → Submission | One open period may hold many submissions; a submission belongs to exactly one period. |
| EntityMaster → Submission | Optional (`EntityId` is nullable) so a legacy XML row with an unmatched entity still imports rather than failing. |
| Submission → QuestionnaireResponse | Exactly 10 rows seeded at draft creation, plus 1 threshold row per applicable group. |
| Submission → Attestation | One row per available module (4 normally, 5 when `Enable404`), each with its own `Selected` / `Acknowledged` flags. |
| Attestation → Attachment | Optional — evidence can attach to the submission generally or to a specific module. |
| UserRole scope columns | All NULL = unscoped grant. Any populated column narrows the reviewer's row-level visibility. |

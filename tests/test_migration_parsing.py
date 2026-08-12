"""Legacy XML field mapping."""
from app.services.migration_service import MigrationService, FIELD_MAP

SAMPLE_XML = """<?xml version="1.0"?>
<my:myFields xmlns:my="http://schemas.microsoft.com/office/infopath/2003/myXSD">
  <my:quarter>Q1 2026</my:quarter>
  <my:Yourname>Vikash Pandey</my:Yourname>
  <my:region>North America</my:region>
  <my:businesssgement>Electrical</my:businesssgement>
  <my:BusinessUnit>Conduit</my:BusinessUnit>
  <my:location>Mokena</my:location>
  <my:preparersrole>Controller</my:preparersrole>
  <my:ORG_CHANGE>false</my:ORG_CHANGE>
  <my:FRAUD_INDICATORS>true</my:FRAUD_INDICATORS>
</my:myFields>"""


def test_field_map_covers_every_legacy_header_field():
    assert set(FIELD_MAP) == {"quarter", "Yourname", "region", "businesssgement",
                              "BusinessUnit", "location", "preparersrole"}


def test_parse_extracts_header_and_questions(app):
    with app.app_context():
        stage = MigrationService.stage_xml("form_2026-01-15.xml", SAMPLE_XML,
                                           "Submitted Forms")
        parsed = MigrationService.parse_staged(stage)
        assert parsed["values"]["EmployeeName"] == "Vikash Pandey"
        assert parsed["values"]["BusinessSegment"] == "Electrical"
        assert parsed["values"]["PreparerRole"] == "Controller"
        assert parsed["questions"]["FRAUD_INDICATORS"] == "true"
        assert stage.ParseStatus == "Parsed"


def test_malformed_xml_is_marked_failed(app):
    with app.app_context():
        stage = MigrationService.stage_xml("broken.xml", "<my:myFields>", "Submitted Forms")
        try:
            MigrationService.parse_staged(stage)
        except Exception:
            pass
        assert stage.ParseStatus == "Failed"
        assert stage.ParseError

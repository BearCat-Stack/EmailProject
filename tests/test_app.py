import json

from app import _normalize_payload, _parse_form_body, _render_page, _validate


def test_render_page_contains_title():
    html = _render_page(
        {
            "name": "",
            "firm": "",
            "role": "",
            "raw_background": "",
            "firm_info": "N/A",
            "email": "Unknown",
            "major": "Finance",
        }
    )
    assert "Finance Outreach Generator" in html


def test_validation_errors_for_missing_required_fields():
    data = _normalize_payload({"name": "Only Name"})
    errors = _validate(data)
    assert "Firm is required." in errors
    assert "Role is required." in errors


def test_parse_form_body_round_trip():
    payload = "name=Jordan+Lee&firm=Apex+Capital&role=Associate&raw_background=Executes+deals"
    parsed = _parse_form_body(payload.encode("utf-8"))
    assert parsed["name"] == "Jordan Lee"
    assert parsed["firm"] == "Apex Capital"


def test_normalize_payload_defaults():
    data = _normalize_payload(
        {
            "name": "Jordan",
            "firm": "Apex",
            "role": "Associate",
            "raw_background": "Deal execution",
        }
    )
    assert data.email == "Unknown"
    assert data.firm_info == "N/A"


def test_render_page_escapes_user_content():
    html = _render_page(
        {
            "name": "<script>",
            "firm": "A",
            "role": "B",
            "raw_background": "C",
            "firm_info": "N/A",
            "email": "Unknown",
            "major": "Finance",
        },
        output=json.dumps({"unsafe": "<tag>"}),
    )
    assert "&lt;script&gt;" in html
    assert "&lt;tag&gt;" in html

import re
import json
from pathlib import Path

import pytest

from finance_outreach_generator import (
    OutreachInput,
    build_email,
    build_firm_insight,
    build_sheet_row,
    generate_output,
    _from_json,
    _validate_required_fields,
    write_sheet_csv,
)


def test_generate_output_sections_present():
    data = OutreachInput(
        name="Jordan Lee",
        firm="Apex Capital Partners",
        role="Senior Associate, Private Equity",
        raw_background=(
            "Leads deal execution and underwriting for lower middle-market industrials. "
            "Previously at Houlihan Lokey. Closed 12+ transactions and supports a $1.2bn AUM strategy."
        ),
        firm_info="control buyouts in industrial and business services with EBITDA $5-25m",
        email="Unknown",
        major="Finance and Statistics",
    )

    output = generate_output(data)

    assert "Key Insights:" in output
    assert "Firm Insight:" in output
    assert "Subject Line Options:" in output
    assert "Email:" in output
    assert "Possible Email Formats:" in output


def test_email_constraints_respected():
    data = OutreachInput(
        name="Taylor Morgan",
        firm="Northbridge Credit",
        role="Vice President, Direct Lending",
        raw_background="Focuses on origination, underwriting, and portfolio monitoring across sponsor-backed loans.",
    )
    firm_insight = build_firm_insight(data)
    email = build_email(data, firm_insight)

    assert "—" not in email
    # Word count excludes line breaks.
    assert len(re.findall(r"\S+", email)) <= 180


def test_from_json_loader(tmp_path: Path):
    payload = {
        "name": "Casey Park",
        "firm": "North Peak Capital",
        "role": "Associate",
        "raw_background": "Supports due diligence and portfolio work.",
    }
    file_path = tmp_path / "input.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = _from_json(str(file_path))
    assert loaded.name == "Casey Park"
    assert loaded.firm_info == "N/A"
    assert loaded.email == "Unknown"


def test_validate_required_fields_raises_without_json():
    class Args:
        input_json = None
        name = "Jordan"
        firm = None
        role = "Associate"
        raw_background = None

    with pytest.raises(SystemExit):
        _validate_required_fields(Args())


def test_sheet_csv_writer_outputs_headers_and_row(tmp_path: Path):
    data = OutreachInput(
        name="Morgan Tate",
        firm="Bluewater Partners",
        role="Investment Associate",
        raw_background="Supports origination and due diligence across industrial deals.",
        email="Unknown",
    )
    output_file = tmp_path / "row.csv"
    write_sheet_csv([build_sheet_row(data)], output_path=str(output_file))

    content = output_file.read_text(encoding="utf-8")
    assert "name,firm,role,source_email" in content
    assert "Morgan Tate" in content
    assert "Bluewater Partners" in content

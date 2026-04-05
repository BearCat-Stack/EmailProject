#!/usr/bin/env python3
"""Generate tailored finance networking outreach from messy profile data."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from textwrap import shorten


@dataclass
class OutreachInput:
    name: str
    firm: str
    role: str
    raw_background: str
    firm_info: str = "N/A"
    email: str = "Unknown"
    major: str = "Finance"


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_metrics(raw_background: str) -> list[str]:
    patterns = [
        r"\$\s?\d+[\d,.]*(?:\s?(?:bn|b|million|m))?",
        r"\d+[\d,.]*\s?(?:bn|b|million|m)\s?(?:aum|fund|enterprise value|ev|ebitda)",
        r"EBITDA\s?(?:range|of)?\s?\$?\d+[\d,.]*\s?-\s?\$?\d+[\d,.]*",
        r"\d+\+?\s?(?:transactions|deals|investments)",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, raw_background, flags=re.IGNORECASE):
            metric = _clean_text(match)
            if metric.lower() not in {m.lower() for m in found}:
                found.append(metric)
    return found[:3]


def _extract_responsibilities(raw_background: str) -> list[str]:
    catalog = {
        "origination": ["origination", "sourcing", "pipeline"],
        "execution": ["execution", "due diligence", "modeling", "underwriting"],
        "investing": ["investing", "investment committee", "portfolio construction"],
        "coverage": ["coverage", "relationship", "advisory"],
        "portfolio management": ["portfolio", "value creation", "board"],
    }
    lower_text = raw_background.lower()
    hits = [label for label, keys in catalog.items() if any(k in lower_text for k in keys)]
    return hits[:3] if hits else ["deal evaluation and transaction support"]


def _extract_trajectory(raw_background: str) -> str:
    snippets = re.findall(
        r"(?:previously|former|before|prior to)\s+(?:at\s+)?([A-Z][A-Za-z0-9&.,\- ]{2,60})",
        raw_background,
        flags=re.IGNORECASE,
    )
    if snippets:
        unique = []
        for s in snippets:
            clean = _clean_text(s).rstrip(".,;")
            if clean.lower() not in {u.lower() for u in unique}:
                unique.append(clean)
        return "Career path includes prior experience at " + ", ".join(unique[:2]) + "."
    return "Background suggests progression through increasingly transaction-focused investing roles."


def build_key_insights(data: OutreachInput) -> list[str]:
    metrics = _extract_metrics(data.raw_background)
    responsibilities = _extract_responsibilities(data.raw_background)
    clean_role = _clean_text(data.role)

    bullet_1 = (
        f"{data.name} is currently {clean_role} at {data.firm}, with seniority aligned to front-office investment decision-making."
    )
    bullet_2 = (
        "Core responsibilities appear centered on "
        + ", ".join(responsibilities)
        + ", based on available background details."
    )
    bullet_3 = _extract_trajectory(data.raw_background)
    if metrics:
        bullet_3 += " Notable metrics mentioned include " + ", ".join(metrics) + "."

    return [bullet_1, bullet_2, bullet_3]


def build_firm_insight(data: OutreachInput) -> str:
    if data.firm_info.strip() and data.firm_info.strip().lower() != "n/a":
        return f"{data.firm} appears focused on {data.firm_info.strip()}, suggesting a disciplined strategy tied to risk-adjusted returns."

    role_lower = data.role.lower()
    firm_lower = data.firm.lower()
    if any(k in role_lower for k in ["private equity", "buyout", "investor"]):
        strategy = "middle-market buyouts and active ownership"
    elif any(k in role_lower for k in ["credit", "direct lending", "debt"]):
        strategy = "private credit with downside protection and structured yield"
    elif "growth" in role_lower:
        strategy = "growth equity in scaling businesses"
    elif any(k in firm_lower for k in ["capital", "partners"]):
        strategy = "private markets investing across control or structured opportunities"
    else:
        strategy = "institutional investing driven by sector and deal discipline"

    return (
        f"Assumption: {data.firm} is likely pursuing {strategy}, based on the role and firm naming context."
    )


def build_subject_lines(data: OutreachInput) -> list[str]:
    first_name = data.name.split()[0]
    return [
        f"Baruch sophomore with DB IB offer | Quick question on {data.firm}",
        f"{first_name}, your {data.firm} investing path stood out",
        f"15-min chat request: Baruch student headed to Deutsche Bank IB",
    ]


def _targeted_reference(data: OutreachInput) -> str:
    role_ref = shorten(_clean_text(data.role), width=65, placeholder="...")
    raw_ref = _clean_text(data.raw_background)
    if raw_ref:
        primary_clause = re.split(r"[.;]", raw_ref)[0].strip()
        if primary_clause:
            first_fact = shorten(primary_clause, width=115, placeholder="...")
        else:
            first_fact = shorten(raw_ref, width=115, placeholder="...")
        return (
            f"Your work as {role_ref} caught my attention, especially your focus on {first_fact.lower()}"
        )
    return f"Your work as {role_ref} caught my attention given the mix of investing judgment and execution required."


def build_email(data: OutreachInput, firm_insight: str) -> str:
    p1 = (
        f"Hi {data.name}, I’m a sophomore at Baruch College majoring in {data.major}, and I accepted a Deutsche Bank Investment Banking offer for next summer. "
        f"I’m reaching out because your path at {data.firm} is exactly the kind of investing trajectory I’m trying to learn from."
    )

    p2 = (
        _targeted_reference(data)
        + ". "
        + f"I also appreciate how your role combines investor conviction with hands-on transaction work. "
        + firm_insight
    )

    p3 = (
        "If you’re open to it, I’d really value 15-20 minutes to hear how you built your perspective and what you look for in junior talent. "
        "If your team hires off-cycle or for summer roles, I’d also appreciate any guidance on how to position myself."
    )

    email = "\n\n".join([p1, p2, p3, "Best,\n[Your Name]"])
    email = email.replace("—", "-")

    words = email.split()
    if len(words) > 180:
        # Trim paragraph two first to preserve intent.
        trimmed_p2 = shorten(p2, width=320, placeholder="...")
        email = "\n\n".join([p1, trimmed_p2, p3, "Best,\n[Your Name]"])
    return email


def guess_email_formats(data: OutreachInput) -> list[str]:
    if data.email.strip().lower() != "unknown":
        return []

    domain = re.sub(r"[^a-z0-9]+", "", data.firm.lower()) + ".com"
    parts = [p.lower() for p in re.split(r"\s+", data.name.strip()) if p]
    if not parts:
        return []
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    first_initial = first[0]

    formats = [
        f"{first}.{last}@{domain}" if last else f"{first}@{domain}",
        f"{first_initial}{last}@{domain}" if last else f"{first}@{domain}",
        f"{first}@{domain}",
    ]
    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for item in formats:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique[:3]


def generate_output(data: OutreachInput) -> str:
    key_insights = build_key_insights(data)
    firm_insight = build_firm_insight(data)
    subject_lines = build_subject_lines(data)
    email = build_email(data, firm_insight)
    formats = guess_email_formats(data)

    lines = [
        "Key Insights:",
        f"- {key_insights[0]}",
        f"- {key_insights[1]}",
        f"- {key_insights[2]}",
        "",
        "Firm Insight:",
        f"- {firm_insight}",
        "",
        "Subject Line Options:",
        f"1. {subject_lines[0]}",
        f"2. {subject_lines[1]}",
        f"3. {subject_lines[2]}",
        "",
        "Email:",
        email,
    ]

    if formats:
        lines.extend([
            "",
            "Possible Email Formats:",
            f"- {formats[0]}",
            f"- {formats[1] if len(formats) > 1 else formats[0]}",
            f"- {formats[2] if len(formats) > 2 else formats[-1]}",
        ])

    return "\n".join(lines)


def build_sheet_row(data: OutreachInput) -> dict[str, str]:
    key_insights = build_key_insights(data)
    firm_insight = build_firm_insight(data)
    subject_lines = build_subject_lines(data)
    email = build_email(data, firm_insight)
    formats = guess_email_formats(data)

    return {
        "name": data.name,
        "firm": data.firm,
        "role": data.role,
        "source_email": data.email,
        "key_insight_1": key_insights[0],
        "key_insight_2": key_insights[1],
        "key_insight_3": key_insights[2],
        "firm_insight": firm_insight,
        "subject_line_1": subject_lines[0],
        "subject_line_2": subject_lines[1],
        "subject_line_3": subject_lines[2],
        "email_body": email,
        "possible_email_formats": "; ".join(formats),
    }


def sheet_columns() -> list[str]:
    return [
        "name",
        "firm",
        "role",
        "source_email",
        "key_insight_1",
        "key_insight_2",
        "key_insight_3",
        "firm_insight",
        "subject_line_1",
        "subject_line_2",
        "subject_line_3",
        "email_body",
        "possible_email_formats",
    ]


def write_sheet_csv(rows: list[dict[str, str]], output_path: str | None = None) -> None:
    destination = open(output_path, "w", encoding="utf-8", newline="") if output_path else sys.stdout
    try:
        writer = csv.DictWriter(destination, fieldnames=sheet_columns())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        if output_path:
            destination.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate personalized finance outreach drafts.")
    parser.add_argument("--name")
    parser.add_argument("--firm")
    parser.add_argument("--role")
    parser.add_argument("--raw-background")
    parser.add_argument("--firm-info", default="N/A")
    parser.add_argument("--email", default="Unknown")
    parser.add_argument("--major", default="Finance")
    parser.add_argument(
        "--input-json",
        help="Path to a JSON file with keys: name, firm, role, raw_background, firm_info, email, major.",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "csv"],
        default="text",
        help="Choose 'text' for email-ready output or 'csv' for Google Sheets-friendly export.",
    )
    parser.add_argument(
        "--output-path",
        help="Optional path for CSV output. If omitted in CSV mode, prints CSV to stdout.",
    )
    return parser.parse_args()


def _from_json(path: str) -> OutreachInput:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return OutreachInput(
        name=payload["name"],
        firm=payload["firm"],
        role=payload["role"],
        raw_background=payload["raw_background"],
        firm_info=payload.get("firm_info", "N/A"),
        email=payload.get("email", "Unknown"),
        major=payload.get("major", "Finance"),
    )


def _validate_required_fields(args: argparse.Namespace) -> None:
    if args.input_json:
        return

    required_fields = {
        "name": args.name,
        "firm": args.firm,
        "role": args.role,
        "raw_background": args.raw_background,
    }
    missing = [field for field, value in required_fields.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required arguments: "
            + ", ".join(missing)
            + ". Provide these flags or use --input-json."
        )


def main() -> None:
    args = parse_args()
    _validate_required_fields(args)

    if args.input_json:
        data = _from_json(args.input_json)
    else:
        data = OutreachInput(
            name=args.name,
            firm=args.firm,
            role=args.role,
            raw_background=args.raw_background,
            firm_info=args.firm_info,
            email=args.email,
            major=args.major,
        )
    if args.output_format == "csv":
        write_sheet_csv([build_sheet_row(data)], output_path=args.output_path)
        return

    print(generate_output(data))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Minimal web app (no external dependencies) for finance outreach generation."""

from __future__ import annotations

import csv
import html
import io
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from finance_outreach_generator import OutreachInput, build_sheet_row, generate_output


HTML_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Finance Outreach App</title>
    <style>
      body {{ font-family: Arial, sans-serif; background:#f7f8fa; margin:0; }}
      .container {{ max-width: 980px; margin: 24px auto; background:#fff; padding: 24px; border-radius: 8px; }}
      h1 {{ margin-top:0; }}
      .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
      label {{ display:block; font-weight:600; margin-bottom:4px; }}
      input, textarea {{ width:100%; padding:10px; border:1px solid #d0d4da; border-radius:6px; box-sizing:border-box; }}
      textarea {{ min-height:120px; }}
      .full {{ grid-column: 1 / -1; }}
      .actions {{ margin-top: 12px; display:flex; gap:10px; }}
      button {{ padding:10px 14px; border:none; border-radius:6px; background:#1f4ed8; color:white; cursor:pointer; }}
      button.secondary {{ background:#0f766e; }}
      .errors {{ background:#fff1f2; border:1px solid #fecdd3; color:#9f1239; padding:10px; border-radius:6px; margin-bottom:12px; }}
      pre {{ white-space:pre-wrap; background:#0b1020; color:#e2e8f0; padding:16px; border-radius:8px; }}
      @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Finance Outreach Generator</h1>
      <p>Paste raw profile notes and generate a personalized outreach email package.</p>

      {errors_html}

      <form method="post" action="/generate">
        <div class="grid">
          <div>
            <label for="name">Name</label>
            <input id="name" name="name" value="{name}" required />
          </div>
          <div>
            <label for="firm">Firm</label>
            <input id="firm" name="firm" value="{firm}" required />
          </div>
          <div>
            <label for="role">Role</label>
            <input id="role" name="role" value="{role}" required />
          </div>
          <div>
            <label for="major">Major</label>
            <input id="major" name="major" value="{major}" />
          </div>
          <div>
            <label for="email">Email</label>
            <input id="email" name="email" value="{email}" />
          </div>
          <div>
            <label for="firm_info">Firm Info</label>
            <input id="firm_info" name="firm_info" value="{firm_info}" />
          </div>
          <div class="full">
            <label for="raw_background">Raw Background</label>
            <textarea id="raw_background" name="raw_background" required>{raw_background}</textarea>
          </div>
        </div>
        <div class="actions">
          <button type="submit">Generate</button>
          <button class="secondary" type="submit" formaction="/download-csv">Download CSV Row</button>
        </div>
      </form>

      {output_html}
    </div>
  </body>
</html>
"""


def _normalize_payload(payload: dict[str, str]) -> OutreachInput:
    return OutreachInput(
        name=payload.get("name", "").strip(),
        firm=payload.get("firm", "").strip(),
        role=payload.get("role", "").strip(),
        raw_background=payload.get("raw_background", "").strip(),
        firm_info=(payload.get("firm_info", "N/A") or "N/A").strip(),
        email=(payload.get("email", "Unknown") or "Unknown").strip(),
        major=(payload.get("major", "Finance") or "Finance").strip(),
    )


def _validate(data: OutreachInput) -> list[str]:
    errors = []
    if not data.name:
        errors.append("Name is required.")
    if not data.firm:
        errors.append("Firm is required.")
    if not data.role:
        errors.append("Role is required.")
    if not data.raw_background:
        errors.append("Raw Background is required.")
    return errors


def _render_page(form: dict[str, str], output: str | None = None, errors: list[str] | None = None) -> str:
    errors = errors or []
    errors_html = ""
    if errors:
        list_items = "".join(f"<li>{html.escape(e)}</li>" for e in errors)
        errors_html = f"<div class=\"errors\"><ul>{list_items}</ul></div>"

    output_html = ""
    if output:
        output_html = f"<h2>Generated Output</h2><pre>{html.escape(output)}</pre>"

    escaped_form = {k: html.escape(v) for k, v in form.items()}
    return HTML_PAGE.format(errors_html=errors_html, output_html=output_html, **escaped_form)


def _parse_form_body(raw_body: bytes) -> dict[str, str]:
    parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in parsed.items()}


class OutreachHandler(BaseHTTPRequestHandler):
    def _send_text(self, content: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        form = {
            "name": "",
            "firm": "",
            "role": "",
            "raw_background": "",
            "firm_info": "N/A",
            "email": "Unknown",
            "major": "Finance",
        }
        self._send_text(_render_page(form))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        if self.path == "/api/generate":
            self._handle_api_generate(body)
        elif self.path == "/generate":
            self._handle_generate(body)
        elif self.path == "/download-csv":
            self._handle_download_csv(body)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def _handle_generate(self, body: bytes) -> None:
        payload = _parse_form_body(body)
        data = _normalize_payload(payload)
        errors = _validate(data)
        if errors:
            self._send_text(_render_page(payload, errors=errors), status=400)
            return

        output = generate_output(data)
        self._send_text(_render_page(payload, output=output))

    def _handle_download_csv(self, body: bytes) -> None:
        payload = _parse_form_body(body)
        data = _normalize_payload(payload)
        errors = _validate(data)
        if errors:
            self._send_text(json.dumps({"errors": errors}), status=400, content_type="application/json")
            return

        row = build_sheet_row(data)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

        csv_data = buffer.getvalue().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=outreach_row.csv")
        self.send_header("Content-Length", str(len(csv_data)))
        self.end_headers()
        self.wfile.write(csv_data)

    def _handle_api_generate(self, body: bytes) -> None:
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._send_text(json.dumps({"errors": ["Invalid JSON payload."]}), status=400, content_type="application/json")
            return

        data = _normalize_payload(payload)
        errors = _validate(data)
        if errors:
            self._send_text(json.dumps({"errors": errors}), status=400, content_type="application/json")
            return

        response = {
            "text_output": generate_output(data),
            "sheet_row": build_sheet_row(data),
        }
        self._send_text(json.dumps(response), content_type="application/json")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), OutreachHandler)
    print(f"Finance Outreach web app running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

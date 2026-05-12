from __future__ import annotations

from html import escape
from pathlib import Path

from .models import AnalyticsResult

try:
    from fpdf import FPDF  # type: ignore[import-untyped]

    _FPDF_AVAILABLE = True
except ModuleNotFoundError:
    _FPDF_AVAILABLE = False


def write_markdown_report(result: AnalyticsResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(result.report_markdown, encoding="utf-8")
    return path


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines: list[str] = ["<html><body>"]
    in_list = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{escape(line)}</p>")

    if in_list:
        html_lines.append("</ul>")
    html_lines.append("</body></html>")
    return "\n".join(html_lines)


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    if not _FPDF_AVAILABLE:
        raise RuntimeError("fpdf2 is not installed. Run: pip install fpdf2")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(left=20, top=20, right=20)

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(3)
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.multi_cell(0, 9, line[2:])
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", style="B", size=13)
            pdf.multi_cell(0, 8, line[3:])
            pdf.ln(1)
        elif line.startswith("- "):
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 7, f"*  {line[2:]}")
        else:
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 7, line)

    return bytes(pdf.output())

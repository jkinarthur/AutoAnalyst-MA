from __future__ import annotations

from pathlib import Path

from .models import AnalyticsResult


def write_markdown_report(result: AnalyticsResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(result.report_markdown, encoding="utf-8")
    return path

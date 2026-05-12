from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class DatasetProfile:
    row_count: int
    column_count: int
    missing_values: int
    duplicate_rows: int
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalyticsResult:
    profile: DatasetProfile
    cleaned_data: pd.DataFrame
    insights: list[str]
    charts: dict[str, dict[str, Any]] = field(default_factory=dict)
    report_markdown: str = ""

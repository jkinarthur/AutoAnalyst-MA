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
class AgentTraceEntry:
    agent: str
    action: str


@dataclass(slots=True)
class BusinessContext:
    objective: str
    recommended_kpis: list[str] = field(default_factory=list)
    recommended_analyses: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationIssue:
    category: str
    severity: str
    message: str


@dataclass(slots=True)
class ValidationSummary:

    confidence_score: float
    confidence_level: str
    checks: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass(slots=True)
class AnalyticsResult:
    profile: DatasetProfile
    cleaned_data: pd.DataFrame
    insights: list[str]
    charts: dict[str, dict[str, Any]] = field(default_factory=dict)
    report_markdown: str = ""
    agent_trace: list[AgentTraceEntry] = field(default_factory=list)
    business_context: BusinessContext | None = None
    validation_summary: ValidationSummary | None = None

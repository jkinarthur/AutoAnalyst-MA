from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    row_count: int
    column_count: int
    missing_values: int
    duplicate_rows: int
    numeric_columns: list[str] = Field(default_factory=list)
    categorical_columns: list[str] = Field(default_factory=list)


class AgentTraceSchema(BaseModel):
    agent: str
    action: str


class BusinessContextSchema(BaseModel):
    objective: str
    recommended_kpis: list[str] = Field(default_factory=list)
    recommended_analyses: list[str] = Field(default_factory=list)


class ValidationIssueSchema(BaseModel):
    category: str
    severity: str
    message: str


class ValidationSummarySchema(BaseModel):
    confidence_score: float
    confidence_level: Literal["high", "medium", "low"]
    checks: list[str] = Field(default_factory=list)
    issues: list[ValidationIssueSchema] = Field(default_factory=list)


class PipelineSummarySchema(BaseModel):
    preprocessing_steps: list[str] = Field(default_factory=list)
    eda_summary: dict[str, Any] = Field(default_factory=dict)


class AnalysisPayloadSchema(BaseModel):
    profile: ProfileSchema
    insights: list[str] = Field(default_factory=list)
    charts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    report_markdown: str
    agent_trace: list[AgentTraceSchema] = Field(default_factory=list)
    business_context: BusinessContextSchema | None = None
    validation_summary: ValidationSummarySchema | None = None
    pipeline_summary: PipelineSummarySchema | None = None
    preview: list[dict[str, Any]] = Field(default_factory=list)


class AnalyzeResponseSchema(AnalysisPayloadSchema):
    run_id: str
    created_at: str


class RunListItemSchema(BaseModel):
    run_id: str
    created_at: str
    filename: str


class RunListResponseSchema(BaseModel):
    runs: list[RunListItemSchema] = Field(default_factory=list)


class StoredRunResponseSchema(AnalysisPayloadSchema):
    run_id: str
    created_at: str
    filename: str
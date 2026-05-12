from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

from .models import (
    AgentTraceEntry,
    AnalyticsResult,
    BusinessContext,
    DatasetProfile,
    ValidationIssue,
    ValidationSummary,
)


class ProfileAgent(Protocol):
    def profile(self, data_frame: pd.DataFrame) -> DatasetProfile:
        ...


class CleaningAgent(Protocol):
    def clean(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        ...


class BusinessUnderstandingAgent(Protocol):
    def derive_business_context(
        self,
        objective: str | None,
        profile: DatasetProfile,
    ) -> BusinessContext:
        ...


class InsightAgent(Protocol):
    def generate_insights(
        self,
        cleaned_data: pd.DataFrame,
        profile: DatasetProfile,
    ) -> list[str]:
        ...


class VisualizationAgent(Protocol):
    def build_chart_specs(self, cleaned_data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        ...


class ValidationAgent(Protocol):
    def validate(
        self,
        cleaned_data: pd.DataFrame,
        profile: DatasetProfile,
        insights: list[str],
        business_context: BusinessContext,
    ) -> ValidationSummary:
        ...


class ReportAgent(Protocol):
    def build_report(
        self,
        profile: DatasetProfile,
        insights: list[str],
        charts: dict[str, dict[str, Any]],
    ) -> str:
        ...


@dataclass(slots=True)
class DefaultProfileAgent:
    pipeline: Any

    def profile(self, data_frame: pd.DataFrame) -> DatasetProfile:
        return self.pipeline.profile(data_frame)


@dataclass(slots=True)
class DefaultCleaningAgent:
    pipeline: Any

    def clean(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        return self.pipeline.clean(data_frame)


@dataclass(slots=True)
class DefaultBusinessUnderstandingAgent:
    def derive_business_context(
        self,
        objective: str | None,
        profile: DatasetProfile,
    ) -> BusinessContext:
        normalized = (objective or "general performance overview").strip().lower()
        if "churn" in normalized:
            return BusinessContext(
                objective=objective or "Analyze customer churn risk",
                recommended_kpis=["churn_rate", "retention_rate", "customer_lifetime_value"],
                recommended_analyses=["cohort_analysis", "classification", "feature_importance"],
            )
        if "fraud" in normalized or "suspicious" in normalized:
            return BusinessContext(
                objective=objective or "Detect suspicious transactions",
                recommended_kpis=["fraud_rate", "false_positive_rate", "investigation_volume"],
                recommended_analyses=["anomaly_detection", "classification", "time_series_spike_detection"],
            )
        if "sales" in normalized or "revenue" in normalized:
            return BusinessContext(
                objective=objective or "Analyze sales performance",
                recommended_kpis=["revenue", "average_order_value", "conversion_rate"],
                recommended_analyses=["trend_analysis", "segmentation", "forecasting"],
            )

        fallback_kpis = ["row_count", "missing_value_rate"]
        if profile.numeric_columns:
            fallback_kpis.append(f"mean_{profile.numeric_columns[0]}")
        return BusinessContext(
            objective=objective or "General data health and performance overview",
            recommended_kpis=fallback_kpis,
            recommended_analyses=["descriptive_statistics", "distribution_analysis"],
        )


@dataclass(slots=True)
class DefaultInsightAgent:
    pipeline: Any

    def generate_insights(
        self,
        cleaned_data: pd.DataFrame,
        profile: DatasetProfile,
    ) -> list[str]:
        return self.pipeline.generate_insights(cleaned_data, profile)


@dataclass(slots=True)
class DefaultVisualizationAgent:
    pipeline: Any

    def build_chart_specs(self, cleaned_data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        return self.pipeline.build_chart_specs(cleaned_data)


@dataclass(slots=True)
class DefaultValidationAgent:
    def validate(
        self,
        cleaned_data: pd.DataFrame,
        profile: DatasetProfile,
        insights: list[str],
        business_context: BusinessContext,
    ) -> ValidationSummary:
        checks: list[str] = []
        issues: list[ValidationIssue] = []
        score = 0.85

        total_cells = max(profile.row_count * profile.column_count, 1)
        missing_ratio = profile.missing_values / total_cells
        if missing_ratio > 0.10:
            score -= 0.10
            issues.append(
                ValidationIssue(
                    category="data_quality",
                    severity="medium",
                    message="High missing-value ratio in raw data may reduce confidence.",
                )
            )
        checks.append(f"Missing-value ratio checked: {missing_ratio:.2%}")

        if profile.row_count < 30:
            score -= 0.15
            issues.append(
                ValidationIssue(
                    category="statistical_weakness",
                    severity="high",
                    message="Small sample size detected; insights may be unstable.",
                )
            )
        checks.append(f"Sample size checked: {profile.row_count} rows")

        if not profile.numeric_columns:
            score -= 0.10
            issues.append(
                ValidationIssue(
                    category="statistical_weakness",
                    severity="medium",
                    message="No numeric columns detected; statistical depth is limited.",
                )
            )
        checks.append("Feature-type coverage checked")

        objective_text = business_context.objective.lower()
        insights_text = " ".join(insights).lower()
        if "churn" in objective_text and "churn" not in insights_text:
            score -= 0.10
            issues.append(
                ValidationIssue(
                    category="objective_mismatch",
                    severity="medium",
                    message="Objective mentions churn but generated insights do not reference churn directly.",
                )
            )
        if "fraud" in objective_text and "fraud" not in insights_text and "anomal" not in insights_text:
            score -= 0.10
            issues.append(
                ValidationIssue(
                    category="objective_mismatch",
                    severity="medium",
                    message="Objective mentions fraud but insights lack fraud or anomaly-specific language.",
                )
            )
        if "sales" in objective_text and "revenue" not in insights_text and "sales" not in insights_text:
            score -= 0.10
            issues.append(
                ValidationIssue(
                    category="objective_mismatch",
                    severity="medium",
                    message="Objective mentions sales but insights lack sales or revenue-specific language.",
                )
            )
        if "churn" in objective_text and "fraud" in insights_text:
            score -= 0.05
            issues.append(
                ValidationIssue(
                    category="contradiction",
                    severity="low",
                    message="Insights mention fraud while objective focuses on churn.",
                )
            )
        checks.append("Objective alignment checked")

        score = max(0.10, min(0.99, score))
        if score >= 0.80:
            level = "high"
        elif score >= 0.60:
            level = "medium"
        else:
            level = "low"

        return ValidationSummary(
            confidence_score=score,
            confidence_level=level,
            checks=checks,
            issues=issues,
        )


@dataclass(slots=True)
class DefaultReportAgent:
    pipeline: Any

    def build_report(
        self,
        profile: DatasetProfile,
        insights: list[str],
        charts: dict[str, dict[str, Any]],
    ) -> str:
        return self.pipeline.build_report(profile, insights, charts)


@dataclass(slots=True)
class PipelineOrchestrator:
    profile_agent: ProfileAgent
    cleaning_agent: CleaningAgent
    business_understanding_agent: BusinessUnderstandingAgent
    insight_agent: InsightAgent
    visualization_agent: VisualizationAgent
    validation_agent: ValidationAgent
    report_agent: ReportAgent

    def run(self, data_frame: pd.DataFrame, objective: str | None = None) -> AnalyticsResult:
        trace: list[AgentTraceEntry] = []

        profile = self.profile_agent.profile(data_frame)
        trace.append(AgentTraceEntry(agent="DataIngestionAgent", action="profiled dataset"))

        business_context = self.business_understanding_agent.derive_business_context(objective, profile)
        trace.append(
            AgentTraceEntry(
                agent="BusinessUnderstandingAgent",
                action="mapped business objective to KPIs and analyses",
            )
        )

        cleaned_data = self.cleaning_agent.clean(data_frame)
        trace.append(AgentTraceEntry(agent="DataCleaningAgent", action="cleaned dataset"))

        insights = self.insight_agent.generate_insights(cleaned_data, profile)
        trace.append(AgentTraceEntry(agent="InsightGenerationAgent", action="generated insights"))

        charts = self.visualization_agent.build_chart_specs(cleaned_data)
        trace.append(AgentTraceEntry(agent="VisualizationAgent", action="prepared chart specs"))

        validation_summary = self.validation_agent.validate(
            cleaned_data,
            profile,
            insights,
            business_context,
        )
        trace.append(
            AgentTraceEntry(
                agent="ValidationExplainabilityAgent",
                action="computed confidence and consistency checks",
            )
        )

        report_markdown = self.report_agent.build_report(profile, insights, charts)
        report_markdown += "\n\n## Validation Summary"
        report_markdown += f"\n- Confidence score: {validation_summary.confidence_score:.2f}"
        report_markdown += f"\n- Confidence level: {validation_summary.confidence_level}"
        if validation_summary.issues:
            report_markdown += "\n- Noted issues:"
            for issue in validation_summary.issues:
                report_markdown += (
                    f"\n  - [{issue.category}/{issue.severity}] {issue.message}"
                )
        trace.append(AgentTraceEntry(agent="ReportGenerationAgent", action="built markdown report"))

        return AnalyticsResult(
            profile=profile,
            cleaned_data=cleaned_data,
            insights=insights,
            charts=charts,
            report_markdown=report_markdown,
            agent_trace=trace,
            business_context=business_context,
            validation_summary=validation_summary,
        )
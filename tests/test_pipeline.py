from __future__ import annotations

import pandas as pd

from autoanalyst_ma.pipeline import AnalyticsPipeline


def test_pipeline_runs_end_to_end() -> None:
    data_frame = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 4],
            "age": [34, 29, 29, 41],
            "segment": ["A", "B", "B", None],
        }
    )

    result = AnalyticsPipeline().run(data_frame)

    assert result.profile.row_count == 4
    assert result.profile.column_count == 3
    assert result.profile.duplicate_rows == 1
    assert result.cleaned_data.shape == (3, 3)
    assert result.insights
    assert "# AutoAnalyst-MA Report" in result.report_markdown
    assert "## Validation Summary" in result.report_markdown
    assert result.validation_summary is not None
    assert result.pipeline_summary is not None
    assert result.pipeline_summary.preprocessing_steps
    assert "row_count" in result.pipeline_summary.eda_summary


def test_pipeline_includes_agent_trace() -> None:
    data_frame = pd.DataFrame(
        {
            "value": [1, 2, 2, 3],
            "category": ["A", "B", "B", "A"],
        }
    )

    result = AnalyticsPipeline().run(data_frame)

    agent_names = [entry.agent for entry in result.agent_trace]
    assert agent_names == [
        "DataIngestionAgent",
        "BusinessUnderstandingAgent",
        "DataCleaningAgent",
        "PreprocessingAgent",
        "InsightGenerationAgent",
        "VisualizationAgent",
        "ValidationExplainabilityAgent",
        "ReportGenerationAgent",
    ]


def test_pipeline_maps_business_goal_to_context() -> None:
    data_frame = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "monthly_spend": [120.0, 75.0, 95.0],
            "status": ["active", "at_risk", "active"],
        }
    )

    result = AnalyticsPipeline().run(data_frame, business_goal="Analyze churn risk")

    assert result.business_context is not None
    assert "churn_rate" in result.business_context.recommended_kpis
    assert "classification" in result.business_context.recommended_analyses
    assert result.validation_summary is not None
    assert result.validation_summary.confidence_level in {"high", "medium", "low"}
    assert 0.10 <= result.validation_summary.confidence_score <= 0.99


def test_validation_issues_include_categories() -> None:
    data_frame = pd.DataFrame(
        {
            "status": ["active", "at_risk", "active"],
            "segment": ["A", "B", "A"],
        }
    )

    result = AnalyticsPipeline().run(data_frame, business_goal="Analyze churn risk")

    assert result.validation_summary is not None
    issue_categories = {issue.category for issue in result.validation_summary.issues}
    assert "statistical_weakness" in issue_categories
    assert "objective_mismatch" in issue_categories

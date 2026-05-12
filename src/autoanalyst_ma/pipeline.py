from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .agents import (
    DefaultCleaningAgent,
    DefaultInsightAgent,
    DefaultProfileAgent,
    DefaultReportAgent,
    DefaultVisualizationAgent,
    PipelineOrchestrator,
)
from .models import AnalyticsResult, DatasetProfile


@dataclass(slots=True)
class PipelineConfig:
    max_insight_columns: int = 8


class AnalyticsPipeline:
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.orchestrator = PipelineOrchestrator(
            profile_agent=DefaultProfileAgent(self),
            cleaning_agent=DefaultCleaningAgent(self),
            insight_agent=DefaultInsightAgent(self),
            visualization_agent=DefaultVisualizationAgent(self),
            report_agent=DefaultReportAgent(self),
        )

    def run_from_csv(self, file_path: str | Path) -> AnalyticsResult:
        data_frame = pd.read_csv(file_path)
        return self.run(data_frame)

    def run(self, data_frame: pd.DataFrame) -> AnalyticsResult:
        return self.orchestrator.run(data_frame)

    def profile(self, data_frame: pd.DataFrame) -> DatasetProfile:
        missing_values = int(data_frame.isna().sum().sum())
        duplicate_rows = int(data_frame.duplicated().sum())
        numeric_columns = list(data_frame.select_dtypes(include="number").columns)
        categorical_columns = list(data_frame.select_dtypes(exclude="number").columns)
        summary = {
            "columns": {name: str(dtype) for name, dtype in data_frame.dtypes.items()},
            "missing_by_column": data_frame.isna().sum().to_dict(),
        }
        return DatasetProfile(
            row_count=int(data_frame.shape[0]),
            column_count=int(data_frame.shape[1]),
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            summary=summary,
        )

    def clean(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        cleaned = data_frame.copy()
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        numeric_columns = list(cleaned.select_dtypes(include="number").columns)
        for column in numeric_columns:
            if cleaned[column].isna().any():
                cleaned[column] = cleaned[column].fillna(cleaned[column].median())
        categorical_columns = list(cleaned.select_dtypes(exclude="number").columns)
        for column in categorical_columns:
            if cleaned[column].isna().any():
                mode_values = cleaned[column].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else "Unknown"
                cleaned[column] = cleaned[column].fillna(fill_value)
        return cleaned

    def generate_insights(self, cleaned_data: pd.DataFrame, profile: DatasetProfile) -> list[str]:
        insights: list[str] = []
        insights.append(
            f"The dataset contains {profile.row_count} rows and {profile.column_count} columns."
        )
        if profile.missing_values > 0:
            insights.append(
                f"The raw dataset included {profile.missing_values} missing values, which were handled during cleaning."
            )
        if profile.duplicate_rows > 0:
            insights.append(
                f"The raw dataset contained {profile.duplicate_rows} duplicate rows that were removed."
            )
        if profile.numeric_columns:
            numeric_summary = cleaned_data[profile.numeric_columns].describe().transpose()
            primary_column = numeric_summary.index[0]
            mean_value = numeric_summary.loc[primary_column, "mean"]
            insights.append(
                f"Numeric profiling shows {primary_column} has an average value of {mean_value:.2f}."
            )
        if len(insights) < 2:
            insights.append("The dataset is ready for deeper domain-specific analysis.")
        return insights[: self.config.max_insight_columns]

    def build_chart_specs(self, cleaned_data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        charts: dict[str, dict[str, Any]] = {}
        numeric_columns = list(cleaned_data.select_dtypes(include="number").columns)
        if numeric_columns:
            charts["numeric_distribution"] = {
                "type": "histogram",
                "columns": numeric_columns[:3],
            }
        categorical_columns = list(cleaned_data.select_dtypes(exclude="number").columns)
        if categorical_columns:
            top_column = categorical_columns[0]
            charts["categorical_counts"] = {
                "type": "bar",
                "column": top_column,
            }
        return charts

    def build_report(
        self,
        profile: DatasetProfile,
        insights: list[str],
        charts: dict[str, dict[str, Any]],
    ) -> str:
        lines = [
            "# AutoAnalyst-MA Report",
            "",
            "## Dataset Profile",
            f"- Rows: {profile.row_count}",
            f"- Columns: {profile.column_count}",
            f"- Missing values: {profile.missing_values}",
            f"- Duplicate rows: {profile.duplicate_rows}",
            "",
            "## Insights",
        ]
        lines.extend(f"- {insight}" for insight in insights)
        if charts:
            lines.extend(["", "## Chart Specifications"])
            for name, spec in charts.items():
                lines.append(f"- {name}: {spec}")
        return "\n".join(lines)

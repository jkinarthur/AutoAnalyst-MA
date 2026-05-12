from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

from .models import AgentTraceEntry, AnalyticsResult, DatasetProfile


class ProfileAgent(Protocol):
    def profile(self, data_frame: pd.DataFrame) -> DatasetProfile:
        ...


class CleaningAgent(Protocol):
    def clean(self, data_frame: pd.DataFrame) -> pd.DataFrame:
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
    insight_agent: InsightAgent
    visualization_agent: VisualizationAgent
    report_agent: ReportAgent

    def run(self, data_frame: pd.DataFrame) -> AnalyticsResult:
        trace: list[AgentTraceEntry] = []

        profile = self.profile_agent.profile(data_frame)
        trace.append(AgentTraceEntry(agent="DataIngestionAgent", action="profiled dataset"))

        cleaned_data = self.cleaning_agent.clean(data_frame)
        trace.append(AgentTraceEntry(agent="DataCleaningAgent", action="cleaned dataset"))

        insights = self.insight_agent.generate_insights(cleaned_data, profile)
        trace.append(AgentTraceEntry(agent="InsightGenerationAgent", action="generated insights"))

        charts = self.visualization_agent.build_chart_specs(cleaned_data)
        trace.append(AgentTraceEntry(agent="VisualizationAgent", action="prepared chart specs"))

        report_markdown = self.report_agent.build_report(profile, insights, charts)
        trace.append(AgentTraceEntry(agent="ReportGenerationAgent", action="built markdown report"))

        return AnalyticsResult(
            profile=profile,
            cleaned_data=cleaned_data,
            insights=insights,
            charts=charts,
            report_markdown=report_markdown,
            agent_trace=trace,
        )
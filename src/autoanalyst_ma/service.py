from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from .pipeline import AnalyticsPipeline
from .schemas import (
    AnalysisPayloadSchema,
    AnalyzeResponseSchema,
    BusinessContextSchema,
    PipelineSummarySchema,
    ProfileSchema,
    RunListItemSchema,
    RunListResponseSchema,
    StoredRunResponseSchema,
    ValidationIssueSchema,
    ValidationSummarySchema,
)
from .storage import AnalysisRunStore


class AnalyticsBackendService:
    def __init__(
        self,
        pipeline: AnalyticsPipeline,
        run_store: AnalysisRunStore,
    ) -> None:
        self.pipeline = pipeline
        self.run_store = run_store

    def analyze_csv_upload(
        self,
        file_bytes: bytes,
        filename: str,
        business_goal: str | None = None,
    ) -> AnalyzeResponseSchema:
        suffix = Path(filename or "dataset.csv").suffix or ".csv"
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(file_bytes)
            temporary_path = Path(temporary_file.name)
        try:
            result = self.pipeline.run_from_csv(temporary_path, business_goal=business_goal)
        finally:
            temporary_path.unlink(missing_ok=True)

        payload = self._to_payload(result)
        run_record = self.run_store.save_run(filename or "dataset.csv", payload.model_dump())
        return AnalyzeResponseSchema(
            run_id=run_record.run_id,
            created_at=run_record.created_at,
            **payload.model_dump(),
        )

    def list_runs(self, limit: int = 20) -> RunListResponseSchema:
        records = self.run_store.list_runs(limit=limit)
        return RunListResponseSchema(
            runs=[
                RunListItemSchema(
                    run_id=record.run_id,
                    created_at=record.created_at,
                    filename=record.filename,
                )
                for record in records
            ]
        )

    def get_run(self, run_id: str) -> StoredRunResponseSchema | None:
        record = self.run_store.get_run(run_id)
        if record is None:
            return None
        return StoredRunResponseSchema(
            run_id=record.run_id,
            created_at=record.created_at,
            filename=record.filename,
            **record.payload,
        )

    def _to_payload(self, result) -> AnalysisPayloadSchema:
        business_context_payload = None
        if result.business_context is not None:
            business_context_payload = BusinessContextSchema(
                objective=result.business_context.objective,
                recommended_kpis=result.business_context.recommended_kpis,
                recommended_analyses=result.business_context.recommended_analyses,
            )

        validation_payload = None
        if result.validation_summary is not None:
            validation_payload = ValidationSummarySchema(
                confidence_score=result.validation_summary.confidence_score,
                confidence_level=result.validation_summary.confidence_level,
                checks=result.validation_summary.checks,
                issues=[
                    ValidationIssueSchema(
                        category=issue.category,
                        severity=issue.severity,
                        message=issue.message,
                    )
                    for issue in result.validation_summary.issues
                ],
            )

        pipeline_summary_payload = None
        if result.pipeline_summary is not None:
            pipeline_summary_payload = PipelineSummarySchema(
                preprocessing_steps=result.pipeline_summary.preprocessing_steps,
                eda_summary=result.pipeline_summary.eda_summary,
            )

        return AnalysisPayloadSchema(
            profile=ProfileSchema(
                row_count=result.profile.row_count,
                column_count=result.profile.column_count,
                missing_values=result.profile.missing_values,
                duplicate_rows=result.profile.duplicate_rows,
                numeric_columns=result.profile.numeric_columns,
                categorical_columns=result.profile.categorical_columns,
            ),
            insights=result.insights,
            charts=result.charts,
            report_markdown=result.report_markdown,
            agent_trace=[
                {
                    "agent": entry.agent,
                    "action": entry.action,
                }
                for entry in result.agent_trace
            ],
            business_context=business_context_payload,
            validation_summary=validation_payload,
            pipeline_summary=pipeline_summary_payload,
            preview=result.cleaned_data.head(5).to_dict(orient="records"),
        )
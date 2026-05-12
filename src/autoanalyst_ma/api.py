from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from .pipeline import AnalyticsPipeline
from .reporting import markdown_to_html, markdown_to_pdf_bytes
from .storage import AnalysisRunStore

app = FastAPI(title="AutoAnalyst-MA", version="0.1.0")
pipeline = AnalyticsPipeline()
run_store = AnalysisRunStore(Path("data") / "analysis_runs.db")


def _to_payload(result) -> dict:
    business_context_payload = None
    if result.business_context is not None:
        business_context_payload = {
            "objective": result.business_context.objective,
            "recommended_kpis": result.business_context.recommended_kpis,
            "recommended_analyses": result.business_context.recommended_analyses,
        }

    validation_payload = None
    if result.validation_summary is not None:
        validation_payload = {
            "confidence_score": result.validation_summary.confidence_score,
            "confidence_level": result.validation_summary.confidence_level,
            "checks": result.validation_summary.checks,
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in result.validation_summary.issues
            ],
        }

    return {
        "profile": {
            "row_count": result.profile.row_count,
            "column_count": result.profile.column_count,
            "missing_values": result.profile.missing_values,
            "duplicate_rows": result.profile.duplicate_rows,
            "numeric_columns": result.profile.numeric_columns,
            "categorical_columns": result.profile.categorical_columns,
        },
        "insights": result.insights,
        "charts": result.charts,
        "report_markdown": result.report_markdown,
        "agent_trace": [
            {"agent": entry.agent, "action": entry.action}
            for entry in result.agent_trace
        ],
        "business_context": business_context_payload,
        "validation_summary": validation_payload,
        "preview": result.cleaned_data.head(5).to_dict(orient="records"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    business_goal: str | None = Form(default=None),
) -> dict:
    suffix = Path(file.filename or "dataset.csv").suffix or ".csv"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        temporary_file.write(await file.read())
        temporary_path = Path(temporary_file.name)
    try:
        result = pipeline.run_from_csv(temporary_path, business_goal=business_goal)
        payload = _to_payload(result)
        run_record = run_store.save_run(file.filename or "dataset.csv", payload)
        return {
            "run_id": run_record.run_id,
            "created_at": run_record.created_at,
            **payload,
        }
    finally:
        temporary_path.unlink(missing_ok=True)


@app.get("/runs")
def list_runs(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    records = run_store.list_runs(limit=limit)
    return {
        "runs": [
            {
                "run_id": record.run_id,
                "created_at": record.created_at,
                "filename": record.filename,
            }
            for record in records
        ]
    }


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    record = run_store.get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": record.run_id,
        "created_at": record.created_at,
        "filename": record.filename,
        **record.payload,
    }


@app.get("/runs/{run_id}/report")
def export_run_report(
    run_id: str,
    format: Literal["md", "html", "pdf"] = Query(default="md"),
):
    record = run_store.get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")

    markdown_report = record.payload.get("report_markdown")
    if not isinstance(markdown_report, str) or not markdown_report.strip():
        raise HTTPException(status_code=404, detail="Report content not found")

    if format == "html":
        html_report = markdown_to_html(markdown_report)
        return HTMLResponse(
            content=html_report,
            headers={
                "Content-Disposition": f'attachment; filename="{run_id}.html"',
            },
        )

    if format == "pdf":
        pdf_bytes = markdown_to_pdf_bytes(markdown_report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{run_id}.pdf"',
            },
        )

    return PlainTextResponse(
        content=markdown_report,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{run_id}.md"',
        },
    )

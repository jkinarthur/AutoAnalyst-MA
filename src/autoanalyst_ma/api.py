from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from .pipeline import AnalyticsPipeline
from .reporting import markdown_to_html, markdown_to_pdf_bytes
from .schemas import AnalyzeResponseSchema, RunListResponseSchema, StoredRunResponseSchema
from .service import AnalyticsBackendService
from .storage import AnalysisRunStore

app = FastAPI(title="AutoAnalyst-MA", version="0.1.0")
pipeline = AnalyticsPipeline()
run_store = AnalysisRunStore(Path("data") / "analysis_runs.db")


def get_backend_service() -> AnalyticsBackendService:
    return AnalyticsBackendService(pipeline=pipeline, run_store=run_store)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponseSchema)
async def analyze(
    file: UploadFile = File(...),
    business_goal: str | None = Form(default=None),
) -> AnalyzeResponseSchema:
    file_bytes = await file.read()
    return get_backend_service().analyze_csv_upload(
        file_bytes=file_bytes,
        filename=file.filename or "dataset.csv",
        business_goal=business_goal,
    )


@app.get("/runs", response_model=RunListResponseSchema)
def list_runs(limit: int = Query(default=20, ge=1, le=200)) -> RunListResponseSchema:
    return get_backend_service().list_runs(limit=limit)


@app.get("/runs/{run_id}", response_model=StoredRunResponseSchema)
def get_run(run_id: str) -> StoredRunResponseSchema:
    run_record = get_backend_service().get_run(run_id)
    if run_record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_record


@app.get("/runs/{run_id}/report")
def export_run_report(
    run_id: str,
    format: Literal["md", "html", "pdf"] = Query(default="md"),
):
    run_record = get_backend_service().get_run(run_id)
    if run_record is None:
        raise HTTPException(status_code=404, detail="Run not found")

    markdown_report = run_record.report_markdown
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

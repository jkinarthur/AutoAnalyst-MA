from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from .pipeline import AnalyticsPipeline
from .storage import AnalysisRunStore

app = FastAPI(title="AutoAnalyst-MA", version="0.1.0")
pipeline = AnalyticsPipeline()
run_store = AnalysisRunStore(Path("data") / "analysis_runs.db")


def _to_payload(result) -> dict:
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
        "preview": result.cleaned_data.head(5).to_dict(orient="records"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "dataset.csv").suffix or ".csv"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        temporary_file.write(await file.read())
        temporary_path = Path(temporary_file.name)
    try:
        result = pipeline.run_from_csv(temporary_path)
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

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from fastapi import FastAPI, File, UploadFile

from .pipeline import AnalyticsPipeline

app = FastAPI(title="AutoAnalyst-MA", version="0.1.0")
pipeline = AnalyticsPipeline()


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
    finally:
        temporary_path.unlink(missing_ok=True)

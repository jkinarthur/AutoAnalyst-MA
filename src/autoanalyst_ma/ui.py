from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px

from .models import AnalyticsResult
from .pipeline import AnalyticsPipeline
from .storage import AnalysisRunStore


def run_analysis_from_upload(
    uploaded_file,
    business_goal: str | None = None,
) -> tuple[pd.DataFrame, AnalyticsResult]:
    data_frame = pd.read_csv(uploaded_file)
    result = AnalyticsPipeline().run(data_frame, business_goal=business_goal)
    return data_frame, result


def dataframe_preview_html(data_frame: pd.DataFrame) -> str:
    buffer = StringIO()
    buffer.write(data_frame.head(10).to_html(index=False, classes="autoanalyst-preview"))
    return buffer.getvalue()


def build_chart_frames(result: AnalyticsResult) -> list[tuple[str, object]]:
    charts: list[tuple[str, object]] = []
    cleaned_data = result.cleaned_data

    numeric_columns = list(cleaned_data.select_dtypes(include="number").columns)
    for column in numeric_columns[:2]:
        figure = px.histogram(cleaned_data, x=column, title=f"Distribution of {column}")
        charts.append((column, figure))

    categorical_columns = list(cleaned_data.select_dtypes(exclude="number").columns)
    if categorical_columns:
        column = categorical_columns[0]
        counts = cleaned_data[column].value_counts().reset_index()
        counts.columns = [column, "count"]
        figure = px.bar(counts, x=column, y="count", title=f"Counts for {column}")
        charts.append((column, figure))

    return charts


def list_saved_runs(limit: int = 50, database_path: str | Path = Path("data") / "analysis_runs.db") -> list[dict[str, str]]:
    store = AnalysisRunStore(database_path)
    records = store.list_runs(limit=limit)
    return [
        {
            "run_id": record.run_id,
            "created_at": record.created_at,
            "filename": record.filename,
        }
        for record in records
    ]


def load_saved_run(run_id: str, database_path: str | Path = Path("data") / "analysis_runs.db") -> dict[str, Any] | None:
    store = AnalysisRunStore(database_path)
    record = store.get_run(run_id)
    if record is None:
        return None
    return {
        "run_id": record.run_id,
        "created_at": record.created_at,
        "filename": record.filename,
        **record.payload,
    }
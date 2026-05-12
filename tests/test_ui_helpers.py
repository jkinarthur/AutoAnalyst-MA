from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd

from autoanalyst_ma.pipeline import AnalyticsPipeline
from autoanalyst_ma.storage import AnalysisRunStore
from autoanalyst_ma.ui import (
    build_chart_frames,
    dataframe_preview_html,
    list_saved_runs,
    load_saved_run,
    run_analysis_from_upload,
)


def test_run_analysis_from_upload_and_preview_html() -> None:
    uploaded = StringIO("customer_id,amount,status\n1,100,active\n2,80,at_risk\n")
    data_frame, result = run_analysis_from_upload(uploaded, business_goal="Analyze churn risk")

    assert data_frame.shape == (2, 3)
    assert result.business_context is not None

    preview_html = dataframe_preview_html(data_frame)
    assert "<table" in preview_html


def test_build_chart_frames_returns_figures() -> None:
    data_frame = pd.DataFrame(
        {
            "amount": [100, 90, 110],
            "status": ["active", "at_risk", "active"],
        }
    )
    result = AnalyticsPipeline().run(data_frame)

    frames = build_chart_frames(result)
    assert frames


def test_saved_run_helpers_roundtrip(tmp_path: Path) -> None:
    store = AnalysisRunStore(tmp_path / "ui_runs.db")
    payload = {
        "profile": {
            "row_count": 1,
            "column_count": 1,
            "missing_values": 0,
            "duplicate_rows": 0,
            "numeric_columns": ["amount"],
            "categorical_columns": [],
        },
        "insights": ["Sample"],
        "charts": {},
        "report_markdown": "# Report",
        "agent_trace": [],
        "preview": [{"amount": 100}],
    }
    created = store.save_run("ui.csv", payload)

    listed = list_saved_runs(database_path=tmp_path / "ui_runs.db")
    assert listed
    assert listed[0]["run_id"] == created.run_id

    loaded = load_saved_run(created.run_id, database_path=tmp_path / "ui_runs.db")
    assert loaded is not None
    assert loaded["filename"] == "ui.csv"

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from autoanalyst_ma import api
from autoanalyst_ma.storage import AnalysisRunStore


def _sample_payload() -> dict:
    return {
        "profile": {
            "row_count": 3,
            "column_count": 2,
            "missing_values": 0,
            "duplicate_rows": 0,
            "numeric_columns": ["value"],
            "categorical_columns": ["group"],
        },
        "insights": ["Sample insight"],
        "charts": {},
        "report_markdown": "# Report",
        "agent_trace": [],
        "preview": [{"value": 1, "group": "A"}],
    }


def test_analysis_run_store_roundtrip(tmp_path: Path) -> None:
    store = AnalysisRunStore(tmp_path / "runs.db")
    created = store.save_run("sample.csv", _sample_payload())

    fetched = store.get_run(created.run_id)
    assert fetched is not None
    assert fetched.run_id == created.run_id
    assert fetched.filename == "sample.csv"
    assert fetched.payload["profile"]["row_count"] == 3

    listed = store.list_runs(limit=10)
    assert listed
    assert listed[0].run_id == created.run_id


def test_api_run_endpoints_return_saved_runs(tmp_path: Path) -> None:
    isolated_store = AnalysisRunStore(tmp_path / "api_runs.db")
    created = isolated_store.save_run("api.csv", _sample_payload())

    original_store = api.run_store
    api.run_store = isolated_store
    try:
        client = TestClient(api.app)

        list_response = client.get("/runs")
        assert list_response.status_code == 200
        runs = list_response.json()["runs"]
        assert runs
        assert runs[0]["run_id"] == created.run_id

        get_response = client.get(f"/runs/{created.run_id}")
        assert get_response.status_code == 200
        payload = get_response.json()
        assert payload["run_id"] == created.run_id
        assert payload["filename"] == "api.csv"

        missing_response = client.get("/runs/nonexistent")
        assert missing_response.status_code == 404
    finally:
        api.run_store = original_store
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
        "report_markdown": "# Report\n\n- Sample insight",
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


def test_api_report_export_endpoints(tmp_path: Path) -> None:
    isolated_store = AnalysisRunStore(tmp_path / "api_report_runs.db")
    created = isolated_store.save_run("report.csv", _sample_payload())

    original_store = api.run_store
    api.run_store = isolated_store
    try:
        client = TestClient(api.app)

        markdown_response = client.get(f"/runs/{created.run_id}/report")
        assert markdown_response.status_code == 200
        assert markdown_response.headers["content-type"].startswith("text/markdown")
        assert "# Report" in markdown_response.text

        html_response = client.get(f"/runs/{created.run_id}/report?format=html")
        assert html_response.status_code == 200
        assert html_response.headers["content-type"].startswith("text/html")
        assert "<h1>Report</h1>" in html_response.text

        missing_response = client.get("/runs/nonexistent/report")
        assert missing_response.status_code == 404

        pdf_response = client.get(f"/runs/{created.run_id}/report?format=pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert pdf_response.content[:4] == b"%PDF"
    finally:
        api.run_store = original_store
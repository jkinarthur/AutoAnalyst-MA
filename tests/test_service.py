from __future__ import annotations

from pathlib import Path

from autoanalyst_ma.pipeline import AnalyticsPipeline
from autoanalyst_ma.service import AnalyticsBackendService
from autoanalyst_ma.storage import AnalysisRunStore


def test_service_analyze_csv_upload_persists_run(tmp_path: Path) -> None:
    store = AnalysisRunStore(tmp_path / "service_runs.db")
    service = AnalyticsBackendService(pipeline=AnalyticsPipeline(), run_store=store)

    csv_bytes = b"customer_id,amount,status\n1,120,active\n2,90,at_risk\n"
    response = service.analyze_csv_upload(
        file_bytes=csv_bytes,
        filename="sample.csv",
        business_goal="Analyze churn risk",
    )

    assert response.run_id
    assert response.profile.row_count == 2
    assert response.business_context is not None
    assert response.pipeline_summary is not None

    saved = store.get_run(response.run_id)
    assert saved is not None
    assert saved.filename == "sample.csv"


def test_service_list_and_get_run(tmp_path: Path) -> None:
    store = AnalysisRunStore(tmp_path / "service_list.db")
    service = AnalyticsBackendService(pipeline=AnalyticsPipeline(), run_store=store)

    csv_bytes = b"customer_id,amount,status\n1,120,active\n"
    created = service.analyze_csv_upload(file_bytes=csv_bytes, filename="single.csv")

    listed = service.list_runs(limit=10)
    assert listed.runs
    assert listed.runs[0].run_id == created.run_id

    fetched = service.get_run(created.run_id)
    assert fetched is not None
    assert fetched.filename == "single.csv"

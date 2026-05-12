from __future__ import annotations

import pandas as pd

from autoanalyst_ma.pipeline import AnalyticsPipeline


def test_pipeline_runs_end_to_end() -> None:
    data_frame = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 4],
            "age": [34, 29, 29, 41],
            "segment": ["A", "B", "B", None],
        }
    )

    result = AnalyticsPipeline().run(data_frame)

    assert result.profile.row_count == 4
    assert result.profile.column_count == 3
    assert result.profile.duplicate_rows == 1
    assert result.cleaned_data.shape == (3, 3)
    assert result.insights
    assert "# AutoAnalyst-MA Report" in result.report_markdown

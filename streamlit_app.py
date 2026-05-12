from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from autoanalyst_ma.reporting import markdown_to_html, markdown_to_pdf_bytes
from autoanalyst_ma.ui import (
    build_chart_frames,
    list_saved_runs,
    load_saved_run,
    run_analysis_from_upload,
)


st.set_page_config(page_title="AutoAnalyst-MA", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background: radial-gradient(circle at top right, #e8f4ff 0%, #f9fbfd 45%, #ffffff 100%);
}

[data-testid="stMetricValue"] {
    color: #123a5a;
}

.app-banner {
    border: 1px solid #d6e7f5;
    border-radius: 14px;
    padding: 14px 18px;
    background: linear-gradient(90deg, #f3f9ff 0%, #eef7f6 100%);
    margin-bottom: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)


def _render_validation_dashboard(
    confidence_score: float,
    confidence_level: str,
    checks: list[str],
    issues: list[dict[str, str]],
) -> None:
    st.subheader("Validation summary")
    st.write(f"Confidence: {confidence_score:.2f} ({confidence_level})")

    confidence_figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=confidence_score * 100,
            title={"text": "Confidence"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2E86C1"},
                "steps": [
                    {"range": [0, 60], "color": "#F8D7DA"},
                    {"range": [60, 80], "color": "#FFF3CD"},
                    {"range": [80, 100], "color": "#D4EDDA"},
                ],
            },
        )
    )
    confidence_figure.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(confidence_figure, use_container_width=True)

    category_counts: dict[str, int] = {}
    for issue in issues:
        category = issue.get("category", "uncategorized")
        category_counts[category] = category_counts.get(category, 0) + 1

    if category_counts:
        count_columns = st.columns(len(category_counts))
        for index, (category, count) in enumerate(sorted(category_counts.items())):
            with count_columns[index]:
                st.metric(f"{category} warnings", count)

    if checks:
        st.write("Checks")
        for check in checks:
            st.write(f"- {check}")
    if issues:
        st.write("Issues")
        for issue in issues:
            st.write(
                f"- [{issue.get('category', 'uncategorized')}/{issue.get('severity', 'unknown')}] {issue.get('message', '')}"
            )


def _render_saved_run_payload(payload: dict[str, Any]) -> None:
    profile = payload.get("profile", {})
    metric_columns = st.columns(4)
    metric_columns[0].metric("Rows", profile.get("row_count", 0))
    metric_columns[1].metric("Columns", profile.get("column_count", 0))
    metric_columns[2].metric("Missing values", profile.get("missing_values", 0))
    metric_columns[3].metric("Duplicate rows", profile.get("duplicate_rows", 0))

    insights = payload.get("insights", [])
    if insights:
        st.subheader("Insights")
        for insight in insights:
            st.write(f"- {insight}")

    business_context = payload.get("business_context")
    if isinstance(business_context, dict):
        st.subheader("Business context")
        st.write(f"Objective: {business_context.get('objective', 'N/A')}")
        st.write("Suggested KPIs")
        for kpi in business_context.get("recommended_kpis", []):
            st.write(f"- {kpi}")
        st.write("Suggested analyses")
        for analysis_name in business_context.get("recommended_analyses", []):
            st.write(f"- {analysis_name}")

    validation = payload.get("validation_summary")
    if isinstance(validation, dict):
        _render_validation_dashboard(
            confidence_score=float(validation.get("confidence_score", 0.0)),
            confidence_level=str(validation.get("confidence_level", "unknown")),
            checks=list(validation.get("checks", [])),
            issues=list(validation.get("issues", [])),
        )

    preview = payload.get("preview")
    if isinstance(preview, list) and preview:
        st.subheader("Preview")
        st.dataframe(pd.DataFrame(preview), use_container_width=True)

    report_markdown = str(payload.get("report_markdown", ""))
    if report_markdown:
        st.subheader("Report draft")
        st.text_area("Stored Markdown report", value=report_markdown, height=260, key="stored_report")
        dl_left, dl_mid, dl_right = st.columns(3)
        with dl_left:
            st.download_button(
                "Download Stored Markdown",
                data=report_markdown.encode("utf-8"),
                file_name=f"saved_{payload.get('run_id', 'report')}.md",
                mime="text/markdown",
                key="stored_md_download",
            )
        with dl_mid:
            st.download_button(
                "Download Stored HTML",
                data=markdown_to_html(report_markdown).encode("utf-8"),
                file_name=f"saved_{payload.get('run_id', 'report')}.html",
                mime="text/html",
                key="stored_html_download",
            )
        with dl_right:
            st.download_button(
                "Download Stored PDF",
                data=markdown_to_pdf_bytes(report_markdown),
                file_name=f"saved_{payload.get('run_id', 'report')}.pdf",
                mime="application/pdf",
                key="stored_pdf_download",
            )

st.markdown(
    """
<div class="app-banner">
  <h2 style="margin:0; color:#13415f;">AutoAnalyst-MA</h2>
  <p style="margin:4px 0 0 0; color:#305f80;">Multi-agent analytics with explainable validation and report exports.</p>
</div>
""",
    unsafe_allow_html=True,
)

analysis_tab, history_tab = st.tabs(["New Analysis", "Saved Runs"])

with analysis_tab:
    business_goal = st.text_input(
        "Business objective (optional)",
        placeholder="Example: Analyze customer churn risk",
    )
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is None:
        st.info("Upload a CSV file to begin.")
    else:
        try:
            _, result = run_analysis_from_upload(uploaded_file, business_goal=business_goal)
        except Exception as exc:  # pragma: no cover - UI safety net
            st.error(f"Could not analyze file: {exc}")
        else:
            metric_columns = st.columns(4)
            metric_columns[0].metric("Rows", result.profile.row_count)
            metric_columns[1].metric("Columns", result.profile.column_count)
            metric_columns[2].metric("Missing values", result.profile.missing_values)
            metric_columns[3].metric("Duplicate rows", result.profile.duplicate_rows)

            st.subheader("Insights")
            for insight in result.insights:
                st.write(f"- {insight}")

            st.subheader("Preview")
            st.dataframe(result.cleaned_data.head(10), use_container_width=True)

            if result.business_context is not None:
                st.subheader("Business context")
                st.write(f"Objective: {result.business_context.objective}")
                kpi_col, analysis_col = st.columns(2)
                with kpi_col:
                    st.write("Suggested KPIs")
                    for kpi in result.business_context.recommended_kpis:
                        st.write(f"- {kpi}")
                with analysis_col:
                    st.write("Suggested analyses")
                    for analysis_name in result.business_context.recommended_analyses:
                        st.write(f"- {analysis_name}")

            if result.validation_summary is not None:
                _render_validation_dashboard(
                    confidence_score=result.validation_summary.confidence_score,
                    confidence_level=result.validation_summary.confidence_level,
                    checks=result.validation_summary.checks,
                    issues=[
                        {
                            "category": issue.category,
                            "severity": issue.severity,
                            "message": issue.message,
                        }
                        for issue in result.validation_summary.issues
                    ],
                )

            st.subheader("Charts")
            chart_frames = build_chart_frames(result)
            if chart_frames:
                for _, figure in chart_frames:
                    st.plotly_chart(figure, use_container_width=True)
            else:
                st.info("No chartable columns were detected.")

            st.subheader("Report draft")
            st.text_area("Markdown report", value=result.report_markdown, height=320)

            download_left, download_mid, download_right = st.columns(3)
            markdown_bytes = result.report_markdown.encode("utf-8")
            html_bytes = markdown_to_html(result.report_markdown).encode("utf-8")
            pdf_bytes = markdown_to_pdf_bytes(result.report_markdown)

            with download_left:
                st.download_button(
                    "Download Markdown",
                    data=markdown_bytes,
                    file_name="autoanalyst_report.md",
                    mime="text/markdown",
                )

            with download_mid:
                st.download_button(
                    "Download HTML",
                    data=html_bytes,
                    file_name="autoanalyst_report.html",
                    mime="text/html",
                )

            with download_right:
                st.download_button(
                    "Download PDF",
                    data=pdf_bytes,
                    file_name="autoanalyst_report.pdf",
                    mime="application/pdf",
                )

            st.subheader("Agent trace")
            for step in result.agent_trace:
                st.write(f"- {step.agent}: {step.action}")

with history_tab:
    st.caption("Browse previously saved analyses from local SQLite history.")
    runs = list_saved_runs(limit=75)
    if not runs:
        st.info("No saved runs yet. Complete at least one analysis to populate history.")
    else:
        options = {
            f"{record['created_at']} | {record['filename']} | {record['run_id'][:8]}": record["run_id"]
            for record in runs
        }
        selected_label = st.selectbox("Select a saved run", list(options.keys()))
        selected_run_id = options[selected_label]
        saved_payload = load_saved_run(selected_run_id)

        if saved_payload is None:
            st.error("Could not load the selected run.")
        else:
            st.write(f"Run ID: {saved_payload.get('run_id', 'N/A')}")
            st.write(f"Created: {saved_payload.get('created_at', 'N/A')}")
            st.write(f"Filename: {saved_payload.get('filename', 'N/A')}")
            _render_saved_run_payload(saved_payload)
from __future__ import annotations

import streamlit as st

from autoanalyst_ma.reporting import markdown_to_html, markdown_to_pdf_bytes
from autoanalyst_ma.ui import build_chart_frames, run_analysis_from_upload


st.set_page_config(page_title="AutoAnalyst-MA", layout="wide")

st.title("AutoAnalyst-MA")
st.caption("Upload a CSV file to generate a profile, insights, and a report draft.")
business_goal = st.text_input(
    "Business objective (optional)",
    placeholder="Example: Analyze customer churn risk",
)

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
else:
    try:
        data_frame, result = run_analysis_from_upload(uploaded_file, business_goal=business_goal)
    except Exception as exc:  # pragma: no cover - UI safety net
        st.error(f"Could not analyze file: {exc}")
    else:
        left_column, right_column = st.columns(2)

        with left_column:
            st.subheader("Dataset profile")
            st.metric("Rows", result.profile.row_count)
            st.metric("Columns", result.profile.column_count)
            st.metric("Missing values", result.profile.missing_values)
            st.metric("Duplicate rows", result.profile.duplicate_rows)

        with right_column:
            st.subheader("Insights")
            for insight in result.insights:
                st.write(f"- {insight}")

        st.subheader("Preview")
        st.dataframe(result.cleaned_data.head(10), use_container_width=True)

        if result.business_context is not None:
            st.subheader("Business context")
            st.write(f"Objective: {result.business_context.objective}")
            st.write("Suggested KPIs")
            for kpi in result.business_context.recommended_kpis:
                st.write(f"- {kpi}")
            st.write("Suggested analyses")
            for analysis_name in result.business_context.recommended_analyses:
                st.write(f"- {analysis_name}")

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
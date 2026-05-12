from __future__ import annotations

import streamlit as st

from autoanalyst_ma.ui import build_chart_frames, run_analysis_from_upload


st.set_page_config(page_title="AutoAnalyst-MA", layout="wide")

st.title("AutoAnalyst-MA")
st.caption("Upload a CSV file to generate a profile, insights, and a report draft.")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
else:
    try:
        data_frame, result = run_analysis_from_upload(uploaded_file)
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

        st.subheader("Charts")
        chart_frames = build_chart_frames(result)
        if chart_frames:
            for _, figure in chart_frames:
                st.plotly_chart(figure, use_container_width=True)
        else:
            st.info("No chartable columns were detected.")

        st.subheader("Report draft")
        st.text_area("Markdown report", value=result.report_markdown, height=320)

        st.subheader("Agent trace")
        for step in result.agent_trace:
            st.write(f"- {step.agent}: {step.action}")
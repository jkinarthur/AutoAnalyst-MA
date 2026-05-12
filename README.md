# AutoAnalyst-MA

AutoAnalyst-MA is an open-source multi-agent analytics system that turns tabular data into cleaned datasets, exploratory analysis, visualizations, validated insights, and executive-ready reports.

## MVP

- Upload a CSV file
- Profile the dataset
- Clean common data issues
- Run exploratory data analysis
- Generate charts and insights
- Export a Markdown report

## Project structure

- `src/autoanalyst_ma/` - application package
- `src/autoanalyst_ma/api.py` - FastAPI application
- `src/autoanalyst_ma/agents.py` - multi-agent orchestration skeleton
- `src/autoanalyst_ma/pipeline.py` - analytics pipeline
- `tests/` - automated tests

## Development

Install dependencies with your preferred Python environment manager, then run:

```bash
uvicorn autoanalyst_ma.api:app --reload
```

To launch the Streamlit UI for CSV upload and analysis:

```bash
streamlit run streamlit_app.py
```

If you have not installed the UI extras yet, use:

```bash
pip install -e .[ui]
```

## Notes

This repository starts with the MVP backend and data pipeline.
The current implementation includes a coordinator and stage agents for profile, cleaning, insights, visualization, and reporting, plus an execution trace exposed by the API/UI for explainability.

# AutoAnalyst-MA

AutoAnalyst-MA is an open-source multi-agent analytics system that turns tabular data into cleaned datasets, exploratory analysis, visualizations, validated insights, and executive-ready reports.

## MVP

- Upload a CSV file
- Profile the dataset
- Clean common data issues
- Run exploratory data analysis
- Generate charts and insights
- Compute confidence and validation checks
- Export a Markdown report

## Project structure

- `src/autoanalyst_ma/` - application package
- `src/autoanalyst_ma/api.py` - FastAPI application
- `src/autoanalyst_ma/agents.py` - multi-agent orchestration skeleton
- `src/autoanalyst_ma/pipeline.py` - analytics pipeline
- `tests/` - automated tests

## Development

Create and activate your Python environment, then install dependencies:

```bash
pip install -e .[dev,ui,pdf]
```

Run the API:

```bash
uvicorn autoanalyst_ma.api:app --reload
```

Core API endpoints:

- `POST /analyze` runs analysis and stores the result in SQLite. You can pass an optional `business_goal` form field. The response includes `business_context` and `validation_summary`.
- `GET /runs` lists recent analysis runs.
- `GET /runs/{run_id}` returns a stored run payload.
- `GET /runs/{run_id}/report` exports a stored report as markdown (`?format=md`), HTML (`?format=html`), or PDF (`?format=pdf`).

To launch the Streamlit UI for CSV upload and analysis:

```bash
streamlit run streamlit_app.py
```

If you have not installed the UI extras yet, use:

```bash
pip install -e .[ui]
```

## Testing

Run the full test suite:

```bash
pytest
```

Current tests cover:

- pipeline orchestration and stage traces
- API routes including report export formats
- persistence layer behavior
- backend service contract behavior
- UI helper behavior for analysis and saved runs

## Backend Package Overview

Key backend modules:

- `src/autoanalyst_ma/api.py`: FastAPI route layer
- `src/autoanalyst_ma/service.py`: backend service orchestration and serialization
- `src/autoanalyst_ma/schemas.py`: typed API request/response models
- `src/autoanalyst_ma/pipeline.py`: core analytics pipeline implementation
- `src/autoanalyst_ma/agents.py`: multi-agent orchestration and stage agents
- `src/autoanalyst_ma/storage.py`: SQLite run persistence

## Notes

This repository starts with the MVP backend and data pipeline.
The current implementation includes a coordinator and stage agents for profile, cleaning, insights, visualization, and reporting, plus an execution trace exposed by the API/UI for explainability.

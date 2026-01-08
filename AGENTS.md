# Repository Guidelines

## Project Structure & Module Organization
- `app/` — FastAPI service code (routers, schemas, handlers). Keep the entrypoint in `app/main.py` when adding.
- `model/` — training/inference code, feature engineering, and serialized model artifacts.
- `data/` — raw/processed datasets; keep large or sensitive files out of git.
- `tests/` — pytest suite mirroring the `app/` and `model/` layout.
- `deployed/` — local virtualenv/runtime artifacts; regenerated, avoid editing.
- `requirements.txt` — pinned dependencies.

## Build, Test, and Development Commands
- `python -m venv deployed` and `source deployed/bin/activate` — create/activate a local env if needed.
- `python -m pip install -r requirements.txt` — install dependencies.
- `uvicorn app.main:app --reload` — run the API locally (adjust module path to match the entrypoint you add).
- `pytest` — run unit tests.
- `pytest --cov=app --cov-report=term-missing` — run tests with coverage (update package path if needed).

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8, type hints where practical.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants.
- Keep modules focused; prefer small, testable functions.

## Testing Guidelines
- Framework: pytest (and `httpx` for API client tests).
- File naming: `test_*.py`; place tests under `tests/` mirroring source structure.
- Cover new features and bug fixes with targeted tests.

## Commit & Pull Request Guidelines
- Git history is not present in this workspace; use clear, imperative messages (e.g., `feat: add churn feature pipeline`).
- PRs should describe intent, list tests run, and link relevant issues or tickets. Include sample requests/responses for API changes.

## Configuration & Data Handling
- Store secrets and endpoints via env vars (e.g., `MLFLOW_TRACKING_URI`) rather than hardcoding.
- Do not commit large datasets or model binaries; document where to fetch or generate them.

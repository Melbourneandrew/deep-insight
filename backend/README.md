# Deep Insight Backend

FastAPI backend initialized with Poetry.

## Requirements

- Python 3.10–3.12
- Poetry

## Setup

```bash
cd backend
poetry install
```

## Run (development)

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health check

After starting, open:

- http://localhost:8000/ for a welcome message
- http://localhost:8000/health for status

## API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

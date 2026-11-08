# AI & Data Inventory

A starter web app for cataloging reusable datasets, models, code, tools, and reports. The UI uses Streamlit, the REST API uses FastAPI, SQLAlchemy handles persistence, and the database is SQLite locally or PostgreSQL with Docker.

## Run locally

Requires Python 3.10+.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the API and UI in separate terminals from this folder:

```powershell
uvicorn app.main:app --reload
```

```powershell
streamlit run streamlit_app.py
```

Open the UI at http://localhost:8501 and API docs at http://localhost:8000/docs. The local SQLite database `inventory.db` is created automatically on first API start.

## Run with PostgreSQL

```powershell
docker compose up --build
```

Open http://localhost:8501. To use PostgreSQL without Docker, set `DATABASE_URL` to a SQLAlchemy URL such as `postgresql+psycopg://user:password@host:5432/inventory` before starting the API.

## Included

- Inventory catalog with search and filters by asset type and status
- Asset details: owner, team, version, license, tags, description, and location
- Create and delete actions from the UI; full create, read, update, delete API
- Dashboard counts, type chart, and recent activity log
- OpenAPI docs and health check

## API quick reference

- `GET /assets?q=&asset_type=&status=&team=`
- `POST /assets`
- `GET /assets/{id}`
- `PUT /assets/{id}`
- `DELETE /assets/{id}`
- `GET /stats`, `GET /activity`, `GET /health`

This is a development starter. Add authentication, role-based access, migrations, backups, and deployment secrets before exposing it to a wider team.

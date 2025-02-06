![GitHub last commit](https://img.shields.io/github/last-commit/felixchiasson/jellynalyst) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/felixchiasson/jellynalyst)



# Jellynalyst

Analytics dashboard for Jellyseerr and Jellyfin.

## Setup

1. Create a virtual environment:
```bash
uv venv
source .venv/bin/activate  # Unix
# or
.venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the application:
```bash
uvicorn jellynalyst.main:app --reload
```

## Development

- Format code: `black .`
- Sort imports: `isort .`
- Type check: `pyright`
- Run tests: `pytest`

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Docker

Build and run with Docker:
```bash
docker compose up --build
```

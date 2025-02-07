#!/bin/bash
set -e

# Set default port
APP_PORT="${APP_PORT:-8000}"

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

echo "Checking database state..."
if ! alembic current 2>/dev/null; then
    echo "No alembic history found - initializing fresh database..."
    python << END
from sqlalchemy import create_engine
from jellynalyst.database.models import Base
from jellynalyst.config import Settings

settings = Settings()
engine = create_engine(settings.SYNC_DATABASE_URL)
Base.metadata.create_all(engine)
END

    # Mark current state as head
    echo "Marking current state as head..."
    alembic stamp head
else
    echo "Existing database found - running migrations..."
    alembic upgrade head
fi

# Start the application
echo "Starting application on port ${APP_PORT}..."
uvicorn jellynalyst.main:app --host 0.0.0.0 --port "${APP_PORT}"

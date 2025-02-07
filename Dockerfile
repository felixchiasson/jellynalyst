# Build stage
FROM python:3.13-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Final stage
FROM python:3.13-slim-bookworm

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=8000

# Copy application code
COPY jellynalyst/ /app/jellynalyst/
COPY static/ /app/static/
COPY templates/ /app/templates/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY scripts/start.sh /start.sh

# Make the startup script executable
RUN chmod +x /start.sh

# Create non-root user
RUN adduser --disabled-password --gecos '' jellynalyst && \
    chown -R jellynalyst:jellynalyst /app /opt/venv /start.sh

# Switch to non-root user
USER jellynalyst

# Command to run the application
CMD ["/start.sh"]

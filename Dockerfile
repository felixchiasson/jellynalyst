FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

# Initial setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install uv

# Create virtual environment using uv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY requirements-dev.txt .

# Install dependencies using uv
RUN uv pip install -r requirements.txt
RUN uv pip install -r requirements-dev.txt

COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' jellynalyst
USER jellynalyst

CMD ["uvicorn", "jellynalyst.main:app", "--host", "0.0.0.0", "--port", "8000"]

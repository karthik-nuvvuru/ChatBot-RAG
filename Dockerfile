# =============================================================================
# Dockerfile - NelloreRuchullu (Conversation AI Platform)
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first (for caching)
COPY pyproject.toml ./

# Install dependencies - poetry.lock will be used if present, otherwise poetry will resolve
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY alembic ./alembic
COPY alembic.ini ./
COPY app ./app
COPY tests ./tests

# Create storage directory
RUN mkdir -p /app/storage/attachments

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default command - will be overridden by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

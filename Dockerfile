# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Installa uv
RUN pip install --no-cache-dir uv

# Copia pyproject.toml e uv.lock
COPY pyproject.toml uv.lock ./

# Installa dipendenze con uv
RUN uv sync --frozen --no-dev

# Stage 2: Runtime (minimalista)
FROM python:3.11-slim

WORKDIR /app

# Installa uv
RUN pip install --no-cache-dir uv

# Copia pyproject.toml e uv.lock
COPY pyproject.toml uv.lock ./

# Installa dipendenze con uv
RUN uv sync --frozen --no-dev

# Copia il codice
COPY src/ ./src/

# Copia .env.example se esiste
COPY .env.example* ./

# Crea .env se non esiste
RUN [ -f .env.example ] && cp .env.example .env || touch .env

# Usa python dal venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastmcp", "run", "src/server_mcp.py:mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
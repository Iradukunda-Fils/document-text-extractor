# Builder stage
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml requirements.txt ./

# install dependencies into a virtual environment
RUN uv venv /app/.venv && \
    uv pip install -r requirements.txt

# Runtime stage
FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
WORKDIR /app

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]

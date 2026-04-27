# --------------------------------------------------------------
# Multi-stage Dockerfile for the CrewAI “software_builder” service
# --------------------------------------------------------------

# ---------- Builder stage ----------
FROM python:3.11-slim AS builder

# Install build-time dependencies (git, curl) and a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment in /opt/venv
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy only requirements first (leverages Docker cache)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.11-slim AS runtime
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Add a non-root user for security
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser

# Copy the source code
COPY --chown=appuser:appuser . .

# Expose the port that the generated app will listen on (default 8000)
EXPOSE 8000

# Entrypoint – start the crew orchestrator
ENTRYPOINT ["python", "software_builder.py"]

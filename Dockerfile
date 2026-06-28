FROM python:3.14-slim

LABEL maintainer="mementobloom"
LABEL description="MementoBloom runtime for memory management tools"

WORKDIR /app

# System dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Runtime is stdlib-only; dev deps are optional (redis, openpyxl, etc.)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt || true

# Copy project source
COPY . .

# Ensure workspace directories exist
RUN mkdir -p /app/.agent_context/secure /app/memory/graph /app/.memento_runtime /app/projects

# Default to interactive shell; override with docker-compose command
CMD ["bash"]

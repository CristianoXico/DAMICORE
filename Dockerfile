# Single stage build for simplicity
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DAMICORE_TIMEOUT=7200 \
    DAMICORE_CHUNK_SIZE=500 \
    DAMICORE_BOOTSTRAP_SAMPLES=2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libhdf5-dev \
    libopenblas-dev \
    libhdf5-310 \
    libhdf5-hl-310 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p \
    examples \
    results \
    temp \
    data

# Create additional directories
RUN mkdir -p \
    config \
    damicore_analysis \
    external_drive \
    logs

# Make scripts executable
RUN chmod +x src/scripts/*.py

# Create non-root user
RUN groupadd -r damicore && useradd -r -g damicore damicore \
    && chown -R damicore:damicore /app

# Switch to non-root user
USER damicore

# Set health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Set labels
LABEL maintainer="DAMICORE Team" \
      version="2.1" \
      description="DAMICORE Pipeline with Fixed Visualizations, Resume Functionality and Ultra-Large File Support" \
      python.version="3.11" \
      features="checkpoint,resume,streaming,ultra-large-files,adaptive-visualizations,variable-name-mapping" \
      last_updated="2025-01-25" \
      visualization_fixes="variable-names,adaptive-sizing,label-truncation"

# Install Python dependencies as root to ensure they're in the system path
RUN pip install --no-cache-dir -r requirements.txt

# Set entrypoint to a shell script that will be created
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Set environment variables for user damicore
ENV PATH="/home/damicore/.local/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

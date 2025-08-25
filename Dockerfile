# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libhdf5-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:${PATH}" \
    DAMICORE_TIMEOUT=7200 \
    DAMICORE_CHUNK_SIZE=500 \
    DAMICORE_BOOTSTRAP_SAMPLES=2

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libhdf5-310 \
    libhdf5-hl-310 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    examples \
    results \
    temp \
    data \
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

# Set entrypoint
ENTRYPOINT ["python", "src/scripts/DAMICORE_File_Slicer_Processor.py"]

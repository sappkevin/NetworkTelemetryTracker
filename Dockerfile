FROM python:3.11-slim

# Install system dependencies for network tools
RUN apt-get update && apt-get install -y \
    iputils-ping \
    traceroute \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (including scripts in root)
COPY . .

# Make entrypoint script executable
RUN chmod +x docker_entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
RUN useradd -m -u 1000 telemetry && chown -R telemetry:telemetry /app
USER telemetry

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import docker_telemetry_service; print('Service is healthy')" || exit 1

# Run the entrypoint script
CMD ["./docker_entrypoint.sh"]

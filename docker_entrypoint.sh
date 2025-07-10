#!/bin/bash
# Docker entrypoint script that sets up InfluxDB token and starts telemetry service.

set -e

echo "Starting Network Telemetry Service in Docker..."
echo "Target(s): ${TARGET_FQDNS:-${TARGET_FQDN:-google.com}}"
echo "InfluxDB URL: ${INFLUXDB_URL:-http://influxdb2:8086}"

# Run setup script to get InfluxDB token
echo "Setting up InfluxDB token..."
python docker_setup_script.py

# Check if token setup was successful
if [ -f "/app/influx_token.txt" ]; then
    export INFLUXDB_TOKEN=$(cat /app/influx_token.txt)
    echo "InfluxDB token configured from setup script"
fi

# Start the telemetry service for all targets
python run_multi_target_collector.py
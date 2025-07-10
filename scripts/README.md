# Scripts Directory

This directory contains utility, testing, and setup scripts that are not required for Docker container operation.

## 📁 Directory Structure

### 🧪 **testing/**
Scripts for testing, validation, and verification of telemetry functionality.

- **`check_telemetry_fields.py`** - Simple field analysis without complex imports
- **`validate_telemetry_fields.py`** - Comprehensive telemetry data validation
- **`test_geolocation.py`** - Test geolocation data collection
- **`test_geolocation_simple.py`** - Simplified geolocation testing
- **`test_influx_data.py`** - Test InfluxDB data operations
- **`test_influx_schema.py`** - Validate InfluxDB schema and data structure
- **`test_telemetry_standalone.py`** - Standalone telemetry collection testing

### 🏃 **runners/**
Alternative service runners and collectors for different use cases.

- **`run_geolocation_collector.py`** - Geolocation-focused data collection
- **`run_telemetry_standalone.py`** - Standalone telemetry service runner
- **`start_telemetry_service.py`** - Service startup script
- **`telemetry_runner.py`** - Alternative telemetry runner

### ⚙️ **setup/**
Setup, configuration, and troubleshooting scripts.

- **`setup_influxdb.py`** - InfluxDB database setup and configuration
- **`fix_influxdb_auth.py`** - Fix InfluxDB authentication issues
- **`fix_telemetry_service.py`** - Telemetry service troubleshooting

### 🔧 **utilities/**
General utility scripts for data collection and storage.

- **`collect_sample_data.py`** - Generate sample telemetry data
- **`simple_storage.py`** - Simple data storage utilities

## 🐳 **Docker Integration**

The following scripts remain in the root directory as they are **required by Docker/docker-compose**:

- **`docker_setup_script.py`** - Used by `docker_entrypoint.sh` for container setup
- **`docker_telemetry_service.py`** - Container-optimized telemetry service
- **`run_multi_target_collector.py`** - Main script executed by Docker container

## 📖 **Usage Examples**

### Testing System Components
```bash
# Test telemetry collection
python scripts/testing/test_telemetry_standalone.py

# Validate all data fields
python scripts/testing/validate_telemetry_fields.py

# Test geolocation features
python scripts/testing/test_geolocation.py
```

### Local Development
```bash
# Set up InfluxDB locally
python scripts/setup/setup_influxdb.py

# Run standalone telemetry service
python scripts/runners/run_telemetry_standalone.py

# Collect sample data for testing
python scripts/utilities/collect_sample_data.py
```

### Troubleshooting
```bash
# Fix InfluxDB authentication
python scripts/setup/fix_influxdb_auth.py

# Troubleshoot telemetry service
python scripts/setup/fix_telemetry_service.py
```

## 🎯 **Script Categories**

| Category | Purpose | When to Use |
|----------|---------|-------------|
| **Testing** | Validate functionality | Development, CI/CD, troubleshooting |
| **Runners** | Alternative service execution | Local development, custom deployments |
| **Setup** | Configuration and fixes | Initial setup, troubleshooting |
| **Utilities** | Helper functions | Data generation, storage operations |

---

*This organization keeps the root directory clean while maintaining easy access to development and testing tools.*
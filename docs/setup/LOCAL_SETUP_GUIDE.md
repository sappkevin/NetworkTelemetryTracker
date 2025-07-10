# Local Environment Setup Guide

## Current Status
The telemetry service is now working in containerized environments, and you can apply these configurations to your local system.

## Local Environment Configuration

### 1. Main Telemetry Service
Use the standard telemetry service for local development. The system provides:
- Works without raw socket access (no ping command issues)
- Uses HTTP requests for latency measurement
- Collects all dashboard fields
- Supports both PostgreSQL and file-based storage

### 2. Database Setup Script
Use `setup_influxdb.py` to set up your local database properly.

### 3. Configuration Files
Copy the updated `.env` file with correct database settings.

## Local Setup Steps

### Step 1: Install Dependencies
```bash
pip install psycopg2-binary aiohttp requests
```

### Step 2: Set Up Database
Choose one of these options:

#### Option A: Use InfluxDB (Recommended)
1. Install InfluxDB locally
2. Start InfluxDB service
3. Run: `python setup_influxdb.py`

#### Option B: Use Docker InfluxDB
1. Use Docker Compose to start InfluxDB
2. Run: `docker-compose up -d influxdb2`
3. Configure with setup script

### Step 3: Test the Fixed Service
```bash
# Test single collection
python test_telemetry_standalone.py

# Start continuous monitoring
python start_telemetry_service.py
```

### Step 4: Configure Grafana Data Source
For InfluxDB integration:
1. Configure InfluxDB data source in Grafana
2. Test dashboard connectivity
3. Verify dashboard panels display data

## Key Differences for Local Environment

### Network Access
- **Container Environment**: Limited raw socket access, uses HTTP requests
- **Local**: Full network access, can use ping commands or HTTP requests

### Database Options
- **Container Environment**: Built-in InfluxDB configuration
- **Local**: Use InfluxDB for optimal performance with time-series data

### Service Management
- **Container Environment**: Docker-based service management
- **Local**: Manual service start/stop or systemd integration

## Files Used for Local Setup

1. `src/telemetry.py` - Main telemetry service
2. `setup_influxdb.py` - Database setup for InfluxDB
3. `.env` - Environment configuration
4. `docker-compose.yml` - Container orchestration

## Recommended Local Setup

For best results on your local system:

1. **Use the standard telemetry service** (`src/telemetry.py`) for full functionality
2. **Set up InfluxDB** for time-series data storage - optimized for metrics
3. **Keep the existing Grafana dashboards** - they are optimized for InfluxDB
4. **Test with sample data first** to verify dashboard functionality

## Next Steps

1. Copy the fixed files to your local environment
2. Choose your database setup (PostgreSQL recommended)
3. Run the telemetry service locally
4. Verify dashboards display data correctly
5. Set up continuous monitoring

The core telemetry collection logic is now proven to work - it just needs to be adapted to your local environment setup.
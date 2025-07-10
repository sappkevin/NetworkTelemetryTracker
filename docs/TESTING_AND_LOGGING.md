# Testing and Logging Guide

**Comprehensive testing framework and logging system for Network Telemetry Service**

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Framework](#testing-framework)
3. [Logging System](#logging-system)
4. [Health Monitoring](#health-monitoring)
5. [Service Validation](#service-validation)
6. [Continuous Integration](#continuous-integration)
7. [Production Monitoring](#production-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Network Telemetry Service includes a comprehensive testing and logging framework designed for:

- **Development**: Unit and integration testing during development
- **Validation**: End-to-end service validation and health checks
- **Production**: Structured logging and monitoring in production environments
- **Operations**: Health endpoints for container orchestration and monitoring

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Service Validator** | Comprehensive end-to-end testing | `scripts/testing/service_validator.py` |
| **Health Checker** | Component health monitoring | `src/health_check.py` |
| **Logging System** | Structured logging framework | `src/logging_config.py` |
| **Service Monitor** | HTTP monitoring endpoints | `service_monitor.py` |
| **Unit Tests** | Component-level testing | `tests/` |

---

## Testing Framework

### Test Categories

#### 1. Unit Tests (`tests/`)
Component-level testing with mocks and fixtures.

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_telemetry.py -v
```

#### 2. Integration Tests (`scripts/testing/`)
Real system integration testing.

```bash
# Test individual components
python scripts/testing/test_telemetry_standalone.py
python scripts/testing/test_influx_data.py
python scripts/testing/test_geolocation.py

# Validate field collection
python scripts/testing/validate_telemetry_fields.py
```

#### 3. End-to-End Validation
Comprehensive service validation.

```bash
# Run complete service validation
python scripts/testing/service_validator.py

# Validation includes:
# - Service health check
# - Database connectivity
# - Telemetry collection
# - Data pipeline testing
# - Dashboard compatibility
# - Performance benchmarks
# - Error handling
```

### Service Validation

The service validator performs comprehensive testing:

```python
# Example validation usage
from scripts.testing.service_validator import ServiceValidator

async def validate_service():
    validator = ServiceValidator()
    report = await validator.run_comprehensive_validation()
    
    print(f"Overall Success: {report.overall_success}")
    print(f"Tests Passed: {report.passed_tests}/{report.total_tests}")
    
    return report.overall_success
```

#### Validation Test Suite

| Test Category | Purpose | Success Criteria |
|---------------|---------|------------------|
| **Service Health** | Overall service status | All components healthy or degraded |
| **Database Connectivity** | InfluxDB connection and operations | Connection, query, and write successful |
| **Telemetry Collection** | Data collection functionality | Multiple targets successfully monitored |
| **Data Pipeline** | End-to-end data flow | Data collected, stored, and retrievable |
| **Dashboard Compatibility** | Required fields present | All dashboard fields available |
| **Performance Benchmarks** | Performance within thresholds | Collection < 30s, writes < 5s |
| **Error Handling** | Graceful error recovery | Invalid targets handled gracefully |

---

## Logging System

### Structured Logging

The service uses a comprehensive structured logging system with multiple output formats:

```python
from src.logging_config import TelemetryLogger

# Setup logging
logger = TelemetryLogger.setup_logging(
    log_level='INFO',
    log_format='console',  # or 'detailed', 'json'
    log_file='logs/telemetry.log',
    enable_json=False
)

# Log with structured data
logger.info("Collection completed", extra={
    'target': 'google.com',
    'fields_collected': 45,
    'duration_ms': 1250
})
```

### Log Formats

#### Console Format (Development)
```
2025-01-10 15:30:45 - telemetry.network - INFO - Collection completed for google.com
```

#### Detailed Format (Production Files)
```
2025-01-10 15:30:45 - telemetry.network - INFO - telemetry:collect_metrics:245 - Collection completed for google.com
```

#### JSON Format (Production/Monitoring)
```json
{
  "timestamp": "2025-01-10T15:30:45.123Z",
  "level": "INFO",
  "logger": "telemetry.network",
  "message": "Collection completed for google.com",
  "module": "telemetry",
  "function": "collect_metrics",
  "line": 245,
  "target": "google.com",
  "fields_collected": 45,
  "duration_ms": 1250
}
```

### Logging Configuration

#### Environment Variables
```bash
# Logging configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=console          # console, detailed, json
LOG_FILE=logs/telemetry.log # Optional log file path
```

#### Code Configuration
```python
# Development logging
logger = setup_development_logging()

# Production logging  
logger = setup_production_logging()

# Custom logging
logger = TelemetryLogger.setup_logging(
    log_level='DEBUG',
    log_format='json',
    log_file='logs/custom.log',
    enable_json=True
)
```

### Specialized Loggers

#### Performance Logging
```python
from src.logging_config import TelemetryLogger

# Log performance metrics
TelemetryLogger.log_performance_metrics(
    logger=logger,
    operation='telemetry_collection',
    duration=1.25,  # seconds
    success=True,
    additional_data={'target': 'google.com', 'fields': 45}
)
```

#### Service Health Logging
```python
from src.logging_config import ServiceHealthLogger

health_logger = ServiceHealthLogger(logger)

# Log service events
health_logger.log_service_start('telemetry_service', {'interval': 60})
health_logger.log_health_check('healthy', {'components': 4})
health_logger.log_database_connection('influxdb', 'connected')
```

---

## Health Monitoring

### Health Check System

The service provides comprehensive health monitoring:

```python
from src.health_check import HealthChecker

# Create health checker
health_checker = HealthChecker(config)

# Quick health check
quick_result = await health_checker.quick_health_check()

# Comprehensive health check
detailed_result = await health_checker.perform_comprehensive_health_check()
```

### Health Check Components

| Component | Purpose | Health Criteria |
|-----------|---------|-----------------|
| **Database** | InfluxDB connectivity and performance | Connection successful, response time < 2s |
| **Network** | Target reachability | Targets accessible via HTTP or DNS |
| **System Resources** | CPU, memory, disk usage | Usage below 80% thresholds |
| **Telemetry Collection** | Data collection functionality | Successful collection with adequate fields |

### Health Status Levels

- **Healthy**: All components functioning normally
- **Degraded**: Some issues but service operational
- **Unhealthy**: Critical issues affecting service
- **Unknown**: Unable to determine status

---

## Service Validation

### HTTP Monitoring Endpoints

Start the service monitor for HTTP-based health checks:

```bash
# Start service monitor
python service_monitor.py --port 8080

# Available endpoints:
# http://localhost:8080/health          - Quick health check
# http://localhost:8080/health/live     - Liveness probe
# http://localhost:8080/health/ready    - Readiness probe
# http://localhost:8080/health/detailed - Comprehensive health
# http://localhost:8080/metrics         - Prometheus metrics
# http://localhost:8080/status          - Service status
# http://localhost:8080/validate        - Trigger validation
```

### Kubernetes Integration

#### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

#### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3
```

### Prometheus Metrics

The service exposes Prometheus-compatible metrics:

```
# HELP telemetry_service_uptime_seconds Service uptime in seconds
# TYPE telemetry_service_uptime_seconds gauge
telemetry_service_uptime_seconds 3600.0

# HELP telemetry_service_health Service health status
# TYPE telemetry_service_health gauge
telemetry_service_health 1.0

# HELP telemetry_component_health Component health status
# TYPE telemetry_component_health gauge
telemetry_component_health{component="database"} 1.0
telemetry_component_health{component="network"} 1.0
telemetry_component_health{component="system_resources"} 0.5
telemetry_component_health{component="telemetry_collection"} 1.0
```

---

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test and Validate Service

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      influxdb:
        image: influxdb:2.7
        ports:
          - 8086:8086
        env:
          DOCKER_INFLUXDB_INIT_MODE: setup
          DOCKER_INFLUXDB_INIT_USERNAME: admin
          DOCKER_INFLUXDB_INIT_PASSWORD: password
          DOCKER_INFLUXDB_INIT_ORG: test
          DOCKER_INFLUXDB_INIT_BUCKET: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        python scripts/testing/test_telemetry_standalone.py
        python scripts/testing/validate_telemetry_fields.py
    
    - name: Run service validation
      run: |
        python scripts/testing/service_validator.py
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Setup pre-commit testing:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: python
        types: [python]
        args: [tests/, -v]
        pass_filenames: false
        
      - id: service-validation
        name: service-validation
        entry: python
        language: python
        args: [scripts/testing/service_validator.py]
        pass_filenames: false
EOF

# Install hooks
pre-commit install
```

---

## Production Monitoring

### Log Aggregation

#### ELK Stack Integration
```yaml
# docker-compose.yml addition for ELK
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

#### Logstash Configuration
```ruby
# logstash.conf
input {
  file {
    path => "/var/log/telemetry/*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  if [logger] =~ /telemetry/ {
    mutate {
      add_tag => ["telemetry"]
    }
  }
  
  if [performance_metric] {
    mutate {
      add_tag => ["performance"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "telemetry-logs-%{+YYYY.MM.dd}"
  }
}
```

### Alerting Rules

#### Prometheus Alert Rules
```yaml
# alerts.yml
groups:
- name: telemetry_service
  rules:
  - alert: TelemetryServiceDown
    expr: up{job="telemetry-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Telemetry service is down"
      
  - alert: TelemetryServiceUnhealthy
    expr: telemetry_service_health < 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Telemetry service health degraded"
      
  - alert: TelemetryCollectionSlow
    expr: telemetry_component_response_time_ms{component="telemetry_collection"} > 30000
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Telemetry collection is slow"
```

### Dashboard Monitoring

#### Grafana Service Health Dashboard
```json
{
  "dashboard": {
    "title": "Telemetry Service Health",
    "panels": [
      {
        "title": "Service Uptime",
        "type": "stat",
        "targets": [
          {
            "expr": "telemetry_service_uptime_seconds",
            "legendFormat": "Uptime"
          }
        ]
      },
      {
        "title": "Component Health",
        "type": "bargauge",
        "targets": [
          {
            "expr": "telemetry_component_health",
            "legendFormat": "{{component}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "timeseries",
        "targets": [
          {
            "expr": "telemetry_component_response_time_ms",
            "legendFormat": "{{component}}"
          }
        ]
      }
    ]
  }
}
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Tests Failing
```bash
# Check service health first
python service_monitor.py &
curl http://localhost:8080/health

# Run individual test components
python scripts/testing/test_influx_data.py
python scripts/testing/test_telemetry_standalone.py

# Check logs for errors
tail -f logs/telemetry.log
```

#### 2. Health Checks Failing
```bash
# Check detailed health status
curl http://localhost:8080/health/detailed

# Validate service manually
python scripts/testing/service_validator.py

# Check database connectivity
python -c "
from src.database import InfluxDBClient
from src.config import Config
import asyncio

async def test():
    db = InfluxDBClient(Config())
    await db.initialize()
    print('Database connected successfully')

asyncio.run(test())
"
```

#### 3. Logging Issues
```bash
# Check log file permissions
ls -la logs/

# Create log directory if missing
mkdir -p logs/

# Test logging configuration
python -c "
from src.logging_config import setup_development_logging
logger = setup_development_logging()
logger.info('Test log message')
"
```

#### 4. Performance Issues
```bash
# Run performance benchmarks
python scripts/testing/service_validator.py | grep -A 10 "Performance Benchmarks"

# Check system resources
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# Monitor real-time performance
curl http://localhost:8080/metrics | grep response_time
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or in code
from src.logging_config import TelemetryLogger

logger = TelemetryLogger.setup_logging(
    log_level='DEBUG',
    log_format='detailed',
    enable_json=False
)
```

### Health Check Debugging

```python
from src.health_check import HealthChecker
from src.config import Config

async def debug_health():
    checker = HealthChecker(Config())
    
    # Test individual components
    db_health = await checker.check_database_health()
    print(f"Database: {db_health.status.value} - {db_health.message}")
    
    network_health = await checker.check_network_connectivity()
    print(f"Network: {network_health.status.value} - {network_health.message}")
    
    telemetry_health = await checker.check_telemetry_collection()
    print(f"Telemetry: {telemetry_health.status.value} - {telemetry_health.message}")

# Run debug
import asyncio
asyncio.run(debug_health())
```

---

## Best Practices

### Testing
1. **Run tests regularly** during development
2. **Use service validation** before deployment
3. **Monitor test coverage** and maintain >80%
4. **Test error conditions** and edge cases
5. **Validate in production-like environment**

### Logging
1. **Use structured logging** with consistent fields
2. **Log at appropriate levels** (DEBUG for development, INFO for production)
3. **Include context** in log messages (target, duration, etc.)
4. **Avoid logging sensitive data** (tokens, passwords)
5. **Implement log rotation** to manage disk space

### Monitoring
1. **Set up health check endpoints** for orchestration
2. **Monitor service metrics** with Prometheus/Grafana
3. **Configure alerting** for critical failures
4. **Track performance trends** over time
5. **Implement automated remediation** where possible

---

*This testing and logging framework ensures reliable operation and easy troubleshooting of the Network Telemetry Service in production environments.*

**Developed by Kevin Sapp for Netflix SDE Assessment**
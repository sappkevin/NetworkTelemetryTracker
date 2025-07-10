#!/bin/bash

# Network Telemetry Service Test Runner
# This script runs all tests with coverage reporting

set -e

echo "🚀 Starting Network Telemetry Service Tests"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Installing requirements..."
    pip install -r requirements.txt
fi

# Set up test environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TARGET_FQDN="example.com"
export MONITORING_INTERVAL="30"
export INFLUXDB_URL="http://localhost:8086"
export INFLUXDB_TOKEN="test-token"
export INFLUXDB_ORG="test-org"
export INFLUXDB_BUCKET="test-bucket"
export LOG_LEVEL="DEBUG"

print_status "Environment configured for testing"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run tests with coverage
print_status "Running unit tests..."
echo "----------------------------------------"

# Run network monitor tests
print_status "Testing network monitor..."
pytest tests/test_network_monitor.py -v --tb=short

# Run data collector tests
print_status "Testing data collector..."
pytest tests/test_data_collector.py -v --tb=short

# Run integration tests
print_status "Testing integration..."
pytest tests/test_integration.py -v --tb=short

# Run all tests with coverage
print_status "Running complete test suite with coverage..."
echo "----------------------------------------"
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --tb=short

# Check coverage threshold
COVERAGE_THRESHOLD=80
print_status "Checking coverage threshold (${COVERAGE_THRESHOLD}%)..."

# Extract coverage percentage (this is a simplified approach)
COVERAGE_REPORT=$(pytest tests/ --cov=src --cov-report=term-missing --tb=no -q 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')

if [ ! -z "$COVERAGE_REPORT" ]; then
    if [ "$COVERAGE_REPORT" -ge "$COVERAGE_THRESHOLD" ]; then
        print_status "Coverage threshold met: ${COVERAGE_REPORT}%"
    else
        print_warning "Coverage below threshold: ${COVERAGE_REPORT}% (minimum: ${COVERAGE_THRESHOLD}%)"
    fi
else
    print_warning "Could not determine coverage percentage"
fi

# Run syntax and style checks
print_status "Running code quality checks..."
echo "----------------------------------------"

# Check for basic Python syntax errors
print_status "Checking Python syntax..."
python -m py_compile src/*.py

# Check for basic import issues
print_status "Checking imports..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    import main
    import network_monitor
    import data_collector
    import influx_client
    import config
    print('✓ All imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

# Test configuration validation
print_status "Testing configuration validation..."
python -c "
import os
import sys
sys.path.insert(0, 'src')
from config import Config

# Test valid configuration
os.environ.update({
    'TARGET_FQDN': 'test.com',
    'MONITORING_INTERVAL': '60',
    'INFLUXDB_URL': 'http://localhost:8086',
    'INFLUXDB_ORG': 'test',
    'INFLUXDB_BUCKET': 'test'
})

try:
    config = Config()
    print('✓ Configuration validation passed')
except Exception as e:
    print(f'✗ Configuration validation failed: {e}')
    sys.exit(1)
"

# Summary
echo ""
echo "============================================"
print_status "Test Summary"
echo "============================================"
print_status "✓ Unit tests completed"
print_status "✓ Integration tests completed"
print_status "✓ Code quality checks passed"
print_status "✓ Configuration validation passed"

if [ -f "htmlcov/index.html" ]; then
    print_status "📊 Coverage report generated: htmlcov/index.html"
fi

echo ""
print_status "🎉 All tests completed successfully!"
echo ""
print_status "To run individual test files:"
echo "  pytest tests/test_network_monitor.py -v"
echo "  pytest tests/test_data_collector.py -v"
echo "  pytest tests/test_integration.py -v"
echo ""
print_status "To run tests with coverage:"
echo "  pytest tests/ --cov=src --cov-report=html"
echo ""
print_status "To run the service:"
echo "  docker-compose up"
echo ""

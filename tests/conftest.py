"""
Test configuration and fixtures.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import MagicMock

from src.config import Config
from src.network_monitor import NetworkMonitor
from src.influx_client import InfluxDBClient
from src.data_collector import DataCollector


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Create a test configuration."""
    # Set test environment variables
    os.environ['TARGET_FQDN'] = 'example.com'
    os.environ['MONITORING_INTERVAL'] = '30'
    os.environ['INFLUXDB_URL'] = 'http://localhost:8086'
    os.environ['INFLUXDB_TOKEN'] = 'test-token'
    os.environ['INFLUXDB_ORG'] = 'test-org'
    os.environ['INFLUXDB_BUCKET'] = 'test-bucket'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    config = Config()
    
    # Clean up environment variables
    for key in ['TARGET_FQDN', 'MONITORING_INTERVAL', 'INFLUXDB_URL', 
                'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 'INFLUXDB_BUCKET', 'LOG_LEVEL']:
        if key in os.environ:
            del os.environ[key]
    
    return config


@pytest.fixture
def network_monitor(test_config):
    """Create a network monitor instance."""
    return NetworkMonitor(test_config.target_fqdn)


@pytest.fixture
def mock_influx_client():
    """Create a mock InfluxDB client."""
    mock_client = MagicMock(spec=InfluxDBClient)
    mock_client.initialize.return_value = True
    mock_client.write_metrics.return_value = True
    mock_client.close.return_value = None
    return mock_client


@pytest.fixture
def data_collector(mock_influx_client, test_config):
    """Create a data collector instance."""
    return DataCollector(mock_influx_client, test_config)


@pytest.fixture
def sample_ping_output():
    """Sample ping command output for testing."""
    return """PING example.com (93.184.216.34) 56(84) bytes of data.
64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=23.2 ms
64 bytes from 93.184.216.34: icmp_seq=2 ttl=56 time=24.1 ms
64 bytes from 93.184.216.34: icmp_seq=3 ttl=56 time=22.8 ms
64 bytes from 93.184.216.34: icmp_seq=4 ttl=56 time=23.5 ms
64 bytes from 93.184.216.34: icmp_seq=5 ttl=56 time=23.0 ms

--- example.com ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4007ms
rtt min/avg/max/mdev = 22.806/23.320/24.089/0.482 ms
"""


@pytest.fixture
def sample_traceroute_output():
    """Sample traceroute command output for testing."""
    return """traceroute to example.com (93.184.216.34), 30 hops max, 60 byte packets
 1  192.168.1.1  1.234 ms  1.123 ms  1.456 ms
 2  10.0.0.1  12.345 ms  12.234 ms  12.456 ms
 3  172.16.0.1  23.456 ms  23.345 ms  23.567 ms
 4  93.184.216.34  24.567 ms  24.456 ms  24.678 ms
"""


@pytest.fixture
def sample_metrics():
    """Sample network metrics for testing."""
    return {
        'timestamp': 1640995200,
        'target': 'example.com',
        'collection_duration': 2.5,
        'rtt_min': 22.806,
        'rtt_avg': 23.320,
        'rtt_max': 24.089,
        'rtt_mdev': 0.482,
        'packet_loss': 0.0,
        'packets_transmitted': 5,
        'packets_received': 5,
        'hop_count': 4,
        'route_path': [
            {'hop': 1, 'ip': '192.168.1.1', 'raw_data': '192.168.1.1  1.234 ms  1.123 ms  1.456 ms'},
            {'hop': 2, 'ip': '10.0.0.1', 'raw_data': '10.0.0.1  12.345 ms  12.234 ms  12.456 ms'},
            {'hop': 3, 'ip': '172.16.0.1', 'raw_data': '172.16.0.1  23.456 ms  23.345 ms  23.567 ms'},
            {'hop': 4, 'ip': '93.184.216.34', 'raw_data': '93.184.216.34  24.567 ms  24.456 ms  24.678 ms'}
        ]
    }

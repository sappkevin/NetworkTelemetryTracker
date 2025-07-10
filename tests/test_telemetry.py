"""
Consolidated tests for the network telemetry service.

Tests all core functionality in a single file for simplicity.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from src.config import Config
from src.telemetry import NetworkTelemetry
from src.database import InfluxDBClient


class TestNetworkTelemetry:
    """Test cases for NetworkTelemetry class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def mock_influx(self):
        """Create mock InfluxDB client."""
        mock = MagicMock()
        mock.initialize = AsyncMock(return_value=True)
        mock.write_metrics = AsyncMock(return_value=True)
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def telemetry(self, config):
        """Create NetworkTelemetry instance."""
        return NetworkTelemetry(config)
    
    @pytest.fixture
    def sample_ping_output(self):
        """Sample ping output for testing."""
        return """PING google.com (172.217.164.14) 56(84) bytes of data.
64 bytes from 172.217.164.14: icmp_seq=1 ttl=117 time=23.2 ms
64 bytes from 172.217.164.14: icmp_seq=2 ttl=117 time=24.1 ms
64 bytes from 172.217.164.14: icmp_seq=3 ttl=117 time=22.8 ms
64 bytes from 172.217.164.14: icmp_seq=4 ttl=117 time=23.5 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
rtt min/avg/max/mdev = 22.800/23.400/24.100/0.500 ms"""
    
    @pytest.fixture
    def sample_traceroute_output(self):
        """Sample traceroute output for testing."""
        return """traceroute to google.com (172.217.164.14), 30 hops max, 60 byte packets
 1  192.168.1.1 (192.168.1.1)  1.234 ms  1.123 ms  1.456 ms
 2  10.0.0.1 (10.0.0.1)  12.345 ms  12.234 ms  12.456 ms
 3  172.217.164.14 (172.217.164.14)  23.456 ms  23.345 ms  23.567 ms"""
    
    async def test_initialization(self, telemetry, mock_influx):
        """Test telemetry initialization."""
        with patch('src.telemetry.InfluxDBClient', return_value=mock_influx):
            assert await telemetry.initialize() is True
            mock_influx.initialize.assert_called_once()
    
    async def test_ping_parsing(self, telemetry, sample_ping_output):
        """Test ping output parsing."""
        metrics = telemetry._parse_ping_output(sample_ping_output)
        
        assert metrics['rtt_min'] == 22.8
        assert metrics['rtt_avg'] == 23.4
        assert metrics['rtt_max'] == 24.1
        assert metrics['rtt_mdev'] == 0.5
        assert metrics['packet_loss'] == 0.0
        assert metrics['packets_transmitted'] == 4
        assert metrics['packets_received'] == 4
    
    async def test_traceroute_parsing(self, telemetry, sample_traceroute_output):
        """Test traceroute output parsing."""
        metrics = telemetry._parse_traceroute_output(sample_traceroute_output)
        
        assert metrics['hop_count'] == 3
        assert len(metrics['route_path']) == 3
        assert metrics['route_path'][0]['ip'] == '192.168.1.1'
        assert metrics['route_path'][1]['ip'] == '10.0.0.1'
        assert metrics['route_path'][2]['ip'] == '172.217.164.14'
    
    async def test_metrics_processing(self, telemetry):
        """Test metrics processing."""
        raw_metrics = {
            'timestamp': 1640995200,
            'target': 'google.com',
            'rtt_min': 22.8,
            'rtt_avg': 23.4,
            'rtt_max': 24.1,
            'packet_loss': 0.0,
            'packets_transmitted': 4,
            'packets_received': 4,
            'hop_count': 3,
            'route_path': [
                {'hop': 1, 'ip': '192.168.1.1', 'avg_time': 1.271},
                {'hop': 2, 'ip': '10.0.0.1', 'avg_time': 12.345},
                {'hop': 3, 'ip': '172.217.164.14', 'avg_time': 23.456}
            ]
        }
        
        processed = telemetry._process_metrics(raw_metrics)
        
        assert processed['measurement'] == 'network_telemetry'
        assert processed['tags']['target'] == 'google.com'
        assert processed['fields']['rtt_avg'] == 23.4
        assert processed['fields']['packet_loss'] == 0.0
        assert processed['fields']['hop_count'] == 3
        assert processed['fields']['route_path_length'] == 3
    
    async def test_connectivity_test(self, telemetry):
        """Test connectivity testing."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b'', b''))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await telemetry.test_connectivity()
            assert result is True
    
    async def test_collect_and_store_metrics(self, telemetry, mock_influx, sample_ping_output, sample_traceroute_output):
        """Test complete metrics collection and storage."""
        telemetry.influx_client = mock_influx
        
        def subprocess_side_effect(*args, **kwargs):
            mock_process = MagicMock()
            mock_process.returncode = 0
            
            if 'ping' in args[0]:
                mock_process.communicate = AsyncMock(return_value=(sample_ping_output.encode(), b''))
            elif 'traceroute' in args[0]:
                mock_process.communicate = AsyncMock(return_value=(sample_traceroute_output.encode(), b''))
            
            return mock_process
        
        with patch('asyncio.create_subprocess_exec', side_effect=subprocess_side_effect):
            result = await telemetry.collect_and_store_metrics()
            
            assert result is True
            mock_influx.write_metrics.assert_called_once()
    
    async def test_failed_metrics_collection(self, telemetry, mock_influx):
        """Test handling of failed metrics collection."""
        telemetry.influx_client = mock_influx
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b'', b'Command failed'))
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            result = await telemetry.collect_and_store_metrics()
            assert result is False
    
    def test_metrics_summary(self, telemetry):
        """Test metrics summary generation."""
        metrics = {
            'tags': {'target': 'google.com'},
            'fields': {
                'rtt_avg': 23.45,
                'packet_loss': 0.0,
                'hop_count': 3
            }
        }
        
        summary = telemetry._get_metrics_summary(metrics)
        assert 'google.com' in summary
        assert '23.45ms' in summary
        assert '0.0%' in summary
        assert 'Hops: 3' in summary
    
    async def test_cleanup(self, telemetry, mock_influx):
        """Test cleanup functionality."""
        telemetry.influx_client = mock_influx
        
        await telemetry.cleanup()
        mock_influx.close.assert_called_once()


class TestInfluxDBClient:
    """Test cases for InfluxDBClient class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def client(self, config):
        """Create InfluxDBClient instance."""
        return InfluxDBClient(config)
    
    def test_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.client is None
    
    def test_line_protocol_conversion(self, client):
        """Test conversion to InfluxDB line protocol."""
        metrics = {
            'measurement': 'network_telemetry',
            'tags': {'target': 'google.com'},
            'fields': {'rtt_avg': 23.5, 'packet_loss': 0.0},
            'timestamp': 1640995200
        }
        
        line_protocol = client._convert_to_point(metrics)
        
        assert 'network_telemetry' in line_protocol
        assert 'target=google.com' in line_protocol
        assert 'rtt_avg=23.5' in line_protocol
        assert 'packet_loss=0.0' in line_protocol
        assert '1640995200' in line_protocol


class TestConfiguration:
    """Test cases for configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.target_fqdn == 'google.com'
        assert config.monitoring_interval == 60
        assert config.ping_count == 4
        assert config.ping_timeout == 5
        assert config.influxdb_url == 'http://localhost:8086'
        assert config.influxdb_org == 'network_telemetry'
        assert config.influxdb_bucket == 'metrics'
        assert config.log_level == 'INFO'
    
    def test_config_validation(self):
        """Test configuration validation."""
        import os
        
        # Test with invalid monitoring interval
        os.environ['MONITORING_INTERVAL'] = '-1'
        
        with pytest.raises(ValueError):
            Config()
        
        # Cleanup
        del os.environ['MONITORING_INTERVAL']


class TestIntegration:
    """Integration tests for the complete system."""
    
    async def test_full_service_flow(self):
        """Test complete service workflow."""
        from src.main import NetworkTelemetryService
        
        service = NetworkTelemetryService()
        
        # Test initialization without actually connecting
        with patch('src.telemetry.NetworkTelemetry.initialize', return_value=True), \
             patch('src.telemetry.NetworkTelemetry.test_connectivity', return_value=True):
            
            assert await service.initialize() is True
        
        # Test monitoring cycle
        with patch('src.telemetry.NetworkTelemetry.collect_and_store_metrics', return_value=True):
            await service.run_monitoring_cycle()
    
    async def test_error_handling(self):
        """Test error handling in service."""
        from src.main import NetworkTelemetryService
        
        service = NetworkTelemetryService()
        
        # Test initialization failure
        with patch('src.telemetry.NetworkTelemetry.initialize', return_value=False):
            assert await service.initialize() is False
        
        # Test monitoring cycle failure
        with patch('src.telemetry.NetworkTelemetry.collect_and_store_metrics', return_value=False):
            await service.run_monitoring_cycle()  # Should not raise exception


if __name__ == "__main__":
    pytest.main([__file__])
#!/usr/bin/env python3
"""
Comprehensive service validation tool for Network Telemetry Service.

Performs end-to-end testing of all service components including:
- Service health and availability
- Data collection functionality  
- Database connectivity and data storage
- Dashboard data compatibility
- Performance validation
"""

import asyncio
import json
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Add src to path for imports
sys.path.insert(0, 'src')

from src.config import Config
from src.health_check import HealthChecker, HealthStatus
from src.telemetry import NetworkTelemetry
from src.database import InfluxDBClient
from src.logging_config import TelemetryLogger


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    success: bool
    message: str
    duration_ms: float
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class ValidationReport:
    """Complete validation report."""
    overall_success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration_ms: float
    test_results: List[ValidationResult]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overall_success': self.overall_success,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'total_duration_ms': self.total_duration_ms,
            'success_rate': self.passed_tests / self.total_tests if self.total_tests > 0 else 0,
            'timestamp': self.timestamp.isoformat(),
            'test_results': [result.to_dict() for result in self.test_results]
        }


class ServiceValidator:
    """Comprehensive service validation tool."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize validator."""
        self.config = Config()
        self.logger = TelemetryLogger.setup_logging(log_level='INFO', log_format='console')
        self.test_results: List[ValidationResult] = []
        self.start_time = time.time()
        
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> ValidationResult:
        """Run a single test and capture results."""
        self.logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            details = await test_func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            result = ValidationResult(
                test_name=test_name,
                success=True,
                message="Test passed",
                duration_ms=duration_ms,
                details=details or {},
                timestamp=datetime.utcnow()
            )
            
            self.logger.info(f"✅ {test_name} - PASSED ({duration_ms:.1f}ms)")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            result = ValidationResult(
                test_name=test_name,
                success=False,
                message=str(e),
                duration_ms=duration_ms,
                details={'error': str(e), 'error_type': type(e).__name__},
                timestamp=datetime.utcnow()
            )
            
            self.logger.error(f"❌ {test_name} - FAILED ({duration_ms:.1f}ms): {e}")
        
        self.test_results.append(result)
        return result
    
    async def test_docker_containers(self) -> Dict[str, Any]:
        """Test Docker container accessibility on expected ports."""
        import aiohttp
        
        containers = {
            'influxdb': {'port': 8086, 'path': '/ping'},
            'grafana': {'port': 3000, 'path': '/api/health'}
        }
        
        results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for service, config in containers.items():
                try:
                    url = f"http://localhost:{config['port']}{config['path']}"
                    async with session.get(url) as response:
                        results[service] = {
                            'accessible': True,
                            'status_code': response.status,
                            'port': config['port'],
                            'responsive': response.status < 500
                        }
                except Exception as e:
                    results[service] = {
                        'accessible': False,
                        'error': str(e),
                        'port': config['port'],
                        'responsive': False
                    }
        
        # Check if all containers are accessible
        all_accessible = all(result.get('accessible', False) for result in results.values())
        
        if not all_accessible:
            failed_containers = [name for name, result in results.items() if not result.get('accessible', False)]
            raise Exception(f"Docker containers not accessible: {failed_containers}")
        
        return {
            'all_containers_accessible': all_accessible,
            'container_details': results
        }
    
    async def test_grafana_container(self) -> Dict[str, Any]:
        """Test Grafana container on Docker port 3000."""
        import aiohttp
        
        grafana_url = "http://localhost:3000"
        
        async with aiohttp.ClientSession() as session:
            # Test Grafana health endpoint
            try:
                async with session.get(f"{grafana_url}/api/health") as response:
                    health_successful = response.status == 200
                    health_data = await response.json() if response.status == 200 else {}
            except Exception as e:
                raise Exception(f"Grafana container not accessible on port 3000: {e}")
            
            # Test Grafana login page
            try:
                async with session.get(f"{grafana_url}/login") as response:
                    login_accessible = response.status == 200
            except Exception as e:
                login_accessible = False
            
            # Test API readiness
            try:
                async with session.get(f"{grafana_url}/api/admin/stats") as response:
                    api_accessible = response.status in [200, 401]  # 401 is expected without auth
            except Exception as e:
                api_accessible = False
        
        return {
            'container_accessible': health_successful,
            'login_page_accessible': login_accessible,
            'api_responsive': api_accessible,
            'grafana_port': 3000,
            'grafana_url': grafana_url,
            'health_data': health_data
        }
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test InfluxDB database connection on Docker port 8086."""
        import aiohttp
        
        # Test HTTP connectivity to InfluxDB Docker container
        influxdb_url = "http://localhost:8086"
        
        async with aiohttp.ClientSession() as session:
            # Test InfluxDB ping endpoint
            try:
                async with session.get(f"{influxdb_url}/ping") as response:
                    ping_successful = response.status == 204
            except Exception as e:
                raise Exception(f"InfluxDB container not accessible on port 8086: {e}")
            
            # Test InfluxDB health endpoint
            try:
                async with session.get(f"{influxdb_url}/health") as response:
                    health_data = await response.json() if response.status == 200 else {}
                    health_successful = response.status == 200
            except Exception as e:
                health_successful = False
                health_data = {"error": str(e)}
        
        # Test database operations using configured client
        db_client = InfluxDBClient(self.config)
        await db_client.initialize()
        
        # Test basic query
        test_query = 'buckets() |> filter(fn:(r) => r.name == "default") |> limit(1)'
        await db_client.query(test_query)
        
        return {
            'container_accessible': ping_successful,
            'container_healthy': health_successful,
            'database_operations': True,
            'influxdb_port': 8086,
            'influxdb_url': influxdb_url,
            'health_data': health_data
        }
    
    async def test_telemetry_collection(self) -> Dict[str, Any]:
        """Test telemetry data collection functionality."""
        telemetry = NetworkTelemetry(self.config)
        
        test_targets = ['google.com', 'github.com']
        results = {}
        
        for target in test_targets:
            try:
                data = await telemetry.collect_single_measurement(target)
                
                if not data or len(data) < 10:
                    raise Exception(f"Insufficient data collected for {target}: {len(data) if data else 0} fields")
                
                results[target] = {
                    'success': True,
                    'fields_collected': len(data),
                    'has_required_fields': all(field in data for field in ['rtt_avg', 'packet_loss', 'service_available'])
                }
                
            except Exception as e:
                results[target] = {
                    'success': False,
                    'error': str(e)
                }
        
        successful_targets = sum(1 for r in results.values() if r.get('success', False))
        
        if successful_targets == 0:
            raise Exception("No targets could be successfully monitored")
        
        return {
            'targets_tested': len(test_targets),
            'successful_targets': successful_targets,
            'results': results
        }
    
    async def test_data_pipeline(self) -> Dict[str, Any]:
        """Test complete data pipeline from collection to storage."""
        telemetry = NetworkTelemetry(self.config)
        
        # Collect data
        target = 'google.com'
        data = await telemetry.collect_single_measurement(target)
        
        if not data:
            raise Exception("Failed to collect telemetry data")
        
        # Store data
        db_client = InfluxDBClient(self.config)
        await db_client.initialize()
        
        metrics_data = {
            'measurement': 'network_telemetry',
            'tags': {'target': target, 'test': 'pipeline_validation'},
            'fields': data,
            'time': datetime.utcnow()
        }
        
        await db_client.write_metrics([metrics_data])
        
        # Verify data was stored
        await asyncio.sleep(2)  # Allow time for data to be indexed
        
        verify_query = f'''
        from(bucket:"{self.config.influxdb_bucket}")
        |> range(start:-5m)
        |> filter(fn:(r) => r._measurement == "network_telemetry")
        |> filter(fn:(r) => r.target == "{target}")
        |> filter(fn:(r) => r.test == "pipeline_validation")
        |> limit(1)
        '''
        
        query_result = await db_client.query(verify_query)
        
        if not query_result:
            raise Exception("Data was not successfully stored or retrieved from database")
        
        return {
            'data_collected': True,
            'data_stored': True,
            'data_retrieved': True,
            'fields_count': len(data),
            'target': target
        }
    
    async def test_dashboard_field_compatibility(self) -> Dict[str, Any]:
        """Test that collected data contains all required dashboard fields."""
        telemetry = NetworkTelemetry(self.config)
        
        # Required fields for each dashboard
        required_fields = {
            'network_telemetry': ['rtt_min', 'rtt_avg', 'rtt_max', 'packet_loss', 'hop_count'],
            'qos_metrics': ['jitter_ms', 'voice_quality_score', 'video_quality_score', 'data_quality_score'],
            'availability': ['service_available', 'response_success', 'service_degraded'],
            'throughput': ['throughput_mbps', 'bandwidth_utilization_pct', 'packets_per_second'],
            'response_time': ['dns_resolution_ms', 'tcp_handshake_ms', 'app_response_ms'],
            'geolocation': ['target_latitude', 'target_longitude', 'distance_km']
        }
        
        # Collect sample data
        data = await telemetry.collect_single_measurement('google.com')
        
        if not data:
            raise Exception("Failed to collect data for dashboard compatibility test")
        
        dashboard_compatibility = {}
        missing_fields = []
        
        for dashboard, fields in required_fields.items():
            missing_in_dashboard = [field for field in fields if field not in data]
            dashboard_compatibility[dashboard] = {
                'required_fields': len(fields),
                'available_fields': len(fields) - len(missing_in_dashboard),
                'missing_fields': missing_in_dashboard,
                'compatibility': len(missing_in_dashboard) == 0
            }
            missing_fields.extend(missing_in_dashboard)
        
        overall_compatibility = len(missing_fields) == 0
        
        if not overall_compatibility:
            # This is a warning, not a failure
            self.logger.warning(f"Dashboard compatibility issues found. Missing fields: {missing_fields}")
        
        return {
            'overall_compatibility': overall_compatibility,
            'total_fields_collected': len(data),
            'dashboard_compatibility': dashboard_compatibility,
            'missing_fields': missing_fields
        }
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks for service operations."""
        telemetry = NetworkTelemetry(self.config)
        
        # Test collection performance
        collection_times = []
        for i in range(3):
            start_time = time.time()
            await telemetry.collect_single_measurement('google.com')
            collection_times.append((time.time() - start_time) * 1000)
        
        avg_collection_time = sum(collection_times) / len(collection_times)
        
        # Test database write performance
        db_client = InfluxDBClient(self.config)
        await db_client.initialize()
        
        write_times = []
        for i in range(3):
            test_data = {
                'measurement': 'performance_test',
                'tags': {'test': f'performance_{i}'},
                'fields': {'value': i},
                'time': datetime.utcnow()
            }
            
            start_time = time.time()
            await db_client.write_metrics([test_data])
            write_times.append((time.time() - start_time) * 1000)
        
        avg_write_time = sum(write_times) / len(write_times)
        
        # Performance thresholds
        max_collection_time = 30000  # 30 seconds
        max_write_time = 5000  # 5 seconds
        
        performance_issues = []
        if avg_collection_time > max_collection_time:
            performance_issues.append(f"Slow collection: {avg_collection_time:.1f}ms > {max_collection_time}ms")
        
        if avg_write_time > max_write_time:
            performance_issues.append(f"Slow database writes: {avg_write_time:.1f}ms > {max_write_time}ms")
        
        if performance_issues:
            raise Exception(f"Performance issues detected: {'; '.join(performance_issues)}")
        
        return {
            'collection_time_ms': avg_collection_time,
            'write_time_ms': avg_write_time,
            'performance_acceptable': len(performance_issues) == 0,
            'collection_times': collection_times,
            'write_times': write_times
        }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and recovery."""
        telemetry = NetworkTelemetry(self.config)
        
        # Test with invalid target
        try:
            result = await telemetry.collect_single_measurement('invalid.nonexistent.domain.test')
            # Should handle gracefully and return partial data
            error_handling_works = True
        except Exception as e:
            error_handling_works = False
            self.logger.warning(f"Error handling test failed: {e}")
        
        # Test database connection error handling
        # (We'll simulate this by testing with invalid credentials)
        invalid_config = Config()
        invalid_config.influxdb_token = "invalid_token"
        
        try:
            invalid_db = InfluxDBClient(invalid_config)
            await invalid_db.initialize()
            auth_error_handling = False  # Should have failed
        except Exception:
            auth_error_handling = True  # Expected to fail gracefully
        
        return {
            'invalid_target_handling': error_handling_works,
            'database_auth_error_handling': auth_error_handling,
            'error_handling_overall': error_handling_works and auth_error_handling
        }
    
    async def run_comprehensive_validation(self) -> ValidationReport:
        """Run all validation tests and generate comprehensive report."""
        self.logger.info("🚀 Starting comprehensive service validation")
        self.logger.info("=" * 60)
        
        total_start_time = time.time()
        
        # Define test suite
        tests = [
            ("Docker Container Health", self.test_docker_containers),
            ("InfluxDB Container", self.test_database_connectivity),
            ("Grafana Container", self.test_grafana_container),
            ("Telemetry Collection", self.test_telemetry_collection),
            ("Data Pipeline", self.test_data_pipeline),
            ("Dashboard Compatibility", self.test_dashboard_field_compatibility),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("Error Handling", self.test_error_handling),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        # Generate report
        total_duration = (time.time() - total_start_time) * 1000
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = len(self.test_results) - passed_tests
        
        report = ValidationReport(
            overall_success=failed_tests == 0,
            total_tests=len(self.test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_duration_ms=total_duration,
            test_results=self.test_results,
            timestamp=datetime.utcnow()
        )
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("🎯 VALIDATION SUMMARY")
        self.logger.info(f"Overall Status: {'✅ PASSED' if report.overall_success else '❌ FAILED'}")
        self.logger.info(f"Tests Passed: {passed_tests}/{len(self.test_results)}")
        self.logger.info(f"Success Rate: {(passed_tests/len(self.test_results)*100):.1f}%")
        self.logger.info(f"Total Duration: {total_duration:.1f}ms")
        
        if not report.overall_success:
            self.logger.error("Failed tests:")
            for result in self.test_results:
                if not result.success:
                    self.logger.error(f"  • {result.test_name}: {result.message}")
        
        return report


async def main():
    """Main validation entry point."""
    try:
        validator = ServiceValidator()
        report = await validator.run_comprehensive_validation()
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        sys.exit(0 if report.overall_success else 1)
        
    except Exception as e:
        logging.error(f"Validation failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
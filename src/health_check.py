"""
Health check system for Network Telemetry Service.

Provides comprehensive health monitoring including service status,
database connectivity, network reachability, and performance metrics.
"""

import asyncio
import time
import json
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import logging

from .config import Config
from .database import InfluxDBClient
from .logging_config import ServiceHealthLogger


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class ServiceHealth:
    """Overall service health status."""
    status: HealthStatus
    components: List[HealthCheckResult]
    uptime_seconds: float
    version: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'status': self.status.value,
            'uptime_seconds': self.uptime_seconds,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'components': [component.to_dict() for component in self.components]
        }


class HealthChecker:
    """Comprehensive health check system for telemetry service."""
    
    def __init__(self, config: Config):
        """Initialize health checker."""
        self.config = config
        self.logger = logging.getLogger('telemetry.health')
        self.health_logger = ServiceHealthLogger(self.logger)
        self.start_time = time.time()
        self.version = "1.0.0"  # Should be loaded from config or environment
        
        # Health check thresholds
        self.max_response_time_ms = 5000
        self.max_database_response_time_ms = 2000
        self.max_network_response_time_ms = 10000
        
    async def check_database_health(self) -> HealthCheckResult:
        """Check InfluxDB database connectivity and performance."""
        start_time = time.time()
        
        try:
            # Create database client
            db_client = InfluxDBClient(self.config)
            
            # Test connection
            await db_client.initialize()
            
            # Test basic query
            test_query = 'buckets() |> filter(fn:(r) => r.name == "default") |> limit(1)'
            await db_client.query(test_query)
            
            response_time = (time.time() - start_time) * 1000
            
            if response_time > self.max_database_response_time_ms:
                status = HealthStatus.DEGRADED
                message = f"Database responding slowly ({response_time:.1f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection healthy"
            
            details = {
                'database_url': self.config.influxdb_url,
                'organization': self.config.influxdb_org,
                'bucket': self.config.influxdb_bucket,
                'response_time_ms': round(response_time, 2)
            }
            
            self.health_logger.log_database_connection('influxdb', 'connected', details)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.UNHEALTHY
            message = f"Database connection failed: {str(e)}"
            details = {
                'error': str(e),
                'database_url': self.config.influxdb_url,
                'response_time_ms': round(response_time, 2)
            }
            
            self.health_logger.log_database_connection('influxdb', 'failed', details)
        
        return HealthCheckResult(
            component="database",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            response_time_ms=round(response_time, 2)
        )
    
    async def check_network_connectivity(self, targets: Optional[List[str]] = None) -> HealthCheckResult:
        """Check network connectivity to monitoring targets."""
        start_time = time.time()
        
        if not targets:
            targets = self.config.target_fqdn.split(',') if hasattr(self.config, 'target_fqdn') else ['google.com']
        
        successful_targets = []
        failed_targets = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for target in targets:
                    target = target.strip()
                    try:
                        # Test HTTP connectivity
                        async with session.get(f'http://{target}', timeout=5) as response:
                            if response.status < 500:
                                successful_targets.append({
                                    'target': target,
                                    'status_code': response.status,
                                    'reachable': True
                                })
                            else:
                                failed_targets.append({
                                    'target': target,
                                    'status_code': response.status,
                                    'error': f'HTTP {response.status}'
                                })
                    except Exception as e:
                        # Try DNS resolution as fallback
                        try:
                            socket.gethostbyname(target)
                            successful_targets.append({
                                'target': target,
                                'dns_resolvable': True,
                                'http_reachable': False
                            })
                        except Exception:
                            failed_targets.append({
                                'target': target,
                                'error': str(e)
                            })
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status
            if not successful_targets:
                status = HealthStatus.UNHEALTHY
                message = "No targets reachable"
            elif failed_targets:
                status = HealthStatus.DEGRADED
                message = f"{len(successful_targets)}/{len(targets)} targets reachable"
            else:
                status = HealthStatus.HEALTHY
                message = "All targets reachable"
            
            details = {
                'successful_targets': successful_targets,
                'failed_targets': failed_targets,
                'total_targets': len(targets),
                'success_rate': len(successful_targets) / len(targets),
                'response_time_ms': round(response_time, 2)
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.UNHEALTHY
            message = f"Network connectivity check failed: {str(e)}"
            details = {
                'error': str(e),
                'targets': targets,
                'response_time_ms': round(response_time, 2)
            }
        
        return HealthCheckResult(
            component="network",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            response_time_ms=round(response_time, 2)
        )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            issues = []
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 80:
                issues.append(f"High memory usage: {memory.percent}%")
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent}%")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 2 else HealthStatus.UNHEALTHY
                message = f"Resource issues: {', '.join(issues)}"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            details = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'issues': issues
            }
            
        except ImportError:
            # psutil not available, basic check
            status = HealthStatus.UNKNOWN
            message = "System resource monitoring not available (psutil not installed)"
            details = {'error': 'psutil module not available'}
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = f"System resource check failed: {str(e)}"
            details = {'error': str(e)}
        
        response_time = (time.time() - start_time) * 1000
        
        return HealthCheckResult(
            component="system_resources",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            response_time_ms=round(response_time, 2)
        )
    
    async def check_telemetry_collection(self) -> HealthCheckResult:
        """Check if telemetry collection is working properly."""
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from .telemetry import NetworkTelemetry
            
            # Create telemetry instance
            telemetry = NetworkTelemetry(self.config)
            
            # Test single collection
            test_target = 'google.com'
            result = await telemetry.collect_single_measurement(test_target)
            
            response_time = (time.time() - start_time) * 1000
            
            if result and len(result) > 10:  # Should have collected multiple fields
                status = HealthStatus.HEALTHY
                message = f"Telemetry collection working ({len(result)} fields collected)"
                details = {
                    'test_target': test_target,
                    'fields_collected': len(result),
                    'sample_fields': list(result.keys())[:10],
                    'collection_time_ms': round(response_time, 2)
                }
            else:
                status = HealthStatus.DEGRADED
                message = "Telemetry collection returned insufficient data"
                details = {
                    'test_target': test_target,
                    'fields_collected': len(result) if result else 0,
                    'collection_time_ms': round(response_time, 2)
                }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.UNHEALTHY
            message = f"Telemetry collection failed: {str(e)}"
            details = {
                'error': str(e),
                'collection_time_ms': round(response_time, 2)
            }
        
        return HealthCheckResult(
            component="telemetry_collection",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            response_time_ms=round(response_time, 2)
        )
    
    async def perform_comprehensive_health_check(self) -> ServiceHealth:
        """Perform all health checks and return overall status."""
        start_time = time.time()
        
        self.logger.info("Starting comprehensive health check")
        
        # Run all health checks concurrently
        health_checks = await asyncio.gather(
            self.check_database_health(),
            self.check_network_connectivity(),
            self.check_system_resources(),
            self.check_telemetry_collection(),
            return_exceptions=True
        )
        
        # Process results
        components = []
        for check in health_checks:
            if isinstance(check, Exception):
                components.append(HealthCheckResult(
                    component="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(check)}",
                    details={'error': str(check)},
                    timestamp=datetime.utcnow(),
                    response_time_ms=0
                ))
            else:
                components.append(check)
        
        # Determine overall status
        statuses = [comp.status for comp in components]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN
        
        uptime = time.time() - self.start_time
        
        service_health = ServiceHealth(
            status=overall_status,
            components=components,
            uptime_seconds=uptime,
            version=self.version,
            timestamp=datetime.utcnow()
        )
        
        # Log overall result
        total_time = (time.time() - start_time) * 1000
        self.health_logger.log_health_check(
            overall_status.value,
            {
                'total_components': len(components),
                'healthy_components': len([c for c in components if c.status == HealthStatus.HEALTHY]),
                'total_check_time_ms': round(total_time, 2),
                'uptime_seconds': uptime
            }
        )
        
        return service_health
    
    async def quick_health_check(self) -> Dict[str, Any]:
        """Perform a quick health check for liveness probes."""
        start_time = time.time()
        
        try:
            # Quick database ping
            db_client = InfluxDBClient(self.config)
            await db_client.initialize()
            
            # Quick network test
            socket.gethostbyname('google.com')
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': round(response_time, 2),
                'uptime_seconds': time.time() - self.start_time
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': round(response_time, 2),
                'uptime_seconds': time.time() - self.start_time,
                'error': str(e)
            }
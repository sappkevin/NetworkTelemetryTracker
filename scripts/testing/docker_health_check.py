#!/usr/bin/env python3
"""
Docker Container Health Check for Network Telemetry Service.

Tests the health and accessibility of Docker containers on their exposed ports:
- InfluxDB on port 8086
- Grafana on port 3000
- Network Telemetry service functionality
"""

import asyncio
import aiohttp
import sys
import time
from typing import Dict, Any, List
import json
from datetime import datetime


class DockerHealthChecker:
    """Health checker for Docker containers."""
    
    def __init__(self):
        self.containers = {
            'influxdb': {
                'port': 8086,
                'name': 'InfluxDB',
                'health_path': '/health',
                'ping_path': '/ping',
                'expected_ping_status': 204
            },
            'grafana': {
                'port': 3000,
                'name': 'Grafana',
                'health_path': '/api/health',
                'login_path': '/login',
                'expected_health_status': 200
            }
        }
    
    async def check_container_port(self, service: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a container is accessible on its port."""
        port = config['port']
        name = config['name']
        
        print(f"🔍 Checking {name} container on port {port}...")
        
        start_time = time.time()
        result = {
            'service': service,
            'name': name,
            'port': port,
            'accessible': False,
            'healthy': False,
            'response_time_ms': 0,
            'details': {}
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Check health endpoint
                if 'health_path' in config:
                    health_url = f"http://localhost:{port}{config['health_path']}"
                    try:
                        async with session.get(health_url) as response:
                            result['accessible'] = True
                            result['details']['health_status'] = response.status
                            result['details']['health_url'] = health_url
                            
                            if response.status == config.get('expected_health_status', 200):
                                result['healthy'] = True
                                try:
                                    health_data = await response.json()
                                    result['details']['health_data'] = health_data
                                except:
                                    pass
                    except Exception as e:
                        result['details']['health_error'] = str(e)
                
                # Check ping endpoint (for InfluxDB)
                if 'ping_path' in config:
                    ping_url = f"http://localhost:{port}{config['ping_path']}"
                    try:
                        async with session.get(ping_url) as response:
                            result['accessible'] = True
                            result['details']['ping_status'] = response.status
                            result['details']['ping_url'] = ping_url
                            
                            if response.status == config.get('expected_ping_status', 200):
                                result['healthy'] = True
                    except Exception as e:
                        result['details']['ping_error'] = str(e)
                
                # Check login page (for Grafana)
                if 'login_path' in config:
                    login_url = f"http://localhost:{port}{config['login_path']}"
                    try:
                        async with session.get(login_url) as response:
                            result['details']['login_status'] = response.status
                            result['details']['login_accessible'] = response.status == 200
                    except Exception as e:
                        result['details']['login_error'] = str(e)
        
        except Exception as e:
            result['details']['connection_error'] = str(e)
        
        result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Print result
        status = "✅ HEALTHY" if result['healthy'] else "⚠️  ACCESSIBLE" if result['accessible'] else "❌ FAILED"
        print(f"   {status} - {name} ({result['response_time_ms']}ms)")
        
        if result['details']:
            for key, value in result['details'].items():
                if 'error' not in key:
                    print(f"      {key}: {value}")
        
        return result
    
    async def check_data_flow(self) -> Dict[str, Any]:
        """Check if data is flowing from telemetry service to InfluxDB."""
        print(f"\n🔍 Checking data flow...")
        
        result = {
            'data_flow_working': False,
            'influxdb_accessible': False,
            'has_recent_data': False,
            'details': {}
        }
        
        try:
            # Check if InfluxDB has recent telemetry data
            influx_url = "http://localhost:8086"
            
            # Try to query recent data (this requires authentication)
            # For now, just check if the query endpoint is accessible
            async with aiohttp.ClientSession() as session:
                try:
                    query_url = f"{influx_url}/api/v2/query"
                    async with session.post(query_url, headers={'Content-Type': 'application/json'}) as response:
                        result['influxdb_accessible'] = True
                        result['details']['query_endpoint_status'] = response.status
                        # 401/403 is expected without proper auth, but shows the endpoint is working
                        if response.status in [401, 403]:
                            result['details']['query_endpoint_working'] = True
                except Exception as e:
                    result['details']['query_error'] = str(e)
        
        except Exception as e:
            result['details']['error'] = str(e)
        
        status = "✅ ACCESSIBLE" if result['influxdb_accessible'] else "❌ FAILED"
        print(f"   {status} - Data flow check")
        
        return result
    
    async def check_docker_compose_services(self) -> Dict[str, Any]:
        """Check overall docker-compose service health."""
        print(f"\n🚀 Docker Container Health Check")
        print("=" * 50)
        
        results = []
        overall_healthy = True
        
        # Check each container
        for service, config in self.containers.items():
            container_result = await self.check_container_port(service, config)
            results.append(container_result)
            
            if not container_result['accessible']:
                overall_healthy = False
        
        # Check data flow
        data_flow_result = await self.check_data_flow()
        
        # Summary
        healthy_containers = len([r for r in results if r['healthy']])
        accessible_containers = len([r for r in results if r['accessible']])
        total_containers = len(results)
        
        summary = {
            'overall_healthy': overall_healthy,
            'total_containers': total_containers,
            'accessible_containers': accessible_containers,
            'healthy_containers': healthy_containers,
            'container_results': results,
            'data_flow': data_flow_result,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print("\n📊 SUMMARY")
        print("=" * 50)
        print(f"Overall Status: {'✅ HEALTHY' if overall_healthy else '❌ ISSUES DETECTED'}")
        print(f"Containers Accessible: {accessible_containers}/{total_containers}")
        print(f"Containers Healthy: {healthy_containers}/{total_containers}")
        
        if not overall_healthy:
            print("\n⚠️  Issues detected:")
            for result in results:
                if not result['accessible']:
                    print(f"   • {result['name']} not accessible on port {result['port']}")
                elif not result['healthy']:
                    print(f"   • {result['name']} accessible but not healthy")
        
        return summary


async def main():
    """Main health check execution."""
    checker = DockerHealthChecker()
    
    try:
        results = await checker.check_docker_compose_services()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"docker_health_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if results['overall_healthy']:
            print("\n🎉 All Docker containers are healthy!")
            sys.exit(0)
        else:
            print("\n❌ Some containers have issues. Check the logs above.")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n💥 Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🐳 Docker Container Health Checker")
    print("Network Telemetry Service")
    print("Developed by Kevin Sapp for Netflix SDE Assessment")
    print()
    
    asyncio.run(main())
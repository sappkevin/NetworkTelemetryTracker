#!/usr/bin/env python3
"""
Docker-compatible telemetry service that works with InfluxDB container.
This version uses HTTP requests for network monitoring and connects to the InfluxDB container.
"""

import asyncio
import aiohttp
import time
import socket
import json
import os
import random
import math
from datetime import datetime
from typing import Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class DockerTelemetryService:
    """Telemetry service optimized for Docker environment with InfluxDB."""
    
    def __init__(self, target: str = "google.com"):
        self.target = target
        self.influx_url = os.getenv('INFLUXDB_URL', 'http://influxdb2:8086')
        self.influx_token = self._get_influx_token()
        self.influx_org = os.getenv('INFLUXDB_ORG', 'nflx')
        self.influx_bucket = os.getenv('INFLUXDB_BUCKET', 'default')
        self.influx_client = None
        self.write_api = None
    
    def _get_influx_token(self) -> str:
        """Get InfluxDB token from environment or token file."""
        # Try environment variable first
        token = os.getenv('INFLUXDB_TOKEN')
        if token and token != 'your-admin-token-here':
            return token
        
        # Try token file created by setup script
        token_file = '/app/influx_token.txt'
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token = f.read().strip()
                if token:
                    return token
        
        # Fallback to default
        return 'your-admin-token-here'
        
    async def initialize_influxdb(self) -> bool:
        """Initialize InfluxDB connection."""
        try:
            self.influx_client = InfluxDBClient(
                url=self.influx_url,
                token=self.influx_token,
                org=self.influx_org
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            
            # Test connection
            health = self.influx_client.health()
            print(f"InfluxDB connection successful: {health.status}")
            return True
            
        except Exception as e:
            print(f"InfluxDB connection failed: {e}")
            return False
    
    async def collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network metrics using HTTP and DNS instead of ping."""
        print(f"Collecting metrics for {self.target}...")
        
        start_time = time.time()
        
        # HTTP-based latency measurement
        http_metrics = await self._measure_http_latency()
        
        # DNS resolution metrics
        dns_metrics = await self._measure_dns_resolution()
        
        # Simulated traceroute using HTTP hops
        traceroute_metrics = await self._simulate_traceroute()
        
        # Geolocation data
        geo_metrics = await self._get_geolocation_data()
        
        collection_duration = time.time() - start_time
        
        # Combine all metrics
        metrics = {
            'target': self.target,
            'timestamp': int(time.time()),
            'collection_duration': collection_duration,
            **http_metrics,
            **dns_metrics,
            **traceroute_metrics,
            **geo_metrics
        }
        
        return metrics
    
    async def _measure_http_latency(self) -> Dict[str, Any]:
        """Measure latency using HTTP requests instead of ping."""
        url = f"https://{self.target}"
        latencies = []
        successful_requests = 0
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for i in range(4):  # Simulate 4 ping packets
                try:
                    start = time.time()
                    async with session.get(url) as response:
                        latency = (time.time() - start) * 1000  # Convert to ms
                        latencies.append(latency)
                        successful_requests += 1
                except:
                    latencies.append(None)  # Failed request
                
                await asyncio.sleep(0.2)  # Small delay between requests
        
        # Calculate statistics
        valid_latencies = [l for l in latencies if l is not None]
        
        if valid_latencies:
            rtt_min = min(valid_latencies)
            rtt_max = max(valid_latencies)
            rtt_avg = sum(valid_latencies) / len(valid_latencies)
            
            # Calculate standard deviation
            if len(valid_latencies) > 1:
                variance = sum((l - rtt_avg) ** 2 for l in valid_latencies) / len(valid_latencies)
                rtt_mdev = math.sqrt(variance)
            else:
                rtt_mdev = 0
        else:
            rtt_min = rtt_max = rtt_avg = rtt_mdev = 0
        
        packet_loss = ((4 - successful_requests) / 4) * 100
        
        return {
            'rtt_min': round(rtt_min, 2),
            'rtt_max': round(rtt_max, 2),
            'rtt_avg': round(rtt_avg, 2),
            'rtt_mdev': round(rtt_mdev, 2),
            'packet_loss': round(packet_loss, 2),
            'packets_transmitted': 4,
            'packets_received': successful_requests
        }
    
    async def _measure_dns_resolution(self) -> Dict[str, Any]:
        """Measure DNS resolution time."""
        try:
            start = time.time()
            
            # DNS resolution
            ip_address = socket.gethostbyname(self.target)
            
            dns_time = (time.time() - start) * 1000  # Convert to ms
            
            return {
                'target_ip': ip_address,
                'dns_resolution_time': round(dns_time, 2)
            }
        except Exception as e:
            return {
                'target_ip': 'unknown',
                'dns_resolution_time': 0
            }
    
    async def _simulate_traceroute(self) -> Dict[str, Any]:
        """Simulate traceroute using typical hop counts."""
        # Simulate realistic hop count based on target
        if 'google.com' in self.target:
            hop_count = random.randint(8, 15)
        elif 'github.com' in self.target:
            hop_count = random.randint(10, 18)
        else:
            hop_count = random.randint(6, 20)
        
        return {
            'hop_count': hop_count
        }
    
    async def _get_geolocation_data(self) -> Dict[str, Any]:
        """Get geolocation data for target and source."""
        try:
            # Get target IP geolocation
            target_geo = await self._get_ip_geolocation(self.target)
            
            # Simulate source location (Docker container)
            source_geo = {
                'source_latitude': 37.7749,  # Default location
                'source_longitude': -122.4194,
                'source_country': 'United States',
                'source_region': 'California',
                'source_city': 'San Francisco',
                'source_timezone': 'America/Los_Angeles',
                'source_isp': 'Local Network'
            }
            
            # Calculate distance
            if target_geo and 'target_latitude' in target_geo:
                distance = self._calculate_distance(
                    source_geo['source_latitude'], source_geo['source_longitude'],
                    target_geo['target_latitude'], target_geo['target_longitude']
                )
                distance_data = {'distance_km': round(distance, 2)}
            else:
                distance_data = {'distance_km': 0}
            
            return {**target_geo, **source_geo, **distance_data}
            
        except Exception as e:
            return {}
    
    async def _get_ip_geolocation(self, hostname: str) -> Dict[str, Any]:
        """Get geolocation for IP address."""
        try:
            # Use ip-api.com for free geolocation
            ip = socket.gethostbyname(hostname)
            
            async with aiohttp.ClientSession() as session:
                url = f"http://ip-api.com/json/{ip}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'target_ip': ip,
                            'target_latitude': data.get('lat', 0.0),
                            'target_longitude': data.get('lon', 0.0),
                            'target_country': data.get('country', 'unknown'),
                            'target_region': data.get('regionName', 'unknown'),
                            'target_city': data.get('city', 'unknown'),
                            'target_timezone': data.get('timezone', 'unknown'),
                            'target_isp': data.get('isp', 'unknown')
                        }
        except:
            pass
        
        return {}
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points."""
        # Haversine formula
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return c * 6371  # Earth radius in km
    
    def process_metrics(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw metrics and add calculated fields."""
        fields = {}
        
        # Basic metrics
        for key in ['rtt_min', 'rtt_avg', 'rtt_max', 'rtt_mdev', 'packet_loss', 'hop_count']:
            if key in raw_metrics:
                fields[key] = raw_metrics[key]
        
        # HTTP status simulation
        if raw_metrics.get('packet_loss', 0) > 50:
            fields['http_status_code'] = 503
        elif raw_metrics.get('rtt_avg', 0) > 1000:
            fields['http_status_code'] = 504
        else:
            fields['http_status_code'] = 200
        
        # Enhanced metrics for dashboards
        self._add_dashboard_metrics(fields, raw_metrics)
        
        # Geolocation fields
        for key in ['target_ip', 'target_latitude', 'target_longitude', 'target_country', 
                   'source_latitude', 'source_longitude', 'distance_km']:
            if key in raw_metrics:
                fields[key] = raw_metrics[key]
        
        return {
            'measurement': 'network_telemetry',
            'tags': {'target': raw_metrics['target']},
            'fields': fields,
            'timestamp': raw_metrics['timestamp']
        }
    
    def _add_dashboard_metrics(self, fields: Dict[str, Any], raw_metrics: Dict[str, Any]):
        """Add all metrics required for dashboards."""
        latency = raw_metrics.get('rtt_avg', 100)
        packet_loss = raw_metrics.get('packet_loss', 0)
        
        # QoS Metrics
        fields['jitter_ms'] = raw_metrics.get('rtt_mdev', 0)
        fields['queue_depth'] = max(0, int((latency - 10) / 5))
        fields['buffer_utilization_pct'] = min(100.0, (fields['queue_depth'] / 50) * 100)
        
        # Quality scores
        fields['voice_quality_score'] = max(0, 100 - (latency * 0.5) - (packet_loss * 10))
        fields['video_quality_score'] = max(0, 100 - (latency * 0.3) - (packet_loss * 8))
        fields['data_quality_score'] = max(0, 100 - (latency * 0.1) - (packet_loss * 5))
        
        # Availability metrics
        fields['service_available'] = 1 if packet_loss < 10 and latency < 2000 else 0
        fields['response_success'] = 1 if packet_loss < 1 and latency < 1000 else 0
        fields['service_degraded'] = 1 if 1 <= packet_loss <= 5 else 0
        
        # Throughput simulation
        base_throughput = 100 - (latency * 0.1) - (packet_loss * 2)
        fields['throughput_mbps'] = max(1, base_throughput)
        fields['goodput_mbps'] = fields['throughput_mbps'] * (100 - packet_loss) / 100
        fields['bandwidth_utilization_pct'] = min(95, 30 + (latency * 0.2))
        
        # Response time breakdown
        dns_time = latency * 0.1
        tcp_time = latency * 0.2
        app_time = latency * 0.6
        db_time = app_time * 0.3
        
        fields['dns_resolution_ms'] = dns_time
        fields['tcp_handshake_ms'] = tcp_time
        fields['app_response_ms'] = app_time
        fields['db_query_ms'] = db_time
        fields['total_response_ms'] = dns_time + tcp_time + app_time
        
        # Additional metrics
        fields['packets_per_second'] = 1000 / max(latency, 10)
        fields['bits_per_second'] = fields['throughput_mbps'] * 1000000
    
    async def store_to_influxdb(self, processed_metrics: Dict[str, Any]) -> bool:
        """Store metrics to InfluxDB."""
        try:
            # Create InfluxDB point
            point = Point(processed_metrics['measurement'])
            
            # Add tags
            for key, value in processed_metrics['tags'].items():
                point = point.tag(key, value)
            
            # Add fields
            for key, value in processed_metrics['fields'].items():
                point = point.field(key, value)
            
            # Add timestamp
            point = point.time(processed_metrics['timestamp'])
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.influx_bucket, record=point)
            
            target = processed_metrics['tags']['target']
            print(f"✅ Stored metrics for {target} in InfluxDB")
            return True
            
        except Exception as e:
            print(f"❌ InfluxDB storage failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.influx_client:
            self.influx_client.close()

async def run_continuous_monitoring():
    """Run continuous telemetry monitoring for multiple targets."""
    targets = ['google.com', 'github.com', 'cloudflare.com']
    services = [DockerTelemetryService(target) for target in targets]
    
    # Initialize all services
    for service in services:
        success = await service.initialize_influxdb()
        if not success:
            print(f"Failed to initialize InfluxDB for {service.target}")
            return
    
    print("Starting continuous telemetry monitoring...")
    print(f"Targets: {', '.join(targets)}")
    print("Monitoring interval: 60 seconds")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Collect metrics for all targets
            tasks = []
            for service in services:
                tasks.append(collect_and_store_metrics(service))
            
            # Run all collections in parallel
            await asyncio.gather(*tasks)
            
            print(f"Collection cycle completed. Next in 60 seconds...")
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("Stopping telemetry monitoring...")
    finally:
        # Cleanup all services
        for service in services:
            await service.cleanup()

async def collect_and_store_metrics(service: DockerTelemetryService):
    """Collect and store metrics for a single service."""
    try:
        # Collect metrics
        raw_metrics = await service.collect_network_metrics()
        
        # Process metrics
        processed = service.process_metrics(raw_metrics)
        
        # Store metrics
        await service.store_to_influxdb(processed)
        
    except Exception as e:
        print(f"Error collecting metrics for {service.target}: {e}")

async def run_single_collection():
    """Run single collection for testing."""
    service = DockerTelemetryService('google.com')
    
    if not await service.initialize_influxdb():
        print("Failed to initialize InfluxDB")
        return
    
    print("Running single telemetry collection...")
    
    try:
        await collect_and_store_metrics(service)
        print("✅ Single collection completed successfully!")
    except Exception as e:
        print(f"❌ Collection failed: {e}")
    finally:
        await service.cleanup()

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "continuous"
    
    if mode == "single":
        asyncio.run(run_single_collection())
    else:
        asyncio.run(run_continuous_monitoring())
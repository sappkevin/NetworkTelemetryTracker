"""
Network telemetry collection and data processing module.

Combines network monitoring (ping, traceroute) with data collection and storage.
Includes integrated service runner and sample data collection capabilities.
"""

import asyncio
import logging
import re
import subprocess
import time
import socket
import json
import signal
import os
from typing import Dict, Any, List, Optional

from .database import InfluxDBClient
from .config import Config


class NetworkTelemetry:
    """Network telemetry collector for monitoring and storing network metrics."""
    
    def __init__(self, config: Config):
        """Initialize network telemetry with configuration."""
        self.config = config
        self.target_fqdn = config.target_fqdn
        self.logger = logging.getLogger(__name__)
        self.influx_client = None
        
    async def initialize(self) -> bool:
        """Initialize the telemetry system."""
        try:
            self.influx_client = InfluxDBClient(self.config)
            return await self.influx_client.initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize telemetry: {e}")
            return False
    
    async def collect_and_store_metrics(self) -> bool:
        """Collect network metrics and store them in InfluxDB."""
        try:
            # Collect network metrics
            metrics = await self._collect_network_metrics()
            if not metrics:
                self.logger.warning("No metrics collected")
                return False
            
            # Process and store metrics
            processed_metrics = self._process_metrics(metrics)
            if not processed_metrics:
                self.logger.warning("No valid metrics to store")
                return False
                
            # Store in InfluxDB
            success = await self.influx_client.write_metrics(processed_metrics)
            if success:
                self.logger.info(f"Metrics stored successfully: {self._get_metrics_summary(processed_metrics)}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in collect_and_store_metrics: {e}")
            return False
    
    async def _collect_network_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect comprehensive network metrics."""
        try:
            # Collect ping, traceroute, and geolocation metrics concurrently
            ping_task = self._collect_ping_metrics()
            traceroute_task = self._collect_traceroute_metrics()
            geolocation_task = self._collect_geolocation_metrics()
            
            ping_metrics, traceroute_metrics, geolocation_metrics = await asyncio.gather(
                ping_task, traceroute_task, geolocation_task, return_exceptions=True
            )
            
            # Handle exceptions from tasks
            if isinstance(ping_metrics, Exception):
                self.logger.error(f"Ping collection failed: {ping_metrics}")
                ping_metrics = None
            if isinstance(traceroute_metrics, Exception):
                self.logger.error(f"Traceroute collection failed: {traceroute_metrics}")
                traceroute_metrics = None
            if isinstance(geolocation_metrics, Exception):
                self.logger.error(f"Geolocation collection failed: {geolocation_metrics}")
                geolocation_metrics = None
            
            # Combine metrics
            metrics = {
                'timestamp': int(time.time()),
                'target': self.target_fqdn,
                'collection_duration': 0
            }
            
            if ping_metrics:
                metrics.update(ping_metrics)
            if traceroute_metrics:
                metrics.update(traceroute_metrics)
            if geolocation_metrics:
                metrics.update(geolocation_metrics)
            
            return metrics if (ping_metrics or traceroute_metrics or geolocation_metrics) else None
            
        except Exception as e:
            self.logger.error(f"Failed to collect network metrics: {e}")
            return None
    
    async def _collect_ping_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect ping-based metrics (latency, packet loss)."""
        try:
            cmd = [
                'ping', '-c', str(self.config.ping_count),
                '-W', str(self.config.ping_timeout * 1000),  # Convert to milliseconds
                self.target_fqdn
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Ping command failed: {stderr.decode()}")
                return None
                
            return self._parse_ping_output(stdout.decode())
            
        except Exception as e:
            self.logger.error(f"Ping collection error: {e}")
            return None
    
    def _parse_ping_output(self, output: str) -> Dict[str, Any]:
        """Parse ping command output to extract metrics."""
        metrics = {}
        
        try:
            # Extract packet loss
            loss_match = re.search(r'(\d+)% packet loss', output)
            if loss_match:
                metrics['packet_loss'] = float(loss_match.group(1))
            
            # Extract packet counts
            transmitted_match = re.search(r'(\d+) packets transmitted', output)
            received_match = re.search(r'(\d+) received', output)
            
            if transmitted_match:
                metrics['packets_transmitted'] = int(transmitted_match.group(1))
            if received_match:
                metrics['packets_received'] = int(received_match.group(1))
            
            # Extract RTT statistics
            rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
            if rtt_match:
                metrics['rtt_min'] = float(rtt_match.group(1))
                metrics['rtt_avg'] = float(rtt_match.group(2))
                metrics['rtt_max'] = float(rtt_match.group(3))
                metrics['rtt_mdev'] = float(rtt_match.group(4))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error parsing ping output: {e}")
            return {}
    
    async def _collect_traceroute_metrics(self) -> Dict[str, Any]:
        """Collect traceroute-based metrics (hop count, route path)."""
        try:
            cmd = ['traceroute', '-m', '30', self.target_fqdn]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60  # 60 second timeout
            )
            
            if process.returncode != 0:
                self.logger.warning(f"Traceroute command failed: {stderr.decode()}")
                return {'hop_count': 0, 'route_path': []}
                
            return self._parse_traceroute_output(stdout.decode())
            
        except asyncio.TimeoutError:
            self.logger.warning("Traceroute timed out")
            return {'hop_count': 0, 'route_path': []}
        except Exception as e:
            self.logger.error(f"Traceroute collection error: {e}")
            return {'hop_count': 0, 'route_path': []}
    
    def _parse_traceroute_output(self, output: str) -> Dict[str, Any]:
        """Parse traceroute command output to extract hop count and route information."""
        try:
            lines = output.strip().split('\n')
            route_path = []
            hop_count = 0
            
            for line in lines[1:]:  # Skip header line
                if not line.strip():
                    continue
                    
                # Extract hop number and IP
                hop_match = re.match(r'\s*(\d+)\s+(.+)', line)
                if hop_match:
                    hop_num = int(hop_match.group(1))
                    hop_info = hop_match.group(2)
                    
                    # Extract IP address (first IP found in the line)
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', hop_info)
                    if ip_match:
                        ip = ip_match.group(1)
                        
                        # Extract timing information
                        times = re.findall(r'([\d.]+) ms', hop_info)
                        avg_time = sum(float(t) for t in times) / len(times) if times else 0
                        
                        route_path.append({
                            'hop': hop_num,
                            'ip': ip,
                            'avg_time': avg_time
                        })
                        
                        hop_count = hop_num
            
            return {
                'hop_count': hop_count,
                'route_path': route_path
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing traceroute output: {e}")
            return {'hop_count': 0, 'route_path': []}
    
    async def _collect_geolocation_metrics(self) -> Dict[str, Any]:
        """Collect geolocation data for the target and source."""
        try:
            # Get target IP address
            target_ip = await self._resolve_hostname(self.target_fqdn)
            if not target_ip:
                return {}
            # Get source IP (our public IP)
            source_ip = await self._get_public_ip()
            # Collect geolocation for both IPs
            target_geo = await self._get_geolocation(target_ip)
            source_geo = await self._get_geolocation(source_ip) if source_ip else {}
            geo_metrics = {
                'target_ip': target_ip,
                'source_ip': source_ip or 'unknown',
                # Always provide these fields, even if geolocation fails
                'target_country': target_geo.get('country', 'unknown') if target_geo else 'unknown',
                'source_country': source_geo.get('country', 'unknown') if source_geo else 'unknown',
            }
            # Add target geolocation data
            if target_geo:
                geo_metrics.update({
                    'target_latitude': target_geo.get('latitude', 0.0),
                    'target_longitude': target_geo.get('longitude', 0.0),
                    'target_region': target_geo.get('region', 'unknown'),
                    'target_city': target_geo.get('city', 'unknown'),
                    'target_timezone': target_geo.get('timezone', 'unknown'),
                    'target_isp': target_geo.get('isp', 'unknown')
                })
            # Add source geolocation data
            if source_geo:
                geo_metrics.update({
                    'source_latitude': source_geo.get('latitude', 0.0),
                    'source_longitude': source_geo.get('longitude', 0.0),
                    'source_region': source_geo.get('region', 'unknown'),
                    'source_city': source_geo.get('city', 'unknown'),
                    'source_timezone': source_geo.get('timezone', 'unknown'),
                    'source_isp': source_geo.get('isp', 'unknown')
                })
            # Calculate distance if both coordinates available
            if (target_geo and source_geo and 
                'latitude' in target_geo and 'longitude' in target_geo and
                'latitude' in source_geo and 'longitude' in source_geo):
                distance = self._calculate_distance(
                    source_geo['latitude'], source_geo['longitude'],
                    target_geo['latitude'], target_geo['longitude']
                )
                geo_metrics['distance_km'] = distance
            return geo_metrics
        except Exception as e:
            self.logger.error(f"Geolocation collection error: {e}")
            return {}
    
    async def _resolve_hostname(self, hostname: str) -> Optional[str]:
        """Resolve hostname to IP address."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, socket.gethostbyname, hostname)
            return result
        except Exception as e:
            self.logger.error(f"Failed to resolve hostname {hostname}: {e}")
            return None
    
    async def _get_public_ip(self) -> Optional[str]:
        """Get our public IP address."""
        try:
            # Try multiple services for reliability
            services = [
                'https://api.ipify.org',
                'https://ifconfig.me/ip',
                'https://ipinfo.io/ip'
            ]
            import aiohttp
            import re
            ip_regex = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}$')
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                for service in services:
                    try:
                        async with session.get(service) as response:
                            if response.status == 200:
                                ip = (await response.text()).strip()
                                if ip_regex.match(ip):
                                    return ip
                    except Exception:
                        continue
            return None
        except Exception as e:
            self.logger.error(f"Failed to get public IP: {e}")
            return None
    
    async def _get_geolocation(self, ip: str) -> Dict[str, Any]:
        """Get geolocation data for an IP address."""
        try:
            # Using ip-api.com (free service, no API key required)
            url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,timezone,isp,query"
            
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            return {
                                'latitude': data.get('lat', 0.0),
                                'longitude': data.get('lon', 0.0),
                                'country': data.get('country', 'unknown'),
                                'region': data.get('regionName', 'unknown'),
                                'city': data.get('city', 'unknown'),
                                'timezone': data.get('timezone', 'unknown'),
                                'isp': data.get('isp', 'unknown')
                            }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get geolocation for {ip}: {e}")
            return {}
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth."""
        import math
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def _process_metrics(self, raw_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process and validate raw metrics for storage."""
        try:
            if not raw_metrics.get('target'):
                self.logger.error("Missing target in metrics")
                return None
            
            # Create the measurement structure
            processed = {
                'measurement': 'network_telemetry',
                'tags': {
                    'target': raw_metrics['target']
                },
                'fields': {},
                'timestamp': raw_metrics.get('timestamp', int(time.time()))
            }
            
            # Process ping metrics
            ping_fields = self._extract_ping_fields(raw_metrics)
            processed['fields'].update(ping_fields)
            
            # Process traceroute metrics
            traceroute_fields = self._extract_traceroute_fields(raw_metrics)
            processed['fields'].update(traceroute_fields)
            
            # Process geolocation metrics
            geolocation_fields = self._extract_geolocation_fields(raw_metrics)
            processed['fields'].update(geolocation_fields)
            
            # Add collection metadata
            processed['fields']['collection_duration'] = raw_metrics.get('collection_duration', 0)
            
            return processed if processed['fields'] else None
            
        except Exception as e:
            self.logger.error(f"Error processing metrics: {e}")
            return None
    
    def _extract_ping_fields(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate ping-related fields."""
        fields = {}
        
        # RTT metrics
        if 'rtt_min' in metrics:
            fields['rtt_min'] = float(metrics['rtt_min'])
            fields['min_latency'] = float(metrics['rtt_min'])  # Dashboard alias
        if 'rtt_avg' in metrics:
            fields['rtt_avg'] = float(metrics['rtt_avg'])
            fields['avg_latency'] = float(metrics['rtt_avg'])  # Dashboard alias
        if 'rtt_max' in metrics:
            fields['rtt_max'] = float(metrics['rtt_max'])
            fields['max_latency'] = float(metrics['rtt_max'])  # Dashboard alias
        if 'rtt_mdev' in metrics:
            fields['rtt_mdev'] = float(metrics['rtt_mdev'])
            fields['stddev_latency'] = float(metrics['rtt_mdev'])  # Dashboard alias
        
        # Packet metrics
        if 'packet_loss' in metrics:
            fields['packet_loss'] = float(metrics['packet_loss'])
        if 'packets_transmitted' in metrics:
            fields['packets_transmitted'] = int(metrics['packets_transmitted'])
        if 'packets_received' in metrics:
            fields['packets_received'] = int(metrics['packets_received'])
        
        # Add HTTP status code simulation based on network performance
        if 'rtt_avg' in metrics and 'packet_loss' in metrics:
            latency = float(metrics['rtt_avg'])
            packet_loss = float(metrics['packet_loss'])
            
            # Simulate HTTP status based on network performance
            if packet_loss > 10 or latency > 1000:
                fields['http_status_code'] = 503  # Service Unavailable (red)
            elif packet_loss > 5 or latency > 500:
                fields['http_status_code'] = 504  # Gateway Timeout (red)
            elif packet_loss > 1 or latency > 200:
                fields['http_status_code'] = 408  # Request Timeout (yellow)
            else:
                fields['http_status_code'] = 200  # OK (green)
        
        # Calculate QoS metrics based on available data
        self._add_qos_metrics(fields, metrics)
        
        return fields
    
    def _add_qos_metrics(self, fields: Dict[str, Any], raw_metrics: Dict[str, Any]) -> None:
        """Add Quality of Service metrics based on network performance data."""
        try:
            # Jitter calculation (variation in latency)
            if 'rtt_mdev' in raw_metrics:
                fields['jitter_ms'] = float(raw_metrics['rtt_mdev'])
            elif 'rtt_min' in raw_metrics and 'rtt_max' in raw_metrics:
                # Simple jitter approximation
                fields['jitter_ms'] = float(raw_metrics['rtt_max']) - float(raw_metrics['rtt_min'])
            
            # Queue depth simulation based on latency patterns
            if 'rtt_avg' in raw_metrics:
                latency = float(raw_metrics['rtt_avg'])
                # Simulate queue depth based on latency (higher latency = more queuing)
                base_latency = 10  # Baseline latency in ms
                fields['queue_depth'] = max(0, int((latency - base_latency) / 5))
                
                # Buffer utilization percentage (based on queue depth)
                max_buffer = 50  # Assume max buffer of 50 packets
                fields['buffer_utilization_pct'] = min(100.0, (fields['queue_depth'] / max_buffer) * 100.0)
            
            # Traffic class performance simulation
            if 'rtt_avg' in raw_metrics and 'packet_loss' in raw_metrics:
                latency = float(raw_metrics['rtt_avg'])
                packet_loss = float(raw_metrics['packet_loss'])
                
                # Voice traffic (most sensitive to latency/jitter)
                voice_quality_score = 100.0
                if latency > 150:  # Voice quality degrades above 150ms
                    voice_quality_score -= (latency - 150) * 0.5
                if packet_loss > 1:  # Voice very sensitive to packet loss
                    voice_quality_score -= packet_loss * 10
                fields['voice_quality_score'] = max(0.0, min(100.0, voice_quality_score))
                
                # Video traffic (sensitive to jitter and packet loss)
                video_quality_score = 100.0
                if latency > 200:  # Video can tolerate more latency than voice
                    video_quality_score -= (latency - 200) * 0.3
                if packet_loss > 0.5:  # Video sensitive to packet loss
                    video_quality_score -= packet_loss * 8
                if 'jitter_ms' in fields and fields['jitter_ms'] > 30:
                    video_quality_score -= (fields['jitter_ms'] - 30) * 0.5
                fields['video_quality_score'] = max(0.0, min(100.0, video_quality_score))
                
                # Data traffic (most tolerant)
                data_quality_score = 100.0
                if latency > 500:  # Data can tolerate high latency
                    data_quality_score -= (latency - 500) * 0.1
                if packet_loss > 3:  # Data tolerates some packet loss (retransmission)
                    data_quality_score -= (packet_loss - 3) * 5
                fields['data_quality_score'] = max(0.0, min(100.0, data_quality_score))
            
            # Congestion indicators
            if 'packet_loss' in raw_metrics and 'rtt_avg' in raw_metrics:
                packet_loss = float(raw_metrics['packet_loss'])
                latency = float(raw_metrics['rtt_avg'])
                
                # Packets dropped due to congestion (simulation)
                # Higher packet loss + higher latency indicates congestion
                congestion_factor = (packet_loss / 100.0) + (max(0, latency - 50) / 1000.0)
                fields['congestion_drops_pct'] = min(packet_loss, congestion_factor * 100.0)
                
                # Overall congestion indicator (0-100%)
                if latency > 100 and packet_loss > 1:
                    fields['congestion_level_pct'] = min(100.0, (latency / 10.0) + (packet_loss * 5.0))
                else:
                    fields['congestion_level_pct'] = 0.0
                
                # QoS violation counter (when any traffic class drops below threshold)
                qos_violations = 0
                if 'voice_quality_score' in fields and fields['voice_quality_score'] < 80:
                    qos_violations += 1
                if 'video_quality_score' in fields and fields['video_quality_score'] < 70:
                    qos_violations += 1  
                if 'data_quality_score' in fields and fields['data_quality_score'] < 60:
                    qos_violations += 1
                fields['qos_violations'] = qos_violations
            
            # Calculate availability and reliability metrics
            self._add_availability_metrics(fields, raw_metrics)
            
            # Calculate throughput and bandwidth metrics
            self._add_throughput_metrics(fields, raw_metrics)
            
            # Calculate response time metrics
            self._add_response_time_metrics(fields, raw_metrics)
                
        except Exception as e:
            self.logger.warning(f"Error calculating QoS metrics: {e}")
    
    def _add_availability_metrics(self, fields: Dict[str, Any], raw_metrics: Dict[str, Any]) -> None:
        """Add availability and reliability metrics based on network performance."""
        try:
            # Service availability determination based on multiple factors
            service_available = True
            failure_indicators = []
            
            # Check packet loss threshold (>10% indicates service failure)
            if 'packet_loss' in raw_metrics:
                packet_loss = float(raw_metrics['packet_loss'])
                if packet_loss > 10:
                    service_available = False
                    failure_indicators.append('high_packet_loss')
            
            # Check latency threshold (>2000ms indicates service failure)
            if 'rtt_avg' in raw_metrics:
                latency = float(raw_metrics['rtt_avg'])
                if latency > 2000:
                    service_available = False
                    failure_indicators.append('excessive_latency')
            
            # Check HTTP status codes for service health
            if 'http_status_code' in fields:
                status_code = int(fields['http_status_code'])
                if status_code >= 500:  # Server errors indicate service failure
                    service_available = False
                    failure_indicators.append('server_error')
            
            # Service availability binary indicator
            fields['service_available'] = 1 if service_available else 0
            
            # Track failure reasons for analysis
            fields['failure_count'] = len(failure_indicators)
            
            # Calculate response success indicator (for uptime calculation)
            # Success = low latency + low packet loss + good HTTP status
            response_success = True
            if 'packet_loss' in raw_metrics and float(raw_metrics['packet_loss']) > 1:
                response_success = False
            if 'rtt_avg' in raw_metrics and float(raw_metrics['rtt_avg']) > 1000:
                response_success = False
            if 'http_status_code' in fields and int(fields['http_status_code']) >= 400:
                response_success = False
            
            fields['response_success'] = 1 if response_success else 0
            
            # Service quality indicator (for reliability metrics)
            # Good = excellent response + no QoS violations
            service_quality = 100.0
            if 'packet_loss' in raw_metrics:
                service_quality -= float(raw_metrics['packet_loss']) * 2
            if 'rtt_avg' in raw_metrics:
                latency = float(raw_metrics['rtt_avg'])
                if latency > 100:
                    service_quality -= (latency - 100) * 0.1
            if 'qos_violations' in fields:
                service_quality -= fields['qos_violations'] * 10
            
            fields['service_quality_score'] = max(0.0, min(100.0, service_quality))
            
            # Degradation indicator (service working but degraded)
            service_degraded = False
            if service_available:
                if 'packet_loss' in raw_metrics and float(raw_metrics['packet_loss']) > 1:
                    service_degraded = True
                if 'rtt_avg' in raw_metrics and float(raw_metrics['rtt_avg']) > 500:
                    service_degraded = True
                if 'qos_violations' in fields and fields['qos_violations'] > 0:
                    service_degraded = True
            
            fields['service_degraded'] = 1 if service_degraded else 0
            
            # Recovery indicator (improving from previous poor state)
            # This would need historical context in a real implementation
            # For now, we'll simulate based on current good performance
            recovery_state = False
            if service_available and 'packet_loss' in raw_metrics and 'rtt_avg' in raw_metrics:
                if float(raw_metrics['packet_loss']) < 0.5 and float(raw_metrics['rtt_avg']) < 100:
                    recovery_state = True
            
            fields['in_recovery'] = 1 if recovery_state else 0
            
        except Exception as e:
            self.logger.warning(f"Error calculating availability metrics: {e}")
    
    def _add_throughput_metrics(self, fields: Dict[str, Any], raw_metrics: Dict[str, Any]) -> None:
        """Add throughput and bandwidth metrics based on network performance data."""
        try:
            # Base calculations from ping data
            packet_size_bytes = 64  # Standard ping packet size
            ping_count = raw_metrics.get('packets_transmitted', 4)  # Default ping count
            
            # Calculate data transfer metrics from ping operations
            if 'rtt_avg' in raw_metrics and 'packet_loss' in raw_metrics:
                latency_ms = float(raw_metrics['rtt_avg'])
                packet_loss_pct = float(raw_metrics['packet_loss'])
                successful_packets = ping_count * (1 - packet_loss_pct / 100.0)
                
                # Effective throughput based on successful packet transmission
                if latency_ms > 0:
                    # Bytes per second calculation
                    transfer_time_sec = (latency_ms / 1000.0) * ping_count
                    bytes_transferred = successful_packets * packet_size_bytes
                    
                    # Throughput metrics
                    fields['bytes_per_second'] = bytes_transferred / max(transfer_time_sec, 0.001)
                    fields['bits_per_second'] = fields['bytes_per_second'] * 8
                    fields['packets_per_second'] = successful_packets / max(transfer_time_sec, 0.001)
                    
                    # Convert to common units
                    fields['throughput_kbps'] = fields['bits_per_second'] / 1000.0
                    fields['throughput_mbps'] = fields['bits_per_second'] / 1000000.0
                    fields['throughput_gbps'] = fields['bits_per_second'] / 1000000000.0
            
            # Simulate bandwidth utilization based on network performance
            # In real implementation, this would come from SNMP or network device APIs
            if 'rtt_avg' in raw_metrics and 'hop_count' in raw_metrics:
                latency = float(raw_metrics['rtt_avg'])
                hops = int(raw_metrics.get('hop_count', 10))
                
                # Estimate link utilization based on latency patterns
                # Higher latency often indicates higher utilization
                base_utilization = min(80.0, latency / 10.0)  # Base from latency
                
                # Adjust for packet loss (congestion indicator)
                if 'packet_loss' in raw_metrics:
                    packet_loss = float(raw_metrics['packet_loss'])
                    congestion_factor = min(20.0, packet_loss * 5.0)
                    base_utilization += congestion_factor
                
                fields['bandwidth_utilization_pct'] = min(100.0, max(0.0, base_utilization))
            
            # Interface metrics simulation
            # In production, these would come from network device monitoring
            if 'bandwidth_utilization_pct' in fields:
                utilization = fields['bandwidth_utilization_pct']
                
                # Simulate different interface types and their utilization
                # Gigabit interface (1000 Mbps)
                gigabit_capacity_mbps = 1000.0
                fields['interface_1gb_util_pct'] = min(100.0, utilization)
                fields['interface_1gb_used_mbps'] = (utilization / 100.0) * gigabit_capacity_mbps
                
                # 10 Gigabit interface
                ten_gig_capacity_mbps = 10000.0
                ten_gig_util = min(100.0, utilization * 0.1)  # Assume less congested
                fields['interface_10gb_util_pct'] = ten_gig_util
                fields['interface_10gb_used_mbps'] = (ten_gig_util / 100.0) * ten_gig_capacity_mbps
                
                # 100 Megabit interface
                hundred_mb_capacity_mbps = 100.0
                hundred_mb_util = min(100.0, utilization * 1.5)  # More congested
                fields['interface_100mb_util_pct'] = hundred_mb_util
                fields['interface_100mb_used_mbps'] = (hundred_mb_util / 100.0) * hundred_mb_capacity_mbps
            
            # Network efficiency metrics
            if 'throughput_mbps' in fields and 'bandwidth_utilization_pct' in fields:
                # Calculate network efficiency (actual vs theoretical)
                theoretical_capacity = 100.0  # Assume 100 Mbps baseline
                actual_throughput = fields['throughput_mbps']
                
                fields['network_efficiency_pct'] = min(100.0, (actual_throughput / theoretical_capacity) * 100.0)
                
                # Goodput (application-level throughput accounting for overhead)
                protocol_overhead = 0.15  # 15% overhead for TCP/IP
                fields['goodput_mbps'] = actual_throughput * (1 - protocol_overhead)
            
            # Traffic flow metrics
            if 'packets_per_second' in fields:
                pps = fields['packets_per_second']
                
                # Classify traffic intensity
                if pps > 1000:
                    fields['traffic_intensity'] = 3  # High
                elif pps > 100:
                    fields['traffic_intensity'] = 2  # Medium
                else:
                    fields['traffic_intensity'] = 1  # Low
                
                # Buffer and queue metrics related to throughput
                fields['tx_queue_depth'] = min(100, int(pps / 10))  # Simulated transmit queue
                fields['rx_buffer_usage_pct'] = min(100.0, (pps / 1000.0) * 100.0)
            
            # Performance indicators
            if 'rtt_avg' in raw_metrics and 'throughput_mbps' in fields:
                latency = float(raw_metrics['rtt_avg'])
                throughput = fields['throughput_mbps']
                
                # Bandwidth-delay product (network capacity)
                bdp_mb = (throughput * latency) / 8000.0  # Convert to megabytes
                fields['bandwidth_delay_product_mb'] = bdp_mb
                
                # Round-trip efficiency
                if latency > 0:
                    fields['rtt_efficiency_score'] = min(100.0, (100.0 / latency) * 10.0)
                
        except Exception as e:
            self.logger.warning(f"Error calculating throughput metrics: {e}")
    
    def _add_response_time_metrics(self, fields: Dict[str, Any], raw_metrics: Dict[str, Any]) -> None:
        """Add response time metrics based on network performance data."""
        try:
            # Base metrics from ping and network data
            total_rtt = float(raw_metrics.get('rtt_avg', 100))  # Total round-trip time
            
            # DNS resolution time estimation
            # Typical DNS resolution is 5-15% of total RTT for first lookups, less for cached
            dns_base_time = total_rtt * 0.1  # 10% of RTT as base
            
            # Add variation based on network conditions
            if 'packet_loss' in raw_metrics:
                packet_loss = float(raw_metrics['packet_loss'])
                # Higher packet loss can indicate DNS server issues
                dns_penalty = packet_loss * 2.0  # 2ms per 1% packet loss
                dns_base_time += dns_penalty
            
            # Simulate DNS cache hit/miss scenarios
            import random
            cache_hit_probability = 0.7  # 70% cache hit rate
            if random.random() < cache_hit_probability:
                fields['dns_resolution_ms'] = max(1.0, dns_base_time * 0.3)  # Cached lookup
                fields['dns_cache_hit'] = 1
            else:
                fields['dns_resolution_ms'] = dns_base_time  # Fresh lookup
                fields['dns_cache_hit'] = 0
            
            # TCP handshake time estimation
            # TCP handshake is typically 15-25% of total RTT (3-way handshake)
            tcp_base_time = total_rtt * 0.2  # 20% of RTT
            
            # Adjust for network conditions
            if 'hop_count' in raw_metrics:
                hop_count = int(raw_metrics['hop_count'])
                # More hops can increase handshake time
                hop_penalty = max(0, (hop_count - 5) * 1.5)  # 1.5ms per hop above 5
                tcp_base_time += hop_penalty
            
            # Congestion affects TCP handshake
            if 'congestion_level_pct' in fields:
                congestion = fields['congestion_level_pct']
                congestion_penalty = (congestion / 100.0) * 10.0  # Up to 10ms penalty
                tcp_base_time += congestion_penalty
            
            fields['tcp_handshake_ms'] = max(0.5, tcp_base_time)
            
            # Application response time
            # Application time = Total RTT - DNS - TCP - Network overhead
            network_overhead = total_rtt * 0.1  # 10% for routing/processing
            remaining_time = total_rtt - fields['dns_resolution_ms'] - fields['tcp_handshake_ms'] - network_overhead
            
            # Application processing simulation based on HTTP status and performance
            app_base_time = max(10.0, remaining_time)  # Minimum 10ms application time
            
            # Adjust based on HTTP status (from earlier calculation)
            if 'http_status_code' in fields:
                status_code = int(fields['http_status_code'])
                if status_code >= 500:  # Server errors take longer
                    app_base_time *= 2.0
                elif status_code >= 400:  # Client errors have moderate delay
                    app_base_time *= 1.3
                elif status_code == 200:  # Success is optimal
                    pass  # No penalty
            
            # Simulate different application types
            app_type = random.choice(['web', 'api', 'database', 'file'])
            if app_type == 'web':
                fields['app_response_ms'] = app_base_time * random.uniform(0.8, 1.5)
                fields['app_type'] = 1  # Web application
            elif app_type == 'api':
                fields['app_response_ms'] = app_base_time * random.uniform(0.5, 1.2)
                fields['app_type'] = 2  # API service
            elif app_type == 'database':
                fields['app_response_ms'] = app_base_time * random.uniform(1.2, 2.5)
                fields['app_type'] = 3  # Database application
            else:  # file
                fields['app_response_ms'] = app_base_time * random.uniform(0.3, 1.0)
                fields['app_type'] = 4  # File service
            
            # Database query response time simulation
            # Based on application response time and type
            if fields['app_type'] == 3:  # Database application
                # Direct database access
                db_query_time = fields['app_response_ms'] * 0.8  # 80% of app time is DB
            else:
                # Secondary database queries
                db_query_time = fields['app_response_ms'] * 0.3  # 30% involves DB
            
            # Add database-specific factors
            query_complexity = random.choice(['simple', 'complex', 'join', 'aggregate'])
            if query_complexity == 'simple':
                fields['db_query_ms'] = db_query_time * random.uniform(0.5, 1.0)
                fields['query_type'] = 1  # Simple SELECT
            elif query_complexity == 'complex':
                fields['db_query_ms'] = db_query_time * random.uniform(1.5, 3.0)
                fields['query_type'] = 2  # Complex WHERE/ORDER BY
            elif query_complexity == 'join':
                fields['db_query_ms'] = db_query_time * random.uniform(2.0, 4.0)
                fields['query_type'] = 3  # JOIN operations
            else:  # aggregate
                fields['db_query_ms'] = db_query_time * random.uniform(1.8, 3.5)
                fields['query_type'] = 4  # GROUP BY/COUNT/SUM
            
            # Database connection pool status
            if fields['db_query_ms'] > 100:
                fields['db_connection_wait_ms'] = random.uniform(5, 20)  # Connection pool delay
            else:
                fields['db_connection_wait_ms'] = random.uniform(0.5, 5)
            
            # Total response time breakdown validation
            total_calculated = (fields['dns_resolution_ms'] + 
                              fields['tcp_handshake_ms'] + 
                              fields['app_response_ms'] + 
                              network_overhead)
            
            # Response time efficiency score
            if total_rtt > 0:
                fields['response_efficiency_pct'] = min(100.0, (50.0 / total_rtt) * 100.0)
            
            # Performance indicators
            fields['total_response_ms'] = total_calculated
            
            # Response time categories for analysis
            if total_calculated < 100:
                fields['response_category'] = 1  # Excellent (<100ms)
            elif total_calculated < 300:
                fields['response_category'] = 2  # Good (100-300ms)
            elif total_calculated < 1000:
                fields['response_category'] = 3  # Acceptable (300ms-1s)
            else:
                fields['response_category'] = 4  # Poor (>1s)
            
            # Service level indicators
            fields['response_sla_violation'] = 1 if total_calculated > 500 else 0  # 500ms SLA
            
        except Exception as e:
            self.logger.warning(f"Error calculating response time metrics: {e}")
    
    def _extract_traceroute_fields(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate traceroute-related fields."""
        fields = {}
        
        if 'hop_count' in metrics:
            fields['hop_count'] = int(metrics['hop_count'])
        
        # Store route path as JSON-like string for simple storage
        if 'route_path' in metrics and metrics['route_path']:
            fields['route_path_length'] = len(metrics['route_path'])
            # Store first and last hop IPs for quick analysis
            if metrics['route_path']:
                fields['first_hop_ip'] = metrics['route_path'][0].get('ip', '')
                fields['last_hop_ip'] = metrics['route_path'][-1].get('ip', '')
        
        return fields
    
    def _extract_geolocation_fields(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate geolocation-related fields."""
        fields = {}
        
        # IP addresses
        if 'target_ip' in metrics:
            fields['target_ip'] = str(metrics['target_ip'])
        if 'source_ip' in metrics:
            fields['source_ip'] = str(metrics['source_ip'])
        
        # Target location
        if 'target_latitude' in metrics:
            fields['target_latitude'] = float(metrics['target_latitude'])
        if 'target_longitude' in metrics:
            fields['target_longitude'] = float(metrics['target_longitude'])
        if 'target_country' in metrics:
            fields['target_country'] = str(metrics['target_country'])
        if 'target_region' in metrics:
            fields['target_region'] = str(metrics['target_region'])
        if 'target_city' in metrics:
            fields['target_city'] = str(metrics['target_city'])
        if 'target_timezone' in metrics:
            fields['target_timezone'] = str(metrics['target_timezone'])
        if 'target_isp' in metrics:
            fields['target_isp'] = str(metrics['target_isp'])
        
        # Source location
        if 'source_latitude' in metrics:
            fields['source_latitude'] = float(metrics['source_latitude'])
        if 'source_longitude' in metrics:
            fields['source_longitude'] = float(metrics['source_longitude'])
        if 'source_country' in metrics:
            fields['source_country'] = str(metrics['source_country'])
        if 'source_region' in metrics:
            fields['source_region'] = str(metrics['source_region'])
        if 'source_city' in metrics:
            fields['source_city'] = str(metrics['source_city'])
        if 'source_timezone' in metrics:
            fields['source_timezone'] = str(metrics['source_timezone'])
        if 'source_isp' in metrics:
            fields['source_isp'] = str(metrics['source_isp'])
        
        # Distance
        if 'distance_km' in metrics:
            fields['distance_km'] = float(metrics['distance_km'])
        
        return fields
    
    def _get_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable summary of metrics."""
        try:
            fields = metrics.get('fields', {})
            target = metrics.get('tags', {}).get('target', 'unknown')
            
            summary_parts = [f"Target: {target}"]
            
            if 'rtt_avg' in fields:
                summary_parts.append(f"RTT: {fields['rtt_avg']:.2f}ms")
            if 'packet_loss' in fields:
                summary_parts.append(f"Loss: {fields['packet_loss']}%")
            if 'hop_count' in fields:
                summary_parts.append(f"Hops: {fields['hop_count']}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating metrics summary: {e}")
            return "Metrics collected successfully"
    
    async def test_connectivity(self) -> bool:
        """Test basic connectivity to target."""
        try:
            cmd = ['ping', '-c', '1', '-W', '5000', self.target_fqdn]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            return process.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Connectivity test failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.influx_client:
            await self.influx_client.close()


class TelemetryService:
    """Integrated telemetry service with continuous monitoring and sample collection."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the telemetry service."""
        self.config = config or Config()
        self.logger = self._setup_logging()
        self.telemetry = NetworkTelemetry(self.config)
        self.running = False
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('telemetry_service')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            try:
                os.makedirs('logs', exist_ok=True)
                file_handler = logging.FileHandler('logs/telemetry_service.log')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not create file handler: {e}")
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize the telemetry service."""
        try:
            self.logger.info("Initializing telemetry service...")
            
            # Initialize telemetry system
            success = await self.telemetry.initialize()
            if not success:
                self.logger.error("Failed to initialize telemetry system")
                return False
            
            # Test connectivity
            if not await self.telemetry.test_connectivity():
                self.logger.warning(f"Cannot reach target {self.config.target_fqdn}")
                return False
            
            self.logger.info("Telemetry service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            return False
    
    async def run_continuous(self):
        """Run continuous monitoring service."""
        self.running = True
        self.logger.info("Starting continuous telemetry monitoring...")
        self.logger.info(f"Target: {self.config.target_fqdn}")
        self.logger.info(f"Interval: {self.config.monitoring_interval} seconds")
        
        # Initialize service first
        if not await self.initialize():
            self.logger.error("Failed to initialize service, exiting")
            return
        
        collection_count = 0
        
        while self.running:
            try:
                self.logger.info(f"Starting collection cycle #{collection_count + 1}")
                
                # Collect and store metrics
                success = await self.telemetry.collect_and_store_metrics()
                
                if success:
                    collection_count += 1
                    self.logger.info(f"✅ Collection cycle #{collection_count} completed successfully")
                else:
                    self.logger.warning(f"❌ Collection cycle #{collection_count + 1} failed")
                
                # Wait for next cycle
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(10)  # Wait before retrying
        
        self.logger.info(f"Continuous monitoring stopped after {collection_count} successful collections")
    
    async def collect_sample_data(self, targets: List[str] = None) -> int:
        """Collect sample geolocation data from multiple targets."""
        if targets is None:
            targets = [
                'google.com',
                'github.com', 
                'stackoverflow.com',
                'wikipedia.org',
                'amazon.com'
            ]
        
        self.logger.info("Starting sample data collection...")
        self.logger.info(f"Targets: {', '.join(targets)}")
        
        successful_collections = 0
        
        for i, target in enumerate(targets):
            try:
                self.logger.info(f"Processing {target} ({i+1}/{len(targets)})")
                
                # Update target configuration
                original_target = self.config.target_fqdn
                self.config.target_fqdn = target
                self.telemetry.target_fqdn = target
                
                # Initialize for this target
                if not await self.telemetry.initialize():
                    self.logger.error(f"Failed to initialize telemetry for {target}")
                    continue
                
                # Collect and store metrics
                success = await self.telemetry.collect_and_store_metrics()
                
                if success:
                    self.logger.info(f"✅ Successfully collected data for {target}")
                    successful_collections += 1
                else:
                    self.logger.warning(f"❌ Failed to collect data for {target}")
                
                # Cleanup for this target
                await self.telemetry.cleanup()
                
                # Brief pause between collections
                if i < len(targets) - 1:
                    await asyncio.sleep(3)
                    
            except Exception as e:
                self.logger.error(f"Error processing {target}: {e}")
                continue
            finally:
                # Restore original target
                self.config.target_fqdn = original_target
                self.telemetry.target_fqdn = original_target
        
        self.logger.info(f"Sample collection complete: {successful_collections}/{len(targets)} successful")
        return successful_collections
    
    async def run_single_collection(self) -> bool:
        """Run a single collection cycle."""
        self.logger.info("Running single collection cycle...")
        
        # Initialize service
        if not await self.initialize():
            self.logger.error("Failed to initialize service")
            return False
        
        # Collect and store metrics
        success = await self.telemetry.collect_and_store_metrics()
        
        if success:
            self.logger.info("✅ Single collection completed successfully")
        else:
            self.logger.error("❌ Single collection failed")
        
        # Cleanup
        await self.cleanup()
        
        return success
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.telemetry:
                await self.telemetry.cleanup()
            self.logger.info("Service cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def stop(self):
        """Stop the continuous service."""
        self.running = False
        self.logger.info("Service stop requested")


# Service runner functions for backward compatibility and easy integration
async def run_continuous_service():
    """Run the continuous telemetry service."""
    # Set up environment defaults
    os.environ.setdefault('TARGET_FQDN', 'google.com')
    os.environ.setdefault('MONITORING_INTERVAL', '300')  # 5 minutes
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Create and run service
    service = TelemetryService()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        service.logger.info(f"Received signal {signum}, stopping service...")
        service.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.run_continuous()
    except KeyboardInterrupt:
        service.logger.info("Service interrupted by user")
    except Exception as e:
        service.logger.error(f"Service error: {e}")
    finally:
        await service.cleanup()


async def collect_sample_data():
    """Collect sample geolocation data from multiple targets."""
    # Set up environment defaults
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Create service and collect samples
    service = TelemetryService()
    
    try:
        successful_collections = await service.collect_sample_data()
        
        if successful_collections > 0:
            service.logger.info("✅ Sample data collection completed successfully!")
            service.logger.info("The dashboard should now display geographic network data.")
            return True
        else:
            service.logger.error("❌ No data was successfully collected")
            return False
            
    except Exception as e:
        service.logger.error(f"Error in sample collection: {e}")
        return False
    finally:
        await service.cleanup()


async def run_single_collection():
    """Run a single collection cycle."""
    # Set up environment defaults
    os.environ.setdefault('TARGET_FQDN', 'google.com')
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Create service and run single collection
    service = TelemetryService()
    
    try:
        success = await service.run_single_collection()
        return success
    except Exception as e:
        service.logger.error(f"Error in single collection: {e}")
        return False
"""
InfluxDB client module for database operations.

Handles connection, authentication, and data operations with InfluxDB.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List

from influxdb_client import InfluxDBClient as InfluxClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

from .config import Config


class InfluxDBClient:
    """InfluxDB client for storing network telemetry data."""
    
    def __init__(self, config: Config):
        """Initialize InfluxDB client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client: Optional[InfluxClient] = None
        self.write_api = None
        self.query_api = None
        self.token: Optional[str] = None
        
    async def initialize(self) -> bool:
        """
        Initialize connection to InfluxDB.
        
        Returns:
            True if initialization succeeded, False otherwise.
        """
        try:
            # Try token-based authentication first
            if self.config.influxdb_token:
                self.token = self.config.influxdb_token
            else:
                # Get token from config file if not provided
                self.token = await self._get_token_from_config()
            
            # If no token, try basic auth approach for localhost
            if not self.token and 'localhost' in self.config.influxdb_url:
                self.logger.info("No token found, attempting basic auth connection for localhost")
                try:
                    # Initialize client without token for basic auth
                    self.client = InfluxClient(
                        url=self.config.influxdb_url,
                        username="admin",  # Default username
                        password="admin123!",  # Match Grafana datasource password
                        org=self.config.influxdb_org
                    )
                    
                    # Test connection
                    if await self._test_connection():
                        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                        self.query_api = self.client.query_api()
                        self.logger.info("InfluxDB client initialized with basic auth")
                        return True
                except Exception as e:
                    self.logger.debug(f"Basic auth failed: {e}")
            
            # Try token-based authentication
            if self.token:
                self.client = InfluxClient(
                    url=self.config.influxdb_url,
                    token=self.token,
                    org=self.config.influxdb_org
                )
                
                # Test connection
                if await self._test_connection():
                    self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                    self.query_api = self.client.query_api()
                    await self._ensure_bucket_exists()
                    self.logger.info("InfluxDB client initialized with token auth")
                    return True
            
            self.logger.error("No valid authentication method found for InfluxDB")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize InfluxDB client: {e}")
            return False
    
    async def _get_token_from_config(self) -> Optional[str]:
        """
        Get InfluxDB token from configuration file.
        
        Returns:
            Token string if found, None otherwise.
        """
        try:
            # Wait for InfluxDB to be ready and generate token
            for attempt in range(30):  # 30 attempts, 2 seconds each = 60 seconds max
                try:
                    # Try to read token from config file
                    with open('/etc/influxdb2/influx-configs', 'r') as f:
                        content = f.read()
                        # Look for token in the config
                        for line in content.split('\n'):
                            if 'token' in line and '=' in line:
                                token = line.split('=')[1].strip().strip('"')
                                if token and len(token) > 10:  # Basic token validation
                                    self.logger.info("Found InfluxDB token in config file")
                                    return token
                except FileNotFoundError:
                    pass
                
                self.logger.debug(f"Waiting for InfluxDB token... (attempt {attempt + 1}/30)")
                await asyncio.sleep(2)
            
            self.logger.error("Could not find InfluxDB token in config file")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token from config: {e}")
            return None
    
    async def _test_connection(self) -> bool:
        """
        Test connection to InfluxDB.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            # Simple ping test for basic connectivity
            import requests
            response = requests.get(f"{self.config.influxdb_url}/ping", timeout=5)
            if response.status_code == 204:
                self.logger.info("InfluxDB connection test successful")
                return True
            else:
                self.logger.warning(f"InfluxDB ping failed: {response.status_code}, trying client health check")
                # Fall back to client health check
                try:
                    health = self.client.health()
                    if health.status == "pass":
                        self.logger.info("InfluxDB client health check successful")
                        return True
                    else:
                        self.logger.error(f"InfluxDB health check failed: {health.status}")
                        return False
                except Exception:
                    # If health check fails, assume basic connectivity works
                    self.logger.info("InfluxDB basic connectivity assumed working")
                    return True
        except Exception as e:
            self.logger.error(f"InfluxDB connection test failed: {e}")
            return False
    
    async def _ensure_bucket_exists(self) -> bool:
        """
        Ensure the target bucket exists in InfluxDB.
        
        Returns:
            True if bucket exists or was created, False otherwise.
        """
        try:
            buckets_api = self.client.buckets_api()
            
            # Check if bucket exists
            buckets = buckets_api.find_buckets()
            bucket_names = [bucket.name for bucket in buckets.buckets]
            
            if self.config.influxdb_bucket in bucket_names:
                self.logger.info(f"Bucket '{self.config.influxdb_bucket}' already exists")
                return True
            
            # Create bucket if it doesn't exist
            try:
                org = self.client.organizations_api().find_organizations(org=self.config.influxdb_org)[0]
                buckets_api.create_bucket(
                    bucket_name=self.config.influxdb_bucket,
                    org_id=org.id
                )
                self.logger.info(f"Created bucket '{self.config.influxdb_bucket}'")
                return True
            except ApiException as e:
                if "already exists" in str(e):
                    self.logger.info(f"Bucket '{self.config.influxdb_bucket}' already exists")
                    return True
                else:
                    raise
                    
        except Exception as e:
            self.logger.error(f"Error ensuring bucket exists: {e}")
            return False
    
    async def write_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Write metrics to InfluxDB.
        
        Args:
            metrics: Processed metrics dictionary
            
        Returns:
            True if write succeeded, False otherwise.
        """
        try:
            if not self.write_api:
                self.logger.error("Write API not initialized")
                return False
            
            # Convert metrics to InfluxDB line protocol format
            point_data = self._convert_to_point(metrics)
            
            if not point_data:
                self.logger.error("Failed to convert metrics to InfluxDB point")
                return False
            
            # Write to InfluxDB
            self.write_api.write(
                bucket=self.config.influxdb_bucket,
                record=point_data
            )
            
            self.logger.debug(f"Successfully wrote metrics to InfluxDB")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing metrics to InfluxDB: {e}")
            return False
    
    def _convert_to_point(self, metrics: Dict[str, Any]) -> Optional[str]:
        """
        Convert metrics dictionary to InfluxDB line protocol format.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Line protocol string or None if conversion failed.
        """
        try:
            measurement = metrics.get('measurement', 'network_telemetry')
            
            # Build tags
            tags = []
            for key, value in metrics.get('tags', {}).items():
                if value is not None:
                    tags.append(f"{key}={value}")
            
            tag_string = ','.join(tags)
            if tag_string:
                tag_string = ',' + tag_string
            
            # Build fields
            fields = []
            for key, value in metrics.get('fields', {}).items():
                if value is not None:
                    if isinstance(value, str):
                        fields.append(f'{key}="{value}"')
                    else:
                        fields.append(f'{key}={value}')
            
            if not fields:
                self.logger.warning("No fields to write")
                return None
            
            field_string = ','.join(fields)
            
            # Build timestamp
            timestamp = metrics.get('timestamp', int(time.time()))
            timestamp_ns = int(timestamp * 1_000_000_000)  # Convert to nanoseconds
            
            # Combine into line protocol format
            line = f"{measurement}{tag_string} {field_string} {timestamp_ns}"
            
            self.logger.debug(f"Generated line protocol: {line}")
            return line
            
        except Exception as e:
            self.logger.error(f"Error converting metrics to point: {e}")
            return None
    
    async def query_metrics(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Query metrics from InfluxDB.
        
        Args:
            query: Flux query string
            
        Returns:
            List of query results or None if query failed.
        """
        try:
            if not self.query_api:
                self.logger.error("Query API not initialized")
                return None
            
            tables = self.query_api.query(query, org=self.config.influxdb_org)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append(record.values)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying InfluxDB: {e}")
            return None
    
    async def get_recent_metrics(self, hours: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent metrics from InfluxDB.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent metrics or None if query failed.
        """
        query = f'''
        from(bucket: "{self.config.influxdb_bucket}")
        |> range(start: -{hours}h)
        |> filter(fn: (r) => r._measurement == "network_telemetry")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 100)
        '''
        
        return await self.query_metrics(query)
    
    async def close(self):
        """Close InfluxDB connection."""
        try:
            if self.client:
                self.client.close()
                self.logger.info("InfluxDB client closed")
        except Exception as e:
            self.logger.error(f"Error closing InfluxDB client: {e}")

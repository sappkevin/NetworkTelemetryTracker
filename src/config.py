"""
Configuration module for Network Telemetry Service.

Handles all configuration parameters from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration class for the network telemetry service."""
    
    # Network monitoring configuration
    target_fqdn: str
    monitoring_interval: int
    ping_count: int
    ping_timeout: int
    
    # InfluxDB configuration
    influxdb_url: str
    influxdb_token: Optional[str]
    influxdb_org: str
    influxdb_bucket: str
    
    # Logging configuration
    log_level: str
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.target_fqdn = os.getenv("TARGET_FQDN", "google.com")
        self.monitoring_interval = int(os.getenv("MONITORING_INTERVAL", "60"))
        self.ping_count = int(os.getenv("PING_COUNT", "5"))
        self.ping_timeout = int(os.getenv("PING_TIMEOUT", "10"))
        
        self.influxdb_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.influxdb_token = os.getenv("INFLUXDB_TOKEN")
        self.influxdb_org = os.getenv("INFLUXDB_ORG", "nflx")
        self.influxdb_bucket = os.getenv("INFLUXDB_BUCKET", "default")
        
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate configuration parameters."""
        if not self.target_fqdn:
            raise ValueError("TARGET_FQDN cannot be empty")
        
        if self.monitoring_interval < 10:
            raise ValueError("MONITORING_INTERVAL must be at least 10 seconds")
        
        if self.ping_count < 1:
            raise ValueError("PING_COUNT must be at least 1")
        
        if self.ping_timeout < 1:
            raise ValueError("PING_TIMEOUT must be at least 1 second")
        
        if not self.influxdb_url:
            raise ValueError("INFLUXDB_URL cannot be empty")
        
        if not self.influxdb_org:
            raise ValueError("INFLUXDB_ORG cannot be empty")
        
        if not self.influxdb_bucket:
            raise ValueError("INFLUXDB_BUCKET cannot be empty")
    
    def __str__(self) -> str:
        """String representation of configuration (excluding sensitive data)."""
        return f"""Configuration:
  Target FQDN: {self.target_fqdn}
  Monitoring Interval: {self.monitoring_interval}s
  Ping Count: {self.ping_count}
  Ping Timeout: {self.ping_timeout}s
  InfluxDB URL: {self.influxdb_url}
  InfluxDB Org: {self.influxdb_org}
  InfluxDB Bucket: {self.influxdb_bucket}
  Log Level: {self.log_level}
"""

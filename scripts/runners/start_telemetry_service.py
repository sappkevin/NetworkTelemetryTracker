#!/usr/bin/env python3
"""
Start the telemetry service with geolocation collection.
This runs the service continuously to collect and store network + geolocation data.
"""

import asyncio
import sys
import os
import signal
import logging

sys.path.insert(0, 'src')

from src.main import NetworkTelemetryService

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('telemetry_service.log')
        ]
    )

async def main():
    """Start the telemetry service."""
    # Set up environment if not already configured
    os.environ.setdefault('TARGET_FQDN', 'google.com')
    os.environ.setdefault('MONITORING_INTERVAL', '300')  # 5 minutes
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Network Telemetry Service with Geolocation")
    logger.info("=" * 60)
    
    # Create and start service
    service = NetworkTelemetryService()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, stopping service...")
        service.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await service.cleanup()
        logger.info("Service stopped")

if __name__ == "__main__":
    asyncio.run(main())
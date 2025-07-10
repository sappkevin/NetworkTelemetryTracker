#!/usr/bin/env python3
"""
Collect a few sample data points with geolocation to populate the dashboard.
Run this to quickly get some geolocation data into InfluxDB for testing.
"""

import asyncio
import sys
import os
import logging
import time

sys.path.insert(0, 'src')

from src.config import Config
from src.telemetry import NetworkTelemetry

async def collect_sample_data():
    """Collect several sample data points with different targets."""
    
    # Set up environment
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Test different targets for variety
    targets = [
        'google.com',
        'github.com', 
        'stackoverflow.com',
        'wikipedia.org'
    ]
    
    logger.info("Collecting sample geolocation data...")
    logger.info("=" * 50)
    
    for i, target in enumerate(targets):
        try:
            logger.info(f"Collecting data for {target} ({i+1}/{len(targets)})")
            
            # Update target
            os.environ['TARGET_FQDN'] = target
            
            # Create fresh config and telemetry
            config = Config()
            telemetry = NetworkTelemetry(config)
            
            # Initialize and collect
            if await telemetry.initialize():
                success = await telemetry.collect_and_store_metrics()
                if success:
                    logger.info(f"✅ Successfully collected data for {target}")
                else:
                    logger.warning(f"⚠️ Failed to collect data for {target}")
                
                await telemetry.cleanup()
            else:
                logger.error(f"❌ Failed to initialize telemetry for {target}")
            
            # Small delay between collections
            if i < len(targets) - 1:
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error collecting data for {target}: {e}")
    
    logger.info("Sample data collection completed!")
    logger.info("Check the Geolocation Dashboard in Grafana - it should now show data")

if __name__ == "__main__":
    asyncio.run(collect_sample_data())
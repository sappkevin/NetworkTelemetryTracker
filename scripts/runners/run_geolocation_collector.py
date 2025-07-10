#!/usr/bin/env python3
"""
Simple geolocation data collector that works with your existing database setup.
This will collect and store geolocation data in InfluxDB.
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

async def collect_geolocation_data():
    """Collect geolocation data and store in InfluxDB."""
    
    # Configure environment
    os.environ.setdefault('TARGET_FQDN', 'google.com')
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        from src.config import Config
        from src.telemetry import NetworkTelemetry
        
        # Test different targets for variety
        targets = ['google.com', 'github.com', 'stackoverflow.com', 'wikipedia.org', 'amazon.com']
        
        logger.info("Starting geolocation data collection...")
        logger.info(f"Targets: {', '.join(targets)}")
        
        successful_collections = 0
        
        for i, target in enumerate(targets):
            logger.info(f"Processing {target} ({i+1}/{len(targets)})")
            
            try:
                # Update target
                os.environ['TARGET_FQDN'] = target
                
                # Create config and telemetry
                config = Config()
                telemetry = NetworkTelemetry(config)
                
                # Initialize with database connection
                if await telemetry.initialize():
                    logger.info(f"Initialized telemetry for {target}")
                    
                    # Collect metrics (this includes geolocation)
                    success = await telemetry.collect_and_store_metrics()
                    
                    if success:
                        logger.info(f"✅ Successfully stored geolocation data for {target}")
                        successful_collections += 1
                    else:
                        logger.warning(f"❌ Failed to store data for {target}")
                        
                    await telemetry.cleanup()
                    
                else:
                    logger.error(f"Failed to initialize telemetry for {target}")
                
                # Brief pause between collections
                if i < len(targets) - 1:
                    await asyncio.sleep(3)
                    
            except Exception as e:
                logger.error(f"Error processing {target}: {e}")
                continue
        
        logger.info(f"Collection complete: {successful_collections}/{len(targets)} successful")
        
        if successful_collections > 0:
            logger.info("✅ Geolocation data has been stored in InfluxDB")
            logger.info("Open your Geolocation Dashboard - it should now show data!")
        else:
            logger.error("❌ No data was successfully collected")
            
        return successful_collections > 0
        
    except ImportError as e:
        logger.error(f"Module import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(collect_geolocation_data())
    if success:
        print("\n🎉 Geolocation data collection completed successfully!")
        print("The dashboard should now display geographic network data.")
    else:
        print("\n❌ Collection failed. Check the logs above for details.")
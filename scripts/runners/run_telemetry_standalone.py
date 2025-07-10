#!/usr/bin/env python3
"""
Standalone telemetry runner to test geolocation data collection.
This script runs the telemetry service once to collect and store geolocation data.
"""

import asyncio
import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, 'src')

from src.config import Config
from src.telemetry import NetworkTelemetry
from src.database import InfluxDBClient

async def run_telemetry_once():
    """Run telemetry collection once and store in InfluxDB."""
    
    # Set up environment for testing
    os.environ.setdefault('TARGET_FQDN', 'google.com')
    os.environ.setdefault('MONITORING_INTERVAL', '60')
    os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
    os.environ.setdefault('INFLUXDB_ORG', 'nflx')
    os.environ.setdefault('INFLUXDB_BUCKET', 'default')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration
        config = Config()
        logger.info(f"Initialized config for target: {config.target_fqdn}")
        
        # Initialize telemetry
        telemetry = NetworkTelemetry(config)
        
        # Initialize database connection
        success = await telemetry.initialize()
        if not success:
            logger.error("Failed to initialize telemetry system")
            return False
        
        logger.info("Telemetry system initialized successfully")
        
        # Collect and store metrics
        logger.info("Collecting network and geolocation metrics...")
        success = await telemetry.collect_and_store_metrics()
        
        if success:
            logger.info("✅ Metrics collected and stored successfully!")
            logger.info("Check the Geolocation Dashboard in Grafana - it should now show data")
        else:
            logger.error("❌ Failed to collect or store metrics")
        
        # Cleanup
        await telemetry.cleanup()
        
        return success
        
    except Exception as e:
        logger.error(f"Error running telemetry: {e}")
        return False

async def verify_data():
    """Verify that data was stored in InfluxDB."""
    
    try:
        # Check if we can query the data
        config = Config()
        db_client = InfluxDBClient(config)
        
        if await db_client.initialize():
            # Query recent metrics
            query = '''
            from(bucket: "default")
              |> range(start: -1h)
              |> filter(fn: (r) => r._measurement == "network_telemetry")
              |> filter(fn: (r) => r._field == "target_country" or r._field == "distance_km")
              |> last()
            '''
            
            results = await db_client.query_metrics(query)
            if results:
                print(f"\n✅ Found {len(results)} recent records in InfluxDB")
                for record in results[:5]:  # Show first 5
                    field = record.get('_field', 'unknown')
                    value = record.get('_value', 'unknown')
                    print(f"   {field}: {value}")
                return True
            else:
                print("\n❌ No data found in InfluxDB")
                return False
        else:
            print("\n❌ Could not connect to InfluxDB")
            return False
            
    except Exception as e:
        print(f"\n❌ Error verifying data: {e}")
        return False

async def main():
    """Main function."""
    print("🚀 Running Network Telemetry with Geolocation Collection")
    print("=" * 60)
    
    # Run telemetry once
    success = await run_telemetry_once()
    
    if success:
        print("\n🔍 Verifying data was stored...")
        await verify_data()
        
        print("\n💡 Next steps:")
        print("   1. Open Grafana: http://localhost:3000")
        print("   2. Go to the 'Network Geolocation Dashboard'")
        print("   3. You should now see geolocation data!")
        print("   4. To collect data continuously, start the full service:")
        print("      docker-compose up -d")
    else:
        print("\n❌ Failed to collect telemetry data")
        print("   - Check InfluxDB is running: curl http://localhost:8086/ping")
        print("   - Check logs above for specific errors")
        print("   - Ensure network connectivity for geolocation API calls")

if __name__ == "__main__":
    asyncio.run(main())
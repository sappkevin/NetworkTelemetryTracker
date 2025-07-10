#!/usr/bin/env python3
"""
Simple test to verify geolocation collection works and identify what's missing.
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, 'src')

async def test_geolocation_collection():
    """Test just the geolocation collection without database."""
    
    try:
        from src.config import Config
        from src.telemetry import NetworkTelemetry
        
        # Set up basic config
        os.environ.setdefault('TARGET_FQDN', 'google.com')
        os.environ.setdefault('MONITORING_INTERVAL', '60')
        os.environ.setdefault('INFLUXDB_URL', 'http://localhost:8086')
        os.environ.setdefault('INFLUXDB_ORG', 'nflx')
        os.environ.setdefault('INFLUXDB_BUCKET', 'default')
        
        config = Config()
        telemetry = NetworkTelemetry(config)
        
        print("Testing geolocation collection...")
        
        # Test individual components
        print("\n1. Testing network metrics collection...")
        network_metrics = await telemetry._collect_network_metrics()
        
        if network_metrics:
            print(f"✅ Collected {len(network_metrics)} network metrics fields")
            
            # Check if geolocation fields are present
            geo_fields = [k for k in network_metrics.keys() if any(
                x in k for x in ['target_', 'source_', 'distance_', 'latitude', 'longitude', 'country', 'city']
            )]
            
            if geo_fields:
                print(f"✅ Found {len(geo_fields)} geolocation fields:")
                for field in geo_fields[:10]:  # Show first 10
                    value = network_metrics[field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"   {field}: {value}")
                
                # Test metrics processing
                print("\n2. Testing metrics processing...")
                processed = telemetry._process_metrics(network_metrics)
                if processed:
                    geo_processed = {k: v for k, v in processed['fields'].items() if any(
                        x in k for x in ['target_', 'source_', 'distance_']
                    )}
                    print(f"✅ Processed {len(geo_processed)} geolocation fields for storage")
                    
                    # Show sample processed data
                    sample_data = {}
                    for key in ['target_country', 'target_city', 'source_country', 'source_city', 'distance_km']:
                        if key in geo_processed:
                            sample_data[key] = geo_processed[key]
                    
                    print("Sample processed geolocation data:")
                    print(json.dumps(sample_data, indent=2))
                    
                    return True
                else:
                    print("❌ Failed to process metrics")
                    return False
            else:
                print("❌ No geolocation fields found in collected metrics")
                print("Available fields:", list(network_metrics.keys()))
                return False
        else:
            print("❌ Failed to collect network metrics")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🧪 Testing Geolocation Collection")
    print("=" * 50)
    
    success = await test_geolocation_collection()
    
    if success:
        print("\n✅ Geolocation collection is working!")
        print("\nTo get this data into InfluxDB:")
        print("1. Ensure InfluxDB container is running")
        print("2. Start the telemetry service")
        print("3. The service will collect and store geolocation data automatically")
    else:
        print("\n❌ Geolocation collection needs to be fixed")
        print("Check the errors above for details")

if __name__ == "__main__":
    asyncio.run(main())
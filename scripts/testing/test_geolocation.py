#!/usr/bin/env python3
"""
Test script to verify geolocation functionality works properly.
"""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

from src.config import Config
from src.telemetry import NetworkTelemetry

async def test_geolocation():
    """Test the geolocation functionality."""
    
    # Set up a test configuration
    os.environ['TARGET_FQDN'] = 'google.com'
    os.environ['MONITORING_INTERVAL'] = '60'
    os.environ['INFLUXDB_URL'] = 'http://localhost:8086'
    os.environ['INFLUXDB_ORG'] = 'test'
    os.environ['INFLUXDB_BUCKET'] = 'test'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    config = Config()
    telemetry = NetworkTelemetry(config)
    
    print("Testing geolocation functionality...")
    print("=" * 50)
    
    # Test hostname resolution
    print("1. Testing hostname resolution...")
    target_ip = await telemetry._resolve_hostname('google.com')
    print(f"   google.com resolves to: {target_ip}")
    
    # Test public IP detection
    print("\n2. Testing public IP detection...")
    source_ip = await telemetry._get_public_ip()
    print(f"   Public IP: {source_ip}")
    
    # Test geolocation lookup
    if target_ip:
        print(f"\n3. Testing geolocation lookup for {target_ip}...")
        target_geo = await telemetry._get_geolocation(target_ip)
        print(f"   Target location: {target_geo}")
    
    if source_ip:
        print(f"\n4. Testing geolocation lookup for {source_ip}...")
        source_geo = await telemetry._get_geolocation(source_ip)
        print(f"   Source location: {source_geo}")
    
    # Test distance calculation
    if target_ip and source_ip:
        print(f"\n5. Testing distance calculation...")
        target_geo = await telemetry._get_geolocation(target_ip)
        source_geo = await telemetry._get_geolocation(source_ip)
        
        if (target_geo and source_geo and 
            'latitude' in target_geo and 'longitude' in target_geo and
            'latitude' in source_geo and 'longitude' in source_geo):
            
            distance = telemetry._calculate_distance(
                source_geo['latitude'], source_geo['longitude'],
                target_geo['latitude'], target_geo['longitude']
            )
            print(f"   Distance: {distance:.2f} km")
            
            # Test complete metrics collection
            print(f"\n6. Testing complete geolocation metrics collection...")
            geo_metrics = await telemetry._collect_geolocation_metrics()
            print(f"   Collected metrics: {len(geo_metrics)} fields")
            
            # Show some key metrics
            for key in ['target_country', 'target_city', 'source_country', 'source_city', 'distance_km']:
                if key in geo_metrics:
                    print(f"   {key}: {geo_metrics[key]}")
        else:
            print("   Could not calculate distance - missing coordinate data")
    
    print("\n" + "=" * 50)
    print("Geolocation test completed!")

if __name__ == "__main__":
    asyncio.run(test_geolocation())
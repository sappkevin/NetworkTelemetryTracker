#!/usr/bin/env python3
"""
Unified telemetry runner that provides all functionality in one place.
This replaces the separate start_telemetry_service.py and run_geolocation_collector.py files.
"""

import asyncio
import sys
import os
import argparse

# Add src to path
sys.path.insert(0, 'src')

from src.telemetry import run_continuous_service, collect_sample_data, run_single_collection

def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(description='Network Telemetry Service')
    parser.add_argument('mode', choices=['continuous', 'sample', 'single'], 
                       help='Mode to run: continuous monitoring, sample data collection, or single collection')
    parser.add_argument('--target', default='google.com', 
                       help='Target FQDN to monitor (default: google.com)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    parser.add_argument('--influxdb-url', default='http://localhost:8086',
                       help='InfluxDB URL (default: http://localhost:8086)')
    parser.add_argument('--influxdb-org', default='nflx',
                       help='InfluxDB organization (default: nflx)')
    parser.add_argument('--influxdb-bucket', default='default',
                       help='InfluxDB bucket (default: default)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ['TARGET_FQDN'] = args.target
    os.environ['MONITORING_INTERVAL'] = str(args.interval)
    os.environ['INFLUXDB_URL'] = args.influxdb_url
    os.environ['INFLUXDB_ORG'] = args.influxdb_org
    os.environ['INFLUXDB_BUCKET'] = args.influxdb_bucket
    os.environ['LOG_LEVEL'] = args.log_level
    
    # Run based on mode
    if args.mode == 'continuous':
        print("🚀 Starting continuous telemetry monitoring...")
        print(f"   Target: {args.target}")
        print(f"   Interval: {args.interval} seconds")
        print(f"   Database: {args.influxdb_url}")
        print("   Press Ctrl+C to stop")
        print("=" * 60)
        asyncio.run(run_continuous_service())
        
    elif args.mode == 'sample':
        print("🧪 Collecting sample geolocation data...")
        print(f"   Database: {args.influxdb_url}")
        print("=" * 60)
        success = asyncio.run(collect_sample_data())
        if success:
            print("\n✅ Sample data collection completed!")
            print("   Check your Geolocation Dashboard - it should now show data")
        else:
            print("\n❌ Sample data collection failed")
            
    elif args.mode == 'single':
        print("🎯 Running single collection cycle...")
        print(f"   Target: {args.target}")
        print(f"   Database: {args.influxdb_url}")
        print("=" * 60)
        success = asyncio.run(run_single_collection())
        if success:
            print("\n✅ Single collection completed successfully!")
        else:
            print("\n❌ Single collection failed")

if __name__ == "__main__":
    main()
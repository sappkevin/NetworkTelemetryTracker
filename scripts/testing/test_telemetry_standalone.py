#!/usr/bin/env python3
"""
Standalone telemetry test that works without InfluxDB.
This tests the core telemetry collection functionality.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from src.config import Config
from src.telemetry import NetworkTelemetry

async def test_telemetry_collection():
    """Test telemetry collection without database dependency."""
    print("Testing core telemetry collection functionality...")
    
    try:
        # Create config
        config = Config()
        print(f"Target: {config.target_fqdn}")
        print(f"Ping count: {config.ping_count}")
        
        # Create telemetry instance
        telemetry = NetworkTelemetry(config)
        
        # Test network metrics collection (without database)
        print("\n=== Testing Network Metrics Collection ===")
        raw_metrics = await telemetry._collect_network_metrics()
        
        if not raw_metrics:
            print("❌ Failed to collect network metrics")
            return False
        
        print("✅ Network metrics collected successfully:")
        for key, value in raw_metrics.items():
            if isinstance(value, (int, float)):
                print(f"   {key}: {value}")
            elif isinstance(value, str):
                print(f"   {key}: {value}")
            elif isinstance(value, list) and len(value) < 5:
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: <{type(value).__name__}>")
        
        # Test metrics processing
        print("\n=== Testing Metrics Processing ===")
        processed = telemetry._process_metrics(raw_metrics)
        
        if not processed:
            print("❌ Failed to process metrics")
            return False
        
        print("✅ Metrics processed successfully:")
        print(f"   Measurement: {processed['measurement']}")
        print(f"   Tags: {processed['tags']}")
        print(f"   Fields count: {len(processed['fields'])}")
        
        # Show key fields for dashboard compatibility
        print("\n=== Key Dashboard Fields ===")
        key_fields = [
            'rtt_avg', 'packet_loss', 'hop_count', 'http_status_code',
            'jitter_ms', 'service_available', 'throughput_mbps',
            'dns_resolution_ms', 'tcp_handshake_ms'
        ]
        
        missing_fields = []
        for field in key_fields:
            if field in processed['fields']:
                value = processed['fields'][field]
                print(f"   ✅ {field}: {value}")
            else:
                missing_fields.append(field)
                print(f"   ❌ {field}: MISSING")
        
        if missing_fields:
            print(f"\n⚠️ Missing {len(missing_fields)} key fields")
            return False
        else:
            print("\n✅ All key dashboard fields present")
        
        # Save test data to file for inspection
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'raw_metrics': raw_metrics,
            'processed_metrics': processed
        }
        
        with open('test_telemetry_output.json', 'w') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        print("\n📁 Test data saved to: test_telemetry_output.json")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("TELEMETRY SERVICE STANDALONE TEST")
    print("=" * 60)
    
    success = await test_telemetry_collection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TELEMETRY SERVICE IS WORKING")
        print("The core functionality is operational.")
        print("Next step: Set up InfluxDB for data storage.")
    else:
        print("❌ TELEMETRY SERVICE HAS ISSUES")
        print("Core functionality needs debugging.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test InfluxDB schema and data structure for dashboard compatibility.
This script checks what data structure is being written to InfluxDB.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from telemetry import NetworkTelemetry

async def test_influx_data_structure():
    """Test the actual data structure being written to InfluxDB."""
    print("🔍 Testing InfluxDB data structure...")
    
    try:
        config = Config()
        telemetry = NetworkTelemetry(config)
        
        # Simulate a complete collection cycle
        print("📊 Simulating complete metrics collection...")
        
        # Create mock raw metrics that would come from actual network monitoring
        raw_metrics = {
            'target': 'google.com',
            'timestamp': 1689000000,
            'collection_duration': 5.2,
            'rtt_min': 15.5,
            'rtt_avg': 25.2,
            'rtt_max': 45.8,
            'rtt_mdev': 8.3,
            'packet_loss': 1.2,
            'packets_transmitted': 4,
            'packets_received': 4,
            'hop_count': 12,
            'route_path': [{'ip': '8.8.8.8', 'rtt': 25.2}],
            'target_ip': '8.8.8.8',
            'source_ip': '203.0.113.1',
            'target_latitude': 37.7749,
            'target_longitude': -122.4194,
            'target_country': 'United States',
            'target_region': 'California',
            'target_city': 'San Francisco',
            'target_timezone': 'America/Los_Angeles',
            'target_isp': 'Google LLC',
            'source_latitude': 40.7128,
            'source_longitude': -74.0060,
            'source_country': 'United States',
            'source_region': 'New York',
            'source_city': 'New York',
            'source_timezone': 'America/New_York',
            'source_isp': 'Example ISP',
            'distance_km': 4135.2
        }
        
        # Process metrics through the telemetry system
        processed = telemetry._process_metrics(raw_metrics)
        
        if not processed:
            print("❌ Failed to process metrics")
            return
        
        print(f"✅ Processed metrics successfully")
        print(f"📊 Measurement: {processed['measurement']}")
        print(f"🏷️  Tags: {processed['tags']}")
        print(f"📈 Fields count: {len(processed['fields'])}")
        
        # Analyze field categories
        field_categories = {
            'Basic Network': ['rtt_avg', 'rtt_min', 'rtt_max', 'packet_loss', 'hop_count'],
            'HTTP Status': ['http_status_code'],
            'QoS Metrics': ['jitter_ms', 'queue_depth', 'buffer_utilization_pct', 'voice_quality_score', 'video_quality_score', 'data_quality_score'],
            'Availability': ['service_available', 'response_success', 'service_degraded', 'failure_count'],
            'Throughput': ['throughput_mbps', 'goodput_mbps', 'bandwidth_utilization_pct', 'bits_per_second', 'packets_per_second'],
            'Response Time': ['dns_resolution_ms', 'tcp_handshake_ms', 'app_response_ms', 'db_query_ms', 'total_response_ms'],
            'Geolocation': ['target_latitude', 'target_longitude', 'source_latitude', 'source_longitude', 'distance_km']
        }
        
        print(f"\n📋 FIELD ANALYSIS BY CATEGORY:")
        print("-" * 60)
        
        total_expected = 0
        total_present = 0
        
        for category, expected_fields in field_categories.items():
            present_fields = [f for f in expected_fields if f in processed['fields']]
            missing_fields = [f for f in expected_fields if f not in processed['fields']]
            
            total_expected += len(expected_fields)
            total_present += len(present_fields)
            
            status = "✅" if len(missing_fields) == 0 else "⚠️"
            coverage = (len(present_fields) / len(expected_fields)) * 100
            
            print(f"{status} {category}: {coverage:.1f}% ({len(present_fields)}/{len(expected_fields)})")
            
            if missing_fields:
                print(f"    Missing: {', '.join(missing_fields)}")
            
            # Show sample values for present fields
            if present_fields:
                sample_values = []
                for field in present_fields[:3]:  # Show first 3 as examples
                    value = processed['fields'][field]
                    sample_values.append(f"{field}={value}")
                print(f"    Sample: {', '.join(sample_values)}")
            print()
        
        overall_coverage = (total_present / total_expected) * 100
        print(f"📊 OVERALL COVERAGE: {overall_coverage:.1f}% ({total_present}/{total_expected} fields)")
        
        # Test InfluxDB line protocol conversion
        print(f"\n🗄️  TESTING INFLUXDB LINE PROTOCOL:")
        print("-" * 60)
        
        # This tests the conversion that would happen when writing to InfluxDB
        line_protocol = telemetry.db_client._convert_to_point(processed)
        
        if line_protocol:
            print("✅ Line protocol conversion successful")
            # Show truncated version for readability
            if len(line_protocol) > 200:
                print(f"📝 Line Protocol: {line_protocol[:200]}...")
            else:
                print(f"📝 Line Protocol: {line_protocol}")
        else:
            print("❌ Line protocol conversion failed")
        
        print(f"\n🎯 DASHBOARD READINESS SUMMARY:")
        print("=" * 60)
        
        if overall_coverage >= 95:
            print("🎉 EXCELLENT: All dashboards should work perfectly")
        elif overall_coverage >= 85:
            print("✅ GOOD: Most dashboard features will work")
        elif overall_coverage >= 70:
            print("⚠️  PARTIAL: Some dashboard panels may show no data")
        else:
            print("❌ INCOMPLETE: Significant dashboard features missing")
        
        return processed
        
    except Exception as e:
        print(f"❌ Error testing data structure: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    result = await test_influx_data_structure()
    
    if result:
        print(f"\n✅ Test completed successfully")
        print(f"📊 Total fields collected: {len(result['fields'])}")
    else:
        print(f"\n❌ Test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
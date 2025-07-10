#!/usr/bin/env python3
"""
Check telemetry data collection fields for dashboard compatibility.
Simple field analysis without complex imports.
"""

import json
import os
from datetime import datetime

def analyze_telemetry_implementation():
    """Analyze the telemetry.py file to identify all collected fields."""
    telemetry_files = [
        'docker_telemetry_service.py',
        'src/telemetry.py'
    ]
    
    collected_fields = set()
    
    for file_path in telemetry_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for field assignments
                lines = content.split('\n')
                for line in lines:
                    if 'fields[' in line and ']' in line:
                        # Extract field name
                        start = line.find("fields['") + 8
                        if start > 7:
                            end = line.find("']", start)
                            if end > start:
                                field_name = line[start:end]
                                collected_fields.add(field_name)
                        else:
                            start = line.find('fields["') + 8
                            if start > 7:
                                end = line.find('"]', start)
                                if end > start:
                                    field_name = line[start:end]
                                    collected_fields.add(field_name)
    
    return collected_fields

def check_database_schema():
    """Check database configuration and setup."""
    database_info = {}
    
    # Check PostgreSQL setup
    if os.getenv('DATABASE_URL'):
        database_info['postgresql'] = {
            'available': True,
            'url_configured': True,
            'table_exists': 'network_telemetry'
        }
    
    # Check InfluxDB setup
    influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    influx_token = os.getenv('INFLUXDB_TOKEN')
    
    database_info['influxdb'] = {
        'url': influx_url,
        'token_configured': bool(influx_token and influx_token != 'your-admin-token-here'),
        'bucket': os.getenv('INFLUXDB_BUCKET', 'default'),
        'organization': os.getenv('INFLUXDB_ORG', 'nflx')
    }
    
    return database_info

def main():
    """Main analysis function."""
    print("=" * 70)
    print("TELEMETRY FIELD COLLECTION ANALYSIS")
    print("=" * 70)
    
    # Analyze collected fields
    fields = analyze_telemetry_implementation()
    
    print(f"\n📊 COLLECTED FIELDS ({len(fields)} total):")
    print("-" * 50)
    
    # Group fields by category
    field_categories = {
        'Basic Network': ['rtt_min', 'rtt_max', 'rtt_avg', 'rtt_mdev', 'packet_loss', 'hop_count'],
        'HTTP Metrics': ['http_status_code', 'dns_resolution_ms', 'tcp_handshake_ms'],
        'QoS Metrics': ['jitter_ms', 'queue_depth', 'voice_quality_score', 'video_quality_score', 'data_quality_score'],
        'Availability': ['service_available', 'response_success', 'service_degraded'],
        'Throughput': ['throughput_mbps', 'goodput_mbps', 'bandwidth_utilization_pct'],
        'Response Times': ['app_response_ms', 'db_query_ms', 'total_response_ms'],
        'Geolocation': ['target_latitude', 'target_longitude', 'source_latitude', 'source_longitude', 'distance_km'],
        'Additional': ['packets_per_second', 'bits_per_second', 'buffer_utilization_pct']
    }
    
    total_expected = sum(len(cat_fields) for cat_fields in field_categories.values())
    
    for category, expected_fields in field_categories.items():
        found_fields = [f for f in expected_fields if f in fields]
        missing_fields = [f for f in expected_fields if f not in fields]
        
        print(f"\n{category}:")
        print(f"  ✅ Found ({len(found_fields)}/{len(expected_fields)}): {', '.join(found_fields)}")
        if missing_fields:
            print(f"  ❌ Missing: {', '.join(missing_fields)}")
    
    # Check database configuration
    print(f"\n🗄️  DATABASE CONFIGURATION:")
    print("-" * 50)
    
    db_info = check_database_schema()
    
    for db_type, info in db_info.items():
        print(f"\n{db_type.upper()}:")
        for key, value in info.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
    
    # Overall status
    print(f"\n📈 OVERALL STATUS:")
    print("-" * 50)
    coverage = (len(fields) / total_expected) * 100
    print(f"Field Coverage: {len(fields)}/{total_expected} ({coverage:.1f}%)")
    
    if coverage >= 90:
        print("✅ EXCELLENT: All major telemetry fields are being collected")
    elif coverage >= 75:
        print("⚠️  GOOD: Most telemetry fields are being collected")
    else:
        print("❌ NEEDS WORK: Many telemetry fields are missing")
    
    # Check recent telemetry data
    telemetry_files = ['telemetry_data', 'test_telemetry_output.json']
    
    recent_data = None
    for data_source in telemetry_files:
        if os.path.isdir(data_source):
            # Check directory for recent files
            files = [f for f in os.listdir(data_source) if f.endswith('.json')]
            if files:
                latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(data_source, x)))
                file_path = os.path.join(data_source, latest_file)
                try:
                    with open(file_path, 'r') as f:
                        recent_data = json.load(f)
                    break
                except:
                    pass
        elif os.path.exists(data_source):
            try:
                with open(data_source, 'r') as f:
                    recent_data = json.load(f)
                break
            except:
                pass
    
    if recent_data:
        print(f"\n📝 RECENT DATA SAMPLE:")
        print("-" * 50)
        
        if 'processed_metrics' in recent_data:
            sample_fields = recent_data['processed_metrics'].get('fields', {})
        elif 'fields' in recent_data:
            sample_fields = recent_data['fields']
        else:
            sample_fields = recent_data
        
        print(f"Sample contains {len(sample_fields)} fields:")
        
        # Show key dashboard fields
        key_fields = ['rtt_avg', 'packet_loss', 'hop_count', 'http_status_code', 'jitter_ms']
        for field in key_fields:
            if field in sample_fields:
                print(f"  ✅ {field}: {sample_fields[field]}")
            else:
                print(f"  ❌ {field}: MISSING")

if __name__ == "__main__":
    main()
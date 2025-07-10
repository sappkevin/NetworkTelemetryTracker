#!/usr/bin/env python3
"""
Test script to check what data exists in InfluxDB and help debug dashboard issues.
"""

import subprocess
import json

def test_influx_query(query, description):
    """Test a specific InfluxDB query."""
    print(f"\n🔍 {description}")
    print("-" * 50)
    
    # Use curl to query InfluxDB directly
    cmd = [
        'curl', '-s', '-X', 'POST',
        'http://localhost:8086/api/v2/query?org=nflx',
        '-H', 'Accept: application/csv',
        '-H', 'Content-Type: application/vnd.flux',
        '-d', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and not output.startswith('error'):
                print("✅ Query successful:")
                # Show first few lines
                lines = output.split('\n')
                for i, line in enumerate(lines[:10]):
                    print(f"   {line}")
                if len(lines) > 10:
                    print(f"   ... and {len(lines)-10} more lines")
                return True
            else:
                print("❌ No data returned or error:")
                print(f"   {output}")
                return False
        else:
            print("❌ Query failed:")
            print(f"   {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test various queries to understand the data situation."""
    print("🔍 InfluxDB Data Diagnostic Tool")
    print("=" * 60)
    
    # Test 1: Check if any data exists
    query1 = '''
    from(bucket: "default")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_telemetry")
      |> count()
    '''
    test_influx_query(query1, "Check for any network_telemetry data in last 24 hours")
    
    # Test 2: Check what fields exist
    query2 = '''
    from(bucket: "default")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_telemetry")
      |> keep(columns: ["_field"])
      |> group()
      |> distinct(column: "_field")
    '''
    test_influx_query(query2, "List all available fields in network_telemetry")
    
    # Test 3: Check for geolocation fields specifically
    query3 = '''
    from(bucket: "default")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_telemetry")
      |> filter(fn: (r) => r._field =~ /target_.*/ or r._field =~ /source_.*/ or r._field == "distance_km")
      |> count()
    '''
    test_influx_query(query3, "Check for geolocation fields (target_*, source_*, distance_km)")
    
    # Test 4: Get recent data sample
    query4 = '''
    from(bucket: "default")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "network_telemetry")
      |> limit(n: 5)
    '''
    test_influx_query(query4, "Show recent data sample (last hour)")
    
    # Test 5: Check for basic network metrics
    query5 = '''
    from(bucket: "default")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_telemetry")
      |> filter(fn: (r) => r._field == "rtt_avg" or r._field == "packet_loss")
      |> count()
    '''
    test_influx_query(query5, "Check for basic network metrics (rtt_avg, packet_loss)")
    
    print("\n" + "=" * 60)
    print("💡 Diagnostic Summary:")
    print("   - If no data found: telemetry service needs to be running")
    print("   - If basic metrics exist but no geolocation: service needs restart with new code")
    print("   - If geolocation fields exist: dashboard queries may need adjustment")
    print("   - Use 'docker logs network-telemetry' to check service logs")

if __name__ == "__main__":
    main()
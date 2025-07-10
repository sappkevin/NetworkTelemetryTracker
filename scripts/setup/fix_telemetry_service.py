#!/usr/bin/env python3
"""
Fix and verify telemetry service operation.
This script diagnoses and fixes common telemetry service issues.
"""

import subprocess
import os
import time
import requests
import json

def check_dependencies():
    """Check if required system dependencies are available."""
    print("Checking system dependencies...")
    
    dependencies = ['ping', 'traceroute', 'curl']
    missing = []
    
    for dep in dependencies:
        try:
            result = subprocess.run(['which', dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {dep}: {result.stdout.strip()}")
            else:
                print(f"   ❌ {dep}: Not found")
                missing.append(dep)
        except Exception as e:
            print(f"   ❌ {dep}: Error checking - {e}")
            missing.append(dep)
    
    return len(missing) == 0

def test_network_connectivity():
    """Test basic network connectivity."""
    print("Testing network connectivity...")
    
    try:
        # Test ping to Google
        result = subprocess.run(['ping', '-c', '2', 'google.com'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Ping to google.com successful")
            return True
        else:
            print(f"   ❌ Ping failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Ping timeout")
        return False
    except Exception as e:
        print(f"   ❌ Ping error: {e}")
        return False

def setup_simple_data_storage():
    """Set up a simple file-based data storage for testing."""
    print("Setting up simple data storage...")
    
    # Create data directory
    os.makedirs('telemetry_data', exist_ok=True)
    
    # Create a simple data storage script
    storage_script = '''#!/usr/bin/env python3
"""Simple telemetry data storage for testing."""

import json
import os
from datetime import datetime

class SimpleDataStore:
    def __init__(self, data_dir="telemetry_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def store_metrics(self, metrics):
        """Store metrics to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"Metrics stored: {filepath}")
        return True
    
    def get_recent_metrics(self, count=10):
        """Get recent metrics files."""
        files = []
        for f in os.listdir(self.data_dir):
            if f.startswith('metrics_') and f.endswith('.json'):
                files.append(f)
        
        files.sort(reverse=True)
        return files[:count]

if __name__ == "__main__":
    store = SimpleDataStore()
    print(f"Data directory: {store.data_dir}")
    recent = store.get_recent_metrics()
    print(f"Recent files: {len(recent)}")
'''
    
    with open('simple_storage.py', 'w') as f:
        f.write(storage_script)
    
    print("   ✅ Simple data storage ready")
    return True

def run_telemetry_test():
    """Run a basic telemetry test."""
    print("Running telemetry functionality test...")
    
    try:
        # Run the standalone test
        result = subprocess.run(['python', 'test_telemetry_standalone.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Telemetry test passed")
            
            # Check if test output file was created
            if os.path.exists('test_telemetry_output.json'):
                with open('test_telemetry_output.json', 'r') as f:
                    data = json.load(f)
                
                fields = data.get('processed_metrics', {}).get('fields', {})
                print(f"   ✅ Collected {len(fields)} telemetry fields")
                
                # Show sample data
                sample_fields = ['rtt_avg', 'packet_loss', 'hop_count']
                for field in sample_fields:
                    if field in fields:
                        print(f"       {field}: {fields[field]}")
                
                return True
            else:
                print("   ⚠️ Test passed but no output file generated")
                return False
        else:
            print(f"   ❌ Telemetry test failed:")
            print(f"       stdout: {result.stdout}")
            print(f"       stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Telemetry test timeout")
        return False
    except Exception as e:
        print(f"   ❌ Telemetry test error: {e}")
        return False

def provide_next_steps():
    """Provide guidance on next steps."""
    print("\n" + "=" * 60)
    print("NEXT STEPS TO GET DASHBOARDS WORKING")
    print("=" * 60)
    
    print("1. Start InfluxDB (if you have Docker):")
    print("   docker-compose up -d influxdb")
    print("")
    
    print("2. Or install InfluxDB locally:")
    print("   # On macOS: brew install influxdb")
    print("   # On Ubuntu: apt install influxdb2")
    print("")
    
    print("3. Run telemetry with data collection:")
    print("   python telemetry_runner.py continuous")
    print("")
    
    print("4. Check data in InfluxDB:")
    print("   curl http://localhost:8086/ping")
    print("")
    
    print("5. Import dashboards to Grafana:")
    print("   - Access Grafana at http://localhost:3000")
    print("   - Import JSON files from grafana/dashboards/")
    print("")
    
    print("If you see 'no data' in dashboards:")
    print("- Verify InfluxDB is running and accessible")
    print("- Check telemetry service logs for errors")
    print("- Ensure data is being written to correct bucket/measurement")

def main():
    """Main diagnostic and fix routine."""
    print("=" * 60)
    print("TELEMETRY SERVICE DIAGNOSTIC & FIX")
    print("=" * 60)
    
    all_good = True
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Missing system dependencies. Install ping, traceroute, curl")
        all_good = False
    
    # Step 2: Test network
    if not test_network_connectivity():
        print("\n❌ Network connectivity issues")
        all_good = False
    
    # Step 3: Set up simple storage
    if not setup_simple_data_storage():
        print("\n❌ Failed to set up data storage")
        all_good = False
    
    # Step 4: Test telemetry
    if not run_telemetry_test():
        print("\n❌ Telemetry functionality issues")
        all_good = False
    
    if all_good:
        print("\n✅ TELEMETRY SERVICE IS WORKING")
        print("Core telemetry collection is functional.")
        provide_next_steps()
    else:
        print("\n❌ TELEMETRY SERVICE HAS ISSUES")
        print("Please fix the identified problems above.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quick fix script for InfluxDB authorization issues.
This script helps diagnose and fix the "invalid header field value for Authorization" error.
"""

import os
import sys
import subprocess
import json

def check_influxdb_connection():
    """Check if InfluxDB is accessible."""
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:8086/ping'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ InfluxDB is accessible")
            return True
        else:
            print("❌ InfluxDB is not accessible")
            return False
    except Exception as e:
        print(f"❌ Error checking InfluxDB: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = [
        'INFLUXDB_URL',
        'INFLUXDB_ORG', 
        'INFLUXDB_BUCKET'
    ]
    
    optional_vars = [
        'INFLUXDB_TOKEN',
        'INFLUXDB_ADMIN_USER',
        'INFLUXDB_ADMIN_PASSWORD'
    ]
    
    print("\n🔍 Checking environment variables...")
    
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var:
                print(f"✅ {var}: {'*' * min(len(value), 20)}... (hidden)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    return len(missing_required) == 0

def generate_influxdb_datasource():
    """Generate a working InfluxDB datasource configuration."""
    
    config = {
        "apiVersion": 1,
        "datasources": [{
            "name": "InfluxDB",
            "type": "influxdb",
            "access": "proxy",
            "url": os.getenv('INFLUXDB_URL', 'http://influxdb2:8086'),
            "user": os.getenv('INFLUXDB_ADMIN_USER', 'admin'),
            "password": os.getenv('INFLUXDB_ADMIN_PASSWORD', 'admin123!'),
            "database": os.getenv('INFLUXDB_BUCKET', 'default'),
            "jsonData": {
                "version": "Flux",
                "organization": os.getenv('INFLUXDB_ORG', 'nflx'),
                "defaultBucket": os.getenv('INFLUXDB_BUCKET', 'default'),
                "tlsSkipVerify": True,
                "httpMode": "POST"
            },
            "isDefault": True,
            "editable": True,
            "version": 1
        }]
    }
    
    # Add token if available
    token = os.getenv('INFLUXDB_TOKEN')
    if token and token != 'your-admin-token-here':
        config["datasources"][0]["secureJsonData"] = {"token": token}
        # Remove basic auth when using token
        del config["datasources"][0]["user"]
        del config["datasources"][0]["password"]
        del config["datasources"][0]["database"]
    
    return config

def write_datasource_config():
    """Write the corrected datasource configuration."""
    config = generate_influxdb_datasource()
    
    try:
        with open('grafana/provisioning/datasources/influxdb-fixed.yml', 'w') as f:
            import yaml
            yaml.dump(config, f, default_flow_style=False)
        print("✅ Created fixed datasource config: grafana/provisioning/datasources/influxdb-fixed.yml")
        return True
    except ImportError:
        # Fallback to JSON if yaml not available
        try:
            with open('grafana/provisioning/datasources/influxdb-fixed.json', 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Created fixed datasource config: grafana/provisioning/datasources/influxdb-fixed.json")
            return True
        except Exception as e:
            print(f"❌ Error writing config: {e}")
            return False
    except Exception as e:
        print(f"❌ Error writing config: {e}")
        return False

def main():
    """Main function to diagnose and fix InfluxDB issues."""
    print("🔧 InfluxDB Authorization Fix Tool")
    print("=" * 50)
    
    # Check environment variables
    if not check_environment_variables():
        print("\n❌ Missing required environment variables")
        print("Please set the required variables in your .env file")
        return 1
    
    # Check InfluxDB connection
    if not check_influxdb_connection():
        print("\n❌ InfluxDB connection failed")
        print("Make sure InfluxDB container is running")
        return 1
    
    # Generate fixed configuration
    print("\n🔧 Generating fixed datasource configuration...")
    if write_datasource_config():
        print("\n✅ Fix completed successfully!")
        print("\nNext steps:")
        print("1. Restart Grafana container: docker-compose restart grafana")
        print("2. Check Grafana logs: docker logs grafana")
        print("3. Test datasource in Grafana UI")
        return 0
    else:
        print("\n❌ Failed to generate configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
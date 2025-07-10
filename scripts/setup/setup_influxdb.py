#!/usr/bin/env python3
"""
Set up InfluxDB locally for telemetry data collection.
This script initializes a local InfluxDB instance and creates the necessary setup.
"""

import subprocess
import time
import requests
import json
import os

def setup_local_influxdb():
    """Set up a local InfluxDB instance."""
    print("Setting up local InfluxDB for telemetry data...")
    
    # Create InfluxDB data directory
    os.makedirs("influxdb_local", exist_ok=True)
    
    # Start InfluxDB in development mode
    try:
        print("Starting InfluxDB in development mode...")
        
        # Kill any existing influxd processes
        subprocess.run(['pkill', '-f', 'influxd'], capture_output=True)
        time.sleep(2)
        
        # Start InfluxDB with basic configuration
        influx_cmd = [
            'influxd',
            '--http-bind-address=:8086',
            '--storage-path=./influxdb_local',
            '--engine-path=./influxdb_local/engine',
            '--reporting-disabled'
        ]
        
        # Start InfluxDB as background process
        process = subprocess.Popen(
            influx_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"InfluxDB started with PID: {process.pid}")
        
        # Wait for InfluxDB to start
        print("Waiting for InfluxDB to initialize...")
        for i in range(30):
            try:
                response = requests.get('http://localhost:8086/ping', timeout=2)
                if response.status_code == 200:
                    print("InfluxDB is running!")
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("InfluxDB failed to start in 30 seconds")
            return False
            
        # Set up initial configuration
        setup_data = {
            "username": "admin",
            "password": "admin123",
            "org": "nflx", 
            "bucket": "default",
            "retentionPeriodSeconds": 2592000  # 30 days
        }
        
        try:
            setup_response = requests.post(
                'http://localhost:8086/api/v2/setup',
                json=setup_data,
                timeout=10
            )
            
            if setup_response.status_code == 201:
                result = setup_response.json()
                token = result.get('auth', {}).get('token', '')
                
                print(f"InfluxDB setup completed!")
                print(f"Organization: {setup_data['org']}")
                print(f"Bucket: {setup_data['bucket']}")
                print(f"Admin Token: {token[:20]}...")
                
                # Update .env file with the token
                update_env_file(token)
                
                return True
            else:
                print(f"Setup failed: {setup_response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Setup request failed: {e}")
            # InfluxDB might already be set up, try to continue
            return True
            
    except Exception as e:
        print(f"Error starting InfluxDB: {e}")
        return False

def update_env_file(token):
    """Update the .env file with the InfluxDB token."""
    env_content = []
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Update or add the token
    token_updated = False
    for i, line in enumerate(env_content):
        if line.startswith('INFLUXDB_TOKEN='):
            env_content[i] = f'INFLUXDB_TOKEN={token}\n'
            token_updated = True
            break
    
    if not token_updated:
        env_content.append(f'INFLUXDB_TOKEN={token}\n')
    
    with open('.env', 'w') as f:
        f.writelines(env_content)
    
    print("Updated .env file with InfluxDB token")

def test_connection():
    """Test the InfluxDB connection."""
    try:
        response = requests.get('http://localhost:8086/health', timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"InfluxDB Status: {health.get('status', 'unknown')}")
            return True
        else:
            print(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("InfluxDB Local Setup")
    print("=" * 60)
    
    if setup_local_influxdb():
        if test_connection():
            print("\n✅ InfluxDB is ready for telemetry data collection!")
            print("You can now run: python telemetry_runner.py single")
        else:
            print("\n⚠️ InfluxDB started but connection test failed")
    else:
        print("\n❌ InfluxDB setup failed")
#!/usr/bin/env python3
"""
Docker setup script to configure InfluxDB token automatically.
This runs inside the container to get the InfluxDB token and update the environment.
"""

import time
import requests
import os
import json

def wait_for_influxdb():
    """Wait for InfluxDB to be ready."""
    print("Waiting for InfluxDB to be ready...")
    
    for i in range(60):  # Wait up to 60 seconds
        try:
            response = requests.get('http://influxdb2:8086/ping', timeout=2)
            if response.status_code == 200:
                print("InfluxDB is ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print("InfluxDB failed to start within 60 seconds")
    return False

def get_influxdb_token():
    """Get InfluxDB token using the initial setup."""
    try:
        # Try to get existing token first
        config_file = '/etc/influxdb2/config.toml'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                # Look for token in config
                for line in content.split('\n'):
                    if 'token' in line and '=' in line:
                        token = line.split('=')[1].strip().strip('"')
                        if len(token) > 20:  # Valid token length
                            print(f"Found existing token: {token[:20]}...")
                            return token
        
        # If no token found, try authentication with admin credentials
        auth_data = {
            "username": "admin",
            "password": "admin123!"
        }
        
        response = requests.post(
            'http://influxdb2:8086/api/v2/signin',
            json=auth_data,
            timeout=10
        )
        
        if response.status_code == 204:
            # Get session cookie
            session_cookie = response.headers.get('Set-Cookie', '')
            
            # List tokens
            headers = {'Cookie': session_cookie}
            response = requests.get(
                'http://influxdb2:8086/api/v2/authorizations',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                authorizations = data.get('authorizations', [])
                
                for auth in authorizations:
                    if auth.get('status') == 'active':
                        token = auth.get('token', '')
                        if token:
                            print(f"Retrieved admin token: {token[:20]}...")
                            return token
        
        print("Could not retrieve InfluxDB token")
        return None
        
    except Exception as e:
        print(f"Error getting InfluxDB token: {e}")
        return None

def create_admin_token():
    """Create an admin token using the initial setup credentials."""
    try:
        # Create token using admin API
        auth_data = {
            "description": "Telemetry Service Token",
            "orgID": "nflx",
            "permissions": [
                {
                    "action": "read",
                    "resource": {"type": "buckets"}
                },
                {
                    "action": "write", 
                    "resource": {"type": "buckets"}
                }
            ]
        }
        
        # First authenticate
        signin_data = {
            "username": "admin",
            "password": "admin123!"
        }
        
        response = requests.post(
            'http://influxdb2:8086/api/v2/signin',
            json=signin_data,
            timeout=10
        )
        
        if response.status_code == 204:
            session_cookie = response.headers.get('Set-Cookie', '')
            headers = {'Cookie': session_cookie}
            
            # Create new token
            response = requests.post(
                'http://influxdb2:8086/api/v2/authorizations',
                json=auth_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                token = data.get('token', '')
                print(f"Created new admin token: {token[:20]}...")
                return token
                
        print("Failed to create admin token")
        return None
        
    except Exception as e:
        print(f"Error creating admin token: {e}")
        return None

def main():
    """Main setup function."""
    print("=" * 60)
    print("DOCKER INFLUXDB SETUP")
    print("=" * 60)
    
    # Wait for InfluxDB
    if not wait_for_influxdb():
        return False
    
    # Get or create token
    token = get_influxdb_token()
    
    if not token:
        print("Trying to create new admin token...")
        token = create_admin_token()
    
    if token:
        # Save token to environment file for container restart
        with open('/app/influx_token.txt', 'w') as f:
            f.write(token)
        
        # Set environment variable for current session
        os.environ['INFLUXDB_TOKEN'] = token
        
        print(f"✅ InfluxDB token configured: {token[:20]}...")
        return True
    else:
        print("❌ Failed to configure InfluxDB token")
        return False

if __name__ == "__main__":
    main()
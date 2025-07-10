#!/usr/bin/env python3
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

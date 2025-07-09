#!/usr/bin/env python3
"""
ZenMon Load Testing Script
"""

import requests
import time
import random
import os
from datetime import datetime

def generate_metrics(host_id):
    """Generate test metrics"""
    return [
        {'host_id': host_id, 'metric_name': 'CPU Usage', 'unit': '%', 'value': round(random.uniform(10, 90), 2)},
        {'host_id': host_id, 'metric_name': 'Memory Usage', 'unit': '%', 'value': round(random.uniform(20, 80), 2)},
        {'host_id': host_id, 'metric_name': 'Disk Usage', 'unit': '%', 'value': round(random.uniform(30, 70), 2)},
        {'host_id': host_id, 'metric_name': 'Network Response Time', 'unit': 'ms', 'value': round(random.uniform(1, 100), 2)}
    ]

def send_metrics(api_url, host_id):
    """Send metrics for one host"""
    try:
        metrics = generate_metrics(host_id)
        response = requests.post(f'{api_url}/agent/metrics', json={'metrics': metrics}, timeout=10)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if response.status_code == 200:
            print(f'[{timestamp}] Host {host_id}: ✓ {response.status_code}')
            return True
        else:
            print(f'[{timestamp}] Host {host_id}: ✗ {response.status_code}')
            return False
            
    except Exception as e:
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Host {host_id}: ❌ {e}')
        return False

def main():
    api_url = os.environ.get('ZENMON_API_URL', 'http://host.docker.internal:8001/api')
    test_hosts = [13, 14, 15, 16, 17]
    
    print(f"🚀 ZenMon Load Test")
    print(f"📡 API: {api_url}")
    print(f"🖥️  Hosts: {test_hosts}")
    print("-" * 40)
    
    batch = 0
    try:
        while True:
            batch += 1
            print(f"\n📦 Batch #{batch} - {datetime.now().strftime('%H:%M:%S')}")
            
            success = 0
            for host_id in test_hosts:
                if send_metrics(api_url, host_id):
                    success += 1
            
            print(f"   Results: {success}/{len(test_hosts)} success")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Test stopped after {batch} batches")

if __name__ == "__main__":
    main()
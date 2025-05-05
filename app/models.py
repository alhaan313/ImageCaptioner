import json
import os
from datetime import datetime
from threading import Lock

class MetricsManager:
    def __init__(self):
        self.lock = Lock()
        self.metrics_file = '/tmp/metrics.json'
        self.default_metrics = {
            'total_images': 0,
            'total_users': set(),
            'visits': []
        }
        self._ensure_metrics_file()

    def _ensure_metrics_file(self):
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w') as f:
                json.dump(self.default_metrics, f, default=self._serialize)

    def _serialize(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def _deserialize(self, data):
        data['total_users'] = set(data['total_users'])
        return data

    def track_visit(self, ip_address, endpoint, image_processed=False):
        with self.lock:
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    data = self._deserialize(data)
                
                if image_processed:
                    data['total_images'] += 1
                
                data['total_users'].add(ip_address)
                data['visits'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'endpoint': endpoint,
                    'ip': ip_address
                })

                # Keep only last 1000 visits to avoid file size issues
                data['visits'] = data['visits'][-1000:]

                with open(self.metrics_file, 'w') as f:
                    json.dump(data, f, default=self._serialize)

            except Exception as e:
                print(f"Error tracking metrics: {e}")

    def get_metrics(self):
        try:
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
                data = self._deserialize(data)
                
                # Calculate last 24h visits
                now = datetime.utcnow()
                day_ago = (now - datetime.timedelta(days=1)).isoformat()
                last_24h = sum(1 for visit in data['visits'] 
                             if visit['timestamp'] > day_ago)

                return {
                    'total_images': data['total_images'],
                    'total_users': len(data['total_users']),
                    'last_24h': last_24h
                }
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return {
                'total_images': 0,
                'total_users': 0,
                'last_24h': 0
            }

metrics = MetricsManager()

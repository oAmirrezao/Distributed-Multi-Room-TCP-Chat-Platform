import asyncio
import time
import json
from collections import deque, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

class PerformanceMonitor:
    def __init__(self, window_size=1000):
        self.window_size = window_size
        self.metrics = {
            'connections': 0,
            'messages_sent': 0,
            'bytes_transferred': 0,
            'processing_times': deque(maxlen=window_size),
            'message_latencies': deque(maxlen=window_size),
            'concurrent_users': 0,
            'bandwidth_usage': deque(maxlen=60)  # Last 60 seconds
        }
        self.hourly_stats = defaultdict(lambda: {
            'messages': 0,
            'bytes': 0,
            'avg_latency': 0
        })
        self.start_time = time.time()
    
    def record_connection(self):
        self.metrics['connections'] += 1
        self.metrics['concurrent_users'] += 1
    
    def record_disconnection(self):
        self.metrics['concurrent_users'] = max(0, self.metrics['concurrent_users'] - 1)
    
    def record_message(self, size_bytes):
        self.metrics['messages_sent'] += 1
        self.metrics['bytes_transferred'] += size_bytes
        
        # Update hourly stats
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['messages'] += 1
        self.hourly_stats[hour_key]['bytes'] += size_bytes
    
    def record_processing_time(self, time_seconds):
        self.metrics['processing_times'].append(time_seconds)
    
    def record_latency(self, latency_ms):
        self.metrics['message_latencies'].append(latency_ms)
        
        # Update hourly average
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
        stats = self.hourly_stats[hour_key]
        if stats['avg_latency'] == 0:
            stats['avg_latency'] = latency_ms
        else:
            stats['avg_latency'] = (stats['avg_latency'] + latency_ms) / 2
    
    async def report_stats(self):
        """Periodically report and save statistics"""
        while True:
            await asyncio.sleep(60)  # Report every minute
            
            stats = self.get_current_stats()
            
            # Save to file
            with open('logs/performance_stats.json', 'a') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }, f)
                f.write('\n')
            
            # Generate graphs every 5 minutes
            if int(time.time()) % 300 == 0:
                self.generate_performance_graphs()
    
    def get_current_stats(self):
        uptime = time.time() - self.start_time
        
        avg_processing = sum(self.metrics['processing_times']) / len(self.metrics['processing_times']) \
                        if self.metrics['processing_times'] else 0
        
        avg_latency = sum(self.metrics['message_latencies']) / len(self.metrics['message_latencies']) \
                     if self.metrics['message_latencies'] else 0
        
        return {
            'uptime_seconds': uptime,
            'total_connections': self.metrics['connections'],
            'concurrent_users': self.metrics['concurrent_users'],
            'messages_sent': self.metrics['messages_sent'],
            'bytes_transferred': self.metrics['bytes_transferred'],
            'avg_processing_time_ms': avg_processing * 1000,
            'avg_latency_ms': avg_latency,
            'messages_per_second': self.metrics['messages_sent'] / uptime if uptime > 0 else 0,
            'bandwidth_mbps': (self.metrics['bytes_transferred'] * 8) / (uptime * 1_000_000) if uptime > 0 else 0
        }
    
    def generate_performance_graphs(self):
        Path('monitoring/graphs').mkdir(parents=True, exist_ok=True)
        
        # Processing time distribution
        if self.metrics['processing_times']:
            plt.figure(figsize=(10, 6))
            plt.hist(self.metrics['processing_times'], bins=50, edgecolor='black')
            plt.title('Message Processing Time Distribution')
            plt.xlabel('Processing Time (seconds)')
            plt.ylabel('Frequency')
            plt.savefig('monitoring/graphs/processing_times.png')
            plt.close()
        
        # Latency over time
        if self.metrics['message_latencies']:
            plt.figure(figsize=(10, 6))
            plt.plot(self.metrics['message_latencies'])
            plt.title('Message Latency Over Time')
            plt.xlabel('Message Index')
            plt.ylabel('Latency (ms)')
            plt.savefig('monitoring/graphs/latency_timeline.png')
            plt.close()
        
        # Hourly message volume
        if self.hourly_stats:
            hours = sorted(self.hourly_stats.keys())
            messages = [self.hourly_stats[h]['messages'] for h in hours]
            
            plt.figure(figsize=(12, 6))
            plt.bar(range(len(hours)), messages)
            plt.title('Messages Per Hour')
            plt.xlabel('Hour')
            plt.ylabel('Message Count')
            plt.xticks(range(len(hours)), hours, rotation=45)
            plt.tight_layout()
            plt.savefig('monitoring/graphs/hourly_messages.png')
            plt.close()

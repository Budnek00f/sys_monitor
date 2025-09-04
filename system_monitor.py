import psutil
import time
from datetime import datetime

class SystemMonitor:
    @staticmethod
    def get_cpu_info():
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'freq': psutil.cpu_freq().current if psutil.cpu_freq() else None
        }
    
    @staticmethod
    def get_memory_info():
        memory = psutil.virtual_memory()
        return {
            'total': round(memory.total / (1024**3), 2),
            'used': round(memory.used / (1024**3), 2),
            'free': round(memory.free / (1024**3), 2),
            'percent': memory.percent
        }
    
    @staticmethod
    def get_disk_info():
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'mountpoint': partition.mountpoint,
                    'total': round(usage.total / (1024**3), 2),
                    'used': round(usage.used / (1024**3), 2),
                    'free': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        return disks
    
    @staticmethod
    def get_uptime():
        uptime = psutil.uptime()
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}ч {int(minutes)}м {int(seconds)}с"
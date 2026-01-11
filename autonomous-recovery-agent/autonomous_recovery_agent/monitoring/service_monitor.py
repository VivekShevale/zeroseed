import psutil
import time
import threading
import logging
from typing import Dict, Any, Optional


class ServiceMonitor:
    """Monitor Flask service health"""
    
    def __init__(
        self,
        process_name: str = "python",
        max_memory_mb: float = 500,
        max_cpu_percent: float = 80,
        check_interval: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.process_name = process_name
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self._running = False
        self._thread = None
        self._last_health = {}
    
    def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="ServiceMonitor"
        )
        self._thread.start()
        self.logger.info("Service monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Service monitoring stopped")
    
    def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            # Find Flask process
            process = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if self.process_name in proc.info['name'] or \
                       (proc.info['cmdline'] and 'flask' in ' '.join(proc.info['cmdline']).lower()):
                        process = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not process:
                return {
                    "status": "critical",
                    "error_message": "Flask process not found",
                    "is_alive": False,
                    "timestamp": time.time()
                }
            
            # Get metrics
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Determine status
            status = "healthy"
            error_message = None
            
            if memory_mb > self.max_memory_mb:
                status = "unhealthy"
                error_message = f"Memory: {memory_mb:.1f}MB > {self.max_memory_mb}MB"
            elif cpu_percent > self.max_cpu_percent:
                status = "degraded"
                error_message = f"CPU: {cpu_percent:.1f}% > {self.max_cpu_percent}%"
            
            health = {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "pid": process.pid
                },
                "error_message": error_message,
                "is_alive": True,
                "timestamp": time.time()
            }
            
            self._last_health = health
            return health
            
        except Exception as e:
            self.logger.error(f"Error checking service health: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "is_alive": False,
                "timestamp": time.time()
            }
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                self.check_health()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
import time
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class DatabaseMonitor:
    """Monitor MongoDB health"""
    
    def __init__(
        self,
        mongodb_url: str,
        max_connection_time_ms: float = 100,
        max_query_time_ms: float = 500,
        check_interval: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.mongodb_url = mongodb_url
        self.max_connection_time_ms = max_connection_time_ms
        self.max_query_time_ms = max_query_time_ms
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self._running = False
        self._thread = None
        self._last_health = {}
        self._client = None
        self._last_connected_state = True
        self._recovery_attempts = 0
        
    def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DatabaseMonitor"
        )
        self._thread.start()
        self.logger.info("Database monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._client:
            self._client.close()
        self.logger.info("Database monitoring stopped")
    
    def check_health(self) -> Tuple[Dict[str, Any], bool]:
        """Check database health and return (health_data, state_changed)"""
        start_time = time.time()
        state_changed = False
        
        try:
            # Create client if not exists
            if not self._client:
                self._client = MongoClient(
                    self.mongodb_url,
                    serverSelectionTimeoutMS=5000
                )
            
            # Test connection
            ping_start = time.time()
            self._client.admin.command('ping')
            connection_time_ms = (time.time() - ping_start) * 1000
            
            # Get server status
            server_status = self._client.admin.command('serverStatus')
            
            # Determine status
            status = "connected"
            error_message = None
            
            if connection_time_ms > self.max_connection_time_ms:
                status = "slow"
                error_message = f"Slow: {connection_time_ms:.1f}ms"
            
            health = {
                "status": status,
                "metrics": {
                    "connection_time_ms": connection_time_ms,
                    "active_connections": server_status.get('connections', {}).get('active', 0),
                    "memory_mb": server_status.get('mem', {}).get('resident', 0)
                },
                "error_message": error_message,
                "is_reachable": True,
                "timestamp": time.time()
            }
            
            # Check if state changed from disconnected to connected
            if not self._last_connected_state:
                state_changed = True
                self.logger.info("✅ Database reconnected successfully!")
                self._recovery_attempts = 0
            
            self._last_connected_state = True
            self._last_health = health
            return health, state_changed
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            health = {
                "status": "disconnected",
                "error_message": f"Disconnected: {str(e)}",
                "is_reachable": False,
                "timestamp": time.time()
            }
            
            # Check if state changed from connected to disconnected
            if self._last_connected_state:
                state_changed = True
                self.logger.warning("⚠️ Database disconnected")
            
            self._last_connected_state = False
            self._last_health = health
            
            # Increment recovery attempts
            self._recovery_attempts += 1
            return health, state_changed
            
        except Exception as e:
            self.logger.error(f"Error checking database health: {e}")
            health = {
                "status": "error",
                "error_message": str(e),
                "is_reachable": False,
                "timestamp": time.time()
            }
            return health, False
    
    def get_recovery_attempts(self) -> int:
        """Get number of recovery attempts"""
        return self._recovery_attempts
    
    def reset_recovery_attempts(self):
        """Reset recovery attempts counter"""
        self._recovery_attempts = 0
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                health, state_changed = self.check_health()
                
                # Log state changes
                if state_changed:
                    if health["is_reachable"]:
                        self.logger.info(f"✅ Database state changed: {health['status']}")
                    else:
                        self.logger.warning(f"⚠️ Database state changed: {health['status']}")
                
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
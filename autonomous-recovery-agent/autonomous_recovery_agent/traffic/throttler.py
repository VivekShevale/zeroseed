"""
Intelligent traffic throttling during backend overload
"""
import time
import threading
import logging
from typing import Dict, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class ThrottleLevel(Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ThrottleRule:
    """Traffic throttling rule"""
    level: ThrottleLevel
    max_rps: int  # Requests per second
    priority: int  # Higher priority = more important
    methods: list = field(default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE'])
    paths: list = field(default_factory=list)  # Empty = all paths
    user_agents: list = field(default_factory=list)  # Empty = all agents
    enabled: bool = True


class TrafficThrottler:
    """Intelligent traffic throttling based on system load"""
    
    def __init__(
        self,
        default_rps: int = 100,  # Default requests per second
        overload_threshold: float = 0.8,  # 80% system load
        recovery_threshold: float = 0.5,  # 50% system load
        logger: Optional[logging.Logger] = None
    ):
        self.default_rps = default_rps
        self.overload_threshold = overload_threshold
        self.recovery_threshold = recovery_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        self._rules: Dict[ThrottleLevel, ThrottleRule] = {}
        self._request_history: Dict[str, deque] = {}  # IP -> timestamps
        self._system_load: float = 0.0
        self._current_level: ThrottleLevel = ThrottleLevel.NORMAL
        self._lock = threading.RLock()
        
        # Initialize default rules
        self._init_default_rules()
        
        # Cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="ThrottleCleanup"
        )
        self._cleanup_thread.start()
    
    def _init_default_rules(self):
        """Initialize default throttling rules"""
        self._rules = {
            ThrottleLevel.NORMAL: ThrottleRule(
                level=ThrottleLevel.NORMAL,
                max_rps=self.default_rps,
                priority=1
            ),
            ThrottleLevel.DEGRADED: ThrottleRule(
                level=ThrottleLevel.DEGRADED,
                max_rps=self.default_rps // 2,
                priority=2
            ),
            ThrottleLevel.HIGH: ThrottleRule(
                level=ThrottleLevel.HIGH,
                max_rps=self.default_rps // 4,
                priority=3
            ),
            ThrottleLevel.CRITICAL: ThrottleRule(
                level=ThrottleLevel.CRITICAL,
                max_rps=self.default_rps // 10,
                priority=4
            )
        }
    
    def update_system_load(self, cpu_percent: float, memory_percent: float):
        """Update system load and adjust throttling"""
        # Simple load calculation (can be more sophisticated)
        system_load = max(cpu_percent, memory_percent) / 100.0
        
        with self._lock:
            self._system_load = system_load
            
            # Determine throttle level based on system load
            if system_load >= self.overload_threshold:
                new_level = ThrottleLevel.CRITICAL
            elif system_load >= self.overload_threshold * 0.8:
                new_level = ThrottleLevel.HIGH
            elif system_load >= self.overload_threshold * 0.6:
                new_level = ThrottleLevel.DEGRADED
            else:
                new_level = ThrottleLevel.NORMAL
            
            # Only log if level changed
            if new_level != self._current_level:
                self._current_level = new_level
                self.logger.info(
                    f"🚦 Throttle level changed: {self._current_level.value} "
                    f"(System load: {system_load:.1%})"
                )
    
    def should_throttle(
        self,
        client_ip: str,
        path: str = "/",
        method: str = "GET",
        user_agent: str = ""
    ) -> bool:
        """Check if request should be throttled"""
        with self._lock:
            rule = self._rules.get(self._current_level)
            if not rule or not rule.enabled:
                return False
            
            # Check if path/method/user_agent matches rule
            if not self._matches_rule(rule, path, method, user_agent):
                return False
            
            # Initialize history for this IP
            if client_ip not in self._request_history:
                self._request_history[client_ip] = deque(maxlen=rule.max_rps * 10)
            
            history = self._request_history[client_ip]
            now = time.time()
            
            # Remove old entries (older than 1 second)
            while history and now - history[0] > 1.0:
                history.popleft()
            
            # Check if rate limit exceeded
            if len(history) >= rule.max_rps:
                self.logger.debug(
                    f"Throttling {client_ip}: {len(history)} requests in last second "
                    f"(limit: {rule.max_rps})"
                )
                return True
            
            # Add current request
            history.append(now)
            return False
    
    def _matches_rule(self, rule: ThrottleRule, path: str, method: str, user_agent: str) -> bool:
        """Check if request matches rule criteria"""
        # Check method
        if rule.methods and method not in rule.methods:
            return False
        
        # Check path patterns
        if rule.paths:
            matched = False
            for pattern in rule.paths:
                if pattern.endswith('*') and path.startswith(pattern[:-1]):
                    matched = True
                    break
                elif pattern == path:
                    matched = True
                    break
            if not matched:
                return False
        
        # Check user agent patterns
        if rule.user_agents and user_agent:
            matched = False
            for pattern in rule.user_agents:
                if pattern in user_agent:
                    matched = True
                    break
            if not matched:
                return False
        
        return True
    
    def add_rule(self, rule: ThrottleRule):
        """Add a custom throttling rule"""
        with self._lock:
            self._rules[rule.level] = rule
            self.logger.info(f"Added throttling rule: {rule.level.value} (max RPS: {rule.max_rps})")
    
    def remove_rule(self, level: ThrottleLevel):
        """Remove a throttling rule"""
        with self._lock:
            if level in self._rules:
                del self._rules[level]
                self.logger.info(f"Removed throttling rule: {level.value}")
    
    def enable_throttling(self, level: ThrottleLevel = None):
        """Enable throttling"""
        with self._lock:
            if level:
                if level in self._rules:
                    self._rules[level].enabled = True
                    self.logger.info(f"Enabled throttling for level: {level.value}")
            else:
                for rule in self._rules.values():
                    rule.enabled = True
                self.logger.info("Enabled all throttling rules")
    
    def disable_throttling(self, level: ThrottleLevel = None):
        """Disable throttling"""
        with self._lock:
            if level:
                if level in self._rules:
                    self._rules[level].enabled = False
                    self.logger.info(f"Disabled throttling for level: {level.value}")
            else:
                for rule in self._rules.values():
                    rule.enabled = False
                self.logger.info("Disabled all throttling rules")
    
    def get_current_level(self) -> ThrottleLevel:
        """Get current throttling level"""
        return self._current_level
    
    def get_stats(self) -> Dict[str, Any]:
        """Get throttling statistics"""
        with self._lock:
            return {
                "current_level": self._current_level.value,
                "system_load": self._system_load,
                "active_ips": len(self._request_history),
                "rules": {
                    level.value: {
                        "max_rps": rule.max_rps,
                        "enabled": rule.enabled
                    }
                    for level, rule in self._rules.items()
                }
            }
    
    def _cleanup_loop(self):
        """Cleanup old request history"""
        while True:
            try:
                with self._lock:
                    now = time.time()
                    ips_to_remove = []
                    
                    for ip, history in self._request_history.items():
                        # Remove IP if no requests in last 5 minutes
                        if history and now - history[-1] > 300:
                            ips_to_remove.append(ip)
                    
                    for ip in ips_to_remove:
                        del self._request_history[ip]
                
                time.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                self.logger.error(f"Error in throttle cleanup: {e}")
                time.sleep(10)
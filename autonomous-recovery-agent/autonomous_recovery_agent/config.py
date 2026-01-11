"""
Configuration models for Autonomous Recovery Agent
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any
import logging


@dataclass
class AgentConfig:
    """Configuration for the autonomous recovery agent"""
    
    # General settings
    enabled: bool = True
    log_level: str = "INFO"
    check_interval: int = 30
    
    # Service monitoring
    service_monitoring: bool = True
    max_service_memory_mb: float = 500
    max_service_cpu_percent: float = 80
    
    # Database monitoring
    database_monitoring: bool = True
    mongodb_url: Optional[str] = None
    max_db_connection_time_ms: float = 100
    max_db_query_time_ms: float = 500
    
    # Recovery settings
    auto_recovery: bool = True
    max_restart_attempts: int = 3
    restart_cooldown: int = 60
    
    # Web UI
    enable_web_ui: bool = True
    web_ui_port: int = 8081
    web_ui_host: str = "0.0.0.0"
    
    # API endpoints
    enable_api: bool = True
    api_prefix: str = "/recovery"
    
    # Custom callbacks
    on_service_unhealthy: Optional[Callable] = None
    on_database_unhealthy: Optional[Callable] = None
    on_recovery_completed: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and not callable(v)}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
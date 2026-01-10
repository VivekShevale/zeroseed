from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

class IssueType(str, Enum):
    SERVICE_DOWN = "SERVICE_DOWN"
    MEMORY_PRESSURE = "MEMORY_PRESSURE"
    HIGH_LATENCY = "HIGH_LATENCY"
    HIGH_CPU = "HIGH_CPU"
    HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
    CUSTOM = "CUSTOM"

class ActionType(str, Enum):
    RESTART = "restart"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    ROLLBACK = "rollback"
    NOTIFY = "notify"
    CUSTOM = "custom"

class HealthStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"

class ServiceMetrics(BaseModel):
    """Service metrics schema"""
    service_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    health: HealthStatus
    cpu: Optional[float] = None
    memory: Optional[float] = None
    latency: Optional[float] = None
    error_rate: Optional[float] = None
    response_time: Optional[float] = None
    throughput: Optional[float] = None
    custom_metrics: Optional[Dict[str, Any]] = None
    
    @validator('cpu', 'memory', 'error_rate')
    def validate_percentage(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Must be between 0 and 100')
        return v

class FixCatalogEntry(BaseModel):
    """Issue-action mapping with confidence"""
    issue: IssueType
    action: ActionType
    auto: bool = True
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ActionMemory(BaseModel):
    """Record of executed actions"""
    service_id: str
    issue: IssueType
    action: ActionType
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    before_metrics: Optional[Dict[str, Any]] = None
    after_metrics: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None

class ServiceConfig(BaseModel):
    """Service configuration"""
    service_id: str
    name: str
    service_url: str
    metrics_url: str
    health_endpoint: str = "/health"
    restart_endpoint: str = "/agent/restart"
    enabled: bool = True
    tags: List[str] = []
    check_interval: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('service_url', 'metrics_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class Incident(BaseModel):
    """Incident record"""
    incident_id: str
    service_id: str
    issue: IssueType
    severity: str = "medium"  # low, medium, high, critical
    status: str = "detected"  # detected, investigating, acting, resolved, closed
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    actions: List[Dict[str, Any]] = []
    metrics_snapshot: Optional[Dict[str, Any]] = None
    resolution_note: Optional[str] = None
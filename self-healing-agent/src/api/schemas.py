"""
API request and response schemas.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    database: str
    version: str

class ServiceCreate(BaseModel):
    """Service creation request schema"""
    service_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    service_url: str = Field(..., min_length=1)
    metrics_url: str = Field(..., min_length=1)
    health_endpoint: str = Field(default="/health")
    restart_endpoint: str = Field(default="/agent/restart")
    enabled: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)
    custom_thresholds: Optional[Dict[str, float]] = None
    
    @validator('service_url', 'metrics_url')
    def validate_urls(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('service_id')
    def validate_service_id(cls, v):
        # Allow alphanumeric, hyphens, underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Service ID can only contain letters, numbers, hyphens, and underscores')
        return v

class ServiceUpdate(BaseModel):
    """Service update request schema"""
    name: Optional[str] = None
    service_url: Optional[str] = None
    metrics_url: Optional[str] = None
    health_endpoint: Optional[str] = None
    restart_endpoint: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_thresholds: Optional[Dict[str, float]] = None
    
    @validator('service_url', 'metrics_url')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class CatalogCreate(BaseModel):
    """Catalog entry creation request schema"""
    issue: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    auto: bool = Field(default=True)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class MetricsIngest(BaseModel):
    """Metrics ingestion request schema"""
    service_id: str = Field(..., min_length=1)
    metrics: Dict[str, Any] = Field(...)
    timestamp: Optional[datetime] = None

class ManualAction(BaseModel):
    """Manual action execution request schema"""
    service_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class ServiceResponse(BaseModel):
    """Service response schema"""
    service_id: str
    name: str
    service_url: str
    metrics_url: str
    health_endpoint: str
    restart_endpoint: str
    enabled: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime

class CatalogResponse(BaseModel):
    """Catalog response schema"""
    issue: str
    action: str
    auto: bool
    confidence: float
    parameters: Optional[Dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

class ActionHistoryResponse(BaseModel):
    """Action history response schema"""
    service_id: str
    issue: str
    action: str
    success: bool
    timestamp: datetime
    before_metrics: Optional[Dict[str, Any]]
    after_metrics: Optional[Dict[str, Any]]
    execution_time: Optional[float]

class IncidentResponse(BaseModel):
    """Incident response schema"""
    incident_id: str
    service_id: str
    issue: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    actions: List[Dict[str, Any]]
    metrics_snapshot: Optional[Dict[str, Any]]
    resolution_note: Optional[str]

class AgentStatusResponse(BaseModel):
    """Agent status response schema"""
    running: bool
    services_monitored: int
    active_incidents: int
    last_check: datetime
    database_healthy: bool
    services: Dict[str, int]
    catalog: Dict[str, int]
    timestamp: datetime

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    """Success response schema"""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
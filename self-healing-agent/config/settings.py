import os
from dataclasses import dataclass, field
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))

    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB: str = os.getenv("MONGO_DB", "self_healing_agent")

    # Agent
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))

    # Thresholds (FIXED)
    THRESHOLDS: Dict[str, Any] = field(default_factory=lambda: {
        "memory": float(os.getenv("MEMORY_THRESHOLD", "90")),
        "latency": float(os.getenv("LATENCY_THRESHOLD", "1500")),
        "error_rate": float(os.getenv("ERROR_RATE_THRESHOLD", "0.3")),
        "cpu": float(os.getenv("CPU_THRESHOLD", "90")),
        "response_time": float(os.getenv("RESPONSE_TIME_THRESHOLD", "2000")),
    })

    # Services (FIXED)
    SERVICES: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "service_id": "payment-api",
            "name": "Payment API",
            "service_url": os.getenv("SERVICE_URL", "http://localhost:6000"),
            "metrics_url": os.getenv("METRICS_URL", "http://localhost:6000/health"),
            "health_endpoint": "/health",
            "restart_endpoint": "/agent/restart",
            "enabled": True,
            "tags": ["critical", "api"],
        }
    ])

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "agent.log")

    # Security (FIXED)
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    API_KEYS: List[str] = field(
        default_factory=lambda: [
            key for key in os.getenv("API_KEYS", "").split(",") if key
        ]
    )

    @property
    def is_production(self) -> bool:
        return not self.DEBUG


config = Config()

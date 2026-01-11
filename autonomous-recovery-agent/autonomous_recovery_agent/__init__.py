"""
Autonomous Recovery Agent - Self-healing for Flask + MongoDB applications
"""

from .agent import AutonomousRecoveryAgent
from .config import AgentConfig
from .flask_integration import FlaskIntegration
from .mongodb_integration import (
    RecoveryAwareMongoClient,
    RecoveryAwareDatabase,
    RecoveryAwareCollection,
    create_recovery_aware_client,
    patch_pymongo
)

__version__ = "3.0.4"
__author__ = "Autonomous Recovery Team"
__email__ = "support@autonomous-recovery.com"

__all__ = [
    "AutonomousRecoveryAgent",
    "AgentConfig",
    "FlaskIntegration",
    "RecoveryAwareMongoClient",
    "RecoveryAwareDatabase", 
    "RecoveryAwareCollection",
    "create_recovery_aware_client",
    "patch_pymongo"
]
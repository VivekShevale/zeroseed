"""
Self-Healing Web Infrastructure Agent Package
"""

__version__ = '1.0.0'
__author__ = 'Self-Healing Agent Team'

from .agent import SelfHealingAgent
from .models.database import db_instance
from .utils.logger import logger

__all__ = [
    'SelfHealingAgent',
    'db_instance',
    'logger'
]
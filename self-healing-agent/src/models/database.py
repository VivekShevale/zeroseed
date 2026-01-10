from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
import logging
from typing import Optional

from config.settings import config

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database connection and operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                config.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=3000
            )
            # Test connection
            self.client.server_info()
            self.db = self.client[config.MONGO_DB]
            self._create_indexes()
            logger.info("Connected to MongoDB successfully")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create necessary database indexes"""
        # Memory collection indexes
        self.db.agent_memory.create_index([("timestamp", DESCENDING)])
        self.db.agent_memory.create_index([("service_id", ASCENDING)])
        self.db.agent_memory.create_index([("issue", ASCENDING)])
        self.db.agent_memory.create_index([("success", ASCENDING)])
        
        # Catalog collection indexes
        self.db.fix_catalog.create_index([("issue", ASCENDING)], unique=True)
        self.db.fix_catalog.create_index([("confidence", DESCENDING)])
        
        # Service collection indexes
        self.db.services.create_index([("service_id", ASCENDING)], unique=True)
        self.db.services.create_index([("enabled", ASCENDING)])
        
        # Incident collection indexes
        self.db.incidents.create_index([("timestamp", DESCENDING)])
        self.db.incidents.create_index([("service_id", ASCENDING)])
        self.db.incidents.create_index([("resolved", ASCENDING)])
    
    def is_healthy(self) -> bool:
        """Check database health"""
        try:
            self.client.admin.command('ping')
            return True
        except (ConnectionFailure, OperationFailure):
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database instance
db_instance = Database()
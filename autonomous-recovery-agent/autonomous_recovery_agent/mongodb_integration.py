"""
MongoDB integration for Autonomous Recovery Agent
"""
import logging
import time
from typing import Optional
from pymongo import MongoClient, errors
from pymongo.database import Database
from pymongo.collection import Collection


class RecoveryAwareMongoClient(MongoClient):
    """MongoDB client with automatic recovery capabilities"""
    
    def __init__(self, *args, **kwargs):
        # Extract agent from kwargs if provided
        self._recovery_agent = kwargs.pop('agent', None)
        self._logger = logging.getLogger(__name__)
        
        # Set default timeouts
        if 'serverSelectionTimeoutMS' not in kwargs:
            kwargs['serverSelectionTimeoutMS'] = 5000
        
        super().__init__(*args, **kwargs)
    
    def _retry_with_recovery(self, operation, *args, **kwargs):
        """Execute operation with retry and recovery"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except errors.ConnectionFailure as e:
                self._logger.warning(f"🔌 MongoDB connection failed (attempt {attempt + 1}): {e}")
                
                # On first failure, trigger recovery if agent is available
                if attempt == 0 and self._recovery_agent:
                    try:
                        from .agent import AutonomousRecoveryAgent
                        if isinstance(self._recovery_agent, AutonomousRecoveryAgent):
                            self._recovery_agent.trigger_recovery(
                                component="database",
                                reason=f"MongoDB connection failed: {str(e)}"
                            )
                    except Exception as recovery_error:
                        self._logger.error(f"Failed to trigger recovery: {recovery_error}")
                
                # Wait before retry (exponential backoff)
                time.sleep(2 ** attempt)
            except errors.PyMongoError as e:
                self._logger.error(f"❌ MongoDB error: {e}")
                raise
        
        # All retries failed
        raise errors.ConnectionFailure(f"Failed after {max_retries} retries")
    
    def admin(self):
        """Get admin database with recovery support"""
        db = super().admin
        return RecoveryAwareDatabase(db, self._recovery_agent)
    
    def __getitem__(self, name):
        """Get database with recovery support"""
        db = super().__getitem__(name)
        return RecoveryAwareDatabase(db, self._recovery_agent)
    
    def list_database_names(self, *args, **kwargs):
        """List database names with recovery support"""
        return self._retry_with_recovery(super().list_database_names, *args, **kwargs)
    
    def drop_database(self, name_or_database, *args, **kwargs):
        """Drop database with recovery support"""
        return self._retry_with_recovery(super().drop_database, name_or_database, *args, **kwargs)


class RecoveryAwareDatabase(Database):
    """MongoDB database with automatic recovery capabilities"""
    
    def __init__(self, database, agent=None):
        super().__init__(database.client, database.name)
        self._recovery_agent = agent
    
    def __getitem__(self, name):
        """Get collection with recovery support"""
        collection = super().__getitem__(name)
        return RecoveryAwareCollection(collection, self._recovery_agent)
    
    def command(self, command, *args, **kwargs):
        """Execute command with recovery support"""
        client = self.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().command, command, *args, **kwargs)
        return super().command(command, *args, **kwargs)


class RecoveryAwareCollection(Collection):
    """MongoDB collection with automatic recovery capabilities"""
    
    def __init__(self, collection, agent=None):
        super().__init__(collection.database, collection.name)
        self._recovery_agent = agent
    
    def find_one(self, filter=None, *args, **kwargs):
        """Find one document with recovery support"""
        client = self.database.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().find_one, filter, *args, **kwargs)
        return super().find_one(filter, *args, **kwargs)
    
    def insert_one(self, document, *args, **kwargs):
        """Insert one document with recovery support"""
        client = self.database.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().insert_one, document, *args, **kwargs)
        return super().insert_one(document, *args, **kwargs)
    
    def update_one(self, filter, update, *args, **kwargs):
        """Update one document with recovery support"""
        client = self.database.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().update_one, filter, update, *args, **kwargs)
        return super().update_one(filter, update, *args, **kwargs)
    
    def delete_one(self, filter, *args, **kwargs):
        """Delete one document with recovery support"""
        client = self.database.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().delete_one, filter, *args, **kwargs)
        return super().delete_one(filter, *args, **kwargs)
    
    def count_documents(self, filter, *args, **kwargs):
        """Count documents with recovery support"""
        client = self.database.client
        if hasattr(client, '_retry_with_recovery'):
            return client._retry_with_recovery(super().count_documents, filter, *args, **kwargs)
        return super().count_documents(filter, *args, **kwargs)


def create_recovery_aware_client(host='localhost', port=27017, **kwargs):
    """Create a MongoDB client with automatic recovery capabilities"""
    connection_string = f"mongodb://{host}:{port}"
    return RecoveryAwareMongoClient(connection_string, **kwargs)


def patch_pymongo():
    """Monkey-patch pymongo to use recovery-aware clients"""
    import pymongo
    import pymongo.mongo_client
    
    # Store original
    pymongo._original_MongoClient = pymongo.MongoClient
    
    # Replace with recovery-aware version
    def patched_MongoClient(*args, **kwargs):
        return RecoveryAwareMongoClient(*args, **kwargs)
    
    pymongo.MongoClient = patched_MongoClient
    pymongo.mongo_client.MongoClient = patched_MongoClient
    
    logging.getLogger(__name__).info("✅ pymongo patched for automatic recovery")
    
    return True
"""
Repository pattern for database operations.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from src.models.database import db_instance
from src.models.schemas import ServiceConfig, FixCatalogEntry, ActionMemory, Incident, ServiceMetrics
from src.utils.logger import logger

class ServiceRepository:
    """Repository for service operations"""
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all services"""
        try:
            services_col = db_instance.db.services
            services = list(services_col.find({}, {"_id": 0}))
            return services
        except Exception as e:
            logger.error(f"Error getting all services: {e}")
            return []
    
    @staticmethod
    def get_by_id(service_id: str) -> Optional[Dict[str, Any]]:
        """Get service by ID"""
        try:
            services_col = db_instance.db.services
            service = services_col.find_one(
                {"service_id": service_id},
                {"_id": 0}
            )
            return service
        except Exception as e:
            logger.error(f"Error getting service {service_id}: {e}")
            return None
    
    @staticmethod
    def create(service_config: ServiceConfig) -> bool:
        """Create a new service"""
        try:
            services_col = db_instance.db.services
            
            # Check if service already exists
            existing = services_col.find_one({"service_id": service_config.service_id})
            if existing:
                logger.warning(f"Service {service_config.service_id} already exists")
                return False
            
            result = services_col.insert_one(service_config.dict())
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error creating service: {e}")
            return False
    
    @staticmethod
    def update(service_id: str, updates: Dict[str, Any]) -> bool:
        """Update a service"""
        try:
            services_col = db_instance.db.services
            updates["updated_at"] = datetime.utcnow()
            
            result = services_col.update_one(
                {"service_id": service_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating service {service_id}: {e}")
            return False
    
    @staticmethod
    def delete(service_id: str) -> bool:
        """Delete a service"""
        try:
            services_col = db_instance.db.services
            result = services_col.delete_one({"service_id": service_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting service {service_id}: {e}")
            return False
    
    @staticmethod
    def get_enabled_services() -> List[Dict[str, Any]]:
        """Get all enabled services"""
        try:
            services_col = db_instance.db.services
            services = list(services_col.find(
                {"enabled": True},
                {"_id": 0}
            ))
            return services
        except Exception as e:
            logger.error(f"Error getting enabled services: {e}")
            return []

class CatalogRepository:
    """Repository for catalog operations"""
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all catalog entries"""
        try:
            catalog_col = db_instance.db.fix_catalog
            entries = list(catalog_col.find({}, {"_id": 0}))
            return entries
        except Exception as e:
            logger.error(f"Error getting all catalog entries: {e}")
            return []
    
    @staticmethod
    def get_by_issue(issue: str) -> List[Dict[str, Any]]:
        """Get catalog entries by issue"""
        try:
            catalog_col = db_instance.db.fix_catalog
            entries = list(catalog_col.find(
                {"issue": issue},
                {"_id": 0}
            ).sort("confidence", -1))
            return entries
        except Exception as e:
            logger.error(f"Error getting catalog entries for {issue}: {e}")
            return []
    
    @staticmethod
    def create(entry: FixCatalogEntry) -> bool:
        """Create a new catalog entry"""
        try:
            catalog_col = db_instance.db.fix_catalog
            
            # Check if entry already exists
            existing = catalog_col.find_one({
                "issue": entry.issue,
                "action": entry.action
            })
            if existing:
                logger.warning(f"Catalog entry {entry.issue}->{entry.action} already exists")
                return False
            
            result = catalog_col.insert_one(entry.dict())
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error creating catalog entry: {e}")
            return False
    
    @staticmethod
    def update_confidence(issue: str, action: str, confidence: float) -> bool:
        """Update confidence score"""
        try:
            catalog_col = db_instance.db.fix_catalog
            
            result = catalog_col.update_one(
                {"issue": issue, "action": action},
                {
                    "$set": {
                        "confidence": confidence,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating confidence: {e}")
            return False
    
    @staticmethod
    def delete(issue: str, action: str) -> bool:
        """Delete a catalog entry"""
        try:
            catalog_col = db_instance.db.fix_catalog
            result = catalog_col.delete_one({
                "issue": issue,
                "action": action
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting catalog entry: {e}")
            return False

class MemoryRepository:
    """Repository for action memory operations"""
    
    @staticmethod
    def create(memory: ActionMemory) -> bool:
        """Create a new action memory record"""
        try:
            memory_col = db_instance.db.agent_memory
            result = memory_col.insert_one(memory.dict())
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error creating memory record: {e}")
            return False
    
    @staticmethod
    def get_recent(service_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action memories"""
        try:
            memory_col = db_instance.db.agent_memory
            
            query = {}
            if service_id:
                query["service_id"] = service_id
            
            memories = list(memory_col.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit))
            return memories
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            return []
    
    @staticmethod
    def get_success_rate(issue: str, action: str, window_hours: int = 24) -> Optional[float]:
        """Get success rate for an issue-action pair"""
        try:
            memory_col = db_instance.db.agent_memory
            
            cutoff = datetime.utcnow() - timedelta(hours=window_hours)
            
            total = memory_col.count_documents({
                "issue": issue,
                "action": action,
                "timestamp": {"$gte": cutoff}
            })
            
            if total == 0:
                return None
            
            successes = memory_col.count_documents({
                "issue": issue,
                "action": action,
                "success": True,
                "timestamp": {"$gte": cutoff}
            })
            
            return successes / total
        except Exception as e:
            logger.error(f"Error getting success rate: {e}")
            return None
    
    @staticmethod
    def cleanup_old_records(days: int = 30):
        """Clean up old memory records"""
        try:
            memory_col = db_instance.db.agent_memory
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            result = memory_col.delete_many({
                "timestamp": {"$lt": cutoff}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old memory records")
                
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")

class IncidentRepository:
    """Repository for incident operations"""
    
    @staticmethod
    def create(incident: Incident) -> bool:
        """Create a new incident"""
        try:
            incidents_col = db_instance.db.incidents
            result = incidents_col.insert_one(incident.dict())
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return False
    
    @staticmethod
    def get_active() -> List[Dict[str, Any]]:
        """Get active incidents"""
        try:
            incidents_col = db_instance.db.incidents
            incidents = list(incidents_col.find(
                {"status": {"$ne": "resolved"}},
                {"_id": 0}
            ).sort("detected_at", -1))
            return incidents
        except Exception as e:
            logger.error(f"Error getting active incidents: {e}")
            return []
    
    @staticmethod
    def update(incident_id: str, updates: Dict[str, Any]) -> bool:
        """Update an incident"""
        try:
            incidents_col = db_instance.db.incidents
            
            if "resolved_at" in updates and updates["resolved_at"]:
                updates["status"] = "resolved"
            
            updates["updated_at"] = datetime.utcnow()
            
            result = incidents_col.update_one(
                {"incident_id": incident_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating incident {incident_id}: {e}")
            return False
    
    @staticmethod
    def get_by_service(service_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get incidents by service"""
        try:
            incidents_col = db_instance.db.incidents
            incidents = list(incidents_col.find(
                {"service_id": service_id},
                {"_id": 0}
            ).sort("detected_at", -1).limit(limit))
            return incidents
        except Exception as e:
            logger.error(f"Error getting incidents for service {service_id}: {e}")
            return []

class MetricsRepository:
    """Repository for metrics operations"""
    
    @staticmethod
    def store_metrics(metrics: ServiceMetrics) -> bool:
        """Store service metrics"""
        try:
            metrics_col = db_instance.db.metrics_history
            result = metrics_col.insert_one(metrics.dict())
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            return False
    
    @staticmethod
    def get_latest(service_id: str) -> Optional[Dict[str, Any]]:
        """Get latest metrics for a service"""
        try:
            metrics_col = db_instance.db.metrics_history
            latest = metrics_col.find_one(
                {"service_id": service_id},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            return latest
        except Exception as e:
            logger.error(f"Error getting latest metrics for {service_id}: {e}")
            return None
    
    @staticmethod
    def get_history(service_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for a service"""
        try:
            metrics_col = db_instance.db.metrics_history
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            history = list(metrics_col.find(
                {
                    "service_id": service_id,
                    "timestamp": {"$gte": cutoff}
                },
                {"_id": 0}
            ).sort("timestamp", 1))
            return history
        except Exception as e:
            logger.error(f"Error getting metrics history for {service_id}: {e}")
            return []
    
    @staticmethod
    def cleanup_old_metrics(hours: int = 24):
        """Clean up old metrics"""
        try:
            metrics_col = db_instance.db.metrics_history
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            result = metrics_col.delete_many({
                "timestamp": {"$lt": cutoff}
            })
            
            if result.deleted_count > 0:
                logger.debug(f"Cleaned up {result.deleted_count} old metrics")
                
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
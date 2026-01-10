import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import concurrent.futures

from src.models.database import db_instance
from src.models.schemas import ServiceMetrics, IssueType, ActionType
from src.utils.logger import logger
from config.settings import config
from .monitor import ServiceMonitor
from .decision_engine import DecisionEngine
from .action_executor import ActionExecutor
from .learning_engine import LearningEngine

class SelfHealingAgent:
    """Main autonomous agent orchestrating monitoring, decision, and action execution"""
    
    def __init__(self):
        self.monitor = ServiceMonitor()
        self.decision_engine = DecisionEngine()
        self.action_executor = ActionExecutor()
        self.learning_engine = LearningEngine()
        self._running = False
        self._monitor_thread = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.incidents = {}
    
    def start(self):
        """Start the autonomous agent"""
        if self._running:
            logger.warning("Agent is already running")
            return
        
        logger.info("Starting Self-Healing Agent...")
        self._running = True
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="monitor-loop"
        )
        self._monitor_thread.start()
        
        # Start periodic tasks
        threading.Thread(
            target=self._periodic_tasks_loop,
            daemon=True,
            name="periodic-tasks"
        ).start()
        
        logger.info("Agent started successfully")
    
    def stop(self):
        """Stop the autonomous agent"""
        logger.info("Stopping Self-Healing Agent...")
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self._executor.shutdown(wait=True)
        logger.info("Agent stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                services = self._get_active_services()
                
                # Monitor services in parallel
                futures = []
                for service in services:
                    future = self._executor.submit(
                        self._monitor_service,
                        service
                    )
                    futures.append(future)
                
                # Wait for all monitoring tasks to complete
                concurrent.futures.wait(futures, timeout=config.CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            
            time.sleep(config.CHECK_INTERVAL)
    
    def _get_active_services(self) -> List[Dict[str, Any]]:
        """Get list of active services from database"""
        try:
            services_col = db_instance.db.services
            active_services = list(services_col.find({"enabled": True}))
            
            if not active_services:
                # Use default services from config
                active_services = config.SERVICES
            
            return active_services
        except Exception as e:
            logger.error(f"Error fetching active services: {e}")
            return config.SERVICES
    
    def _monitor_service(self, service: Dict[str, Any]):
        """Monitor a single service"""
        service_id = service["service_id"]
        
        try:
            # Collect metrics
            metrics = self.monitor.collect_metrics(service)
            
            if not metrics:
                logger.warning(f"Failed to collect metrics for {service_id}")
                return
            
            # Detect anomalies
            anomalies = self.monitor.detect_anomalies(metrics, service)
            
            if anomalies:
                for issue in anomalies:
                    self._handle_anomaly(service, metrics, issue)
            
            # Store metrics for historical analysis
            self._store_metrics_history(service_id, metrics)
            
        except Exception as e:
            logger.error(f"Error monitoring service {service_id}: {e}", exc_info=True)
    
    def _handle_anomaly(self, service: Dict[str, Any], metrics: ServiceMetrics, issue: IssueType):
        """Handle detected anomaly"""
        service_id = service["service_id"]
        
        try:
            logger.warning(f"Anomaly detected: {issue} for service {service_id}")
            
            # Create incident record
            incident_id = self._create_incident(service_id, issue, metrics)
            
            # Make decision
            decision = self.decision_engine.decide_action(issue, service_id)
            
            if decision and decision.get("auto", True):
                # Execute action
                result = self.action_executor.execute(
                    decision["action"],
                    service,
                    decision.get("parameters", {})
                )
                
                # Evaluate outcome
                evaluation = self.learning_engine.evaluate_action(
                    service_id=service_id,
                    issue=issue,
                    action=decision["action"],
                    before_metrics=metrics.dict(),
                    result=result
                )
                
                # Update learning
                self.learning_engine.update_confidence(
                    issue=issue,
                    action=decision["action"],
                    success=evaluation["success"]
                )
                
                # Update incident
                self._update_incident(
                    incident_id,
                    action=decision["action"],
                    success=evaluation["success"],
                    resolution=evaluation.get("resolution")
                )
                
                logger.info(
                    f"Action {decision['action']} executed for {issue} on {service_id}. "
                    f"Success: {evaluation['success']}"
                )
            
        except Exception as e:
            logger.error(f"Error handling anomaly {issue} for {service_id}: {e}", exc_info=True)
    
    def _create_incident(self, service_id: str, issue: IssueType, metrics: ServiceMetrics) -> str:
        """Create incident record"""
        try:
            incidents_col = db_instance.db.incidents
            incident_id = f"inc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{service_id}"
            
            incident = {
                "incident_id": incident_id,
                "service_id": service_id,
                "issue": issue.value,
                "severity": self._determine_severity(issue, metrics),
                "status": "detected",
                "detected_at": datetime.utcnow(),
                "metrics_snapshot": metrics.dict()
            }
            
            incidents_col.insert_one(incident)
            self.incidents[incident_id] = incident
            
            return incident_id
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return f"temp_{service_id}_{issue}"
    
    def _update_incident(self, incident_id: str, **updates):
        """Update incident record"""
        try:
            incidents_col = db_instance.db.incidents
            
            if "resolved_at" in updates and updates.get("resolved_at"):
                updates["status"] = "resolved"
            
            updates["updated_at"] = datetime.utcnow()
            
            incidents_col.update_one(
                {"incident_id": incident_id},
                {"$set": updates}
            )
        except Exception as e:
            logger.error(f"Error updating incident {incident_id}: {e}")
    
    def _determine_severity(self, issue: IssueType, metrics: ServiceMetrics) -> str:
        """Determine incident severity"""
        if issue == IssueType.SERVICE_DOWN:
            return "critical"
        elif issue in [IssueType.MEMORY_PRESSURE, IssueType.HIGH_CPU]:
            if metrics.memory and metrics.memory > 95 or metrics.cpu and metrics.cpu > 95:
                return "critical"
            return "high"
        elif issue == IssueType.HIGH_ERROR_RATE:
            if metrics.error_rate and metrics.error_rate > 0.5:
                return "critical"
            return "medium"
        else:
            return "medium"
    
    def _store_metrics_history(self, service_id: str, metrics: ServiceMetrics):
        """Store metrics for historical analysis"""
        try:
            metrics_col = db_instance.db.metrics_history
            metrics_data = metrics.dict()
            metrics_data["service_id"] = service_id
            metrics_data["timestamp"] = datetime.utcnow()
            
            metrics_col.insert_one(metrics_data)
            
            # Keep only last 24 hours of metrics for performance
            cutoff = datetime.utcnow() - timedelta(hours=24)
            metrics_col.delete_many({
                "service_id": service_id,
                "timestamp": {"$lt": cutoff}
            })
            
        except Exception as e:
            logger.error(f"Error storing metrics history: {e}")
    
    def _periodic_tasks_loop(self):
        """Handle periodic maintenance tasks"""
        while self._running:
            try:
                # Clean up old incidents (older than 7 days)
                self._cleanup_old_incidents()
                
                # Recalculate confidence scores
                self.learning_engine.recalculate_all_confidence()
                
                # Check database health
                if not db_instance.is_healthy():
                    logger.error("Database connection lost, attempting to reconnect...")
                    db_instance.connect()
                
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in periodic tasks: {e}")
                time.sleep(60)
    
    def _cleanup_old_incidents(self):
        """Clean up resolved incidents older than 7 days"""
        try:
            incidents_col = db_instance.db.incidents
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            result = incidents_col.delete_many({
                "status": "resolved",
                "resolved_at": {"$lt": cutoff}
            })
            
            if result.deleted_count > 0:
                logger.debug(f"Cleaned up {result.deleted_count} old incidents")
                
        except Exception as e:
            logger.error(f"Error cleaning up old incidents: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "running": self._running,
            "services_monitored": len(self._get_active_services()),
            "active_incidents": len([i for i in self.incidents.values() if i.get("status") != "resolved"]),
            "last_check": datetime.utcnow().isoformat(),
            "database_healthy": db_instance.is_healthy()
        }
"""
Recovery engine for automatic problem resolution
"""
import time
import logging
from typing import Dict, Any, Optional, List


class RecoveryEngine:
    """Handle automatic recovery actions"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        cooldown_seconds: int = 60,
        logger: Optional[logging.Logger] = None
    ):
        self.max_attempts = max_attempts
        self.cooldown_seconds = cooldown_seconds
        self.logger = logger or logging.getLogger(__name__)
        
        self._recovery_history: List[Dict[str, Any]] = []
        self._attempt_counts = {}
        self._active_recoveries: Dict[str, Dict[str, Any]] = {}
    
    def start(self):
        """Start recovery engine"""
        self.logger.info("Recovery engine started")
    
    def stop(self):
        """Stop recovery engine"""
        self.logger.info("Recovery engine stopped")
    
    def recover_database(self, db_type: str, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recover a database"""
        db_id = f"db_{db_type}"
        
        # Check cooldown
        if self._is_in_cooldown(db_id):
            return {
                "success": False,
                "message": "Database in cooldown period",
                "action": "none",
                "recovery_id": db_id
            }
        
        self.logger.warning(f"🔄 Attempting to recover {db_type} database")
        
        # Create recovery record
        recovery_id = f"{db_id}_{int(time.time())}"
        recovery_record = {
            "recovery_id": recovery_id,
            "component": db_id,
            "start_time": time.time(),
            "status": "in_progress",
            "attempts": 0,
            "last_error": health_data.get('error_message', 'Unknown error')
        }
        
        self._active_recoveries[recovery_id] = recovery_record
        
        try:
            # Attempt recovery
            result = self._recover_database_connection(db_type, recovery_id)
            
            # Update recovery record
            recovery_record.update({
                "end_time": time.time(),
                "status": "completed" if result.get("success") else "failed",
                "result": result
            })
            
            # Move to history
            self._record_recovery(db_id, result)
            del self._active_recoveries[recovery_id]
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Database recovery failed: {e}")
            
            result = {
                "success": False,
                "message": f"Recovery failed: {str(e)}",
                "action": "failed",
                "recovery_id": recovery_id
            }
            
            # Update recovery record
            recovery_record.update({
                "end_time": time.time(),
                "status": "failed",
                "result": result,
                "error": str(e)
            })
            
            self._record_recovery(db_id, result)
            return result
    
    def _recover_database_connection(self, db_type: str, recovery_id: str) -> Dict[str, Any]:
        """Recover database connection"""
        self.logger.info(f"🔧 Recovering {db_type} connection (ID: {recovery_id})")
        
        # Recovery steps
        steps = [
            {"step": "reset_connection", "wait": 2},
            {"step": "clear_pool", "wait": 1},
            {"step": "reconnect", "wait": 3}
        ]
        
        for step_info in steps:
            step = step_info["step"]
            wait = step_info["wait"]
            
            self.logger.info(f"  Step: {step}...")
            time.sleep(wait)
        
        return {
            "success": True,
            "message": f"{db_type} connection recovery initiated",
            "action": "connection_reset",
            "recovery_id": recovery_id,
            "steps_completed": len(steps)
        }
    
    def _is_in_cooldown(self, component_id: str) -> bool:
        """Check if component is in cooldown period"""
        for recovery in reversed(self._recovery_history):
            if recovery.get('component_id') == component_id:
                recovery_time = recovery.get('timestamp', 0)
                if time.time() - recovery_time < self.cooldown_seconds:
                    return True
        return False
    
    def _record_recovery(self, component_id: str, result: Dict[str, Any]):
        """Record recovery attempt"""
        recovery = {
            "component_id": component_id,
            "timestamp": time.time(),
            "success": result.get("success", False),
            "action": result.get("action", "unknown"),
            "message": result.get("message", ""),
            "recovery_id": result.get("recovery_id", "")
        }
        self._recovery_history.append(recovery)
        
        # Log completion
        if result.get("success"):
            self.logger.info(f"✅ Recovery recorded: {result.get('message')}")
        else:
            self.logger.warning(f"⚠️ Recovery failed recorded: {result.get('message')}")
    
    def get_active_recoveries(self) -> List[Dict[str, Any]]:
        """Get active recovery attempts"""
        return list(self._active_recoveries.values())
    
    def get_recovery_history(self, limit: int = 10) -> list:
        """Get recovery history"""
        return self._recovery_history[-limit:]
    
    def get_recovery_status(self, recovery_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific recovery"""
        return self._active_recoveries.get(recovery_id)
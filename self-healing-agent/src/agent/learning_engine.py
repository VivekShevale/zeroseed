from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

from src.models.schemas import IssueType, ActionType
from src.models.database import db_instance
from src.utils.logger import logger

class LearningEngine:
    """Learning engine for improving action selection based on outcomes"""
    
    def __init__(self):
        self.confidence_cache = {}
        self.trend_analysis = defaultdict(list)
    
    def evaluate_action(self, service_id: str, issue: IssueType, action: str,
                       before_metrics: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the outcome of an action"""
        
        try:
            # Get metrics after action
            after_metrics = self._get_post_action_metrics(service_id)
            
            # Calculate improvement
            improvement = self._calculate_improvement(before_metrics, after_metrics)
            
            # Determine success
            success = self._determine_success(issue, before_metrics, after_metrics, result)
            
            # Store evaluation
            self._store_evaluation(
                service_id=service_id,
                issue=issue,
                action=action,
                success=success,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement=improvement,
                result=result
            )
            
            # Update trend analysis
            self._update_trend_analysis(issue, action, success)
            
            return {
                "success": success,
                "improvement": improvement,
                "resolution": "resolved" if success else "failed",
                "details": {
                    "before": before_metrics,
                    "after": after_metrics,
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluating action: {e}", exc_info=True)
            return {
                "success": False,
                "improvement": 0,
                "resolution": "evaluation_failed",
                "details": {"error": str(e)}
            }
    
    def update_confidence(self, issue: IssueType, action: str, success: bool):
        """Update confidence score for an action"""
        try:
            catalog_col = db_instance.db.fix_catalog
            
            # Get current confidence
            record = catalog_col.find_one({"issue": issue.value, "action": action})
            if not record:
                logger.warning(f"No catalog record for {issue.value}:{action}")
                return
            
            # Get historical data
            memory_col = db_instance.db.agent_memory
            total_attempts = memory_col.count_documents({
                "issue": issue.value,
                "action": action
            })
            
            successful_attempts = memory_col.count_documents({
                "issue": issue.value,
                "action": action,
                "success": True
            })
            
            # Calculate new confidence with smoothing
            if total_attempts > 0:
                raw_confidence = successful_attempts / total_attempts
                # Apply exponential smoothing (alpha = 0.3)
                old_confidence = record.get("confidence", 1.0)
                new_confidence = 0.7 * old_confidence + 0.3 * raw_confidence
            else:
                new_confidence = record.get("confidence", 1.0)
            
            # Update catalog
            catalog_col.update_one(
                {"issue": issue.value, "action": action},
                {
                    "$set": {
                        "confidence": new_confidence,
                        "updated_at": datetime.utcnow(),
                        "stats": {
                            "total_attempts": total_attempts,
                            "successful_attempts": successful_attempts,
                            "last_updated": datetime.utcnow()
                        }
                    }
                }
            )
            
            # Update cache
            cache_key = f"{issue.value}_{action}"
            self.confidence_cache[cache_key] = {
                "confidence": new_confidence,
                "timestamp": datetime.utcnow()
            }
            
            logger.debug(f"Updated confidence for {issue.value}:{action} = {new_confidence:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating confidence: {e}")
    
    def recalculate_all_confidence(self):
        """Recalculate confidence scores for all actions"""
        try:
            catalog_col = db_instance.db.fix_catalog
            memory_col = db_instance.db.agent_memory
            
            all_issues = catalog_col.distinct("issue")
            
            for issue in all_issues:
                actions = catalog_col.distinct("action", {"issue": issue})
                
                for action in actions:
                    # Count successes and failures
                    total_attempts = memory_col.count_documents({
                        "issue": issue,
                        "action": action
                    })
                    
                    successful_attempts = memory_col.count_documents({
                        "issue": issue,
                        "action": action,
                        "success": True
                    })
                    
                    if total_attempts > 0:
                        confidence = successful_attempts / total_attempts
                        
                        # Update with decay for older entries
                        recent_attempts = memory_col.count_documents({
                            "issue": issue,
                            "action": action,
                            "timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}
                        })
                        
                        if recent_attempts < total_attempts * 0.5:
                            # Apply decay for stale data
                            confidence *= 0.9
                        
                        catalog_col.update_one(
                            {"issue": issue, "action": action},
                            {"$set": {"confidence": confidence}}
                        )
            
            logger.info("Recalculated all confidence scores")
            
        except Exception as e:
            logger.error(f"Error recalculating confidence: {e}")
    
    def get_action_stats(self, issue: IssueType, action: str) -> Dict[str, Any]:
        """Get statistics for an action"""
        try:
            memory_col = db_instance.db.agent_memory
            
            # Get recent actions (last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            recent_actions = list(memory_col.find({
                "issue": issue.value,
                "action": action,
                "timestamp": {"$gte": cutoff}
            }))
            
            if not recent_actions:
                return {"total": 0, "successes": 0, "success_rate": 0}
            
            successes = sum(1 for a in recent_actions if a.get("success"))
            total = len(recent_actions)
            
            # Calculate success rate by time of day
            success_by_hour = defaultdict(lambda: {"total": 0, "successes": 0})
            for action_data in recent_actions:
                hour = action_data["timestamp"].hour
                success_by_hour[hour]["total"] += 1
                if action_data.get("success"):
                    success_by_hour[hour]["successes"] += 1
            
            return {
                "total": total,
                "successes": successes,
                "success_rate": successes / total if total > 0 else 0,
                "recent_count": total,
                "success_by_hour": {
                    str(hour): {
                        "rate": data["successes"] / data["total"] if data["total"] > 0 else 0,
                        "count": data["total"]
                    }
                    for hour, data in success_by_hour.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting action stats: {e}")
            return {}
    
    def _get_post_action_metrics(self, service_id: str) -> Dict[str, Any]:
        """Get metrics after action execution"""
        try:
            # In a real implementation, this would fetch fresh metrics
            # For now, return default improved metrics
            return {
                "health": "UP",
                "memory": 50,
                "cpu": 40,
                "error_rate": 0.05,
                "latency": 500
            }
        except:
            return {}
    
    def _calculate_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
        """Calculate improvement score"""
        improvements = []
        
        # Health improvement
        if before.get("health") == "DOWN" and after.get("health") == "UP":
            improvements.append(1.0)
        
        # Memory improvement
        if before.get("memory") and after.get("memory"):
            mem_improvement = max(0, before["memory"] - after["memory"]) / 100
            improvements.append(mem_improvement)
        
        # Error rate improvement
        if before.get("error_rate") and after.get("error_rate"):
            error_improvement = max(0, before["error_rate"] - after["error_rate"])
            improvements.append(error_improvement)
        
        # Latency improvement
        if before.get("latency") and after.get("latency"):
            latency_improvement = max(0, before["latency"] - after["latency"]) / before["latency"]
            improvements.append(latency_improvement)
        
        return statistics.mean(improvements) if improvements else 0
    
    def _determine_success(self, issue: IssueType, before: Dict[str, Any], 
                          after: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Determine if action was successful"""
        
        # Check if HTTP action itself failed
        if not result.get("success", False):
            return False
        
        # Issue-specific success criteria
        if issue == IssueType.SERVICE_DOWN:
            return after.get("health") == "UP"
        
        elif issue == IssueType.MEMORY_PRESSURE:
            if before.get("memory") and after.get("memory"):
                return after["memory"] < before["memory"] * 0.8  # 20% reduction
        
        elif issue == IssueType.HIGH_LATENCY:
            if before.get("latency") and after.get("latency"):
                return after["latency"] < before["latency"] * 0.7  # 30% reduction
        
        elif issue == IssueType.HIGH_ERROR_RATE:
            if before.get("error_rate") and after.get("error_rate"):
                return after["error_rate"] < before["error_rate"] * 0.5  # 50% reduction
        
        # Default: consider successful if health is UP
        return after.get("health") == "UP"
    
    def _store_evaluation(self, **data):
        """Store action evaluation in database"""
        try:
            memory_col = db_instance.db.agent_memory
            
            memory_col.insert_one({
                **data,
                "timestamp": datetime.utcnow(),
                "evaluated_at": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error storing evaluation: {e}")
    
    def _update_trend_analysis(self, issue: IssueType, action: str, success: bool):
        """Update trend analysis data"""
        key = f"{issue.value}_{action}"
        
        # Keep only last 100 entries for trend analysis
        self.trend_analysis[key].append({
            "timestamp": datetime.utcnow(),
            "success": success
        })
        
        if len(self.trend_analysis[key]) > 100:
            self.trend_analysis[key] = self.trend_analysis[key][-100:]
    
    def get_trend(self, issue: IssueType, action: str, window_hours: int = 24) -> Dict[str, Any]:
        """Get success trend for an action"""
        key = f"{issue.value}_{action}"
        entries = self.trend_analysis.get(key, [])
        
        if not entries:
            return {"trend": "insufficient_data", "success_rate": 0}
        
        # Filter by window
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [e for e in entries if e["timestamp"] > cutoff]
        
        if not recent:
            return {"trend": "no_recent_data", "success_rate": 0}
        
        # Calculate success rate
        successes = sum(1 for e in recent if e["success"])
        success_rate = successes / len(recent)
        
        # Determine trend
        if len(recent) >= 10:
            # Split into halves for comparison
            first_half = recent[:len(recent)//2]
            second_half = recent[len(recent)//2:]
            
            first_success = sum(1 for e in first_half if e["success"]) / len(first_half)
            second_success = sum(1 for e in second_half if e["success"]) / len(second_half)
            
            if second_success > first_success + 0.1:
                trend = "improving"
            elif second_success < first_success - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "success_rate": success_rate,
            "recent_count": len(recent),
            "window_hours": window_hours
        }
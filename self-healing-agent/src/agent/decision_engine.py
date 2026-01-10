from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

from src.models.schemas import IssueType, ActionType
from src.models.database import db_instance
from src.utils.logger import logger

class DecisionEngine:
    """Decision engine for choosing remediation actions"""
    
    def __init__(self):
        self.action_history = {}
        self.decision_cache = {}
    
    def decide_action(self, issue: IssueType, service_id: str) -> Optional[Dict[str, Any]]:
        """Decide which action to take for a given issue"""
        
        # Check cache first
        cache_key = f"{issue.value}_{service_id}"
        if cache_key in self.decision_cache:
            cached = self.decision_cache[cache_key]
            if (datetime.utcnow() - cached["timestamp"]).seconds < 60:
                return cached["decision"]
        
        try:
            # Get available actions for this issue
            catalog_col = db_instance.db.fix_catalog
            available_actions = list(catalog_col.find({
                "issue": issue.value,
                "auto": True,
                "confidence": {"$gt": 0.3}  # Minimum confidence threshold
            }).sort("confidence", -1))
            
            if not available_actions:
                logger.warning(f"No auto-remediation actions available for {issue}")
                return None
            
            # Get recent actions for this service
            recent_actions = self._get_recent_actions(service_id, minutes=5)
            
            # Filter out recently failed actions
            filtered_actions = []
            for action in available_actions:
                action_key = f"{issue.value}_{action['action']}"
                recent_failures = self.action_history.get(action_key, {}).get("failures", 0)
                
                # Don't retry recently failed actions too quickly
                if recent_failures > 2:
                    last_failure = self.action_history[action_key].get("last_failure")
                    if last_failure and (datetime.utcnow() - last_failure).seconds < 300:
                        continue
                
                filtered_actions.append(action)
            
            if not filtered_actions:
                logger.warning(f"No suitable actions after filtering for {issue}")
                return None
            
            # Apply decision strategy
            selected_action = self._apply_decision_strategy(filtered_actions, issue, service_id)
            
            if selected_action:
                # Cache the decision
                self.decision_cache[cache_key] = {
                    "decision": selected_action,
                    "timestamp": datetime.utcnow()
                }
                
                return selected_action
            
        except Exception as e:
            logger.error(f"Error in decision engine for {issue}: {e}")
        
        return None
    
    def _apply_decision_strategy(self, actions: List[Dict], issue: IssueType, service_id: str) -> Optional[Dict]:
        """Apply decision-making strategy to select an action"""
        
        # Strategy 1: Highest confidence
        if len(actions) == 1:
            return actions[0]
        
        # Strategy 2: For critical issues, use highest confidence
        if issue == IssueType.SERVICE_DOWN:
            return max(actions, key=lambda x: x.get("confidence", 0))
        
        # Strategy 3: For resource issues, consider escalation
        if issue in [IssueType.MEMORY_PRESSURE, IssueType.HIGH_CPU]:
            # Check if this is a recurring issue
            if self._is_recurring_issue(issue, service_id, minutes=30):
                # Try more aggressive action
                aggressive_actions = [a for a in actions if a.get("action") in ["scale_up", "restart"]]
                if aggressive_actions:
                    return aggressive_actions[0]
        
        # Strategy 4: Explore alternatives sometimes (epsilon-greedy)
        if random.random() < 0.1:  # 10% exploration rate
            return random.choice(actions)
        
        # Default: Highest confidence
        return max(actions, key=lambda x: x.get("confidence", 0))
    
    def _get_recent_actions(self, service_id: str, minutes: int = 5) -> List[Dict]:
        """Get recent actions for a service"""
        try:
            memory_col = db_instance.db.agent_memory
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            
            return list(memory_col.find({
                "service_id": service_id,
                "timestamp": {"$gte": cutoff}
            }).sort("timestamp", -1))
        except Exception as e:
            logger.error(f"Error getting recent actions: {e}")
            return []
    
    def _is_recurring_issue(self, issue: IssueType, service_id: str, minutes: int) -> bool:
        """Check if this issue has occurred recently"""
        try:
            memory_col = db_instance.db.agent_memory
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            
            count = memory_col.count_documents({
                "service_id": service_id,
                "issue": issue.value,
                "timestamp": {"$gte": cutoff}
            })
            
            return count >= 3  # Recurring if happened 3+ times in timeframe
        except:
            return False
    
    def record_action_outcome(self, issue: IssueType, action: str, success: bool):
        """Record action outcome for learning"""
        action_key = f"{issue.value}_{action}"
        
        if action_key not in self.action_history:
            self.action_history[action_key] = {
                "successes": 0,
                "failures": 0,
                "last_failure": None
            }
        
        if success:
            self.action_history[action_key]["successes"] += 1
        else:
            self.action_history[action_key]["failures"] += 1
            self.action_history[action_key]["last_failure"] = datetime.utcnow()
    
    def get_available_actions(self, issue: IssueType) -> List[Dict]:
        """Get all available actions for an issue"""
        try:
            catalog_col = db_instance.db.fix_catalog
            return list(catalog_col.find({"issue": issue.value}).sort("confidence", -1))
        except Exception as e:
            logger.error(f"Error getting available actions: {e}")
            return []
import requests
import time
import subprocess
from typing import Dict, Any, Optional, Tuple
import json

from src.models.schemas import ActionType
from src.utils.logger import logger
from config.settings import config

class ActionExecutor:
    """Execute remediation actions"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = (5, 30)
        self.custom_actions = {}
    
    def execute(self, action: str, service: Dict[str, Any], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a remediation action"""
        start_time = time.time()
        result = {
            "action": action,
            "success": False,
            "execution_time": 0,
            "error": None,
            "details": {}
        }
        
        try:
            action_method = getattr(self, f"_execute_{action}", None)
            if action_method:
                result.update(action_method(service, parameters or {}))
            else:
                # Try custom action
                result.update(self._execute_custom(action, service, parameters or {}))
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error executing action {action}: {e}", exc_info=True)
        finally:
            result["execution_time"] = time.time() - start_time
        
        logger.info(f"Action {action} executed: success={result['success']}, time={result['execution_time']:.2f}s")
        return result
    
    def _execute_restart(self, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restart service"""
        service_url = service["service_url"]
        restart_endpoint = service.get("restart_endpoint", "/agent/restart")
        
        try:
            response = self.session.post(
                f"{service_url.rstrip('/')}{restart_endpoint}",
                json=parameters,
                timeout=10
            )
            response.raise_for_status()
            
            # Wait for service to come back up
            time.sleep(5)
            
            # Verify service is up
            health_url = f"{service_url.rstrip('/')}{service.get('health_endpoint', '/health')}"
            health_response = self.session.get(health_url, timeout=5)
            
            return {
                "success": health_response.status_code == 200,
                "details": {
                    "restart_response": response.json() if response.content else {},
                    "health_after": health_response.status_code
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"HTTP error: {e}",
                "details": {"exception_type": "http_error"}
            }
    
    def _execute_scale_up(self, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scale up service instances"""
        # This would typically call a cloud provider API or container orchestrator
        scale_api = service.get("scale_api_endpoint")
        
        if not scale_api:
            return {
                "success": False,
                "error": "Scale API endpoint not configured",
                "details": {}
            }
        
        try:
            response = self.session.post(
                scale_api,
                json={
                    "action": "scale_up",
                    "service": service["service_id"],
                    "increment": parameters.get("increment", 1)
                },
                timeout=30
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "details": response.json()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Scale API error: {e}",
                "details": {}
            }
    
    def _execute_clear_cache(self, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear service cache"""
        cache_endpoint = service.get("cache_endpoint", "/agent/clear_cache")
        
        try:
            response = self.session.post(
                f"{service['service_url'].rstrip('/')}{cache_endpoint}",
                json=parameters,
                timeout=10
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "details": response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Cache clear error: {e}",
                "details": {}
            }
    
    def _execute_rollback(self, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback to previous version"""
        rollback_endpoint = service.get("rollback_endpoint", "/agent/rollback")
        
        try:
            response = self.session.post(
                f"{service['service_url'].rstrip('/')}{rollback_endpoint}",
                json={
                    "version": parameters.get("version", "previous"),
                    "force": parameters.get("force", False)
                },
                timeout=30
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "details": response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Rollback error: {e}",
                "details": {}
            }
    
    def _execute_notify(self, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification"""
        # This could integrate with Slack, Email, PagerDuty, etc.
        notification_channel = parameters.get("channel", "slack")
        
        try:
            # Example: Slack webhook
            if notification_channel == "slack":
                webhook_url = service.get("slack_webhook")
                if webhook_url:
                    payload = {
                        "text": f"🚨 Incident detected for {service['name']} ({service['service_id']})",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*Incident Alert*\nService: {service['name']}\nID: {service['service_id']}\nAction: {parameters.get('action', 'manual')}"
                                }
                            }
                        ]
                    }
                    
                    response = requests.post(webhook_url, json=payload, timeout=5)
                    response.raise_for_status()
            
            return {
                "success": True,
                "details": {"channel": notification_channel}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Notification error: {e}",
                "details": {}
            }
    
    def _execute_custom(self, action: str, service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom action"""
        # Check if custom action is defined
        custom_action = self.custom_actions.get(action)
        
        if not custom_action:
            return {
                "success": False,
                "error": f"Custom action '{action}' not found",
                "details": {}
            }
        
        try:
            # Execute custom action based on type
            action_type = custom_action.get("type", "http")
            
            if action_type == "http":
                return self._execute_http_action(custom_action, service, parameters)
            elif action_type == "script":
                return self._execute_script_action(custom_action, service, parameters)
            elif action_type == "command":
                return self._execute_command_action(custom_action, service, parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                    "details": {}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Custom action error: {e}",
                "details": {}
            }
    
    def _execute_http_action(self, action_config: Dict[str, Any], service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP-based custom action"""
        try:
            url = action_config.get("url", "").format(service=service, **parameters)
            method = action_config.get("method", "POST")
            
            response = self.session.request(
                method=method,
                url=url,
                json=parameters.get("body", {}),
                headers=parameters.get("headers", {}),
                timeout=action_config.get("timeout", 30)
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "details": response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"HTTP action error: {e}",
                "details": {}
            }
    
    def _execute_script_action(self, action_config: Dict[str, Any], service: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute script-based custom action"""
        try:
            script_path = action_config.get("script_path")
            if not script_path:
                return {
                    "success": False,
                    "error": "Script path not configured",
                    "details": {}
                }
            
            # Prepare environment variables
            env = {
                **action_config.get("env", {}),
                "SERVICE_ID": service["service_id"],
                "SERVICE_URL": service["service_url"],
                **parameters.get("env", {})
            }
            
            # Execute script
            result = subprocess.run(
                [script_path] + parameters.get("args", []),
                env={**subprocess.os.environ, **env},
                capture_output=True,
                text=True,
                timeout=action_config.get("timeout", 60)
            )
            
            return {
                "success": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None,
                "details": {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timeout",
                "details": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution error: {e}",
                "details": {}
            }
    
    def register_custom_action(self, name: str, config: Dict[str, Any]):
        """Register a custom action"""
        self.custom_actions[name] = config
        logger.info(f"Custom action registered: {name}")
    
    def get_available_actions(self) -> list:
        """Get list of available actions"""
        base_actions = [action.value for action in ActionType]
        custom_actions = list(self.custom_actions.keys())
        return base_actions + custom_actions
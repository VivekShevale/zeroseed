from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import uuid
from datetime import datetime

from src.models.schemas import (
    ServiceConfig, FixCatalogEntry, IssueType, ActionType,
    ServiceMetrics, Incident
)
from src.models.database import db_instance
from src.utils.logger import logger
from config.settings import config
from src.utils.validators import validate_api_key

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get(config.API_KEY_HEADER)
        if not api_key or api_key not in config.API_KEYS:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_healthy = db_instance.is_healthy()
    
    return jsonify({
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_healthy else "disconnected",
        "version": "1.0.0"
    })

@api_bp.route('/services', methods=['GET'])
@require_api_key
def list_services():
    """List all registered services"""
    try:
        services_col = db_instance.db.services
        services = list(services_col.find({}, {"_id": 0}))
        
        return jsonify({
            "services": services,
            "count": len(services)
        })
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/services', methods=['POST'])
@require_api_key
def register_service():
    """Register a new service"""
    try:
        data = request.json
        
        # Validate required fields
        required = ["service_id", "name", "service_url", "metrics_url"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if service already exists
        services_col = db_instance.db.services
        if services_col.find_one({"service_id": data["service_id"]}):
            return jsonify({"error": "Service already exists"}), 409
        
        # Create service config
        service_config = ServiceConfig(**data)
        
        # Insert into database
        services_col.insert_one(service_config.dict())
        
        logger.info(f"Service registered: {data['service_id']}")
        
        return jsonify({
            "status": "registered",
            "service_id": data["service_id"],
            "message": "Service registered successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        return jsonify({"error": str(e)}), 400

@api_bp.route('/services/<service_id>', methods=['PUT'])
@require_api_key
def update_service(service_id):
    """Update service configuration"""
    try:
        data = request.json
        
        services_col = db_instance.db.services
        
        # Check if service exists
        if not services_col.find_one({"service_id": service_id}):
            return jsonify({"error": "Service not found"}), 404
        
        # Update service
        update_data = {**data, "updated_at": datetime.utcnow()}
        services_col.update_one(
            {"service_id": service_id},
            {"$set": update_data}
        )
        
        logger.info(f"Service updated: {service_id}")
        
        return jsonify({
            "status": "updated",
            "service_id": service_id
        })
        
    except Exception as e:
        logger.error(f"Error updating service: {e}")
        return jsonify({"error": str(e)}), 400

@api_bp.route('/services/<service_id>', methods=['DELETE'])
@require_api_key
def delete_service(service_id):
    """Delete a service"""
    try:
        services_col = db_instance.db.services
        
        result = services_col.delete_one({"service_id": service_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Service not found"}), 404
        
        logger.info(f"Service deleted: {service_id}")
        
        return jsonify({
            "status": "deleted",
            "service_id": service_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/catalog', methods=['GET'])
@require_api_key
def list_catalog():
    """List all issue-action mappings"""
    try:
        catalog_col = db_instance.db.fix_catalog
        catalog = list(catalog_col.find({}, {"_id": 0}))
        
        return jsonify({
            "catalog": catalog,
            "count": len(catalog)
        })
    except Exception as e:
        logger.error(f"Error listing catalog: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/catalog', methods=['POST'])
@require_api_key
def add_catalog_entry():
    """Add a new issue-action mapping"""
    try:
        data = request.json
        
        # Validate required fields
        required = ["issue", "action"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Validate issue and action types
        try:
            issue = IssueType(data["issue"])
        except ValueError:
            # Allow custom issues
            issue = IssueType.CUSTOM
        
        try:
            action = ActionType(data["action"])
        except ValueError:
            # Allow custom actions
            action = ActionType.CUSTOM
        
        # Check if entry already exists
        catalog_col = db_instance.db.fix_catalog
        if catalog_col.find_one({"issue": data["issue"], "action": data["action"]}):
            return jsonify({"error": "Catalog entry already exists"}), 409
        
        # Create catalog entry
        catalog_entry = FixCatalogEntry(**data)
        
        # Insert into database
        catalog_col.insert_one(catalog_entry.dict())
        
        logger.info(f"Catalog entry added: {data['issue']} -> {data['action']}")
        
        return jsonify({
            "status": "added",
            "entry": catalog_entry.dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding catalog entry: {e}")
        return jsonify({"error": str(e)}), 400

@api_bp.route('/catalog/<issue>/<action>', methods=['DELETE'])
@require_api_key
def delete_catalog_entry(issue, action):
    """Delete a catalog entry"""
    try:
        catalog_col = db_instance.db.fix_catalog
        
        result = catalog_col.delete_one({"issue": issue, "action": action})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Catalog entry not found"}), 404
        
        logger.info(f"Catalog entry deleted: {issue} -> {action}")
        
        return jsonify({
            "status": "deleted",
            "issue": issue,
            "action": action
        })
        
    except Exception as e:
        logger.error(f"Error deleting catalog entry: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/metrics', methods=['POST'])
@require_api_key
def ingest_metrics():
    """Ingest metrics from external services"""
    try:
        data = request.json
        
        # Validate required fields
        required = ["service_id", "metrics"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        service_id = data["service_id"]
        metrics_data = data["metrics"]
        
        # Create metrics object
        metrics = ServiceMetrics(
            service_id=service_id,
            **metrics_data
        )
        
        # Store metrics
        metrics_col = db_instance.db.metrics_history
        metrics_col.insert_one(metrics.dict())
        
        # Trigger anomaly detection
        from src.agent.agent import agent_instance
        if agent_instance:
            # Simulate monitoring for this service
            services_col = db_instance.db.services
            service = services_col.find_one({"service_id": service_id})
            
            if service:
                anomalies = agent_instance.monitor.detect_anomalies(metrics, service)
                
                if anomalies:
                    return jsonify({
                        "status": "anomalies_detected",
                        "anomalies": [a.value for a in anomalies],
                        "message": "Anomalies detected, agent will take action"
                    })
        
        return jsonify({
            "status": "metrics_received",
            "service_id": service_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error ingesting metrics: {e}")
        return jsonify({"error": str(e)}), 400

@api_bp.route('/actions/history', methods=['GET'])
@require_api_key
def get_action_history():
    """Get action execution history"""
    try:
        # Get query parameters
        service_id = request.args.get('service_id')
        issue = request.args.get('issue')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = {}
        if service_id:
            query["service_id"] = service_id
        if issue:
            query["issue"] = issue
        
        memory_col = db_instance.db.agent_memory
        
        # Get total count
        total = memory_col.count_documents(query)
        
        # Get paginated results
        history = list(memory_col.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(offset).limit(limit))
        
        return jsonify({
            "history": history,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(history) < total
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting action history: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/incidents', methods=['GET'])
@require_api_key
def get_incidents():
    """Get incident history"""
    try:
        # Get query parameters
        service_id = request.args.get('service_id')
        status = request.args.get('status')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = {}
        if service_id:
            query["service_id"] = service_id
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        
        incidents_col = db_instance.db.incidents
        
        # Get total count
        total = incidents_col.count_documents(query)
        
        # Get paginated results
        incidents = list(incidents_col.find(
            query,
            {"_id": 0}
        ).sort("detected_at", -1).skip(offset).limit(limit))
        
        return jsonify({
            "incidents": incidents,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(incidents) < total
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting incidents: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/agent/status', methods=['GET'])
@require_api_key
def get_agent_status():
    """Get agent status"""
    try:
        from src.agent.agent import agent_instance
        
        if not agent_instance:
            return jsonify({
                "status": "not_initialized",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        agent_status = agent_instance.get_status()
        
        # Get additional stats
        services_col = db_instance.db.services
        total_services = services_col.count_documents({})
        enabled_services = services_col.count_documents({"enabled": True})
        
        catalog_col = db_instance.db.fix_catalog
        total_catalog_entries = catalog_col.count_documents({})
        
        return jsonify({
            **agent_status,
            "services": {
                "total": total_services,
                "enabled": enabled_services
            },
            "catalog": {
                "total_entries": total_catalog_entries
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/agent/start', methods=['POST'])
@require_api_key
def start_agent():
    """Start the agent"""
    try:
        from src.agent.agent import agent_instance
        
        if not agent_instance:
            return jsonify({"error": "Agent not initialized"}), 500
        
        agent_instance.start()
        
        return jsonify({
            "status": "started",
            "message": "Agent started successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/agent/stop', methods=['POST'])
@require_api_key
def stop_agent():
    """Stop the agent"""
    try:
        from src.agent.agent import agent_instance
        
        if not agent_instance:
            return jsonify({"error": "Agent not initialized"}), 500
        
        agent_instance.stop()
        
        return jsonify({
            "status": "stopped",
            "message": "Agent stopped successfully"
        })
        
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/manual/action', methods=['POST'])
@require_api_key
def execute_manual_action():
    """Execute a manual action"""
    try:
        data = request.json
        
        # Validate required fields
        required = ["service_id", "action"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        service_id = data["service_id"]
        action = data["action"]
        parameters = data.get("parameters", {})
        
        # Get service
        services_col = db_instance.db.services
        service = services_col.find_one({"service_id": service_id})
        
        if not service:
            return jsonify({"error": "Service not found"}), 404
        
        # Execute action
        from src.agent.action_executor import ActionExecutor
        executor = ActionExecutor()
        result = executor.execute(action, service, parameters)
        
        # Log manual action
        memory_col = db_instance.db.agent_memory
        memory_col.insert_one({
            "service_id": service_id,
            "action": action,
            "success": result["success"],
            "timestamp": datetime.utcnow(),
            "manual": True,
            "parameters": parameters,
            "result": result
        })
        
        return jsonify({
            "status": "executed",
            "action": action,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error executing manual action: {e}")
        return jsonify({"error": str(e)}), 500
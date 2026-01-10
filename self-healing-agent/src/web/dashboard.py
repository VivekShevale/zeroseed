"""
Dashboard blueprint for web interface.
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta

from src.models.database import db_instance
from src.utils.logger import logger

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def index():
    """Render main dashboard"""
    return render_template('dashboard.html')

@dashboard_bp.route('/api/status')
def get_status():
    """Get dashboard status data"""
    try:
        # Get services count
        services_col = db_instance.db.services
        total_services = services_col.count_documents({})
        enabled_services = services_col.count_documents({"enabled": True})
        
        # Get active incidents
        incidents_col = db_instance.db.incidents
        active_incidents = incidents_col.count_documents({
            "status": {"$ne": "resolved"}
        })
        
        # Get recent actions
        memory_col = db_instance.db.agent_memory
        recent_actions = list(memory_col.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(10))
        
        # Get catalog stats
        catalog_col = db_instance.db.fix_catalog
        catalog_entries = catalog_col.count_documents({})
        
        # Get metrics history
        metrics_col = db_instance.db.metrics_history
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_metrics = list(metrics_col.find(
            {"timestamp": {"$gte": cutoff}},
            {"_id": 0, "service_id": 1, "health": 1, "timestamp": 1}
        ).sort("timestamp", -1))
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "total": total_services,
                "enabled": enabled_services,
                "disabled": total_services - enabled_services
            },
            "incidents": {
                "active": active_incidents,
                "total_today": incidents_col.count_documents({
                    "detected_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
                })
            },
            "catalog": {
                "total_entries": catalog_entries
            },
            "recent_actions": recent_actions,
            "recent_metrics": recent_metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard status: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_bp.route('/api/services')
def get_services():
    """Get services data for dashboard"""
    try:
        services_col = db_instance.db.services
        services = list(services_col.find({}, {"_id": 0}))
        
        # Get latest metrics for each service
        metrics_col = db_instance.db.metrics_history
        
        for service in services:
            service_id = service["service_id"]
            latest_metric = metrics_col.find_one(
                {"service_id": service_id},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            
            if latest_metric:
                service["latest_metrics"] = latest_metric
            else:
                service["latest_metrics"] = {
                    "health": "UNKNOWN",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return jsonify({
            "services": services,
            "count": len(services)
        })
        
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_bp.route('/api/incidents')
def get_incidents_dashboard():
    """Get incidents for dashboard"""
    try:
        limit = int(request.args.get('limit', 20))
        
        incidents_col = db_instance.db.incidents
        incidents = list(incidents_col.find(
            {},
            {"_id": 0}
        ).sort("detected_at", -1).limit(limit))
        
        return jsonify({
            "incidents": incidents,
            "count": len(incidents)
        })
        
    except Exception as e:
        logger.error(f"Error getting incidents: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_bp.route('/api/catalog')
def get_catalog_dashboard():
    """Get catalog for dashboard"""
    try:
        catalog_col = db_instance.db.fix_catalog
        catalog = list(catalog_col.find({}, {"_id": 0}))
        
        # Group by issue for display
        grouped_catalog = {}
        for entry in catalog:
            issue = entry["issue"]
            if issue not in grouped_catalog:
                grouped_catalog[issue] = []
            grouped_catalog[issue].append(entry)
        
        return jsonify({
            "catalog": catalog,
            "grouped": grouped_catalog,
            "count": len(catalog)
        })
        
    except Exception as e:
        logger.error(f"Error getting catalog: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_bp.route('/api/metrics/<service_id>')
def get_service_metrics(service_id):
    """Get metrics history for a service"""
    try:
        hours = int(request.args.get('hours', 24))
        
        metrics_col = db_instance.db.metrics_history
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = list(metrics_col.find(
            {
                "service_id": service_id,
                "timestamp": {"$gte": cutoff}
            },
            {"_id": 0}
        ).sort("timestamp", 1))
        
        return jsonify({
            "service_id": service_id,
            "metrics": metrics,
            "count": len(metrics),
            "time_range_hours": hours
        })
        
    except Exception as e:
        logger.error(f"Error getting service metrics: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_bp.route('/api/actions/stats')
def get_actions_stats():
    """Get action statistics"""
    try:
        memory_col = db_instance.db.agent_memory
        
        # Get success rate by action
        pipeline = [
            {
                "$group": {
                    "_id": "$action",
                    "total": {"$sum": 1},
                    "successes": {
                        "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "action": "$_id",
                    "total": 1,
                    "successes": 1,
                    "success_rate": {
                        "$cond": [
                            {"$eq": ["$total", 0]},
                            0,
                            {"$divide": ["$successes", "$total"]}
                        ]
                    }
                }
            },
            {"$sort": {"total": -1}}
        ]
        
        action_stats = list(memory_col.aggregate(pipeline))
        
        # Get success rate by hour
        hourly_pipeline = [
            {
                "$project": {
                    "hour": {"$hour": "$timestamp"},
                    "success": 1
                }
            },
            {
                "$group": {
                    "_id": "$hour",
                    "total": {"$sum": 1},
                    "successes": {
                        "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "hour": "$_id",
                    "total": 1,
                    "successes": 1,
                    "success_rate": {
                        "$cond": [
                            {"$eq": ["$total", 0]},
                            0,
                            {"$divide": ["$successes", "$total"]}
                        ]
                    }
                }
            },
            {"$sort": {"hour": 1}}
        ]
        
        hourly_stats = list(memory_col.aggregate(hourly_pipeline))
        
        return jsonify({
            "action_stats": action_stats,
            "hourly_stats": hourly_stats,
            "total_actions": memory_col.count_documents({}),
            "successful_actions": memory_col.count_documents({"success": True})
        })
        
    except Exception as e:
        logger.error(f"Error getting action stats: {e}")
        return jsonify({"error": "Internal server error"}), 500
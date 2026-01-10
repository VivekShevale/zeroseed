"""
Basic Mock Service for Self-Healing Agent Integration
Easy to copy and integrate into any Python backend.
"""
from flask import Flask, jsonify
import random
import time
from datetime import datetime, timezone

app = Flask(__name__)

# Simple service state
service_state = {
    "status": "UP",           # UP, DOWN, DEGRADED
    "memory_usage": 50,       # Percentage (0-100)
    "cpu_usage": 30,          # Percentage (0-100)
    "latency": 100,           # Milliseconds
    "error_rate": 0.01,       # 0-1 (0-100%)
    "requests_served": 0,
    "last_restart": datetime.now(timezone.utc).isoformat()
}

@app.route('/health', methods=['GET'])
def health():
    """Required: Health endpoint for agent monitoring"""
    service_state["requests_served"] += 1
    
    # Return current service state
    return jsonify({
        "status": service_state["status"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": {
            "memory_usage": service_state["memory_usage"],
            "cpu_usage": service_state["cpu_usage"],
            "latency": service_state["latency"],
            "error_rate": service_state["error_rate"],
            "requests_served": service_state["requests_served"]
        }
    })

@app.route('/agent/restart', methods=['POST'])
def restart_service():
    """Required: Restart endpoint for agent remediation"""
    # Reset service to healthy state
    service_state.update({
        "status": "UP",
        "memory_usage": 30,
        "cpu_usage": 20,
        "latency": 100,
        "error_rate": 0.01,
        "last_restart": datetime.now(timezone.utc).isoformat()
    })
    
    print(f"✅ Service restarted by agent at {service_state['last_restart']}")
    
    return jsonify({
        "status": "restarted",
        "message": "Service restarted successfully",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# Optional: Additional endpoints for agent actions
@app.route('/agent/clear_cache', methods=['POST'])
def clear_cache():
    """Optional: Clear cache endpoint"""
    # Reduce latency after cache clear
    service_state["latency"] = max(50, service_state["latency"] - 100)
    
    return jsonify({
        "status": "cache_cleared",
        "message": "Cache cleared successfully",
        "new_latency": service_state["latency"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/agent/scale_up', methods=['POST'])
def scale_up():
    """Optional: Scale up endpoint"""
    # Improve metrics after scaling
    service_state["memory_usage"] = max(20, service_state["memory_usage"] - 15)
    service_state["cpu_usage"] = max(15, service_state["cpu_usage"] - 10)
    
    return jsonify({
        "status": "scaled_up",
        "message": "Service scaled up successfully",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/agent/rollback', methods=['POST'])
def rollback():
    """Optional: Rollback endpoint"""
    # Reduce error rate after rollback
    service_state["error_rate"] = max(0.01, service_state["error_rate"] / 2)
    
    return jsonify({
        "status": "rolled_back",
        "message": "Service rolled back successfully",
        "new_error_rate": service_state["error_rate"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# Simple control endpoints for testing
@app.route('/agent/set_status/<status>', methods=['POST'])
def set_status(status):
    """Set service status for testing (UP, DOWN, DEGRADED)"""
    valid_statuses = ["UP", "DOWN", "DEGRADED"]
    if status not in valid_statuses:
        return jsonify({"error": f"Status must be one of {valid_statuses}"}), 400
    
    service_state["status"] = status
    return jsonify({
        "status": "updated",
        "new_status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/agent/set_metric/<metric>/<value>', methods=['POST'])
def set_metric(metric, value):
    """Set specific metric for testing"""
    if metric not in service_state:
        return jsonify({"error": f"Metric {metric} not found"}), 404
    
    try:
        if metric in ["memory_usage", "cpu_usage"]:
            service_state[metric] = float(value)
        elif metric == "error_rate":
            service_state[metric] = float(value)
        elif metric == "latency":
            service_state[metric] = float(value)
        elif metric == "status":
            service_state[metric] = value
        else:
            return jsonify({"error": f"Cannot set metric {metric}"}), 400
            
        return jsonify({
            "status": "updated",
            "metric": metric,
            "new_value": service_state[metric],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except ValueError:
        return jsonify({"error": f"Invalid value for {metric}"}), 400

@app.route('/agent/status', methods=['GET'])
def get_agent_status():
    """Get current service state"""
    return jsonify({
        "service_state": service_state,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/agent/reset', methods=['POST'])
def reset_service():
    """Reset service to healthy state"""
    service_state.update({
        "status": "UP",
        "memory_usage": 50,
        "cpu_usage": 30,
        "latency": 100,
        "error_rate": 0.01,
        "requests_served": 0,
        "last_restart": datetime.now(timezone.utc).isoformat()
    })
    
    return jsonify({
        "status": "reset",
        "message": "Service reset to healthy state",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Basic Mock Service")
    print("=" * 50)
    print("📋 REQUIRED Endpoints for Agent Integration:")
    print("  GET  /health            - Health check (required)")
    print("  POST /agent/restart     - Restart service (required)")
    print()
    print("📋 OPTIONAL Endpoints (for advanced actions):")
    print("  POST /agent/clear_cache - Clear cache")
    print("  POST /agent/scale_up    - Scale up instances")
    print("  POST /agent/rollback    - Rollback version")
    print()
    print("📋 TESTING Endpoints:")
    print("  POST /agent/set_status/{status} - Set status (UP/DOWN/DEGRADED)")
    print("  POST /agent/set_metric/{metric}/{value} - Set specific metric")
    print("  GET  /agent/status      - Get current state")
    print("  POST /agent/reset       - Reset to healthy")
    print("=" * 50)
    print("🌐 Service running on: http://localhost:6000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=6000, debug=False)
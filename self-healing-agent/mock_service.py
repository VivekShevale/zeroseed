from flask import Flask, jsonify

app = Flask(__name__)

SERVICE_STATE = {"running": True}

@app.route("/agent/restart", methods=["POST"])
def restart_service():
    """Restart endpoint for agent"""
    try:
        # Try to parse JSON, but don't require it
        data = {}
        if request.is_json:
            data = request.get_json() or {}
        
        force = data.get("force", False)
        
        if not SERVICE_STATE["running"] and not force:
            return jsonify({"error": "Service is stopped"}), 400
        
        # Simulate restart
        SERVICE_STATE["running"] = True
        SERVICE_STATE["memory_usage"] = 30
        SERVICE_STATE["cpu_usage"] = 20
        SERVICE_STATE["error_rate"] = 0.01
        SERVICE_STATE["latency"] = 100
        
        # Clear simulated issues
        for issue in ISSUE_SIMULATION:
            ISSUE_SIMULATION[issue] = False
        
        logger.info("Service restarted by agent")
        
        return jsonify({
            "status": "restarted",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "memory_usage": SERVICE_STATE["memory_usage"],
                "cpu_usage": SERVICE_STATE["cpu_usage"]
            }
        })
        
    except Exception as e:
        logger.error(f"Error in restart: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    """Health endpoint"""
    if not SERVICE_STATE["running"] or ISSUE_SIMULATION["service_down"]:
        return jsonify({
            "status": "DOWN",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "issue": "service_down" if ISSUE_SIMULATION["service_down"] else "stopped"
            }
        }), 503
    
    health_status = "UP"
    details = {
        "memory_usage": SERVICE_STATE["memory_usage"],
        "cpu_usage": SERVICE_STATE["cpu_usage"],
        "latency": SERVICE_STATE["latency"],
        "error_rate": SERVICE_STATE["error_rate"]
    }
    
    # Check for other issues
    if SERVICE_STATE["memory_usage"] > 90:
        health_status = "DEGRADED"
        details["warning"] = "High memory usage"
    elif SERVICE_STATE["error_rate"] > 0.3:
        health_status = "DEGRADED"
        details["warning"] = "High error rate"
    elif SERVICE_STATE["latency"] > 1000:
        health_status = "DEGRADED"
        details["warning"] = "High latency"
    
    return jsonify({
        "status": health_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": SERVICE_STATE["version"],
        "details": details
    })

if __name__ == "__main__":
    app.run(port=6000, debug=True)

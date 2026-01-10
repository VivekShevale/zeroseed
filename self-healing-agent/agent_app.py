from flask import Flask, request, jsonify
import requests
import threading
import time
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ---------------- #

# Thresholds for detecting anomalies
THRESHOLDS = {
    "memory": 90,
    "latency": 1500,
    "error_rate": 0.3
}

# Customizable issue → action catalog
FIX_CATALOG = {
    "SERVICE_DOWN": {"action": "restart", "auto": True},
    "MEMORY_PRESSURE": {"action": "restart", "auto": True},
    "HIGH_LATENCY": {"action": "restart", "auto": True}
}

# ---------------- DATABASE ---------------- #

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["self_healing_agent"]
memory_col = db["agent_memory"]

# ---------------- SERVICES ---------------- #

SERVICES = [
    {
        "service_id": "payment-api",
        "service_url": "http://localhost:6000",
        "metrics_url": "http://localhost:6000/health"
    }
]

CHECK_INTERVAL = 10  # seconds

# ---------------- AGENT LOGIC ---------------- #

def detect_anomaly(metrics):
    if metrics["health"] == "DOWN":
        return "SERVICE_DOWN"
    if metrics.get("memory",0) > THRESHOLDS["memory"]:
        return "MEMORY_PRESSURE"
    if metrics.get("latency",0) > THRESHOLDS["latency"]:
        return "HIGH_LATENCY"
    return None

def decide(issue):
    fix = FIX_CATALOG.get(issue)
    if fix and fix["auto"]:
        return fix["action"]
    return None

def execute_action(action, service_url):
    if action == "restart":
        try:
            res = requests.post(f"{service_url}/agent/restart", timeout=3)
            if res.status_code == 200:
                print(f"⚙️ Action executed: {action} on {service_url}")
                return True
        except Exception as e:
            print("❌ Action failed:", e)
            return False
    return False

def evaluate(before_metrics, after_metrics):
    # simple evaluation logic: error_rate decreased
    return after_metrics.get("error_rate", 1) < before_metrics.get("error_rate", 1)

def store_memory(service_id, issue, action, success):
    memory_col.insert_one({
        "service_id": service_id,
        "issue": issue,
        "action": action,
        "success": success,
        "timestamp": datetime.utcnow()
    })

# ---------------- API FOR MANUAL METRICS ---------------- #

@app.route("/agent/metrics", methods=["POST"])
def ingest_metrics():
    data = request.json
    service_id = data["service_id"]
    service_url = data["service_url"]
    metrics = data["metrics"]

    print(f"\n📡 Metrics received from {service_id}: {metrics}")

    issue = detect_anomaly(metrics)
    if not issue:
        return jsonify({"status": "healthy"})

    action = decide(issue)
    if not action:
        return jsonify({"status": "alert_only", "issue": issue})

    success = execute_action(action, service_url)

    # simulate wait & re-evaluation
    time.sleep(2)

    # simulate updated metrics for demo
    after_metrics = metrics.copy()
    after_metrics["error_rate"] = 0.05

    resolved = evaluate(metrics, after_metrics)
    store_memory(service_id, issue, action, resolved)

    return jsonify({
        "issue": issue,
        "action": action,
        "resolved": resolved
    })

# ---------------- BACKGROUND MONITORING ---------------- #

def monitor_services():
    while True:
        for svc in SERVICES:
            try:
                res = requests.get(svc["metrics_url"], timeout=3)
                if res.status_code == 200:
                    metrics = {"health": "UP", "cpu": 70, "memory": 95, "latency": 2100, "error_rate": 0.4}
                else:
                    metrics = {"health": "DOWN", "cpu": 0, "memory": 0, "latency": 0, "error_rate": 1}

                issue = detect_anomaly(metrics)
                if issue:
                    action = decide(issue)
                    if action:
                        success = execute_action(action, svc["service_url"])
                        after_metrics = metrics.copy()
                        after_metrics["error_rate"] = 0.05
                        resolved = evaluate(metrics, after_metrics)
                        store_memory(svc["service_id"], issue, action, resolved)
            except Exception as e:
                print("❌ Error monitoring", svc["service_id"], e)

        time.sleep(CHECK_INTERVAL)

# Start background thread
threading.Thread(target=monitor_services, daemon=True).start()

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(port=5000, debug=True)

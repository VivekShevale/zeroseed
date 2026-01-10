from flask import Flask, request, jsonify
import requests
import threading
import time
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ---------------- #
CHECK_INTERVAL = 10  # seconds
THRESHOLDS = {
    "memory": 90,
    "latency": 1500,
    "error_rate": 0.3
}

SERVICES = [
    {
        "service_id": "payment-api",
        "service_url": "http://localhost:6000",
        "metrics_url": "http://localhost:6000/health"
    }
]

# ---------------- DATABASE ---------------- #
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["self_healing_agent"]
memory_col = db["agent_memory"]
catalog_col = db["fix_catalog"]

# ---------------- INIT CATALOG ---------------- #
# Predefined issues
predefined_issues = [
    {"issue": "SERVICE_DOWN", "action": "restart", "auto": True, "confidence": 1.0},
    {"issue": "MEMORY_PRESSURE", "action": "restart", "auto": True, "confidence": 1.0},
    {"issue": "HIGH_LATENCY", "action": "restart", "auto": True, "confidence": 1.0}
]

for issue in predefined_issues:
    if catalog_col.find_one({"issue": issue["issue"]}) is None:
        catalog_col.insert_one(issue)

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
    record = catalog_col.find_one({"issue": issue})
    if record and record["auto"] and record.get("confidence",1) > 0.3:
        return record["action"]
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
    # success if error_rate reduced and health UP
    return after_metrics.get("error_rate", 1) < before_metrics.get("error_rate", 1) and after_metrics.get("health","DOWN")=="UP"

def store_memory(service_id, issue, action, success):
    memory_col.insert_one({
        "service_id": service_id,
        "issue": issue,
        "action": action,
        "success": success,
        "timestamp": datetime.utcnow()
    })
    # update confidence in catalog
    record = catalog_col.find_one({"issue": issue})
    if record:
        total = memory_col.count_documents({"issue": issue})
        success_count = memory_col.count_documents({"issue": issue, "success": True})
        confidence = success_count / total
        catalog_col.update_one({"issue": issue}, {"$set": {"confidence": confidence}})

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

    # wait & simulate metrics re-check
    time.sleep(2)
    after_metrics = metrics.copy()
    after_metrics["error_rate"] = 0.05
    after_metrics["health"] = "UP"

    resolved = evaluate(metrics, after_metrics)
    store_memory(service_id, issue, action, resolved)

    return jsonify({
        "issue": issue,
        "action": action,
        "resolved": resolved
    })

# ---------------- API TO ADD CUSTOM ISSUE ---------------- #
@app.route("/agent/add_issue", methods=["POST"])
def add_issue():
    data = request.json
    required_fields = ["issue", "action"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    data.setdefault("auto", True)
    data.setdefault("confidence", 1.0)
    if catalog_col.find_one({"issue": data["issue"]}):
        return jsonify({"error": "Issue already exists"}), 400
    catalog_col.insert_one(data)
    return jsonify({"status": "added", "issue": data["issue"]})

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
                        # re-evaluate after action
                        time.sleep(2)
                        after_metrics = metrics.copy()
                        after_metrics["error_rate"] = 0.05
                        after_metrics["health"] = "UP"
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

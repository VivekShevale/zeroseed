"""
Self-Healing Web Infrastructure Agent
Autonomous monitoring and remediation system
"""
import os
import sys
import signal
import threading
import time
from datetime import datetime, timezone
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import requests

# Create Flask app
app = Flask(__name__)

# Configuration
CONFIG = {
    "MONGO_URI": "mongodb://localhost:27017/",
    "MONGO_DB": "self_healing_agent",
    "CHECK_INTERVAL": 10,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 2,
    "THRESHOLDS": {
        "memory": 90,
        "latency": 1500,
        "error_rate": 0.3,
        "cpu": 90,
        "response_time": 2000
    },
    "SERVICES": [
        {
            "service_id": "payment-api",
            "name": "Payment API",
            "service_url": "http://localhost:6000",
            "metrics_url": "http://localhost:6000/health",
            "health_endpoint": "/health",
            "restart_endpoint": "/agent/restart",
            "enabled": True,
            "tags": ["critical", "api"]
        }
    ],
    "LOG_LEVEL": "INFO",
    "SECRET_KEY": "dev-secret-key-change-in-production"
}

# Initialize MongoDB
def init_database():
    """Initialize MongoDB connection and collections"""
    try:
        mongo = MongoClient(
            CONFIG["MONGO_URI"], 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=3000
        )
        mongo.server_info()  # Test connection
        db = mongo[CONFIG["MONGO_DB"]]
        print("✅ Connected to MongoDB")
        
        # Initialize collections
        memory_col = db["agent_memory"]
        catalog_col = db["fix_catalog"]
        services_col = db["services"]
        incidents_col = db["incidents"]
        metrics_col = db["metrics_history"]
        
        # Drop existing incorrect indexes
        try:
            # Get existing indexes
            existing_indexes = catalog_col.index_information()
            
            # If there's an index on just 'issue', drop it
            if 'issue_1' in existing_indexes:
                print("⚠️ Dropping incorrect index on 'issue' field")
                catalog_col.drop_index('issue_1')
                
        except Exception as e:
            print(f"ℹ️ Index check: {e}")
        
        # Create correct indexes
        print("📊 Creating database indexes...")
        
        # Memory collection indexes
        memory_col.create_index([("timestamp", DESCENDING)])
        memory_col.create_index([("service_id", ASCENDING)])
        memory_col.create_index([("type", ASCENDING)])
        memory_col.create_index([("issue", ASCENDING)])
        
        # Catalog collection indexes - compound index on issue + action
        catalog_col.create_index([("issue", ASCENDING), ("action", ASCENDING)], unique=True)
        catalog_col.create_index([("confidence", DESCENDING)])
        catalog_col.create_index([("auto", ASCENDING)])
        
        # Services collection indexes
        services_col.create_index([("service_id", ASCENDING)], unique=True)
        services_col.create_index([("enabled", ASCENDING)])
        
        # Incidents collection indexes
        incidents_col.create_index([("timestamp", DESCENDING)])
        incidents_col.create_index([("service_id", ASCENDING)])
        incidents_col.create_index([("status", ASCENDING)])
        
        # Metrics collection indexes
        metrics_col.create_index([("timestamp", DESCENDING)])
        metrics_col.create_index([("service_id", ASCENDING)])
        
        print("✅ Database indexes created")
        
        # Initialize default catalog entries
        print("📝 Initializing default catalog...")
        
        default_catalog = [
            {
                "issue": "SERVICE_DOWN", 
                "action": "restart", 
                "auto": True, 
                "confidence": 1.0,
                "description": "Restart service when it's down",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "issue": "MEMORY_PRESSURE", 
                "action": "restart", 
                "auto": True, 
                "confidence": 0.9,
                "description": "Restart service when memory usage is high",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "issue": "MEMORY_PRESSURE", 
                "action": "scale_up", 
                "auto": True, 
                "confidence": 0.7,
                "description": "Scale up service instances for memory pressure",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "issue": "HIGH_LATENCY", 
                "action": "clear_cache", 
                "auto": True, 
                "confidence": 0.8,
                "description": "Clear cache to reduce latency",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "issue": "HIGH_ERROR_RATE", 
                "action": "rollback", 
                "auto": True, 
                "confidence": 0.6,
                "description": "Rollback to previous version for high error rates",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "issue": "HIGH_CPU", 
                "action": "scale_up", 
                "auto": True, 
                "confidence": 0.8,
                "description": "Scale up for high CPU usage",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        added_count = 0
        for entry in default_catalog:
            try:
                # Use upsert to insert or update if exists
                result = catalog_col.update_one(
                    {"issue": entry["issue"], "action": entry["action"]},
                    {"$setOnInsert": entry},
                    upsert=True
                )
                if result.upserted_id:
                    added_count += 1
            except Exception as e:
                print(f"⚠️ Error adding catalog entry {entry['issue']}:{entry['action']}: {e}")
        
        print(f"✅ Default catalog initialized ({added_count} entries added)")
        
        # Clear any old data if needed (for development)
        if os.environ.get("CLEAR_DATA", "false").lower() == "true":
            print("🧹 Clearing old data...")
            memory_col.delete_many({})
            incidents_col.delete_many({})
            metrics_col.delete_many({})
            print("✅ Old data cleared")
        
        return mongo, db
        
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        # Try to continue with existing connection
        try:
            mongo = MongoClient(CONFIG["MONGO_URI"])
            db = mongo[CONFIG["MONGO_DB"]]
            return mongo, db
        except:
            sys.exit(1)

# Initialize database
mongo, db = init_database()
memory_col = db["agent_memory"]
catalog_col = db["fix_catalog"]
services_col = db["services"]
incidents_col = db["incidents"]
metrics_col = db["metrics_history"]

# Agent state
agent_running = False
monitor_thread = None
agent_lock = threading.Lock()

# Helper functions
def get_current_time():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

def detect_anomaly(metrics):
    """Detect anomalies in metrics"""
    if not metrics:
        return "SERVICE_DOWN"
    
    if metrics.get("health") == "DOWN":
        return "SERVICE_DOWN"
    
    if metrics.get("memory", 0) > CONFIG["THRESHOLDS"]["memory"]:
        return "MEMORY_PRESSURE"
    
    if metrics.get("latency", 0) > CONFIG["THRESHOLDS"]["latency"]:
        return "HIGH_LATENCY"
    
    if metrics.get("cpu", 0) > CONFIG["THRESHOLDS"]["cpu"]:
        return "HIGH_CPU"
    
    if metrics.get("error_rate", 0) > CONFIG["THRESHOLDS"]["error_rate"]:
        return "HIGH_ERROR_RATE"
    
    return None

def decide_action(issue, service_id=None):
    """Decide which action to take for an issue"""
    try:
        # Get all auto-remediation actions for this issue, sorted by confidence
        records = list(catalog_col.find(
            {"issue": issue, "auto": True}
        ).sort("confidence", DESCENDING))
        
        if not records:
            print(f"⚠️ No auto-remediation actions found for {issue}")
            return None
        
        # Filter out actions with low confidence
        valid_records = [r for r in records if r.get("confidence", 0) > 0.3]
        
        if not valid_records:
            print(f"⚠️ No actions with sufficient confidence for {issue}")
            return None
        
        # Get the highest confidence action
        best_action = valid_records[0]
        
        if service_id:
            # Check if we've recently failed with this action
            one_hour_ago = get_current_time().replace(minute=0, second=0, microsecond=0)
            recent_failures = memory_col.count_documents({
                "service_id": service_id,
                "issue": issue,
                "action": best_action["action"],
                "success": False,
                "timestamp": {"$gte": one_hour_ago}
            })
            
            if recent_failures >= 2:  # If failed twice in last hour
                print(f"⚠️ Skipping {best_action['action']} due to recent failures")
                if len(valid_records) > 1:
                    best_action = valid_records[1]  # Try second best
        
        return best_action
        
    except Exception as e:
        print(f"❌ Error in decision engine: {e}")
        return None

def execute_action(action, service_url, service_id=None, issue=None):
    """Execute remediation action"""
    try:
        print(f"⚡ Executing action: {action} on {service_url}")
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Self-Healing-Agent/1.0',
            'Accept': 'application/json'
        }
        
        if action == "restart":
            response = requests.post(
                f"{service_url}/agent/restart", 
                json={},
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                print(f"✅ Restart successful for {service_id}")
                try:
                    return True, response.json()
                except:
                    return True, {"status": "restarted"}
            else:
                print(f"❌ Restart failed: {response.status_code}")
                return False, {"error": f"HTTP {response.status_code}"}
                
        elif action == "clear_cache":
            response = requests.post(
                f"{service_url}/agent/clear_cache", 
                json={},
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {"status": "cache_cleared"}
            else:
                return False, {"error": f"HTTP {response.status_code}"}
                
        elif action == "scale_up":
            # For demo purposes, we'll just log this
            print(f"📈 Simulating scale_up for {service_id}")
            return True, {"status": "scaled_up", "simulated": True}
            
        elif action == "rollback":
            # For demo purposes, we'll just log this
            print(f"↩️ Simulating rollback for {service_id}")
            return True, {"status": "rolled_back", "simulated": True}
            
        else:
            print(f"⚠️ Unknown action: {action}")
            return False, {"error": f"Unknown action: {action}"}
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout executing action {action}")
        return False, {"error": "Timeout"}
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error executing action {action}")
        return False, {"error": "Connection error"}
    except Exception as e:
        print(f"❌ Error executing action {action}: {e}")
        return False, {"error": str(e)}

def evaluate_action(before_metrics, after_metrics, issue):
    """Evaluate if action was successful"""
    if not before_metrics or not after_metrics:
        return False
    
    # If service was DOWN and now is UP, success
    if before_metrics.get("health") == "DOWN" and after_metrics.get("health") == "UP":
        return True
    
    # If service is still DOWN, failure
    if after_metrics.get("health") == "DOWN":
        return False
    
    # Issue-specific evaluation
    if issue == "MEMORY_PRESSURE":
        if before_metrics.get("memory") and after_metrics.get("memory"):
            return after_metrics["memory"] < before_metrics["memory"] * 0.9  # 10% reduction
    
    elif issue == "HIGH_LATENCY":
        if before_metrics.get("latency") and after_metrics.get("latency"):
            return after_metrics["latency"] < before_metrics["latency"] * 0.8  # 20% reduction
    
    elif issue == "HIGH_ERROR_RATE":
        if before_metrics.get("error_rate") and after_metrics.get("error_rate"):
            return after_metrics["error_rate"] < before_metrics["error_rate"] * 0.7  # 30% reduction
    
    elif issue == "HIGH_CPU":
        if before_metrics.get("cpu") and after_metrics.get("cpu"):
            return after_metrics["cpu"] < before_metrics["cpu"] * 0.8  # 20% reduction
    
    # Default: if health is UP, consider it a success
    return after_metrics.get("health") == "UP"

def update_confidence(issue, action, success):
    """Update confidence score for an action"""
    try:
        record = catalog_col.find_one({"issue": issue, "action": action})
        if not record:
            print(f"⚠️ No catalog record found for {issue}:{action}")
            return
        
        # Get historical data for this issue-action pair
        total_actions = memory_col.count_documents({
            "issue": issue,
            "action": action,
            "type": "action"
        })
        
        successful_actions = memory_col.count_documents({
            "issue": issue,
            "action": action,
            "type": "action",
            "success": True
        })
        
        # Calculate new confidence with smoothing
        if total_actions > 0:
            raw_confidence = successful_actions / total_actions
            old_confidence = record.get("confidence", 1.0)
            # Apply exponential smoothing (alpha = 0.3)
            new_confidence = 0.7 * old_confidence + 0.3 * raw_confidence
        else:
            new_confidence = record.get("confidence", 1.0)
        
        # Update catalog
        catalog_col.update_one(
            {"issue": issue, "action": action},
            {
                "$set": {
                    "confidence": round(new_confidence, 3),
                    "updated_at": get_current_time()
                }
            }
        )
        
        print(f"📈 Updated confidence for {issue}:{action} = {new_confidence:.3f}")
        
    except Exception as e:
        print(f"❌ Error updating confidence: {e}")

def collect_metrics(service):
    """Collect metrics from a service"""
    service_id = service["service_id"]
    metrics_url = service.get("metrics_url", service["service_url"] + "/health")
    
    try:
        start_time = time.time()
        response = requests.get(metrics_url, timeout=5)
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            metrics = {
                "health": data.get("status", "UP"),
                "latency": latency,
                "timestamp": get_current_time()
            }
            
            # Extract additional metrics
            details = data.get("details", {})
            if isinstance(details, dict):
                metrics.update({
                    "memory": details.get("memory_usage"),
                    "cpu": details.get("cpu_usage"),
                    "error_rate": details.get("error_rate"),
                    "response_time": details.get("response_time", latency)
                })
            
            return metrics
        else:
            return {
                "health": "DOWN",
                "latency": latency,
                "error_rate": 1.0,
                "timestamp": get_current_time(),
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "health": "DOWN",
            "latency": 5000,
            "error_rate": 1.0,
            "timestamp": get_current_time(),
            "error": "timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "health": "DOWN",
            "error_rate": 1.0,
            "timestamp": get_current_time(),
            "error": "connection_error"
        }
    except Exception as e:
        return {
            "health": "DOWN",
            "error_rate": 1.0,
            "timestamp": get_current_time(),
            "error": str(e)
        }

def monitor_loop():
    """Main monitoring loop"""
    print("🚀 Starting monitoring loop...")
    
    while agent_running:
        try:
            # Get all enabled services
            enabled_services = list(services_col.find({"enabled": True}))
            if not enabled_services:
                enabled_services = CONFIG["SERVICES"]
            
            for service in enabled_services:
                if not agent_running:
                    break
                    
                service_id = service["service_id"]
                service_name = service.get("name", service_id)
                
                print(f"📡 Monitoring {service_name}...")
                
                # Collect metrics
                metrics = collect_metrics(service)
                
                # Store metrics
                metrics_doc = {
                    "service_id": service_id,
                    "type": "metrics",
                    "metrics": metrics,
                    "timestamp": get_current_time()
                }
                metrics_col.insert_one(metrics_doc)
                
                # Detect anomalies
                issue = detect_anomaly(metrics)
                if issue:
                    print(f"🚨 Detected {issue} for {service_name}")
                    
                    # Create incident
                    incident_id = f"inc_{get_current_time().strftime('%Y%m%d_%H%M%S')}_{service_id}"
                    incident = {
                        "incident_id": incident_id,
                        "service_id": service_id,
                        "issue": issue,
                        "severity": "critical" if issue == "SERVICE_DOWN" else "high",
                        "status": "detected",
                        "detected_at": get_current_time(),
                        "metrics_snapshot": metrics
                    }
                    incidents_col.insert_one(incident)
                    
                    # Decide action
                    action_record = decide_action(issue, service_id)
                    if action_record:
                        action = action_record["action"]
                        print(f"🤔 Decision: {action} for {issue}")
                        
                        # Execute action
                        success, result = execute_action(
                            action, 
                            service["service_url"],
                            service_id,
                            issue
                        )
                        
                        # Wait a bit for action to take effect
                        print("⏳ Waiting for action to take effect...")
                        time.sleep(3)
                        
                        # Collect metrics after action
                        after_metrics = collect_metrics(service)
                        
                        # Evaluate success
                        resolved = evaluate_action(metrics, after_metrics, issue)
                        
                        # Store action memory
                        memory_doc = {
                            "service_id": service_id,
                            "type": "action",
                            "issue": issue,
                            "action": action,
                            "success": resolved,
                            "before_metrics": metrics,
                            "after_metrics": after_metrics,
                            "result": result,
                            "timestamp": get_current_time()
                        }
                        memory_col.insert_one(memory_doc)
                        
                        # Update incident
                        update_data = {
                            "status": "resolved" if resolved else "failed",
                            "updated_at": get_current_time()
                        }
                        if resolved:
                            update_data["resolved_at"] = get_current_time()
                        
                        incidents_col.update_one(
                            {"incident_id": incident_id},
                            {
                                "$set": update_data,
                                "$push": {
                                    "actions": {
                                        "action": action,
                                        "success": resolved,
                                        "timestamp": get_current_time(),
                                        "result": result
                                    }
                                }
                            }
                        )
                        
                        # Update confidence
                        update_confidence(issue, action, resolved)
                        
                        if resolved:
                            print(f"✅ Action {action} SUCCESSFUL for {service_name}")
                        else:
                            print(f"❌ Action {action} FAILED for {service_name}")
                    else:
                        print(f"⚠️ No action available for {issue} on {service_name}")
                
                # Small delay between services
                time.sleep(1)
            
            # Wait for next check interval
            print(f"⏱️ Waiting {CONFIG['CHECK_INTERVAL']} seconds before next check...")
            for _ in range(CONFIG["CHECK_INTERVAL"]):
                if not agent_running:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"⚠️ Error in monitoring loop: {e}")
            time.sleep(5)

def start_agent():
    """Start the agent"""
    global agent_running, monitor_thread
    
    with agent_lock:
        if agent_running:
            return {"status": "already_running", "message": "Agent is already running"}
        
        agent_running = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        print("🤖 Agent started successfully")
        return {"status": "started", "message": "Agent started successfully"}

def stop_agent():
    """Stop the agent"""
    global agent_running
    
    with agent_lock:
        if not agent_running:
            return {"status": "not_running", "message": "Agent is not running"}
        
        agent_running = False
        if monitor_thread:
            monitor_thread.join(timeout=5)
        
        print("🛑 Agent stopped successfully")
        return {"status": "stopped", "message": "Agent stopped successfully"}

# API Routes
@app.route('/')
def index():
    """Home page"""
    return '''
    <html>
        <head>
            <title>Self-Healing Agent</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                }
                header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                h1 {
                    color: #2c3e50;
                    font-size: 3rem;
                    margin-bottom: 10px;
                }
                .tagline {
                    color: #7f8c8d;
                    font-size: 1.2rem;
                    margin-bottom: 30px;
                }
                .status-badge {
                    display: inline-block;
                    padding: 10px 25px;
                    border-radius: 50px;
                    font-weight: bold;
                    font-size: 1.1rem;
                    margin: 20px 0;
                }
                .status-running {
                    background: #d4edda;
                    color: #155724;
                    border: 2px solid #c3e6cb;
                }
                .status-stopped {
                    background: #f8d7da;
                    color: #721c24;
                    border: 2px solid #f5c6cb;
                }
                .controls {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin: 30px 0;
                    flex-wrap: wrap;
                }
                .btn {
                    padding: 15px 30px;
                    border: none;
                    border-radius: 10px;
                    font-size: 1.1rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
                }
                .btn:active {
                    transform: translateY(-1px);
                }
                .btn-start {
                    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                    color: white;
                }
                .btn-stop {
                    background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
                    color: white;
                }
                .btn-refresh {
                    background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                    color: white;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 25px;
                    margin-top: 40px;
                }
                .card {
                    background: white;
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
                    border: 1px solid #e2e8f0;
                    transition: transform 0.3s ease;
                }
                .card:hover {
                    transform: translateY(-5px);
                }
                .card h3 {
                    color: #2d3748;
                    margin-top: 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin-top: 20px;
                }
                .stat-item {
                    text-align: center;
                    padding: 15px;
                    background: #f8fafc;
                    border-radius: 10px;
                }
                .stat-value {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #667eea;
                }
                .stat-label {
                    color: #718096;
                    font-size: 0.9rem;
                    margin-top: 5px;
                }
                .link-list {
                    list-style: none;
                    padding: 0;
                }
                .link-list li {
                    margin: 15px 0;
                }
                .link-list a {
                    color: #4299e1;
                    text-decoration: none;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px;
                    border-radius: 8px;
                    transition: background 0.3s;
                }
                .link-list a:hover {
                    background: #edf2f7;
                }
                footer {
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e2e8f0;
                    color: #718096;
                }
                @media (max-width: 768px) {
                    .container {
                        padding: 20px;
                    }
                    h1 {
                        font-size: 2rem;
                    }
                    .dashboard-grid {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🤖 Self-Healing Agent</h1>
                    <p class="tagline">Autonomous Monitoring & Remediation System</p>
                    <div id="agentStatus" class="status-badge status-stopped">Loading...</div>
                </header>

                <div class="controls">
                    <button class="btn btn-start" onclick="startAgent()">
                        <span>▶</span> Start Agent
                    </button>
                    <button class="btn btn-stop" onclick="stopAgent()">
                        <span>⏹</span> Stop Agent
                    </button>
                    <button class="btn btn-refresh" onclick="refreshStatus()">
                        <span>🔄</span> Refresh
                    </button>
                </div>

                <div class="dashboard-grid">
                    <div class="card">
                        <h3><span>📊</span> System Status</h3>
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-value" id="serviceCount">0</div>
                                <div class="stat-label">Services</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="actionCount">0</div>
                                <div class="stat-label">Actions</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="incidentCount">0</div>
                                <div class="stat-label">Incidents</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="successRate">0%</div>
                                <div class="stat-label">Success Rate</div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h3><span>🔗</span> Quick Links</h3>
                        <ul class="link-list">
                            <li><a href="/health" target="_blank"><span>❤️</span> Health Check</a></li>
                            <li><a href="/status" target="_blank"><span>📈</span> Agent Status</a></li>
                            <li><a href="/dashboard" target="_blank"><span>📱</span> Dashboard</a></li>
                            <li><a href="/api/services" target="_blank"><span>🖥️</span> Services API</a></li>
                            <li><a href="/api/catalog" target="_blank"><span>📚</span> Catalog API</a></li>
                            <li><a href="/api/actions" target="_blank"><span>📝</span> Actions API</a></li>
                        </ul>
                    </div>

                    <div class="card">
                        <h3><span>⚙️</span> Agent Control</h3>
                        <p>Use the buttons above to control the autonomous agent.</p>
                        <p>The agent will:</p>
                        <ul>
                            <li>Monitor service health every 10 seconds</li>
                            <li>Detect anomalies automatically</li>
                            <li>Execute remediation actions</li>
                            <li>Learn from outcomes</li>
                        </ul>
                    </div>

                    <div class="card">
                        <h3><span>📡</span> Current Services</h3>
                        <div id="serviceList">
                            <!-- Will be populated by JavaScript -->
                        </div>
                    </div>
                </div>

                <footer>
                    <p>Self-Healing Agent v1.0.0 | Autonomous Infrastructure Management</p>
                    <p>Last updated: <span id="lastUpdated">Never</span></p>
                </footer>
            </div>

            <script>
                async function updateStatus() {
                    try {
                        const response = await fetch('/status');
                        const data = await response.json();
                        
                        // Update agent status
                        const statusEl = document.getElementById('agentStatus');
                        statusEl.textContent = data.agent_running ? '🟢 AGENT RUNNING' : '🔴 AGENT STOPPED';
                        statusEl.className = data.agent_running ? 'status-badge status-running' : 'status-badge status-stopped';
                        
                        // Update stats
                        document.getElementById('serviceCount').textContent = data.services_monitored;
                        document.getElementById('actionCount').textContent = data.total_actions;
                        document.getElementById('incidentCount').textContent = data.active_incidents;
                        
                        // Calculate success rate
                        const successRate = data.total_actions > 0 
                            ? Math.round((data.successful_actions / data.total_actions) * 100)
                            : 0;
                        document.getElementById('successRate').textContent = successRate + '%';
                        
                        // Update last updated time
                        document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
                        
                        // Update service list
                        updateServiceList();
                        
                    } catch (error) {
                        console.error('Error updating status:', error);
                        document.getElementById('agentStatus').textContent = '❌ CONNECTION ERROR';
                        document.getElementById('agentStatus').className = 'status-badge status-stopped';
                    }
                }
                
                async function updateServiceList() {
                    try {
                        const response = await fetch('/api/services');
                        const data = await response.json();
                        
                        const serviceList = document.getElementById('serviceList');
                        serviceList.innerHTML = '';
                        
                        data.services.forEach(service => {
                            const serviceEl = document.createElement('div');
                            serviceEl.className = 'stat-item';
                            serviceEl.innerHTML = `
                                <div style="text-align: left;">
                                    <strong>${service.name || service.service_id}</strong><br>
                                    <small>${service.service_url}</small>
                                </div>
                            `;
                            serviceList.appendChild(serviceEl);
                        });
                        
                    } catch (error) {
                        console.error('Error updating service list:', error);
                    }
                }
                
                async function startAgent() {
                    try {
                        const response = await fetch('/agent/start', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                        const result = await response.json();
                        alert(result.message);
                        updateStatus();
                    } catch (error) {
                        alert('Error starting agent: ' + error.message);
                    }
                }
                
                async function stopAgent() {
                    try {
                        const response = await fetch('/agent/stop', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                        const result = await response.json();
                        alert(result.message);
                        updateStatus();
                    } catch (error) {
                        alert('Error stopping agent: ' + error.message);
                    }
                }
                
                function refreshStatus() {
                    updateStatus();
                    alert('Status refreshed!');
                }
                
                // Initial load
                updateStatus();
                // Auto-refresh every 5 seconds
                setInterval(updateStatus, 5000);
            </script>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        mongo.admin.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return jsonify({
        "status": "healthy",
        "timestamp": get_current_time().isoformat(),
        "database": db_status,
        "agent_running": agent_running,
        "version": "1.0.0",
        "uptime": time.time() - start_time if 'start_time' in globals() else 0
    })

@app.route('/status')
def status():
    """Agent status endpoint"""
    try:
        mongo.admin.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    services_count = len(CONFIG["SERVICES"])
    actions_count = memory_col.count_documents({"type": "action"})
    successful_actions = memory_col.count_documents({"type": "action", "success": True})
    
    # Get active incidents
    active_incidents = incidents_col.count_documents({"status": {"$ne": "resolved"}})
    
    # Get catalog count
    catalog_count = catalog_col.count_documents({})
    
    return jsonify({
        "agent_running": agent_running,
        "services_monitored": services_count,
        "total_actions": actions_count,
        "successful_actions": successful_actions,
        "active_incidents": active_incidents,
        "catalog_entries": catalog_count,
        "database": db_status,
        "timestamp": get_current_time().isoformat()
    })

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    # Get data for dashboard
    services = CONFIG["SERVICES"]
    
    # Get today's actions
    today = get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    recent_actions = list(memory_col.find({
        "timestamp": {"$gte": today},
        "type": "action"
    }).sort("timestamp", DESCENDING).limit(50))
    
    # Get catalog
    catalog = list(catalog_col.find({}, {"_id": 0}).sort("issue", ASCENDING))
    
    # Get active incidents
    active_incidents = list(incidents_col.find(
        {"status": {"$ne": "resolved"}},
        {"_id": 0}
    ).sort("detected_at", DESCENDING).limit(10))
    
    # Get service health
    for service in services:
        latest_metric = metrics_col.find_one(
            {
                "service_id": service["service_id"],
                "type": "metrics"
            },
            sort=[("timestamp", DESCENDING)]
        )
        
        if latest_metric:
            service["health"] = latest_metric.get("metrics", {}).get("health", "UNKNOWN")
            service["last_check"] = latest_metric.get("timestamp")
            service["metrics"] = latest_metric.get("metrics", {})
        else:
            service["health"] = "UNKNOWN"
            service["last_check"] = None
            service["metrics"] = {}
    
    # Get action statistics
    pipeline = [
        {"$match": {"type": "action"}},
        {"$group": {
            "_id": "$action",
            "total": {"$sum": 1},
            "successes": {"$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}}
        }},
        {"$project": {
            "action": "$_id",
            "total": 1,
            "successes": 1,
            "success_rate": {"$cond": [
                {"$eq": ["$total", 0]},
                0,
                {"$divide": ["$successes", "$total"]}
            ]}
        }},
        {"$sort": {"total": -1}}
    ]
    
    try:
        action_stats = list(memory_col.aggregate(pipeline))
    except:
        action_stats = []
    
    return jsonify({
        "services": services,
        "recent_actions": recent_actions,
        "catalog": catalog,
        "active_incidents": active_incidents,
        "action_stats": action_stats,
        "agent_running": agent_running,
        "timestamp": get_current_time().isoformat(),
        "summary": {
            "total_services": len(services),
            "total_actions": len(recent_actions),
            "total_incidents": len(active_incidents),
            "total_catalog_entries": len(catalog)
        }
    })

@app.route('/agent/start', methods=['POST'])
def api_start_agent():
    """Start agent API"""
    result = start_agent()
    return jsonify(result)

@app.route('/agent/stop', methods=['POST'])
def api_stop_agent():
    """Stop agent API"""
    result = stop_agent()
    return jsonify(result)

@app.route('/agent/metrics', methods=['POST'])
def ingest_metrics():
    """Ingest metrics from external services"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        service_id = data.get("service_id")
        metrics = data.get("metrics", {})
        
        if not service_id:
            return jsonify({"error": "Missing service_id"}), 400
        
        # Store metrics
        metrics_col.insert_one({
            "service_id": service_id,
            "type": "metrics",
            "metrics": metrics,
            "timestamp": get_current_time(),
            "source": "external"
        })
        
        # Detect anomalies
        issue = detect_anomaly(metrics)
        if issue:
            # Create incident
            incident_id = f"inc_ext_{get_current_time().strftime('%Y%m%d_%H%M%S')}_{service_id}"
            incident = {
                "incident_id": incident_id,
                "service_id": service_id,
                "issue": issue,
                "severity": "high" if issue == "SERVICE_DOWN" else "medium",
                "status": "detected",
                "detected_at": get_current_time(),
                "metrics_snapshot": metrics,
                "source": "external"
            }
            incidents_col.insert_one(incident)
            
            return jsonify({
                "status": "anomaly_detected",
                "issue": issue,
                "incident_id": incident_id,
                "message": "Anomaly detected, check catalog for actions"
            })
        
        return jsonify({
            "status": "metrics_received",
            "service_id": service_id,
            "timestamp": get_current_time().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/agent/add_issue', methods=['POST'])
def add_issue():
    """Add custom issue-action mapping"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required = ["issue", "action"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if already exists
        existing = catalog_col.find_one({
            "issue": data["issue"],
            "action": data["action"]
        })
        
        if existing:
            return jsonify({"error": "Issue-action mapping already exists"}), 400
        
        # Add to catalog
        entry = {
            "issue": data["issue"],
            "action": data["action"],
            "auto": data.get("auto", True),
            "confidence": data.get("confidence", 1.0),
            "description": data.get("description", ""),
            "parameters": data.get("parameters", {}),
            "created_at": get_current_time(),
            "updated_at": get_current_time()
        }
        
        catalog_col.insert_one(entry)
        
        return jsonify({
            "status": "added",
            "issue": data["issue"],
            "action": data["action"],
            "message": "Catalog entry added successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/services', methods=['GET'])
def api_services():
    """Get all services"""
    services = list(services_col.find({}, {"_id": 0}))
    if not services:
        services = CONFIG["SERVICES"]
    
    return jsonify({
        "services": services,
        "count": len(services)
    })

@app.route('/api/services', methods=['POST'])
def api_add_service():
    """Add a new service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required = ["service_id", "name", "service_url"]
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if already exists
        existing = services_col.find_one({"service_id": data["service_id"]})
        if existing:
            return jsonify({"error": "Service already exists"}), 400
        
        # Add service
        service = {
            "service_id": data["service_id"],
            "name": data["name"],
            "service_url": data["service_url"],
            "metrics_url": data.get("metrics_url", data["service_url"] + "/health"),
            "health_endpoint": data.get("health_endpoint", "/health"),
            "restart_endpoint": data.get("restart_endpoint", "/agent/restart"),
            "enabled": data.get("enabled", True),
            "tags": data.get("tags", []),
            "custom_thresholds": data.get("custom_thresholds", {}),
            "created_at": get_current_time(),
            "updated_at": get_current_time()
        }
        
        services_col.insert_one(service)
        
        return jsonify({
            "status": "added",
            "service_id": data["service_id"],
            "message": "Service added successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/catalog', methods=['GET'])
def api_catalog():
    """Get all catalog entries"""
    catalog = list(catalog_col.find({}, {"_id": 0}).sort("issue", ASCENDING))
    return jsonify({
        "catalog": catalog,
        "count": len(catalog)
    })

@app.route('/api/actions', methods=['GET'])
def api_actions():
    """Get action history"""
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    actions = list(memory_col.find(
        {"type": "action"},
        {"_id": 0}
    ).sort("timestamp", DESCENDING).skip(offset).limit(limit))
    
    total = memory_col.count_documents({"type": "action"})
    
    return jsonify({
        "actions": actions,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(actions) < total
        }
    })

@app.route('/api/incidents', methods=['GET'])
def api_incidents():
    """Get incidents"""
    limit = min(int(request.args.get('limit', 50)), 500)
    offset = int(request.args.get('offset', 0))
    status_filter = request.args.get('status')
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    incidents = list(incidents_col.find(
        query,
        {"_id": 0}
    ).sort("detected_at", DESCENDING).skip(offset).limit(limit))
    
    total = incidents_col.count_documents(query)
    
    return jsonify({
        "incidents": incidents,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(incidents) < total
        }
    })

@app.route('/api/metrics/<service_id>', methods=['GET'])
def api_service_metrics(service_id):
    """Get metrics for a service"""
    hours = min(int(request.args.get('hours', 24)), 168)  # Max 7 days
    limit = min(int(request.args.get('limit', 100)), 1000)
    
    cutoff = get_current_time()
    if hours > 0:
        cutoff = get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    
    metrics = list(metrics_col.find(
        {
            "service_id": service_id,
            "type": "metrics",
            "timestamp": {"$gte": cutoff}
        },
        {"_id": 0}
    ).sort("timestamp", DESCENDING).limit(limit))
    
    return jsonify({
        "service_id": service_id,
        "metrics": metrics,
        "count": len(metrics),
        "time_range_hours": hours
    })

@app.route('/api/clear', methods=['POST'])
def api_clear_data():
    """Clear all data (for testing)"""
    try:
        # Clear collections
        memory_col.delete_many({})
        incidents_col.delete_many({})
        metrics_col.delete_many({})
        
        # Reset confidence scores
        catalog_col.update_many(
            {},
            {"$set": {"confidence": 1.0, "updated_at": get_current_time()}}
        )
        
        return jsonify({
            "status": "cleared",
            "message": "All data cleared successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutdown signal received")
    stop_agent()
    mongo.close()
    print("👋 Goodbye!")
    sys.exit(0)

if __name__ == '__main__':
    # Record start time
    start_time = time.time()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 Self-Healing Agent - Production Ready")
    print("=" * 60)
    print(f"MongoDB: {CONFIG['MONGO_URI']}")
    print(f"Database: {CONFIG['MONGO_DB']}")
    print(f"Check Interval: {CONFIG['CHECK_INTERVAL']} seconds")
    print(f"Services: {len(CONFIG['SERVICES'])}")
    print("=" * 60)
    print("Starting Flask server on http://localhost:5000")
    print("\n📋 Available Endpoints:")
    print("  • GET  /              - Home page with controls")
    print("  • GET  /health        - Health check")
    print("  • GET  /status        - Agent status")
    print("  • GET  /dashboard     - Dashboard (JSON)")
    print("  • POST /agent/start   - Start agent")
    print("  • POST /agent/stop    - Stop agent")
    print("  • POST /agent/metrics - Ingest external metrics")
    print("  • POST /agent/add_issue - Add custom issue-action")
    print("  • GET  /api/services  - List services")
    print("  • POST /api/services  - Add new service")
    print("  • GET  /api/catalog   - List catalog entries")
    print("  • GET  /api/actions   - Action history")
    print("  • GET  /api/incidents - Incident history")
    print("  • POST /api/clear     - Clear data (testing)")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Start agent automatically
    start_agent()
    
    # Run Flask app
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False, 
        use_reloader=False
    )
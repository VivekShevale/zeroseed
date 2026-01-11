"""
Basic usage example for Autonomous Recovery Agent
"""
from flask import Flask, jsonify
from pymongo import MongoClient
from autonomous_recovery_agent import AutonomousRecoveryAgent, AgentConfig

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection URL
MONGODB_URL = "mongodb://localhost:27017/mydatabase"

# Initialize Autonomous Recovery Agent
agent = AutonomousRecoveryAgent(
    flask_app=app,
    mongodb_url=MONGODB_URL,
    config=AgentConfig(
        check_interval=30,
        max_service_memory_mb=1024,
        max_service_cpu_percent=90,
        max_db_connection_time_ms=200,
        auto_recovery=True,
        enable_web_ui=True,
        web_ui_port=8081
    )
)

# Start the agent (this enables automatic recovery)
agent.start()

# Create MongoDB client (automatically patched for recovery)
client = MongoClient(MONGODB_URL)
db = client.mydatabase

# Your existing Flask routes (no changes needed!)
@app.route('/api/users')
def get_users():
    """Get all users - automatically retries if DB fails"""
    users = list(db.users.find({}, {'_id': 0}).limit(50))
    return jsonify({"users": users})

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create product - automatically recovers on failure"""
    product_data = request.json
    result = db.products.insert_one(product_data)
    return jsonify({"product_id": str(result.inserted_id)})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "running",
        "recovery_agent": "active"
    })

if __name__ == '__main__':
    print("🚀 Starting Flask app with Autonomous Recovery...")
    print("📊 Web Dashboard: http://localhost:8081")
    print("🩺 Health Check: http://localhost:5000/health")
    print("💡 Try stopping MongoDB to see auto-recovery in action!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
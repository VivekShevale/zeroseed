"""
Complete example: Flask + MongoDB app with Autonomous Recovery Agent
"""
from flask import Flask, jsonify, request
from pymongo import MongoClient
from autonomous_recovery import AutonomousRecoveryAgent, AgentConfig

# Initialize Flask app
app = Flask(__name__)

# Configuration
MONGODB_URL = "mongodb://localhost:27017/ecommerce_demo"

# Initialize Autonomous Recovery Agent
agent = AutonomousRecoveryAgent(
    flask_app=app,
    mongodb_url=MONGODB_URL,
    config=AgentConfig(
        check_interval=30,
        max_service_memory_mb=1024,
        max_service_cpu_percent=90,
        max_db_connection_time_ms=200,
        max_db_query_time_ms=1000,
        auto_recovery=True,
        enable_web_ui=True,
        web_ui_port=8081
    )
)

# Start the agent
agent.start()

# MongoDB client (automatically patched for recovery)
client = MongoClient(MONGODB_URL)
db = client.ecommerce_demo

# Create collections if they don't exist
if "products" not in db.list_collection_names():
    db.create_collection("products")
if "orders" not in db.list_collection_names():
    db.create_collection("orders")

# Sample data
sample_products = [
    {"name": "Laptop", "price": 999.99, "stock": 50},
    {"name": "Mouse", "price": 29.99, "stock": 200},
    {"name": "Keyboard", "price": 79.99, "stock": 150},
]

# Insert sample data if collection is empty
if db.products.count_documents({}) == 0:
    db.products.insert_many(sample_products)

# API Routes (all automatically protected by recovery agent)
@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all products - auto-retry on DB failure"""
    products = list(db.products.find({}, {"_id": 0}).limit(50))
    return jsonify({"products": products})

@app.route("/api/products", methods=["POST"])
def create_product():
    """Create a product - auto-recover on failure"""
    product_data = request.json
    if not product_data:
        return jsonify({"error": "No data provided"}), 400
    
    result = db.products.insert_one(product_data)
    return jsonify({
        "success": True,
        "product_id": str(result.inserted_id),
        "message": "Product created"
    })

@app.route("/api/orders", methods=["POST"])
def create_order():
    """Create an order - protected by recovery agent"""
    order_data = request.json
    if not order_data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate product exists and has stock
    product = db.products.find_one({"name": order_data.get("product_name")})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product.get("stock", 0) <= 0:
        return jsonify({"error": "Product out of stock"}), 400
    
    # Create order
    order = {
        "product_name": order_data["product_name"],
        "quantity": order_data.get("quantity", 1),
        "total_price": product["price"] * order_data.get("quantity", 1),
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = db.orders.insert_one(order)
    
    # Update stock
    db.products.update_one(
        {"name": order_data["product_name"]},
        {"$inc": {"stock": -order_data.get("quantity", 1)}}
    )
    
    return jsonify({
        "success": True,
        "order_id": str(result.inserted_id),
        "message": "Order created successfully"
    })

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        # These operations are automatically protected
        product_count = db.products.count_documents({})
        order_count = db.orders.count_documents({})
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "stats": {
                "products": product_count,
                "orders": order_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "database": "error",
            "error": str(e)
        }), 500

@app.route("/")
def home():
    """Home page with instructions"""
    return """
    <h1>E-commerce API with Autonomous Recovery</h1>
    <p>This application is protected by the Autonomous Recovery Agent.</p>
    <p>Endpoints:</p>
    <ul>
        <li><a href="/api/products">GET /api/products</a> - List products</li>
        <li>POST /api/products - Create product (send JSON)</li>
        <li>POST /api/orders - Create order (send JSON)</li>
        <li><a href="/api/health">GET /api/health</a> - Health check</li>
        <li><a href="/health">GET /health</a> - System health</li>
        <li><a href="http://localhost:8081" target="_blank">Recovery Dashboard</a></li>
    </ul>
    <p>Try stopping MongoDB to see automatic recovery in action!</p>
    """

if __name__ == "__main__":
    print("Starting E-commerce API with Autonomous Recovery Agent...")
    print("Main application: http://localhost:5000")
    print("Recovery dashboard: http://localhost:8081")
    print("\nTry these commands to test recovery:")
    print("1. Stop MongoDB: sudo systemctl stop mongod")
    print("2. Make API requests - they'll auto-retry")
    print("3. Start MongoDB: sudo systemctl start mongod")
    print("4. Watch automatic recovery in dashboard")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
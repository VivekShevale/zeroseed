from flask import Flask, jsonify

app = Flask(__name__)

SERVICE_STATE = {"running": True}

@app.route("/agent/restart", methods=["POST"])
def restart_service():
    SERVICE_STATE["running"] = True
    print("🔁 Service restarted by agent")
    return jsonify({"status": "restarted"})

@app.route("/health")
def health():
    if SERVICE_STATE["running"]:
        return jsonify({"status": "UP"})
    return jsonify({"status": "DOWN"}), 500

if __name__ == "__main__":
    app.run(port=6000, debug=True)
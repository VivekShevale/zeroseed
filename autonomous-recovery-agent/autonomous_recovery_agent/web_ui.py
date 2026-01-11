"""
Web UI dashboard for monitoring and control
"""

from flask import Flask, render_template_string
import threading
import logging
import os


# HTML template for dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Recovery Agent - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; 
               background: #0f172a; color: #f8fafc; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; }
        h1 { font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(90deg, #6366f1, #8b5cf6); 
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.1em; color: #94a3b8; margin-bottom: 30px; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 25px; border: 1px solid #334155; }
        .card h2 { margin-bottom: 15px; font-size: 1.3em; color: #e2e8f0; }
        .status { display: flex; align-items: center; margin-bottom: 10px; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }
        .status-healthy { background: #10b981; box-shadow: 0 0 10px #10b981; }
        .status-degraded { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
        .status-unhealthy { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
        .metric { margin: 15px 0; }
        .metric label { display: block; font-size: 0.9em; color: #94a3b8; margin-bottom: 5px; }
        .metric value { font-size: 1.4em; font-weight: bold; color: #e2e8f0; }
        .actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
        button { padding: 10px 20px; border: none; border-radius: 8px; background: #4f46e5; color: white; 
                 cursor: pointer; transition: all 0.3s; font-weight: 600; }
        button:hover { background: #4338ca; transform: translateY(-2px); }
        button.secondary { background: #475569; }
        button.secondary:hover { background: #334155; }
        .history { max-height: 300px; overflow-y: auto; margin-top: 15px; }
        .history-item { padding: 12px; border-bottom: 1px solid #334155; }
        .history-time { font-size: 0.8em; color: #94a3b8; }
        .history-action { font-weight: 600; margin-top: 5px; }
        .history-success { color: #10b981; }
        .history-failed { color: #ef4444; }
        .loading { text-align: center; padding: 20px; color: #94a3b8; }
        .error { color: #ef4444; padding: 10px; background: #450a0a; border-radius: 6px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Autonomous Recovery Agent</h1>
            <p class="subtitle">Self-healing monitoring dashboard for your application</p>
        </header>
        
        <div class="dashboard">
            <!-- Service Health -->
            <div class="card">
                <h2>📊 Service Health</h2>
                <div id="service-status">
                    <div class="loading">Loading service health...</div>
                </div>
                <div id="service-metrics"></div>
            </div>
            
            <!-- Database Health -->
            <div class="card">
                <h2>🗄️ Database Health</h2>
                <div id="database-status">
                    <div class="loading">Loading database health...</div>
                </div>
                <div id="database-metrics"></div>
            </div>
            
            <!-- Quick Actions -->
            <div class="card">
                <h2>⚡ Quick Actions</h2>
                <div class="actions">
                    <button onclick="triggerRecovery('service')">🔄 Recover Service</button>
                    <button onclick="triggerRecovery('database')">🔄 Recover Database</button>
                    <button onclick="refreshData()" class="secondary">🔄 Refresh</button>
                </div>
                <div id="action-result" style="margin-top: 15px;"></div>
            </div>
            
            <!-- Recovery History -->
            <div class="card">
                <h2>📜 Recovery History</h2>
                <div id="recovery-history" class="history">
                    <div class="loading">Loading history...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        # In the DASHBOARD_HTML JavaScript section, update the fetch URLs:
async function fetchData() {
    try {
        const [statusRes, healthRes, historyRes] = await Promise.all([
            fetch('/api/status').catch(e => ({ok: false, error: e})),
            fetch('/api/health').catch(e => ({ok: false, error: e})),
            fetch('/api/recovery/history').catch(e => ({ok: false, error: e}))
        ]);
        
        // Change to use your Flask app endpoints
        const [flaskHealthRes, recoveryStatusRes] = await Promise.all([
            fetch('/health').catch(e => ({ok: false, error: e})),
            fetch('/recovery/status').catch(e => ({ok: false, error: e}))
        ]);
        
        const statusData = recoveryStatusRes.ok ? await recoveryStatusRes.json() : {error: 'Failed to fetch status'};
        const healthData = flaskHealthRes.ok ? await flaskHealthRes.json() : {error: 'Failed to fetch health'};
        const historyData = historyRes.ok ? await historyRes.json() : {error: 'Failed to fetch history'};
        
        updateDashboard(statusData, healthData, historyData);
    } catch (error) {
        console.error('Error fetching data:', error);
        showError('Failed to fetch data. Please check if the agent is running.');
    }
}
        
        function updateDashboard(status, health, history) {
            // Update service health
            const serviceStatus = document.getElementById('service-status');
            const serviceMetrics = document.getElementById('service-metrics');
            
            if (health.error) {
                serviceStatus.innerHTML = `<div class="error">${health.error}</div>`;
                serviceMetrics.innerHTML = '';
            } else if (health.health?.service) {
                const s = health.health.service;
                const statusClass = s.status || 'unknown';
                serviceStatus.innerHTML = `
                    <div class="status">
                        <div class="status-indicator status-${statusClass}"></div>
                        <span style="font-weight: bold; font-size: 1.1em;">${statusClass.toUpperCase()}</span>
                    </div>
                    ${s.error_message ? `<div class="error" style="margin-top: 10px;">${s.error_message}</div>` : ''}
                `;
                
                if (s.metrics) {
                    serviceMetrics.innerHTML = `
                        <div class="metric">
                            <label>🖥️ CPU Usage</label>
                            <value>${s.metrics.cpu_percent?.toFixed(1) || 'N/A'}%</value>
                        </div>
                        <div class="metric">
                            <label>💾 Memory Usage</label>
                            <value>${s.metrics.memory_mb?.toFixed(1) || 'N/A'} MB</value>
                        </div>
                    `;
                }
            }
            
            // Update database health
            const dbStatus = document.getElementById('database-status');
            const dbMetrics = document.getElementById('database-metrics');
            
            if (health.error) {
                dbStatus.innerHTML = `<div class="error">${health.error}</div>`;
                dbMetrics.innerHTML = '';
            } else if (health.health?.database) {
                const d = health.health.database;
                const statusClass = d.status || 'unknown';
                dbStatus.innerHTML = `
                    <div class="status">
                        <div class="status-indicator status-${statusClass}"></div>
                        <span style="font-weight: bold; font-size: 1.1em;">${statusClass.toUpperCase()}</span>
                    </div>
                    ${d.error_message ? `<div class="error" style="margin-top: 10px;">${d.error_message}</div>` : ''}
                `;
                
                if (d.metrics) {
                    dbMetrics.innerHTML = `
                        <div class="metric">
                            <label>⚡ Connection Time</label>
                            <value>${d.metrics.connection_time_ms?.toFixed(1) || 'N/A'} ms</value>
                        </div>
                        <div class="metric">
                            <label>🔗 Active Connections</label>
                            <value>${d.metrics.active_connections || 'N/A'}</value>
                        </div>
                    `;
                }
            }
            
            // Update recovery history
            const historyEl = document.getElementById('recovery-history');
            if (history.error) {
                historyEl.innerHTML = `<div class="error">${history.error}</div>`;
            } else if (history.history?.length > 0) {
                historyEl.innerHTML = history.history.slice(-10).reverse().map(item => `
                    <div class="history-item">
                        <div class="history-time">${new Date(item.timestamp * 1000).toLocaleString()}</div>
                        <div class="history-action ${item.success ? 'history-success' : 'history-failed'}">
                            ${item.action}: ${item.message}
                        </div>
                    </div>
                `).join('');
            } else {
                historyEl.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 20px;">No recovery history yet</div>';
            }
        }
        
        async function triggerRecovery(component) {
            if (!confirm(`Are you sure you want to trigger recovery for ${component}?`)) return;
            
            const resultEl = document.getElementById('action-result');
            resultEl.innerHTML = '<div style="color: #f59e0b;">Triggering recovery...</div>';
            
            try {
                const res = await fetch('/api/recovery/trigger', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        component: component,
                        reason: 'Manual trigger from dashboard'
                    })
                });
                
                const data = await res.json();
                if (data.status === 'ok') {
                    resultEl.innerHTML = `<div style="color: #10b981;">✅ ${data.result?.message || 'Recovery triggered successfully'}</div>`;
                } else {
                    resultEl.innerHTML = `<div class="error">❌ ${data.error || 'Failed to trigger recovery'}</div>`;
                }
                
                // Refresh data after recovery
                setTimeout(refreshData, 2000);
            } catch (error) {
                resultEl.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
            }
        }
        
        function refreshData() {
            const resultEl = document.getElementById('action-result');
            resultEl.innerHTML = '<div style="color: #f59e0b;">Refreshing data...</div>';
            fetchData();
            setTimeout(() => {
                resultEl.innerHTML = '<div style="color: #10b981;">✅ Data refreshed</div>';
                setTimeout(() => resultEl.innerHTML = '', 2000);
            }, 1000);
        }
        
        function showError(message) {
            const container = document.querySelector('.container');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.style.margin = '20px 0';
            errorDiv.innerHTML = `❌ ${message}`;
            container.insertBefore(errorDiv, container.firstChild);
        }
        
        // Initial load
        fetchData();
        
        // Auto-refresh every 10 seconds
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
"""


def create_web_ui(agent=None, host="0.0.0.0", port=8081):
    """Create and start Web UI"""

    app = Flask(__name__)

    # Store agent reference
    app.agent = agent

    @app.route("/")
    def index():
        """Dashboard home page"""
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/status")
    def api_status():
        """Get agent status"""
        if app.agent:
            try:
                status = app.agent.get_status()
                return {"status": "ok", "agent": status}
            except Exception as e:
                return {"status": "error", "error": str(e)}, 500
        else:
            return {"status": "error", "error": "Agent not connected"}, 500

    @app.route("/api/health")
    def api_health():
        """Get health information"""
        health_data = {}

        if app.agent:
            if app.agent.service_monitor:
                health_data["service"] = app.agent.service_monitor.check_health()
            if app.agent.database_monitor:
                health_data["database"] = app.agent.database_monitor.check_health()

        return {"status": "ok", "health": health_data}

    @app.route("/api/recovery/history")
    def api_recovery_history():
        """Get recovery history"""
        if app.agent and app.agent.recovery_engine:
            from .recovery.engine import RecoveryEngine

            if isinstance(app.agent.recovery_engine, RecoveryEngine):
                history = app.agent.recovery_engine.get_recovery_history(limit=20)
                return {"status": "ok", "history": history}
        return {"status": "ok", "history": []}

    @app.route("/api/recovery/trigger", methods=["POST"])
    def api_trigger_recovery():
        """Trigger recovery manually"""
        if not app.agent:
            return {"status": "error", "error": "Agent not connected"}, 500

        import json

        data = json.loads(request.data) if request.data else {}
        component = data.get("component", "service")
        reason = data.get("reason", "Manual trigger")

        try:
            result = app.agent.trigger_recovery(component, reason)
            return {
                "status": "ok" if result.get("success") else "error",
                "result": result,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}, 500

    # Start the Web UI server
    def run_server():
        app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)

    return run_server


def start_web_ui(host="0.0.0.0", port=8081, agent=None):
    """Start Web UI in a separate thread"""
    run_server = create_web_ui(agent, host, port)

    thread = threading.Thread(target=run_server, daemon=True, name="RecoveryAgentWebUI")
    thread.start()

    logging.getLogger(__name__).info(f"Web UI started on http://{host}:{port}")
    return thread

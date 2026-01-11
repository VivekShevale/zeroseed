Collecting workspace information# Autonomous Recovery Agent 🛡️

A comprehensive autonomous monitoring and recovery system for Flask + MongoDB applications. Automatically detects and recovers from service crashes, database failures, and resource exhaustion without human intervention.

## 📋 Table of Contents

- Overview
- Features
- Architecture
- Quick Start
- Installation
- Configuration
- Usage
- API Documentation
- Components
- Dashboard
- Troubleshooting
- Development
- Contributing

## 🎯 Overview

The Autonomous Recovery Agent is a self-healing infrastructure management system designed specifically for Flask + MongoDB applications. It continuously monitors service health and database connectivity, automatically detects failures, and executes intelligent recovery actions to maintain high availability.

**Key Capabilities:**
- ✅ Automatic service restart on crashes
- ✅ Database connection recovery and failover
- ✅ Real-time resource monitoring (CPU, memory, disk)
- ✅ Intelligent traffic throttling during overload
- ✅ Maintenance mode management
- ✅ Configuration hot-reload with file watching
- ✅ Web-based monitoring dashboard
- ✅ RESTful API for programmatic control
- ✅ Zero-configuration deployment

## ✨ Features

### Core Monitoring
- **Service Health Checks** - Continuous Flask process monitoring
- **Database Monitoring** - MongoDB connection health and performance tracking
- **Disk Usage Monitoring** - Automatic cleanup of old logs and temporary files
- **Traffic Analysis** - Request rate monitoring and throttling

### Automatic Recovery
- **Service Restart** - Automatically restart failed Flask services
- **Database Recovery** - Reconnect to MongoDB with exponential backoff
- **Resource Cleanup** - Free disk space by removing old files
- **Graceful Degradation** - Traffic throttling during high load

### Management Features
- **Maintenance Mode** - Schedule maintenance windows with graceful transitions
- **Configuration Management** - Hot-reload YAML/JSON configurations
- **Web UI Dashboard** - Real-time monitoring and manual controls
- **REST API** - Full programmatic control
- **CLI Tools** - Command-line interface for manual operations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Autonomous Recovery Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Service      │  │ Database     │  │ Disk & Traffic   │  │
│  │ Monitor      │  │ Monitor      │  │ Monitor          │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                    │             │
│         └─────────────────┼────────────────────┘             │
│                          │                                   │
│                    ┌─────▼──────┐                            │
│                    │ Recovery   │                            │
│                    │ Engine     │                            │
│                    └─────┬──────┘                            │
│                          │                                   │
│         ┌────────────────┼────────────────┐                  │
│         │                │                │                  │
│    ┌────▼────┐    ┌─────▼─────┐    ┌────▼──────┐           │
│    │ Restart │    │ Throttle  │    │ Maintenance
│    │ Service │    │ Traffic   │    │ Mode       │           │
│    └─────────┘    └───────────┘    └───────────┘           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Configuration Manager (Hot-Reload)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                          │
    ┌────▼──────┐          ┌───────▼────┐
    │ Flask App │          │ Web UI / API│
    └───────────┘          └────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd autonomous-recovery-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup MongoDB

```bash
# Option A: Local installation
# macOS
brew install mongodb-community
brew services start mongodb-community

# Ubuntu
sudo apt-get install mongodb
sudo systemctl start mongodb

# Option B: Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Configure Environment

Create `.env` file in the project root:

```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development

# MongoDB
MONGODB_URL=mongodb://localhost:27017/recovery_test

# Agent Configuration
CHECK_INTERVAL=30
ENABLE_WEB_UI=true
WEB_UI_PORT=8081

# Service Configuration
MAX_SERVICE_MEMORY_MB=1024
MAX_SERVICE_CPU_PERCENT=90

# Database Configuration
MAX_DB_CONNECTION_TIME_MS=200
MONGODB_RECOVERY_TIMEOUT=30

# Disk Configuration
DISK_CLEANUP_THRESHOLD=0.80
DISK_CRITICAL_THRESHOLD=0.95
MAX_LOG_AGE_DAYS=7
MAX_TEMP_AGE_HOURS=24

# Traffic Configuration
DEFAULT_RPS=100
OVERLOAD_THRESHOLD=0.8
```

### 4. Basic Usage

```python
from flask import Flask
from autonomous_recovery_agent import AutonomousRecoveryAgent, AgentConfig

# Initialize Flask app
app = Flask(__name__)

# Create agent with configuration
agent = AutonomousRecoveryAgent(
    flask_app=app,
    mongodb_url="mongodb://localhost:27017/myapp",
    config=AgentConfig(
        check_interval=30,
        auto_recovery=True,
        enable_web_ui=True,
        web_ui_port=8081
    )
)

# Start the agent
agent.start()

# Your Flask routes work as normal
@app.route('/api/data')
def get_data():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run()
```

### 5. Access Dashboard

Navigate to: **http://localhost:8081**

## 📦 Installation

### Requirements

- Python 3.8+
- MongoDB 4.0+
- pip (Python package manager)

### Install Package

```bash
# From source
pip install -e .

# Or install directly
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check if agent can be imported
python -c "from autonomous_recovery_agent import AutonomousRecoveryAgent; print('✓ Installation successful')"

# Check version
python -c "from autonomous_recovery_agent import __version__; print(__version__)"
```

## ⚙️ Configuration

### AgentConfig Options

```python
@dataclass
class AgentConfig:
    # Monitoring
    check_interval: int = 30                          # Health check interval (seconds)
    max_service_memory_mb: int = 1024                 # Memory threshold
    max_service_cpu_percent: int = 90                 # CPU threshold
    max_db_connection_time_ms: int = 200              # Database connection timeout
    
    # Recovery
    auto_recovery: bool = True                        # Enable automatic recovery
    recovery_cooldown_seconds: int = 60               # Cooldown between recovery attempts
    max_recovery_attempts: int = 3                    # Max attempts per incident
    
    # Disk Management
    disk_cleanup_threshold: float = 0.80              # Disk usage threshold (0-1)
    disk_critical_threshold: float = 0.95             # Critical threshold
    max_log_age_days: int = 7                         # Log retention days
    max_temp_age_hours: int = 24                      # Temp file age threshold
    
    # Maintenance
    maintenance_mode: bool = True                     # Enable maintenance mode
    maintenance_status_file: str = "maintenance_status.json"
    
    # Traffic Throttling
    traffic_throttling: bool = True                   # Enable traffic throttling
    default_rps: int = 100                            # Default requests per second
    overload_threshold: float = 0.8                   # Throttle threshold
    recovery_threshold: float = 0.5                   # Recovery threshold
    
    # Web UI
    enable_web_ui: bool = True                        # Enable dashboard
    web_ui_port: int = 8081                           # Dashboard port
    
    # API
    enable_api: bool = True                           # Enable REST API
```

### Configuration Files

The agent can watch and hot-reload configuration files:

**config/database.yaml**
```yaml
mongodb:
  url: mongodb://localhost:27017/myapp
  connection_timeout_ms: 200
  max_retries: 3
```

**config/monitoring.yaml**
```yaml
monitoring:
  check_interval: 30
  service:
    memory_threshold_mb: 1024
    cpu_threshold_percent: 90
  database:
    slow_query_ms: 1000
```

## 🎮 Usage

### Method 1: Web UI

```bash
# Start the agent (includes web UI)
python app.py

# Access dashboard at http://localhost:8081
```

Features:
- Real-time service and database health
- Recovery history
- Manual recovery triggers
- System metrics

### Method 2: REST API

```bash
# Get agent status
curl http://localhost:5000/health

# Get recovery status
curl http://localhost:5000/recovery/status

# Trigger manual recovery
curl -X POST http://localhost:5000/recovery/trigger \
  -H "Content-Type: application/json" \
  -d '{"component": "database", "reason": "Manual test"}'
```

### Method 3: Programmatic Control

```python
from autonomous_recovery_agent import AutonomousRecoveryAgent

# Get current status
status = agent.get_status()
print(f"Agent running: {status['running']}")
print(f"Services monitored: {status['services_monitored']}")

# Manually trigger recovery
result = agent.trigger_recovery(
    component="database",
    reason="Testing recovery"
)
print(f"Recovery triggered: {result['success']}")

# Stop agent
agent.stop()
```

### Method 4: CLI

```bash
# Start agent
recovery-agent start --config config/settings.yaml

# Get status
recovery-agent status

# Trigger recovery
recovery-agent trigger --component database --reason "Manual trigger"

# Show version
recovery-agent version
```

## 📡 API Documentation

### Health Endpoints

#### GET `/health`
System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "flask",
  "recovery_agent": "active",
  "agent_status": {
    "running": true,
    "services_monitored": 1,
    "total_actions": 5,
    "timestamp": 1234567890
  }
}
```

#### GET `/recovery/status`
Get detailed recovery agent status.

**Response:**
```json
{
  "status": "ok",
  "agent": {
    "running": true,
    "monitoring_active": true,
    "service_health": "connected",
    "database_health": "connected",
    "recovery_attempts": 2,
    "last_check": "2024-01-15T10:30:00Z"
  }
}
```

### Recovery Endpoints

#### GET `/recovery/health`
Get detailed health information.

**Response:**
```json
{
  "status": "ok",
  "health": {
    "service": {
      "status": "connected",
      "cpu_percent": 25.5,
      "memory_mb": 256.8,
      "timestamp": 1234567890
    },
    "database": {
      "status": "connected",
      "connection_time_ms": 45,
      "is_reachable": true,
      "timestamp": 1234567890
    }
  }
}
```

#### POST `/recovery/trigger`
Manually trigger recovery for a component.

**Request:**
```json
{
  "component": "database",
  "reason": "Manual recovery test"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Recovery triggered",
  "recovery_id": "db_1705318200",
  "action": "reconnect"
}
```

### Admin Endpoints

#### POST `/admin/maintenance/enable`
Enable maintenance mode.

**Request:**
```json
{
  "level": "degraded",
  "reason": "Scheduled maintenance",
  "duration_minutes": 30
}
```

#### POST `/admin/maintenance/disable`
Disable maintenance mode.

**Request:**
```json
{
  "schedule_id": "maintenance_1705318200"
}
```

#### GET `/admin/maintenance/status`
Get maintenance status.

**Response:**
```json
{
  "current_level": "normal",
  "schedules": {...}
}
```

## 🖥️ Components

### Service Monitor
Monitors Flask service health by:
- Tracking process status
- Collecting CPU and memory metrics
- Detecting service crashes
- Recording health history

**File:** `autonomous_recovery_agent/monitoring/service_monitor.py`

### Database Monitor
Monitors MongoDB connectivity:
- Executes ping commands
- Measures connection time
- Detects connection failures
- Tracks reachability status

**File:** `autonomous_recovery_agent/monitoring/database_monitor.py`

### Disk Monitor
Manages disk usage:
- Monitors disk space
- Cleans old log files
- Removes temporary files
- Rotates log files

**File:** `autonomous_recovery_agent/monitoring/disk_monitor.py`

### Recovery Engine
Executes recovery actions:
- Service restart
- Database reconnection
- Traffic throttling
- Resource cleanup

**File:** `autonomous_recovery_agent/recovery/engine.py`

### Configuration Manager
Manages configuration with hot-reload:
- Loads YAML/JSON configs
- Watches for file changes
- Triggers callbacks on updates
- Maintains change history

**File:** `autonomous_recovery_agent/config_manager.py`

### Maintenance Manager
Handles maintenance windows:
- Schedules maintenance periods
- Returns maintenance pages
- Manages maintenance levels
- Triggers callbacks

**File:** `autonomous_recovery_agent/maintenance/manager.py`

### Traffic Throttler
Controls traffic during overload:
- Monitors request rates
- Implements throttling rules
- Supports multiple throttle levels
- Dynamic threshold adjustment

**File:** `autonomous_recovery_agent/traffic/throttler.py`

## 📊 Dashboard

Access the web dashboard at **http://localhost:8081**

### Dashboard Features

- **Service Health** - Real-time service status with metrics
- **Database Health** - MongoDB connection status
- **Quick Actions** - Trigger manual recovery
- **Recovery History** - View past recovery attempts
- **System Metrics** - CPU, memory, disk usage
- **Maintenance Status** - Current maintenance level

### Dashboard Endpoints

- `/api/status` - Agent status
- `/api/health` - Health information
- `/api/recovery/history` - Recovery history
- `/api/recovery/trigger` - Trigger recovery
- `/admin/maintenance/status` - Maintenance status

## 🔍 Monitoring

### Health Check States

| State | Description | Action |
|-------|-------------|--------|
| **connected** | Service/DB healthy | Continue monitoring |
| **degraded** | Slow response times | Monitor closely |
| **unhealthy** | Frequent errors | Prepare recovery |
| **disconnected** | Unable to reach | Initiate recovery |
| **critical** | Complete failure | Emergency recovery |

### Recovery Workflow

```
Anomaly Detected
       ↓
Check Cooldown Period
       ↓
Attempt Recovery
       ↓
Monitor for Success
       ↓
Update History & Stats
```

## 🐛 Troubleshooting

### Agent Not Starting

**Problem:** Agent fails to start with connection error

**Solutions:**
1. Verify MongoDB is running: `mongosh`
2. Check MongoDB URI in config
3. Verify network connectivity
4. Check logs: `tail -f agent.log`

```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017/').admin.command('ping')"
```

### Service Not Being Detected

**Problem:** Agent can't find Flask service

**Solutions:**
1. Verify Flask process is running
2. Check process name matches configuration
3. Verify service health endpoint works: `curl http://localhost:5000/health`
4. Check agent logs for errors

### High Memory Usage

**Problem:** Agent consuming too much memory

**Solutions:**
1. Increase `check_interval` (monitoring frequency)
2. Reduce `max_log_age_days` to clean up faster
3. Enable disk cleanup in config
4. Check for memory leaks in logs

### Database Recovery Failing

**Problem:** Agent can't reconnect to MongoDB

**Solutions:**
1. Verify MongoDB is accessible
2. Check connection string format
3. Verify authentication credentials
4. Check firewall rules
5. Review MongoDB logs

### Configuration Not Reloading

**Problem:** Configuration changes not taking effect

**Solutions:**
1. Verify `watch_config_files: true` in config
2. Check file permissions on config files
3. Verify file format (YAML/JSON valid)
4. Check agent logs for config errors
5. Restart agent if needed

## 📈 Performance Tuning

### Reduce CPU Usage

```yaml
check_interval: 60          # Increase monitoring interval
max_retries: 2              # Reduce retry attempts
log_rotation_size_mb: 500   # Larger log files
```

### Improve Recovery Speed

```yaml
recovery_cooldown_seconds: 30   # Shorter cooldown
max_recovery_attempts: 5        # More attempts
db_connection_timeout_ms: 100   # Faster detection
```

### Optimize Disk Usage

```yaml
disk_cleanup_threshold: 0.85    # More aggressive cleanup
max_log_age_days: 3             # Clean logs faster
max_temp_age_hours: 12          # Clean temp files faster
```

## 🔒 Security

### API Security

- All API endpoints require authentication
- Use strong API keys in production
- Rotate keys regularly
- Enable HTTPS in production

### Best Practices

1. Store secrets in environment variables
2. Use strong database passwords
3. Restrict network access to agent
4. Enable audit logging
5. Monitor failed recovery attempts

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run test script
python test_recovery.py

# Run with verbose output
python -m pytest tests/ -v
```

### Testing Recovery

```bash
# Terminal 1: Start agent
python app.py

# Terminal 2: Monitor dashboard
open http://localhost:8081

# Terminal 3: Simulate failure
# Stop MongoDB, then restart it

# Watch recovery in action!
```

## 🔧 Development

### Project Structure

```
autonomous-recovery-agent/
├── autonomous_recovery_agent/
│   ├── __init__.py                 # Package exports
│   ├── agent.py                    # Main agent class
│   ├── config.py                   # Configuration classes
│   ├── config_manager.py           # Configuration management
│   ├── cli.py                      # CLI interface
│   ├── flask_integration.py        # Flask integration
│   ├── web_ui.py                   # Web dashboard
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── service_monitor.py      # Service health monitoring
│   │   ├── database_monitor.py     # Database health monitoring
│   │   └── disk_monitor.py         # Disk usage monitoring
│   ├── recovery/
│   │   ├── __init__.py
│   │   └── engine.py               # Recovery execution
│   ├── maintenance/
│   │   └── manager.py              # Maintenance mode
│   ├── traffic/
│   │   ├── __init__.py
│   │   └── throttler.py            # Traffic throttling
│   ├── templates/
│   │   └── dashboard.html          # Web UI template
│   ├── utils/
│   │   └── logging.py              # Logging utilities
│   └── flask_mongodb_app/
│       ├── app.py                  # Example Flask app
│       └── examples/
│           └── basic_usage.py      # Usage example
├── tests/
├── .env.example                    # Environment template
├── requirements.txt                # Dependencies
├── setup.py                        # Package setup
└── README.md                       # This file
```

### Creating Custom Monitors

```python
from autonomous_recovery_agent.monitoring.service_monitor import ServiceMonitor

class CustomMonitor:
    def __init__(self, logger):
        self.logger = logger
    
    def check_health(self):
        """Return health status"""
        return {
            "status": "connected",
            "custom_metric": 42,
            "timestamp": time.time()
        }
    
    def start(self):
        """Start monitoring"""
        pass
    
    def stop(self):
        """Stop monitoring"""
        pass
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to functions
- Include unit tests
- Update documentation
- Add type hints

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Check troubleshooting section
- Review agent logs
- Check configuration

## 🎓 Examples

### Example 1: E-Commerce API

See `autonomous_recovery_agent/flask_mongodb_app/app.py` for a complete e-commerce API example with automatic recovery.

### Example 2: Basic Integration

See `autonomous_recovery_agent/flask_mongodb_app/examples/basic_usage.py` for a minimal setup example.

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "autonomous_recovery_agent"]
```

### Environment Variables

```bash
MONGODB_URL=mongodb://mongo:27017/app
FLASK_ENV=production
ENABLE_WEB_UI=true
WEB_UI_PORT=8081
```

---

**Built with ❤️ for reliable Flask + MongoDB applications**

Version: 3.0.4 | Last Updated: 2025
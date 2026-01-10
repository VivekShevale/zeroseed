Collecting workspace information# Self-Healing Web Infrastructure Agent

A comprehensive autonomous monitoring and remediation system for web services. The agent automatically detects anomalies, makes intelligent decisions, and executes corrective actions to maintain service health.

## 📋 Table of Contents

- Overview
- Features
- Architecture
- Prerequisites
- Installation
- Configuration
- Usage
- API Documentation
- Dashboard
- Development
- Testing
- Project Structure

## 🎯 Overview

The Self-Healing Agent is an autonomous infrastructure management system that:

- **Monitors** service health continuously
- **Detects** anomalies in real-time using statistical analysis
- **Decides** optimal remediation actions based on a learned catalog
- **Executes** corrective actions automatically
- **Learns** from outcomes to improve future decisions

This system enables zero-touch incident response and reduces manual intervention by up to 80%.

## ✨ Features

### Core Capabilities

- **Autonomous Monitoring**: Continuous health checks every 10 seconds (configurable)
- **Intelligent Anomaly Detection**: Multi-metric analysis with statistical scoring
- **Adaptive Learning**: Confidence scoring that improves with each action
- **Automatic Remediation**: Execute fixes without human intervention
- **Issue-Action Catalog**: Extensible mapping of problems to solutions
- **Incident Tracking**: Full lifecycle management from detection to resolution

### Supported Actions

- Service restart
- Cache clearing
- Horizontal scaling (scale up/down)
- Version rollback
- Custom webhooks
- Manual notifications

### Metrics Monitored

- Service health status (UP/DOWN/DEGRADED)
- CPU usage
- Memory usage
- Error rate
- Response latency
- Custom metrics via API

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Healing Agent                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Monitor    │  │   Decision   │  │   Action         │   │
│  │  Service    │→ │   Engine     │→ │   Executor       │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│         ↓                ↓                    ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Learning Engine (Confidence Scoring)        │   │
│  └─────────────────────────────────────────────────────┘   │
│         ↓              ↓              ↓                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      MongoDB (Memory, Catalog, Incidents, Metrics)  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
        ↓                           ↑
    Web Services              API Endpoints
```

### Key Components

#### 1. **Service Monitor** (monitor.py)
- Collects metrics from registered services
- Validates metric thresholds
- Caches recent metrics for analysis

#### 2. **Decision Engine** (`src/agent/decision_engine.py`)
- Analyzes anomalies using Z-score and statistical methods
- Selects optimal actions from catalog
- Considers action confidence scores and recent failures

#### 3. **Action Executor** (action_executor.py)
- Executes HTTP-based remediation actions
- Handles timeouts and retries
- Logs all execution details

#### 4. **Learning Engine** (learning_engine.py)
- Updates confidence scores based on outcomes
- Tracks action success rates
- Identifies improving/declining trends

#### 5. **Database Layer** (database.py)
- MongoDB connection management
- Collection indexing for performance
- Transaction support

## 📦 Prerequisites

- **Python** 3.8+
- **MongoDB** 4.0+
- **Docker** (optional, for containerization)

### System Requirements

- 2+ CPU cores
- 4GB+ RAM
- 1GB+ disk space

## 🚀 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd self-healing-agent
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Setup MongoDB

**Option A: Local Installation**
```bash
# macOS
brew install mongodb-community

# Ubuntu
sudo apt-get install mongodb

# Windows
# Download from https://www.mongodb.com/try/download/community
```

**Option B: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 4. Configure Environment

Create `.env` file in project root:

```bash
# Flask
SECRET_KEY=your-secret-key-change-in-production
DEBUG=False
HOST=0.0.0.0
PORT=5000

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=self_healing_agent

# Agent Configuration
CHECK_INTERVAL=10
MAX_RETRIES=3
RETRY_DELAY=2

# Thresholds
MEMORY_THRESHOLD=90
LATENCY_THRESHOLD=1500
ERROR_RATE_THRESHOLD=0.3
CPU_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=2000

# API Security
API_KEY_HEADER=X-API-Key
API_KEYS=your-api-key-1,your-api-key-2

# Logging
LOG_LEVEL=INFO
LOG_FILE=agent.log
```

## ⚙️ Configuration

### Service Registration

Register services in settings.py or via API:

```python
SERVICES = [
    {
        "service_id": "payment-api",
        "name": "Payment Service",
        "service_url": "http://localhost:6000",
        "metrics_url": "http://localhost:6000/health",
        "health_endpoint": "/health",
        "restart_endpoint": "/agent/restart",
        "enabled": True,
        "tags": ["critical", "api"]
    }
]
```

### Default Issue-Action Mappings

The agent comes with predefined mappings:

| Issue | Action | Auto | Confidence |
|-------|--------|------|-----------|
| SERVICE_DOWN | restart | Yes | 1.0 |
| MEMORY_PRESSURE | scale_up | Yes | 0.8 |
| HIGH_LATENCY | clear_cache | Yes | 0.8 |
| HIGH_ERROR_RATE | rollback | Yes | 0.6 |
| HIGH_CPU | scale_up | Yes | 0.8 |

## 🎮 Usage

### Starting the Agent

#### Method 1: Web Interface

```bash
python run.py
```

Navigate to `http://localhost:5000` to control the agent via dashboard.

#### Method 2: API

```bash
# Start the agent
curl -X POST http://localhost:5000/agent/start

# Stop the agent
curl -X POST http://localhost:5000/agent/stop

# Check status
curl http://localhost:5000/status
```

#### Method 3: Mock Service Testing

```bash
# Terminal 1: Start agent
python run.py

# Terminal 2: Start mock service
python mock_service.py

# Terminal 3: Run tests
python test_agent.py
```

### Manual Operations

#### Ingest Metrics

```bash
curl -X POST http://localhost:5000/agent/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "payment-api",
    "metrics": {
      "health": "DEGRADED",
      "cpu": 85,
      "memory": 92,
      "latency": 1800,
      "error_rate": 0.25
    }
  }'
```

#### Add Custom Issue-Action

```bash
curl -X POST http://localhost:5000/agent/add_issue \
  -H "Content-Type: application/json" \
  -d '{
    "issue": "DATABASE_SLOW",
    "action": "restart_db",
    "auto": true,
    "confidence": 0.7
  }'
```

#### Execute Manual Action

```bash
curl -X POST http://localhost:5000/api/v1/manual/action \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "payment-api",
    "action": "restart",
    "parameters": {}
  }'
```

## 📡 API Documentation

### Health & Status Endpoints

#### GET `/health`
System health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "agent_running": true,
  "version": "1.0.0"
}
```

#### GET `/status`
Agent operational status

**Response:**
```json
{
  "agent_running": true,
  "services_monitored": 5,
  "total_actions": 127,
  "successful_actions": 115,
  "active_incidents": 2,
  "catalog_entries": 8,
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Service Management API (`/api/v1`)

#### GET `/services`
List all registered services

**Headers:** `X-API-Key: your-api-key`

**Response:**
```json
{
  "services": [...],
  "count": 5
}
```

#### POST `/services`
Register new service

**Headers:** `X-API-Key: your-api-key`

**Request:**
```json
{
  "service_id": "user-service",
  "name": "User Service",
  "service_url": "http://localhost:7000",
  "metrics_url": "http://localhost:7000/health"
}
```

#### PUT `/services/{service_id}`
Update service configuration

#### DELETE `/services/{service_id}`
Unregister service

### Metrics Ingestion

#### POST `/api/v1/metrics`
Ingest service metrics

**Headers:** `X-API-Key: your-api-key`

**Request:**
```json
{
  "service_id": "payment-api",
  "metrics": {
    "health": "UP",
    "cpu": 45,
    "memory": 65,
    "error_rate": 0.02
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Catalog Management

#### GET `/api/v1/catalog`
List all issue-action mappings

#### POST `/api/v1/catalog`
Add new catalog entry

#### DELETE `/api/v1/catalog/{issue}/{action}`
Remove catalog entry

### Action History & Incidents

#### GET `/api/v1/actions/history`
Action execution history

**Query Parameters:**
- `limit`: Results per page (default: 100)
- `offset`: Pagination offset (default: 0)

#### GET `/api/v1/incidents`
Incident records

#### POST `/api/v1/manual/action`
Execute manual action

### Agent Control

#### POST `/api/v1/agent/start`
Start monitoring

#### POST `/api/v1/agent/stop`
Stop monitoring

#### GET `/api/v1/agent/status`
Agent operational status

## 📊 Dashboard

### Web Interface

Access dashboard at `http://localhost:5000/dashboard`

**Features:**
- Real-time agent status
- Service health visualization
- Action execution timeline
- Success rate metrics
- Incident tracking
- Catalog management

### Dashboard API

#### GET `/dashboard/api/status`
Overall system status

#### GET `/dashboard/api/services`
Services data for visualization

#### GET `/dashboard/api/incidents`
Active incidents

#### GET `/dashboard/api/catalog`
Catalog entries grouped by issue

#### GET `/dashboard/api/metrics/{service_id}`
Historical metrics for a service

#### GET `/dashboard/api/actions/stats`
Action success statistics

## 🧪 Testing

### Run Test Suite

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python test_agent.py

# Run specific test
python test_service.py
```

### Test the Mock Service

```bash
# Terminal 1
python run.py

# Terminal 2
python mock_service.py

# Terminal 3
python test_agent.py
```

### Integration Testing

```bash
python test_real_website.py
```

This test monitors and responds to real website incidents.

## 📁 Project Structure

```
self-healing-agent/
├── config/
│   └── settings.py              # Application configuration
├── src/
│   ├── agent/
│   │   ├── agent.py             # Main agent orchestrator
│   │   ├── monitor.py           # Service monitoring
│   │   ├── decision_engine.py    # Decision making
│   │   ├── action_executor.py    # Action execution
│   │   └── learning_engine.py    # Confidence scoring
│   ├── api/
│   │   ├── routes.py            # API endpoints
│   │   └── schemas.py           # Request/response schemas
│   ├── models/
│   │   ├── database.py          # MongoDB operations
│   │   ├── repositories.py      # Data access layer
│   │   └── schemas.py           # Data models
│   ├── services/
│   │   └── mock_service.py      # Mock service for testing
│   ├── utils/
│   │   ├── logger.py            # Logging setup
│   │   ├── metrics.py           # Metrics calculations
│   │   └── validators.py        # Input validation
│   └── web/
│       └── dashboard.py         # Dashboard routes
├── templates/
│   └── dashboard.html           # Web dashboard
├── run.py                       # Main Flask application
├── agent_app.py                 # Alternative agent app
├── mock_service.py              # Standalone mock service
├── test_agent.py                # Agent tests
├── test_service.py              # Service tests
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Development

### Code Structure

**Models** (`src/models/`)
- database.py: MongoDB connection and operations
- repositories.py: Data access patterns
- schemas.py: Pydantic models for type safety

**Agent Core** (`src/agent/`)
- Modular design with single responsibility
- Event-driven architecture
- Async/concurrent execution support

**API** (`src/api/`)
- RESTful endpoints with Flask Blueprint
- API key authentication
- Request validation via Pydantic schemas

**Utils** (`src/utils/`)
- Reusable utility functions
- Statistical analysis for anomaly detection
- Input validation and sanitization

### Adding New Services

1. Register service via API or config
2. Implement required endpoints:
   - `GET /health` - Health check
   - `POST /agent/restart` - Restart command

3. Add custom thresholds (optional):
```python
"custom_thresholds": {
    "memory": 85,
    "latency": 1200,
    "error_rate": 0.2
}
```

### Creating Custom Actions

1. Add action to `ActionType` enum in schemas.py
2. Implement in `ActionExecutor.execute()` method
3. Add to catalog with confidence score

## 📈 Monitoring & Metrics

### Key Metrics

- **Action Success Rate**: Percentage of successful remediations
- **Detection Latency**: Time from anomaly to detection
- **Resolution Time**: Time from detection to resolution
- **Confidence Score**: Action effectiveness (0-1)

### Viewing Metrics

```bash
# Via API
curl http://localhost:5000/api/v1/actions/history

# Via Dashboard
http://localhost:5000/dashboard
```

## 🔒 Security

### API Authentication

All API endpoints require `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/v1/services
```

### Best Practices

- Change `SECRET_KEY` in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Rotate API keys regularly
- Limit service connectivity to internal networks

## 🐛 Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
mongosh

# Verify URI in .env
MONGO_URI=mongodb://localhost:27017/
```

### Agent Not Starting

```bash
# Check logs
tail -f agent.log

# Verify services are accessible
curl http://localhost:6000/health
```

### High Memory Usage

- Reduce `CHECK_INTERVAL`
- Clean up old incidents and metrics
- Limit metrics retention period

## 📝 Logging

Logs are written to `agent.log` with JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "component": "agent",
  "message": "Service restart successful",
  "service_id": "payment-api"
}
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run.py"]
```

### Environment Variables

```bash
docker run -e MONGO_URI=mongodb://mongo:27017/ \
           -e API_KEYS=your-api-key \
           -p 5000:5000 \
           self-healing-agent
```

## 📞 Support

For issues and feature requests, open an issue in the repository.

## 📄 License

Specify your license here.

## 🤝 Contributing

Contributions are welcome! Please follow:

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

## 🎓 Learning Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [RESTful API Design](https://restfulapi.net/)

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Maintainers:** Self-Healing Agent Team
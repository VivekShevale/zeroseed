# Self-Healing Agent

An autonomous, AI-powered web infrastructure monitoring and remediation system that automatically detects, diagnoses, and fixes issues in distributed services without human intervention.

## Overview

The Self-Healing Agent is a distributed system designed to maintain high availability and performance of web services. It continuously monitors service health, learns from incidents, makes intelligent decisions, and autonomously executes corrective actions to resolve issues before they impact users.

### Key Features

- **🔍 Intelligent Monitoring**: Real-time health checks with customizable thresholds
- **🧠 Learning Engine**: Learns from past incidents to improve decision-making
- **⚡ Autonomous Remediation**: Automatically executes fixes without human intervention
- **📊 Metrics & Analytics**: Comprehensive metrics collection and visualization
- **🔐 Security**: API key authentication and secure webhooks
- **📈 Scalability**: Handles multiple services and concurrent operations
- **💾 Persistent Memory**: MongoDB-backed incident history and fix catalog
- **🎯 Decision Intelligence**: Advanced decision engine for incident classification
- **📡 Real-time Dashboard**: Web-based monitoring dashboard

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Healing Agent                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  Monitor     │  │  Decision     │  │  Action          │ │
│  │  Services    │→ │  Engine       │→ │  Executor        │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│         ↓                    ↓                   ↓           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Learning Engine                          │   │
│  │  (Improves remediation based on outcomes)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            MongoDB (Incident History & Catalog)      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ↓                                      ↓
    ┌─────────┐                          ┌──────────┐
    │Services │                          │Dashboard │
    └─────────┘                          └──────────┘
```

## Project Structure

```
self-healing-agent/
├── src/
│   ├── agent/                  # Core agent logic
│   │   ├── agent.py           # Main orchestrator
│   │   ├── monitor.py         # Service monitoring
│   │   ├── decision_engine.py # Decision logic
│   │   ├── action_executor.py # Action execution
│   │   └── learning_engine.py # Learning from incidents
│   ├── api/                    # REST API
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Request/response schemas
│   ├── models/                 # Data models
│   │   ├── database.py        # Database connection
│   │   ├── repositories.py    # Data access layer
│   │   └── schemas.py         # Data schemas
│   ├── services/               # Business logic
│   ├── utils/                  # Utilities
│   │   ├── logger.py          # Structured logging
│   │   ├── metrics.py         # Metrics collection
│   │   └── validators.py      # Data validation
│   └── web/                    # Web interface
│       └── dashboard.py       # Dashboard backend
├── config/
│   └── settings.py            # Configuration management
├── templates/
│   └── dashboard.html         # Dashboard frontend
├── run.py                      # Main entry point
├── agent_app.py              # Flask application
├── self_healing_sdk.py        # SDK for service integration
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── .env                       # Environment configuration
└── tests/                     # Test files
    ├── test_agent.py
    ├── test_sdk.py
    ├── test_service.py
    ├── test_real_website.py
    └── mock_service.py
```

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB 4.0+
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   cd self-healing-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start MongoDB**
   ```bash
   # On Windows
   mongod
   
   # Or use Docker
   docker run -d -p 27017:27017 mongo
   ```

6. **Run the agent**
   ```bash
   python run.py
   ```

The agent will start on `http://localhost:5000`

## Configuration

### Environment Variables

```env
# Flask
SECRET_KEY=your-secret-key-here
DEBUG=false
HOST=0.0.0.0
PORT=5000

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=self_healing_agent

# Agent
CHECK_INTERVAL=10              # Health check interval in seconds
MAX_RETRIES=3                  # Max retry attempts
RETRY_DELAY=5                  # Delay between retries

# Thresholds
MEMORY_THRESHOLD=90            # Memory usage %
LATENCY_THRESHOLD=1500         # Latency in ms
ERROR_RATE_THRESHOLD=0.3       # Error rate threshold
CPU_THRESHOLD=90               # CPU usage %
RESPONSE_TIME_THRESHOLD=2000   # Response time in ms

# Security
API_KEY_HEADER=X-API-Key
API_KEYS=dev-key-123,prod-key-456

# Logging
LOG_LEVEL=INFO
LOG_FILE=agent.log
```

## Usage

### Running the Agent

```bash
python run.py
```

### Integrating a Service with SDK

```python
from self_healing_sdk import SelfHealingAgent

# Initialize SDK
agent = SelfHealingAgent(
    agent_url="http://localhost:5000",
    user_id="your-user-id",
    service_id="your-service-id",
    secret="your-secret"
)

# Register your service
agent.register(
    name="Payment API",
    health_url="http://your-service:6000/health",
    webhook_url="http://your-service:6000/webhook",
    tags=["critical", "api"],
    metadata={"version": "1.0"}
)

# Define health callback
def health_callback(health_status):
    print(f"Health: {health_status}")

agent.set_health_callback(health_callback)

# Start monitoring
agent.start_monitoring()
```

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Get Agent Status
```bash
GET /status
Authorization: X-API-Key: your-api-key
```

#### Service Registration
```bash
POST /api/services/register
Authorization: X-API-Key: your-api-key
Content-Type: application/json

{
  "service_id": "payment-api",
  "name": "Payment API",
  "health_url": "http://localhost:6000/health",
  "webhook_url": "http://localhost:6000/webhook",
  "tags": ["critical"],
  "metadata": {}
}
```

#### Get Incidents
```bash
GET /api/incidents
Authorization: X-API-Key: your-api-key
```

#### Get Metrics
```bash
GET /api/metrics
Authorization: X-API-Key: your-api-key
```

## Core Components

### 1. Service Monitor
Continuously monitors registered services by:
- Polling health endpoints
- Collecting metrics (CPU, memory, latency)
- Detecting anomalies and threshold violations
- Tracking service availability

**File**: [src/agent/monitor.py](src/agent/monitor.py)

### 2. Decision Engine
Analyzes incidents and determines appropriate actions:
- Classifies issues by severity and type
- Consults fix catalog for known issues
- Uses machine learning for new issue types
- Calculates confidence scores

**File**: [src/agent/decision_engine.py](src/agent/decision_engine.py)

### 3. Action Executor
Executes remediation actions:
- Service restart
- Resource scaling
- Configuration updates
- Graceful degradation
- Escalation to on-call teams

**File**: [src/agent/action_executor.py](src/agent/action_executor.py)

### 4. Learning Engine
Learns from incidents to improve future responses:
- Tracks action outcomes
- Updates success rates in fix catalog
- Refines decision thresholds
- Identifies patterns and trends

**File**: [src/agent/learning_engine.py](src/agent/learning_engine.py)

### 5. REST API
Provides endpoints for:
- Service registration/management
- Incident queries
- Metrics retrieval
- System configuration
- Webhook integration

**File**: [src/api/routes.py](src/api/routes.py)

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

### Available Tests
- `test_agent.py` - Agent core functionality
- `test_sdk.py` - SDK integration tests
- `test_service.py` - Service monitoring tests
- `test_real_website.py` - Real-world integration tests
- `mock_service.py` - Mock service for testing

### Development Testing
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run mock service
python mock_service.py

# In another terminal, run tests
pytest tests/
```

## Monitoring & Dashboards

### Web Dashboard
Access the monitoring dashboard at:
```
http://localhost:5000/dashboard
```

Features:
- Real-time service status
- Incident history
- Metrics visualization
- Performance analytics
- System health overview

**Files**: 
- [src/web/dashboard.py](src/web/dashboard.py)
- [templates/dashboard.html](templates/dashboard.html)

### Metrics Collection
The system collects metrics via:
- Prometheus-compatible endpoints
- Custom metric collectors
- Service health checks
- System resource monitoring

**File**: [src/utils/metrics.py](src/utils/metrics.py)

## Security

### API Authentication
All API endpoints (except `/health`) require API key authentication:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/incidents
```

### Webhook Security
Webhooks are secured with:
- HMAC-SHA256 signature verification
- Request timestamp validation
- Service ID validation

### Best Practices
- Use strong API keys in production
- Rotate keys regularly
- Use HTTPS in production
- Validate all webhook signatures
- Monitor authentication failures

## Performance Optimization

### Concurrency
- Multi-threaded monitoring
- Thread pool for parallel operations
- Async API requests
- Non-blocking database operations

### Caching
- Redis caching layer (optional)
- In-memory fix catalog cache
- Metric aggregation cache

### Database Optimization
- Indexed queries
- Batch operations
- Connection pooling
- Archive old incidents

## Deployment

### Docker Deployment
```bash
docker build -t self-healing-agent .
docker run -p 5000:5000 \
  -e MONGO_URI=mongodb://mongo:27017 \
  -e REDIS_URL=redis://redis:6379 \
  self-healing-agent
```

### Kubernetes Deployment
See `k8s/` directory for Kubernetes manifests

### Production Checklist
- [ ] Set `DEBUG=false`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure production database
- [ ] Set up monitoring and alerting
- [ ] Enable comprehensive logging
- [ ] Configure backups
- [ ] Set up high availability

## Troubleshooting

### Agent not connecting to services
1. Check service URLs in configuration
2. Verify network connectivity
3. Check firewall rules
4. Review agent logs

### High memory usage
1. Review monitoring frequency
2. Check incident history size
3. Enable caching
4. Archive old incidents

### MongoDB connection issues
1. Verify MongoDB is running
2. Check `MONGO_URI` configuration
3. Verify database credentials
4. Check network connectivity

### API authentication failures
1. Verify `X-API-Key` header
2. Check API key configuration
3. Review security logs

## Logging

The system uses structured logging via the `logger` module:

```python
from src.utils.logger import logger

logger.info("Agent started")
logger.warning("High memory detected")
logger.error("Service connection failed")
```

Log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages for recoverable issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors requiring immediate attention

Configure log level in `.env`:
```env
LOG_LEVEL=INFO
LOG_FILE=agent.log
```

## Metrics

### Prometheus Metrics
The agent exposes Prometheus-compatible metrics at `/metrics`:
- `agent_incidents_total` - Total incidents detected
- `agent_actions_total` - Total actions executed
- `agent_success_rate` - Success rate of actions
- `agent_monitoring_duration_seconds` - Monitoring cycle duration
- `service_health_status` - Service health status (1=healthy, 0=unhealthy)
- `service_latency_ms` - Service latency

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review logs for error details
- Contact the development team

## Roadmap

- [ ] Machine learning model for anomaly detection
- [ ] Advanced visualization and analytics
- [ ] Multi-tenant support
- [ ] Custom action plugins
- [ ] Slack/Teams integration
- [ ] PagerDuty integration
- [ ] GraphQL API
- [ ] Real-time WebSocket updates

## References

- [Self-Healing System Design](docs/architecture.md)
- [API Documentation](docs/api.md)
- [SDK Guide](docs/sdk.md)
- [Contributing Guide](CONTRIBUTING.md)

---

**Built with ❤️ for reliable infrastructure**

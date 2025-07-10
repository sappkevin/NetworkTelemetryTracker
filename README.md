# Network Telemetry Tracker

**Enterprise Network Monitoring System for Netflix SDE Teams**

A comprehensive network monitoring solution that provides real-time performance analytics, geolocation intelligence, and quality-of-service metrics through modern observability infrastructure.

## 🚀 Quick Start

Get started in under 2 minutes:

```bash
# Clone and setup
git clone <repository>
cd NetworkTelemetryTracker

# Start all services
docker-compose up -d

## 🔧 Post-Deployment Configuration

### Grafana InfluxDB Token Setup
After the initial deployment, you need to manually configure the InfluxDB token in Grafana:

1. **Get the token from InfluxDB config:**
   ```bash
   cat ./influxdb2_config/influx-configs
   ```
   Copy the token: `Y4NotDSBnwwfo0RlG5BCqSTZwzKNOhlCTuMVfGhcFJqOizoVCUCngU91CXQEEOhDbPjpEWvakpbV0jCadRAo6w==`

2. **Configure Grafana datasource:**
   - Open http://localhost:3000 (admin/admin123! or via Google 2FA login)
   - Go to **Configuration** → **Data Sources** → **InfluxDB**
   - InfluxDB details -> Token -> Reset
   - Paste the token from step 1
   - Click **Save & Test** to verify connection


# Access dashboards
open http://localhost:3000  # Grafana (admin/admin123! or Google Auth 2FA - only the specified email accounts in the /grafana/grafana.ini file are allowed)
open http://localhost:8086  # InfluxDB
```

**✨ That's it!** The network monitoring system is now collecting metrics and displaying real-time dashboards

## 🎯 What This System Provides

### 📊 **Comprehensive Network Monitoring**
- **Real-time Metrics**: Latency, packet loss, throughput, and availability
- **90+ Data Points**: QoS indicators, performance metrics, and reliability scores
- **Multi-target Support**: Monitor multiple endpoints simultaneously

### 🌍 **Geographic Intelligence** 
- **Global Network Mapping**: Visualize connections on world map
- **Distance Correlation**: Analyze performance vs. geographic distance
- **ISP Analytics**: Performance insights by network provider

### 🔐 **Enterprise Security**
- **OAuth 2.0 Authentication**: Google-based secure access
- **Role-Based Access Control**: Admin, Editor, and Viewer roles
- **Audit Logging**: Complete access and configuration tracking

### 📈 **Advanced Dashboards**
- **7 Specialized Views**: Network performance, QoS, availability, throughput, geolocation
- **Real-time Updates**: Live streaming data with customizable refresh rates
- **Alert Integration**: Threshold-based monitoring with notification support

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Collection │────▶│   Time Series   │────▶│  Visualization  │
│                 │    │    Database     │    │   & Analytics   │
│ • Network Tests │    │                 │    │                 │
│ • Geolocation   │    │ • InfluxDB 2.x  │    │ • Grafana       │
│ • QoS Analysis  │    │ • 90+ Metrics   │    │ • 7 Dashboards  │
│ • 60s Intervals │    │ • Compression   │    │ • OAuth 2.0     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Technologies**: Python 3.11 • InfluxDB 2.x • Grafana • Docker • OAuth 2.0

## 📁 Project Structure

```
NetworkTelemetryTracker/
├── src/                    # Core application code
│   ├── main.py            # Service orchestration
│   ├── telemetry.py       # Network monitoring & data collection
│   ├── database.py        # InfluxDB operations
│   └── config.py          # Configuration management
├── scripts/               # Utility scripts (not used by Docker)
│   ├── testing/          # Test and validation scripts
│   ├── runners/          # Alternative service runners
│   ├── setup/            # Setup and troubleshooting scripts
│   └── utilities/        # Helper utilities
├── docs/                  # Complete documentation
├── grafana/              # Dashboard configurations
├── tests/                # Unit and integration tests
├── docker-compose.yml    # Container orchestration
└── Docker files          # Container deployment (uses 3 root scripts only)
```

## 📚 Documentation

### 📖 **Complete Documentation**
**[📁 /docs](./docs/)** - Comprehensive documentation hub with all guides and references

### 🎯 **Quick Reference**
**[⚡ QUICK_START.md](./QUICK_START.md)** - Essential commands and immediate troubleshooting

### 🏭 **Production Documentation**
**[🏢 Production Guide](./docs/PRODUCTION_DOCUMENTATION.md)** - Complete enterprise deployment guide for Netflix SDE teams

## 📂 Documentation Structure

### 🛠️ **Setup & Configuration**
- **[Docker Deployment](./docs/setup/DOCKER_DEPLOYMENT_GUIDE.md)** - Container-based deployment
- **[Local Setup](./docs/setup/LOCAL_SETUP_GUIDE.md)** - Development environment setup  
- **[OAuth Configuration](./docs/setup/OAUTH_SETUP.md)** - Google OAuth 2.0 authentication
- **[Database Setup](./docs/setup/INFLUXDB_TOKEN_SETUP.md)** - InfluxDB configuration

### ⭐ **Features & Capabilities**
- **[Dashboard Guide](./docs/features/DASHBOARD_GUIDE.md)** - Complete guide to all 7 dashboards
- **[Geolocation Features](./docs/features/GEOLOCATION_FEATURES.md)** - Geographic monitoring capabilities

### 🚀 **Deployment & Operations**
- **[Deployment Summary](./docs/deployment/DEPLOYMENT_SUMMARY.md)** - Complete implementation status
- **[Production Documentation](./docs/PRODUCTION_DOCUMENTATION.md)** - Enterprise deployment guide
- **[Scaling & High Availability](./docs/SCALING_DEPLOYMENT_GUIDE.md)** - Auto-scaling and HA deployment guide

### 🔧 **Troubleshooting & Support**
- **[Quick Fixes](./docs/troubleshooting/QUICK_FIX_SUMMARY.md)** - Common issues and solutions
- **[Telemetry Troubleshooting](./docs/troubleshooting/telemetry_fix_guide.md)** - Data collection issues

## 🎛️ Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Multi-Protocol Monitoring** | Ping, traceroute, HTTP, DNS | Comprehensive network visibility |
| **Geographic Correlation** | IP geolocation with distance analysis | Understand performance vs. location |
| **QoS Analytics** | Voice, video, data quality scoring | Optimize streaming performance |
| **Real-time Dashboards** | 7 specialized Grafana views | Operational insights and alerting |
| **Enterprise Security** | OAuth 2.0 with RBAC | Secure, auditable access control |
| **Container-Native** | Docker Compose deployment | Easy deployment and scaling |

## 🔗 Quick Access Links

| Resource | URL | Purpose |
|----------|-----|---------|
| **Grafana Dashboards** | http://localhost:3000 | Network monitoring and analytics |
| **InfluxDB Interface** | http://localhost:8086 | Database management and queries |
| **Health Check** | `docker-compose ps` | Service status verification |
| **Live Logs** | `docker-compose logs -f` | Real-time service monitoring |

## 🚀 Deployment Options

### **Simple Deployment** (Default)
```bash
docker-compose up -d          # Uses docker-compose.yml (single instances)
```

### **High Availability Deployment**
```bash
docker-compose -f docker-compose.ha.yml up -d    # Multi-instance with load balancing
```

### **Feature Comparison**

| Feature | Simple (`docker-compose.yml`) | HA (`docker-compose.ha.yml`) |
|---------|-------------------------------|------------------------------|
| **InfluxDB** | 1 instance | 2 instances + load balancer |
| **Grafana** | 1 instance | 2 instances + shared storage |
| **Telemetry Service** | 1 instance | 3 instances |
| **Load Balancer** | ❌ | ✅ HAProxy |
| **Monitoring** | Basic | Prometheus + AlertManager |
| **Circuit Breakers** | ❌ | ✅ Fault tolerance |
| **Auto-Scaling** | ❌ | ✅ Kubernetes ready |
| **Resource Usage** | Low | Medium-High |
| **Setup Time** | < 2 minutes | < 5 minutes |
| **Production Ready** | Development/Testing | Enterprise/Production |

## ⚡ Essential Commands

```bash
# Service Management
docker-compose up -d          # Start all services (simple)
docker-compose down           # Stop all services  
docker-compose restart        # Restart services
docker-compose ps             # Check service status

# Service Testing & Validation
python scripts/testing/docker_health_check.py        # Test Docker containers
python scripts/testing/service_validator.py          # Comprehensive validation
python scripts/testing/test_telemetry_standalone.py  # Test data collection

# Container Health Monitoring
curl http://localhost:8086/ping                      # Test InfluxDB
curl http://localhost:3000/api/health               # Test Grafana
docker-compose logs -f network-telemetry            # View live logs

# Data Verification
docker exec influxdb2 influx query 'from(bucket:"default") |> range(start:-5m) |> count()'
```

## 🛠️ Development & Testing

```bash
# Development setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html

# Testing & validation scripts (organized in scripts/ folder)
python scripts/testing/docker_health_check.py        # Docker container health
python scripts/testing/service_validator.py          # Comprehensive service validation
python scripts/testing/test_telemetry_standalone.py  # Test telemetry collection
python scripts/testing/validate_telemetry_fields.py  # Validate data fields
python scripts/setup/setup_influxdb.py               # Setup local InfluxDB

# Code quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 📊 System Capabilities

### Network Metrics Collected
- **Latency**: RTT min/avg/max/mdev measurements
- **Reliability**: Packet loss, availability, success rates  
- **Performance**: Throughput, bandwidth utilization, jitter
- **Quality**: Voice/video/data quality scores
- **Geographic**: Source/target location, distance, ISP data

### Dashboard Coverage
1. **Network Telemetry** - Primary performance overview
2. **QoS Metrics** - Quality of service indicators  
3. **Availability & Reliability** - Service health monitoring
4. **Throughput & Bandwidth** - Traffic analysis
5. **Response Time Breakdown** - Component-level timing
6. **Geolocation** - Global network flow visualization
7. **Node Graph** - Network topology mapping

## 🏢 Enterprise Features

- **Auto-Scaling**: Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA)
- **High Availability**: Multi-instance clustering with HAProxy load balancing
- **Circuit Breakers**: Fault tolerance with automatic recovery mechanisms
- **Connection Pooling**: Optimized async HTTP connection management
- **Multi-Region Support**: Distributed monitoring with centralized aggregation
- **Security**: Enterprise-grade authentication and audit logging
- **Compliance**: SOC 2, GDPR-ready with comprehensive documentation
- **Integration**: REST APIs for custom automation and alerting

## 📞 Support & Contributing

### Getting Help
- **📖 Documentation**: Start with [/docs](./docs/) for comprehensive guides
- **⚡ Quick Issues**: Check [QUICK_START.md](./QUICK_START.md) for immediate solutions
- **🔧 Troubleshooting**: See [troubleshooting guides](./docs/troubleshooting/)

### Contributing
- **🧪 Testing**: Run test suite before submitting changes
- **📝 Documentation**: Update relevant docs for any changes
- **🔒 Security**: Follow security best practices for all contributions

---

**Built for Netflix SDE Assessment by Kevin Sapp** | **Production-Ready Network Monitoring** | **Container-Native Architecture**

> **Ready for Production**: This system is designed to meet Netflix's scale and operational requirements with enterprise-grade reliability, security, and observability.

📚 **[Complete Documentation Hub →](./docs/)**
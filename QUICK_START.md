# ⚡ Quick Start Reference

**30-Second Setup • Essential Commands • Immediate Troubleshooting**

## 🚀 Instant Setup (30 seconds)

```bash
# Start everything
docker-compose up -d

# Verify it's working
docker-compose ps
```

**✅ Success**: All services show "Up" status  
**🌐 Access**: Grafana at http://localhost:3000 (admin/admin123!)

## 🔗 Essential Access

| Service | URL | Login |
|---------|-----|-------|
| **Grafana** | http://localhost:3000 | admin / admin123! |
| **InfluxDB** | http://localhost:8086 | admin / password |

## ⚡ Essential Commands

### Service Management
```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop everything
docker-compose restart        # Restart services
docker-compose ps             # Check status
```

### Health Checks
```bash
# Quick health check
docker-compose ps | grep -v Exit

# Check if data is flowing
docker exec influxdb2 influx query 'from(bucket:"default") |> range(start:-5m) |> count()'

# View live collection logs
docker-compose logs -f network-telemetry | tail -20
```

### Resource Monitoring
```bash
docker stats --no-stream     # Resource usage
docker-compose logs --tail=50 network-telemetry  # Recent logs
```

## 🔧 Instant Troubleshooting

### ❌ Problem: No data in dashboards
```bash
# Check service status
docker-compose ps

# Restart data collection
docker-compose restart network-telemetry

# Verify network connectivity
docker exec network-telemetry ping -c 3 google.com
```

### ❌ Problem: Service won't start
```bash
# Check logs for errors
docker-compose logs network-telemetry

# Reset everything
docker-compose down && docker-compose up -d

# Check disk space
df -h
```

### ❌ Problem: Grafana login issues
```bash
# Reset admin password
docker exec grafana grafana-cli admin reset-admin-password admin123!

# Check service
docker-compose logs grafana
```

### ❌ Problem: High resource usage
```bash
# Check resource consumption
docker stats --no-stream

# Reduce monitoring frequency
vi .env  # Set MONITORING_INTERVAL=120
docker-compose restart network-telemetry
```

## 📊 Quick Data Verification

### Test Data Collection
```bash
# Manual collection test
docker exec network-telemetry python -c "
from src.telemetry import NetworkTelemetry
from src.config import Config
import asyncio
async def test():
    config = Config()
    t = NetworkTelemetry(config)
    result = await t.test_connectivity()
    print(f'Test result: {result}')
asyncio.run(test())
"
```

### Database Query Test
```bash
# Check recent data
docker exec influxdb2 influx query '
from(bucket:"default") 
|> range(start:-1h) 
|> filter(fn:(r) => r._measurement == "network_telemetry")
|> last()
'
```

## 🎯 Quick Configuration

### Change Monitoring Targets
```bash
# Edit environment file
vi .env
# Update: TARGET_FQDN="google.com,github.com,your-target.com"

# Restart to apply changes
docker-compose restart network-telemetry
```

### Adjust Collection Frequency
```bash
# Edit .env file
vi .env
# Update: MONITORING_INTERVAL=30  # seconds

# Restart service
docker-compose restart network-telemetry
```

## 📞 Need More Help?

- **🔧 Detailed Troubleshooting**: [docs/troubleshooting/](./docs/troubleshooting/)
- **⚙️ Setup Guides**: [docs/setup/](./docs/setup/)
- **📖 Complete Documentation**: [docs/](./docs/)
- **🏭 Production Guide**: [docs/PRODUCTION_DOCUMENTATION.md](./docs/PRODUCTION_DOCUMENTATION.md)

## 🎪 Quick Demo Commands

```bash
# Show real-time metrics collection
docker-compose logs -f network-telemetry | grep "Collection completed"

# Display current system resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Test all network targets
docker exec network-telemetry python scripts/testing/test_telemetry_standalone.py
```

---

**⚡ This covers 90% of daily operations** • For complex issues, see [complete documentation](./docs/)

---

*Network Telemetry Tracker developed by Kevin Sapp for Netflix SDE Assessment*
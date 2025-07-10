# Scaling and High Availability Deployment Guide

**Enterprise-grade scaling configuration for Network Telemetry Service**

## Overview

This guide covers deploying the Network Telemetry Service with comprehensive scaling capabilities including:

- **Horizontal Pod Autoscaling (HPA)** - Automatic scaling based on metrics
- **Vertical Pod Autoscaling (VPA)** - Automatic resource adjustment
- **Load Balancing** - Traffic distribution across multiple instances
- **Circuit Breakers** - Fault tolerance and resilience
- **Connection Pooling** - Optimized resource utilization
- **High Availability** - Multi-instance clustering with failover

## Quick Start

### 1. High Availability Docker Deployment

Deploy with load balancing and clustering:

```bash
# Start high-availability stack
docker-compose -f docker-compose.ha.yml up -d

# Verify services
docker-compose -f docker-compose.ha.yml ps

# Access load-balanced services
curl http://localhost:8086/ping      # InfluxDB (load balanced)
curl http://localhost:3000/api/health # Grafana (load balanced)
curl http://localhost:8404/stats     # HAProxy statistics
```

**Services deployed:**
- 2x InfluxDB instances with clustering
- 2x Grafana instances with shared storage
- 3x Telemetry service instances
- HAProxy load balancer
- Redis for caching
- Prometheus + AlertManager for monitoring

### 2. Kubernetes Auto-Scaling Deployment

Deploy with Kubernetes HPA and VPA:

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/telemetry-deployment.yaml

# Verify deployment
kubectl get pods -n telemetry-system
kubectl get hpa -n telemetry-system
kubectl get vpa -n telemetry-system

# Check scaling metrics
kubectl top nodes
kubectl top pods -n telemetry-system
```

## Architecture Components

### Load Balancing (HAProxy)

**Configuration:** `haproxy/haproxy.cfg`

- **InfluxDB Load Balancer:** Round-robin across multiple instances
- **Grafana Load Balancer:** Session-sticky load balancing
- **Health Checks:** Automatic backend health monitoring
- **Statistics:** Real-time load balancer metrics at :8404/stats

```bash
# HAProxy health check
curl http://localhost:8404/stats

# Backend health verification
docker exec telemetry-lb haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
```

### Horizontal Pod Autoscaler (HPA)

**Configuration:** `k8s/telemetry-deployment.yaml:371-420`

**Scaling Metrics:**
- **CPU Utilization:** Target 70% (scales 3-20 pods)
- **Memory Utilization:** Target 80% 
- **Custom Metric:** `telemetry_collection_duration_seconds` target 30s

**Scaling Behavior:**
- **Scale Up:** 50% increase every 60s (max 2 pods)
- **Scale Down:** 10% decrease every 60s (5min stabilization)

```bash
# Monitor HPA status
kubectl describe hpa network-telemetry-hpa -n telemetry-system

# View scaling events
kubectl get events -n telemetry-system --sort-by='.lastTimestamp'
```

### Vertical Pod Autoscaler (VPA)

**Configuration:** `k8s/telemetry-deployment.yaml:422-444`

**Resource Limits:**
- **InfluxDB:** 500m-4000m CPU, 1-8Gi memory
- **Auto-adjustment:** VPA automatically right-sizes containers

```bash
# Check VPA recommendations
kubectl describe vpa influxdb-vpa -n telemetry-system

# View resource recommendations
kubectl get vpa influxdb-vpa -n telemetry-system -o yaml
```

### Circuit Breakers & Resilience

**Implementation:** `src/scaling.py:61-135`

**Circuit Breaker States:**
- **CLOSED:** Normal operation
- **OPEN:** Failing, blocking requests 
- **HALF_OPEN:** Testing recovery

**Configuration:**
```bash
# Environment variables for circuit breakers
CIRCUIT_FAILURE_THRESHOLD=5     # Failures before opening
CIRCUIT_RECOVERY_TIMEOUT=60     # Seconds before retry
CIRCUIT_SUCCESS_THRESHOLD=3     # Successes to close
```

### Connection Pooling

**Implementation:** `src/scaling.py:137-198`

**Pool Configuration:**
```bash
MAX_CONNECTIONS=100             # Total pool size
MAX_CONNECTIONS_PER_HOST=30     # Per-host limit
KEEPALIVE_TIMEOUT=30           # Connection reuse time
CONNECTION_TIMEOUT=10.0        # Connection timeout
READ_TIMEOUT=30.0             # Read timeout
```

## Scaling Configuration

### Environment Variables

**Docker Compose (`docker-compose.ha.yml`):**
```yaml
environment:
  # Scaling configuration
  MAX_CONNECTIONS: 50
  MAX_CONCURRENT_TARGETS: 20
  MAX_CONCURRENT_OPERATIONS: 50
  CIRCUIT_FAILURE_THRESHOLD: 3
  CIRCUIT_RECOVERY_TIMEOUT: 30
  BATCH_SIZE: 5
  WORKER_POOL_SIZE: 10
```

**Kubernetes (`k8s/telemetry-deployment.yaml`):**
```yaml
env:
  - name: MAX_CONNECTIONS
    value: "100"
  - name: MAX_CONCURRENT_TARGETS
    value: "50"
  - name: CIRCUIT_FAILURE_THRESHOLD
    value: "5"
```

### Concurrency Controls

**Implementation:** `src/scaling.py:200-256`

**Semaphore Controls:**
- **Target Slots:** Limit concurrent target processing
- **Operation Slots:** Limit concurrent operations per target
- **Batch Processing:** Process items in configurable batches
- **Worker Pool:** Dedicated worker tasks for processing

## Monitoring & Metrics

### Prometheus Metrics Collection

**Configuration:** `prometheus/prometheus.yml`

**Monitored Services:**
- Network Telemetry instances (ports 8080)
- InfluxDB instances (port 8086)
- Grafana instances (port 3000)
- HAProxy load balancer (port 8404)
- Redis cache (port 6379)

```bash
# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query scaling metrics
curl http://localhost:9090/api/v1/query?query=telemetry_collection_duration_seconds
```

### Auto-Scaling Alerts

**Configuration:** `prometheus/rules/scaling_alerts.yml`

**Alert Categories:**
- **Performance Alerts:** High CPU/memory, slow response times
- **Scaling Triggers:** Queue depth, error rates
- **High Availability:** Service instances down, circuit breakers open
- **Database Health:** Write load, disk usage, query performance

```bash
# View active alerts
curl http://localhost:9090/api/v1/alerts

# AlertManager status
curl http://localhost:9093/api/v1/status
```

## Deployment Commands

### Development Environment

```bash
# Start basic development stack
docker-compose up -d

# Run with scaling features enabled
SCALING_ENABLED=true docker-compose up -d
```

### High Availability Production

```bash
# Deploy HA stack with monitoring
docker-compose -f docker-compose.ha.yml up -d

# Scale specific services
docker-compose -f docker-compose.ha.yml up -d --scale network-telemetry-1=2

# Update configuration
docker-compose -f docker-compose.ha.yml restart load-balancer
```

### Kubernetes Production

```bash
# Deploy complete stack
kubectl apply -f k8s/telemetry-deployment.yaml

# Enable HPA
kubectl autoscale deployment network-telemetry --cpu-percent=70 --min=3 --max=20 -n telemetry-system

# Manual scaling
kubectl scale deployment network-telemetry --replicas=5 -n telemetry-system
```

## Testing Scaling Features

### Load Testing

```bash
# Test connection pooling
python scripts/testing/test_connection_pool.py

# Test circuit breaker
python scripts/testing/test_circuit_breaker.py

# Load test telemetry collection
for i in {1..100}; do 
  curl -X POST http://localhost:8080/collect &
done
```

### Scaling Validation

```bash
# Monitor HPA scaling
watch kubectl get hpa -n telemetry-system

# Monitor resource usage
watch kubectl top pods -n telemetry-system

# Check load balancer distribution
watch curl -s http://localhost:8404/stats | grep network-telemetry
```

### Health Verification

```bash
# Comprehensive service validation
python scripts/testing/service_validator.py

# Docker health checks
python scripts/testing/docker_health_check.py

# Circuit breaker status
curl http://localhost:8080/metrics | grep circuit_breaker
```

## Performance Tuning

### Resource Allocation

**Development Environment:**
```yaml
resources:
  limits:
    cpus: '0.5'
    memory: 256M
  reservations:
    cpus: '0.1'
    memory: 64M
```

**Production Environment:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi" 
    cpu: "500m"
```

### Database Optimization

**InfluxDB Scaling:**
```yaml
# Multi-instance clustering
replicas: 2
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**Storage Configuration:**
```yaml
volumeClaimTemplates:
  - metadata:
      name: influxdb-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

## Troubleshooting

### Scaling Issues

**HPA Not Scaling:**
```bash
# Check metrics server
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml

# Verify resource requests are set
kubectl describe deployment network-telemetry -n telemetry-system

# Check HPA conditions
kubectl describe hpa network-telemetry-hpa -n telemetry-system
```

**Circuit Breaker Stuck Open:**
```bash
# Check circuit breaker metrics
curl http://localhost:8080/metrics | grep circuit_breaker

# View circuit breaker logs
docker logs telemetry-service-1 | grep circuit_breaker

# Reset circuit breaker (restart service)
docker restart telemetry-service-1
```

**Load Balancer Issues:**
```bash
# Check HAProxy status
curl http://localhost:8404/stats

# Verify backend health
docker exec telemetry-lb curl -f http://influxdb-1:8086/ping

# Check load balancer logs
docker logs telemetry-lb
```

### Performance Debugging

**Connection Pool Exhaustion:**
```bash
# Monitor connection metrics
curl http://localhost:8080/metrics | grep connection_pool

# Increase pool size
docker-compose restart -e MAX_CONNECTIONS=200 network-telemetry-1
```

**High Memory Usage:**
```bash
# Check container memory
docker stats --no-stream

# Increase memory limits
kubectl patch deployment network-telemetry -n telemetry-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"telemetry","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

## Security Considerations

### Network Policies

**Kubernetes Network Isolation:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: telemetry-network-policy
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
```

### Resource Limits

**Pod Security Standards:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
  seccompProfile:
    type: RuntimeDefault
```

## Next Steps

1. **Custom Metrics:** Implement application-specific metrics for scaling
2. **Multi-Region:** Deploy across multiple availability zones
3. **Backup Strategy:** Implement automated backup and disaster recovery
4. **Cost Optimization:** Fine-tune resource allocation and scaling thresholds
5. **Advanced Monitoring:** Add distributed tracing and APM integration

---

**Built for Netflix SDE Assessment by Kevin Sapp** | **Production-Ready Auto-Scaling Architecture**
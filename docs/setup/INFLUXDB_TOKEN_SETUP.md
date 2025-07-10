# InfluxDB Token Setup Guide

## Problem
The error "invalid header field value for 'Authorization'" occurs when the InfluxDB token is not properly configured or is empty/invalid.

## Solutions

### Option 1: Generate InfluxDB Token (Recommended)

1. **Access InfluxDB UI**
   - Open http://localhost:8086
   - Login with: admin / admin123!

2. **Generate API Token**
   - Go to **Data** → **API Tokens**
   - Click **+ Generate API Token**
   - Select **Read/Write API Token**
   - Configure permissions:
     - **Buckets**: Read/Write access to `default` bucket
     - **Organization**: `nflx`
   - Copy the generated token

3. **Update Configuration**
   ```bash
   # Add to .env file:
   INFLUXDB_TOKEN=your-actual-token-here
   ```

4. **Restart Services**
   ```bash
   docker-compose restart grafana
   ```

### Option 2: Manual Datasource Configuration

1. **Access Grafana**
   - Open http://localhost:3000
   - Login with admin credentials or Google OAuth

2. **Add Datasource Manually**
   - Go to **Configuration** → **Data Sources**
   - Click **Add data source**
   - Select **InfluxDB**

3. **Configure Settings**
   ```
   Name: InfluxDB
   URL: http://influxdb2:8086
   Access: Server (default)
   
   InfluxDB Details:
   Query Language: Flux
   Organization: nflx
   Token: [paste your token here]
   Default Bucket: default
   ```

4. **Test Connection**
   - Click **Save & Test**
   - Should show "Data source is working"

### Option 3: Use Basic Auth (Alternative)

If token authentication fails, you can use basic authentication:

```yaml
# In grafana/provisioning/datasources/influxdb.yml
datasources:
  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb2:8086
    user: admin
    password: admin123!
    database: default
    jsonData:
      version: Flux
      organization: nflx
      defaultBucket: default
      tlsSkipVerify: true
```

## Troubleshooting

### Check InfluxDB Logs
```bash
docker logs influxdb2
```

### Check Grafana Logs
```bash
docker logs grafana
```

### Verify InfluxDB Setup
```bash
# Check if InfluxDB is running
curl http://localhost:8086/ping

# Check organization
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8086/api/v2/orgs
```

### Common Issues

1. **Empty Token**: Ensure INFLUXDB_TOKEN environment variable is set
2. **Wrong Organization**: Verify organization name is `nflx`
3. **Bucket Access**: Ensure token has read/write access to `default` bucket
4. **Network Issues**: Verify InfluxDB container is accessible from Grafana

## Testing the Fix

1. **Check Datasource Health**
   - Grafana → Configuration → Data Sources → InfluxDB
   - Click "Test" button
   - Should show green success message

2. **Test Query**
   ```flux
   from(bucket: "default")
     |> range(start: -1h)
     |> filter(fn: (r) => r._measurement == "network_telemetry")
     |> limit(n: 10)
   ```

3. **Check Dashboard**
   - Open Network Telemetry Dashboard
   - Panels should load data without errors
   - No "No data" messages if telemetry is running

## Security Notes

- Store tokens securely in environment variables
- Use read-only tokens for dashboards when possible
- Rotate tokens periodically
- Don't commit tokens to version control
# Geolocation Features Documentation

## Overview

The Network Telemetry Service now includes comprehensive geolocation tracking capabilities that map network connections and provide geographical context for network performance metrics.

## New Features

### 1. Geolocation Data Collection

The service now automatically collects:
- **Source Location**: Your public IP geolocation
- **Target Location**: Destination server geolocation
- **Connection Path**: Geographic route mapping
- **Distance Calculation**: Great circle distance between source and target

### 2. Geolocation Metrics

#### IP Address Resolution
- Resolves target hostnames to IP addresses
- Determines source public IP address
- Tracks IP changes over time

#### Geographic Data Points
- **Latitude/Longitude**: Precise coordinate data
- **Country/Region/City**: Location hierarchy
- **Timezone**: Local time zone information
- **ISP Information**: Internet service provider details

#### Distance Metrics
- **Great Circle Distance**: Accurate distance calculation using Haversine formula
- **Connection Distance**: Physical distance between source and target
- **Performance Correlation**: Latency vs. distance analysis

### 3. Enhanced Dashboard

The new **Geolocation Dashboard** provides:

#### Network Connection Map
- Visual representation of connection endpoints
- Geographic distribution of network targets
- Connection flow visualization

#### Distance Analysis
- Time-series tracking of connection distances
- Distance-to-latency correlation charts
- Performance metrics by geographic location

#### Connection Details Table
- Real-time location information
- ISP and timezone details
- Geographic metadata for troubleshooting

#### Target Distribution
- Pie chart showing country distribution
- Regional connection patterns
- Network routing analysis

## Technical Implementation

### Data Collection Process

1. **Hostname Resolution**: Convert target FQDN to IP address
2. **Public IP Discovery**: Determine source public IP using multiple services
3. **Geolocation Lookup**: Query ip-api.com for geographic data
4. **Distance Calculation**: Compute great circle distance
5. **Data Storage**: Store metrics in InfluxDB with geographic tags

### Geolocation API Integration

The service uses **ip-api.com** for geolocation data:
- Free service with generous rate limits
- No API key required
- Comprehensive geographic data
- High accuracy for most locations

### Data Storage Schema

New InfluxDB fields added:
```
target_ip              # Target server IP address
source_ip              # Source public IP address
target_latitude        # Target geographic latitude
target_longitude       # Target geographic longitude
target_country         # Target country name
target_region          # Target region/state
target_city            # Target city name
target_timezone        # Target timezone
target_isp             # Target ISP name
source_latitude        # Source geographic latitude
source_longitude       # Source geographic longitude
source_country         # Source country name
source_region          # Source region/state
source_city            # Source city name
source_timezone        # Source timezone
source_isp             # Source ISP name
distance_km            # Distance in kilometers
```

## Usage Examples

### Dashboard Access
1. Start the service: `docker-compose up -d`
2. Open Grafana: http://localhost:3000
3. Navigate to "Network Geolocation Dashboard"
4. View real-time geographic network data

### Query Examples

#### Distance Analysis
```flux
from(bucket: "default")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "network_telemetry")
  |> filter(fn: (r) => r._field == "distance_km")
  |> mean()
```

#### Connection Origins
```flux
from(bucket: "default")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "network_telemetry")
  |> filter(fn: (r) => r._field == "source_country")
  |> group(columns: ["_value"])
  |> count()
```

## Performance Considerations

### Network Impact
- Minimal additional network overhead
- Geolocation queries cached when possible
- Fallback handling for API failures

### Data Volume
- Moderate increase in stored data volume
- Geographic data provides valuable context
- Efficient storage using InfluxDB tags

### Reliability
- Multiple public IP detection services
- Graceful handling of geolocation failures
- Continues operation if geographic data unavailable

## Privacy and Security

### Data Handling
- No personally identifiable information stored
- Only public IP addresses used
- Geographic data is approximate (city-level)
- No tracking of individual users

### External Dependencies
- Uses public geolocation services
- All data sources are anonymous
- No authentication required
- Rate limits respected

## Troubleshooting

### Common Issues

1. **No geolocation data**: Check internet connectivity
2. **Incorrect location**: Geolocation accuracy varies by provider
3. **Missing distance**: Requires both source and target coordinates
4. **API rate limits**: Service automatically handles rate limiting

### Monitoring

Check service logs for geolocation-related messages:
```bash
docker logs network-telemetry | grep -i geolocation
```

## Future Enhancements

### Planned Features
- Route hop geolocation mapping
- Historical geographic movement tracking
- Geographic performance alerting
- Custom geolocation data sources

### Integration Opportunities
- Network topology visualization
- Geographic load balancing insights
- Regional performance optimization
- Compliance and data sovereignty tracking
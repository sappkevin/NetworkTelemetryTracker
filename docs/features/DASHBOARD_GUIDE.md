# Network Telemetry Dashboard Guide

## Available Dashboards

### 1. Network Telemetry Dashboard (`network-telemetry.json`)
**Purpose**: Core network monitoring with ping and traceroute metrics
**Features**:
- Network latency over time
- Packet loss monitoring  
- Network hop count tracking
- HTTP status code monitoring with color coding
- Success vs error rate tracking
- Basic network performance stats

### 2. Network Traffic Worldmap (`network-worldmap.json`)
**Purpose**: Geographic visualization of network traffic using Worldmap Panel
**Features**:
- **Worldmap Panel**: Displays network targets on a world map based on geolocation data
- Geographic markers showing target locations with latitude/longitude coordinates
- Color-coded markers based on latency performance
- Country distribution pie chart
- Network latency timeline

**Data Requirements**:
- `target_latitude` and `target_longitude` fields from geolocation collection
- `target_country` for geographic grouping
- `avg_latency` for performance color coding

### 3. Network Node Graph (`network-nodegraph.json`)
**Purpose**: Network topology visualization using Node Graph Panel
**Features**:
- **Node Graph Panel**: Shows connections between source and target locations
- Source and target nodes with geographic labels
- Connection edges displaying latency and packet loss metrics
- Network performance statistics (hops, latency, packet loss, distance)

**Data Requirements**:
- `source_country`, `source_city` for source node information
- `target_country`, `target_city` for target node information  
- `avg_latency` and `packet_loss` for connection metrics
- `hop_count` and `distance_km` for network topology data

### 4. Network Quality of Service (QoS) Metrics (`network-qos-metrics.json`)
**Purpose**: Advanced network quality monitoring and traffic class analysis
**Features**:
- **Jitter Monitoring**: Tracks variation in network latency over time
- **Queue Depth & Buffer Utilization**: Shows network device queue status and buffer usage
- **Traffic Class Performance**: Voice, video, and data quality scores with color-coded thresholds
- **Congestion Analysis**: Identifies network congestion and dropped packets
- **QoS Violations Counter**: Tracks when traffic classes fall below quality thresholds

**Data Requirements**:
- `jitter_ms` for latency variation measurement
- `queue_depth` and `buffer_utilization_pct` for network device status
- `voice_quality_score`, `video_quality_score`, `data_quality_score` for traffic class performance
- `congestion_drops_pct` and `congestion_level_pct` for congestion indicators
- `qos_violations` for quality threshold violations

### 5. Network Availability and Reliability (`network-availability-reliability.json`)
**Purpose**: Service uptime monitoring and reliability metrics analysis
**Features**:
- **Service Availability**: Real-time availability percentage (99.9%, 99.99%, etc.)
- **Uptime/Downtime Tracking**: Visual timeline of service status
- **MTBF (Mean Time Between Failures)**: Average time between service failures
- **MTTR (Mean Time To Recovery)**: Average time to restore service after failure
- **Service Status Distribution**: Pie chart showing available/degraded/unavailable percentages
- **SLA Monitoring**: Gauge showing service level agreement compliance

**Data Requirements**:
- `service_available` binary indicator for uptime/downtime status
- `response_success` for successful response tracking
- `service_degraded` for degraded performance detection
- `failure_count` for failure event counting
- `in_recovery` for recovery state tracking
- `service_quality_score` for overall service quality assessment

### 6. Network Throughput and Bandwidth Metrics (`network-throughput-bandwidth.json`)
**Purpose**: Network performance and capacity monitoring with throughput analysis
**Features**:
- **Throughput Performance**: Actual vs goodput (application-level) throughput tracking
- **Bandwidth Utilization**: Percentage of available bandwidth currently in use
- **Data Transfer Rates**: Real-time bits per second (bps) and packets per second (pps) monitoring
- **Interface Utilization**: Multi-speed interface monitoring (100MB, 1GB, 10GB)
- **Network Efficiency**: Performance optimization metrics and queue depth monitoring

**Data Requirements**:
- `throughput_mbps`, `goodput_mbps` for throughput performance
- `bandwidth_utilization_pct` for capacity utilization
- `bits_per_second`, `packets_per_second` for transfer rate monitoring
- `interface_1gb_util_pct`, `interface_10gb_util_pct`, `interface_100mb_util_pct` for interface monitoring
- `network_efficiency_pct`, `tx_queue_depth` for performance optimization

### 7. Network Response Time Metrics (`network-response-time.json`)
**Purpose**: Detailed response time analysis and performance breakdown monitoring
**Features**:
- **Response Time Breakdown**: Stacked visualization of DNS, TCP, application, and database components
- **DNS Resolution Monitoring**: Cache hit vs miss performance tracking
- **TCP Handshake Analysis**: Connection establishment time measurement
- **Application Response Time**: Server processing time monitoring
- **Database Query Performance**: Query type analysis (SELECT, JOIN, aggregates)
- **Performance Categories**: Response time classification (Excellent/Good/Acceptable/Poor)

**Data Requirements**:
- `dns_resolution_ms`, `dns_cache_hit` for DNS performance tracking
- `tcp_handshake_ms` for connection establishment monitoring
- `app_response_ms`, `app_type` for application performance analysis
- `db_query_ms`, `query_type` for database performance tracking
- `total_response_ms`, `response_category` for overall performance classification
- `response_efficiency_pct` for optimization scoring

## Dashboard Configuration

### Worldmap Panel Setup
The Worldmap Panel uses:
- **Location Mode**: Coordinates (latitude/longitude)
- **Latitude Field**: `target_latitude`
- **Longitude Field**: `target_longitude`
- **Color Field**: `avg_latency` (performance-based coloring)
- **Basemap**: Default OpenStreetMap

### Node Graph Panel Setup
The Node Graph Panel creates:
- **Source Node**: Represents your monitoring location
- **Target Node**: Represents the monitored network target
- **Connection Edge**: Shows network path with latency/packet loss metrics
- **Node Styling**: Color-coded by geographic region
- **Edge Styling**: Width/color based on performance metrics

## Data Collection Requirements

For these dashboards to work properly, ensure your telemetry service collects:

### Geographic Fields (17 total)
- `target_ip`, `source_ip`
- `target_latitude`, `target_longitude`
- `source_latitude`, `source_longitude`  
- `target_country`, `target_city`, `target_region`
- `source_country`, `source_city`, `source_region`
- `target_timezone`, `source_timezone`
- `target_isp`, `source_isp`
- `distance_km`

### Network Fields
- `avg_latency`, `min_latency`, `max_latency`
- `packet_loss`, `hop_count`

## Usage Instructions

1. **Start Data Collection**: Run `python telemetry_runner.py sample` to populate initial data
2. **Monitor Continuously**: Run `python telemetry_runner.py continuous` for ongoing collection
3. **Access Dashboards**: Open Grafana at http://localhost:3000
4. **View Maps**: Check the "Network Traffic Worldmap" dashboard for geographic patterns
5. **Analyze Topology**: Use the "Network Node Graph" dashboard for connection analysis

## Troubleshooting

### No Data Displayed
- Verify InfluxDB is running and accessible
- Ensure telemetry service is collecting geolocation data
- Check that the `default` bucket contains `network_telemetry` measurements

### Missing Geographic Data
- Confirm geolocation API calls are working (check logs)
- Verify latitude/longitude fields are being stored in InfluxDB
- Test with `python telemetry_runner.py single` for immediate data collection

### Dashboard Loading Issues
- Refresh the dashboard or restart Grafana
- Verify InfluxDB datasource connection in Grafana settings
- Check time range settings (data may be outside selected range)
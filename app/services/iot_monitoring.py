"""
IoT Monitoring Service for real-time data collection and processing.
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
try:
    import aiohttp
    IOT_DEPENDENCIES_AVAILABLE = True
except ImportError:
    IOT_DEPENDENCIES_AVAILABLE = False
    aiohttp = None

# Skip aioredis due to compatibility issues
aioredis = None
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.transformation_versioning import RealTimeMonitoringEndpoint
from app.models.transformation import TransformationEvent
from app.core.database import get_db

logger = get_logger(__name__)


class DataSourceType(str, Enum):
    """Types of IoT data sources."""
    SENSOR = "sensor"
    API = "api"
    FILE_UPLOAD = "file_upload"
    MANUAL = "manual"


class DataQualityLevel(str, Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"          # 0.7-0.9
    FAIR = "fair"          # 0.5-0.7
    POOR = "poor"          # 0.3-0.5
    CRITICAL = "critical"  # 0.0-0.3


@dataclass
class IoTDataPoint:
    """Represents a single IoT data point."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    quality_score: float
    source_id: str
    facility_id: str
    metadata: Dict[str, Any] = None


@dataclass
class MonitoringAlert:
    """Represents a monitoring alert."""
    alert_id: str
    endpoint_id: str
    facility_id: str
    alert_type: str
    severity: str
    message: str
    threshold_value: float
    actual_value: float
    timestamp: datetime
    is_resolved: bool = False


class IoTDataProcessor:
    """Processes IoT data and applies quality checks."""
    
    def __init__(self):
        self.quality_thresholds = {
            'temperature': {'min': -10, 'max': 100, 'variance': 5.0},
            'pressure': {'min': 0, 'max': 1000, 'variance': 10.0},
            'flow_rate': {'min': 0, 'max': 10000, 'variance': 50.0},
            'energy_consumption': {'min': 0, 'max': 1000000, 'variance': 100.0},
            'water_usage': {'min': 0, 'max': 100000, 'variance': 10.0}
        }
    
    def calculate_quality_score(self, data_point: IoTDataPoint) -> float:
        """Calculate data quality score based on various factors."""
        score = 1.0
        
        # Check if value is within expected range
        if data_point.metric_name in self.quality_thresholds:
            thresholds = self.quality_thresholds[data_point.metric_name]
            if not (thresholds['min'] <= data_point.value <= thresholds['max']):
                score -= 0.3
        
        # Check timestamp freshness (data should be within last 5 minutes)
        age_minutes = (datetime.utcnow() - data_point.timestamp).total_seconds() / 60
        if age_minutes > 5:
            score -= 0.2
        elif age_minutes > 1:
            score -= 0.1
        
        # Check for reasonable variance (simplified)
        if data_point.metadata and 'previous_value' in data_point.metadata:
            prev_value = data_point.metadata['previous_value']
            variance = abs(data_point.value - prev_value) / max(prev_value, 1)
            if variance > 0.5:  # 50% variance
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def get_quality_level(self, score: float) -> DataQualityLevel:
        """Convert quality score to quality level."""
        if score >= 0.9:
            return DataQualityLevel.EXCELLENT
        elif score >= 0.7:
            return DataQualityLevel.GOOD
        elif score >= 0.5:
            return DataQualityLevel.FAIR
        elif score >= 0.3:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL


class IoTDataCollector:
    """Collects data from various IoT sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = IoTDataProcessor()
        self.redis_client = None
    
    async def initialize_redis(self):
        """Initialize Redis connection for caching."""
        if not IOT_DEPENDENCIES_AVAILABLE or aioredis is None:
            logger.warning("Redis not available for IoT monitoring. Monitoring will work in limited mode.")
            return
            
        try:
            self.redis_client = aioredis.from_url("redis://localhost:6379")
            await self.redis_client.ping()
            logger.info("Redis connection established for IoT monitoring")
        except Exception as e:
            logger.warning(f"Redis not available for IoT monitoring: {e}")
    
    async def collect_sensor_data(self, endpoint: RealTimeMonitoringEndpoint) -> List[IoTDataPoint]:
        """Collect data from IoT sensors."""
        data_points = []
        
        try:
            # Simulate sensor data collection
            # In real implementation, this would connect to actual sensors
            sensor_data = await self._read_sensor_data(endpoint)
            
            for metric_name, value in sensor_data.items():
                if metric_name in endpoint.monitored_metrics:
                    data_point = IoTDataPoint(
                        timestamp=datetime.utcnow(),
                        metric_name=metric_name,
                        value=value['value'],
                        unit=value['unit'],
                        quality_score=0.0,  # Will be calculated
                        source_id=endpoint.id,
                        facility_id=endpoint.facility_id,
                        metadata=value.get('metadata', {})
                    )
                    
                    # Calculate quality score
                    data_point.quality_score = self.processor.calculate_quality_score(data_point)
                    data_points.append(data_point)
            
            logger.info(f"Collected {len(data_points)} data points from sensor {endpoint.endpoint_name}")
            
        except Exception as e:
            logger.error(f"Error collecting sensor data from {endpoint.endpoint_name}: {e}")
            # Update endpoint error count
            endpoint.error_count += 1
            endpoint.last_error = str(e)
            self.db.commit()
        
        return data_points
    
    async def collect_api_data(self, endpoint: RealTimeMonitoringEndpoint) -> List[IoTDataPoint]:
        """Collect data from external APIs."""
        data_points = []
        
        if not IOT_DEPENDENCIES_AVAILABLE:
            logger.warning("aiohttp not available. API data collection disabled.")
            return data_points
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                
                # Add authentication if configured
                if endpoint.auth_type == 'api_key' and endpoint.auth_config:
                    headers['Authorization'] = f"Bearer {endpoint.auth_config.get('api_key')}"
                
                async with session.get(endpoint.endpoint_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for metric_name, value in data.items():
                            if metric_name in endpoint.monitored_metrics:
                                data_point = IoTDataPoint(
                                    timestamp=datetime.utcnow(),
                                    metric_name=metric_name,
                                    value=float(value.get('value', 0)),
                                    unit=value.get('unit', ''),
                                    quality_score=0.0,
                                    source_id=endpoint.id,
                                    facility_id=endpoint.facility_id,
                                    metadata=value.get('metadata', {})
                                )
                                
                                data_point.quality_score = self.processor.calculate_quality_score(data_point)
                                data_points.append(data_point)
                    else:
                        raise Exception(f"API returned status {response.status}")
            
            logger.info(f"Collected {len(data_points)} data points from API {endpoint.endpoint_name}")
            
        except Exception as e:
            logger.error(f"Error collecting API data from {endpoint.endpoint_name}: {e}")
            endpoint.error_count += 1
            endpoint.last_error = str(e)
            self.db.commit()
        
        return data_points
    
    async def _read_sensor_data(self, endpoint: RealTimeMonitoringEndpoint) -> Dict[str, Any]:
        """Simulate reading from actual sensors."""
        # In real implementation, this would connect to actual IoT sensors
        # For now, we'll simulate realistic data based on transformation type
        
        base_data = {
            'temperature': {'value': 75.0 + (time.time() % 10), 'unit': '°C'},
            'pressure': {'value': 2.5 + (time.time() % 0.5), 'unit': 'bar'},
            'flow_rate': {'value': 150.0 + (time.time() % 20), 'unit': 'L/min'},
            'energy_consumption': {'value': 2500.0 + (time.time() % 100), 'unit': 'kWh'},
            'water_usage': {'value': 500.0 + (time.time() % 50), 'unit': 'L'},
            'vibration': {'value': 0.5 + (time.time() % 0.2), 'unit': 'mm/s'},
            'ph_level': {'value': 6.8 + (time.time() % 0.4), 'unit': 'pH'},
            'moisture_content': {'value': 15.0 + (time.time() % 3), 'unit': '%'}
        }
        
        # Filter based on monitored metrics
        return {k: v for k, v in base_data.items() if k in endpoint.monitored_metrics}
    
    async def process_data_points(self, data_points: List[IoTDataPoint]) -> List[Dict[str, Any]]:
        """Process and store data points."""
        processed_data = []
        
        for data_point in data_points:
            # Determine quality level
            quality_level = self.processor.get_quality_level(data_point.quality_score)
            
            # Create processed data record
            processed_record = {
                'timestamp': data_point.timestamp.isoformat(),
                'metric_name': data_point.metric_name,
                'value': data_point.value,
                'unit': data_point.unit,
                'quality_score': data_point.quality_score,
                'quality_level': quality_level.value,
                'source_id': data_point.source_id,
                'facility_id': data_point.facility_id,
                'metadata': data_point.metadata or {}
            }
            
            processed_data.append(processed_record)
            
            # Store in Redis for real-time access
            if self.redis_client:
                cache_key = f"iot_data:{data_point.facility_id}:{data_point.metric_name}"
                await self.redis_client.setex(
                    cache_key, 
                    300,  # 5 minutes TTL
                    json.dumps(processed_record)
                )
        
        return processed_data
    
    async def check_alerts(self, data_points: List[IoTDataPoint]) -> List[MonitoringAlert]:
        """Check for monitoring alerts based on data points."""
        alerts = []
        
        # Define alert thresholds
        alert_thresholds = {
            'temperature': {'high': 90, 'low': 10},
            'pressure': {'high': 5.0, 'low': 0.5},
            'flow_rate': {'high': 200, 'low': 10},
            'energy_consumption': {'high': 5000, 'low': 100},
            'water_usage': {'high': 1000, 'low': 50}
        }
        
        for data_point in data_points:
            if data_point.metric_name in alert_thresholds:
                thresholds = alert_thresholds[data_point.metric_name]
                
                # Check high threshold
                if data_point.value > thresholds['high']:
                    alert = MonitoringAlert(
                        alert_id=f"high_{data_point.metric_name}_{int(time.time())}",
                        endpoint_id=data_point.source_id,
                        facility_id=data_point.facility_id,
                        alert_type='threshold_exceeded',
                        severity='high',
                        message=f"{data_point.metric_name} exceeded high threshold",
                        threshold_value=thresholds['high'],
                        actual_value=data_point.value,
                        timestamp=datetime.utcnow()
                    )
                    alerts.append(alert)
                
                # Check low threshold
                elif data_point.value < thresholds['low']:
                    alert = MonitoringAlert(
                        alert_id=f"low_{data_point.metric_name}_{int(time.time())}",
                        endpoint_id=data_point.source_id,
                        facility_id=data_point.facility_id,
                        alert_type='threshold_below',
                        severity='medium',
                        message=f"{data_point.metric_name} below low threshold",
                        threshold_value=thresholds['low'],
                        actual_value=data_point.value,
                        timestamp=datetime.utcnow()
                    )
                    alerts.append(alert)
        
        return alerts


class RealTimeMonitoringOrchestrator:
    """Orchestrates real-time monitoring across all endpoints."""
    
    def __init__(self, db: Session):
        self.db = db
        self.collector = IoTDataCollector(db)
        self.running = False
        self.tasks = []
    
    async def start_monitoring(self):
        """Start real-time monitoring for all active endpoints."""
        await self.collector.initialize_redis()
        self.running = True
        
        # Get all active monitoring endpoints
        endpoints = self.db.query(RealTimeMonitoringEndpoint).filter(
            RealTimeMonitoringEndpoint.is_active == True
        ).all()
        
        # Create monitoring tasks for each endpoint
        for endpoint in endpoints:
            task = asyncio.create_task(self._monitor_endpoint(endpoint))
            self.tasks.append(task)
        
        logger.info(f"Started monitoring {len(endpoints)} endpoints")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks."""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Stopped all monitoring tasks")
    
    async def _monitor_endpoint(self, endpoint: RealTimeMonitoringEndpoint):
        """Monitor a specific endpoint."""
        while self.running:
            try:
                # Collect data based on endpoint type
                if endpoint.endpoint_type == 'sensor':
                    data_points = await self.collector.collect_sensor_data(endpoint)
                elif endpoint.endpoint_type == 'api':
                    data_points = await self.collector.collect_api_data(endpoint)
                else:
                    # Skip other types for now
                    data_points = []
                
                if data_points:
                    # Process data points
                    processed_data = await self.collector.process_data_points(data_points)
                    
                    # Check for alerts
                    alerts = await self.collector.check_alerts(data_points)
                    
                    # Update endpoint status
                    endpoint.last_data_received = datetime.utcnow()
                    endpoint.error_count = 0  # Reset on successful data collection
                    self.db.commit()
                    
                    # Log results
                    logger.info(f"Processed {len(processed_data)} data points from {endpoint.endpoint_name}")
                    if alerts:
                        logger.warning(f"Generated {len(alerts)} alerts from {endpoint.endpoint_name}")
                
                # Wait for next collection cycle
                await asyncio.sleep(endpoint.update_frequency)
                
            except Exception as e:
                logger.error(f"Error monitoring endpoint {endpoint.endpoint_name}: {e}")
                endpoint.error_count += 1
                endpoint.last_error = str(e)
                self.db.commit()
                
                # Wait before retrying
                await asyncio.sleep(60)  # 1 minute retry delay
    
    async def get_real_time_data(self, facility_id: str, metric_name: str = None) -> Dict[str, Any]:
        """Get real-time data for a facility."""
        if not self.collector.redis_client:
            return {}
        
        try:
            if metric_name:
                # Get specific metric
                cache_key = f"iot_data:{facility_id}:{metric_name}"
                data = await self.collector.redis_client.get(cache_key)
                return json.loads(data) if data else {}
            else:
                # Get all metrics for facility
                pattern = f"iot_data:{facility_id}:*"
                keys = await self.collector.redis_client.keys(pattern)
                data = {}
                
                for key in keys:
                    value = await self.collector.redis_client.get(key)
                    if value:
                        metric_data = json.loads(value)
                        data[metric_data['metric_name']] = metric_data
                
                return data
                
        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            return {}
    
    async def get_facility_health(self, facility_id: str) -> Dict[str, Any]:
        """Get overall health status for a facility."""
        endpoints = self.db.query(RealTimeMonitoringEndpoint).filter(
            RealTimeMonitoringEndpoint.facility_id == facility_id,
            RealTimeMonitoringEndpoint.is_active == True
        ).all()
        
        health_status = {
            'facility_id': facility_id,
            'total_endpoints': len(endpoints),
            'healthy_endpoints': 0,
            'unhealthy_endpoints': 0,
            'last_data_received': None,
            'overall_health': 'unknown'
        }
        
        for endpoint in endpoints:
            if endpoint.error_count == 0 and endpoint.last_data_received:
                health_status['healthy_endpoints'] += 1
                if not health_status['last_data_received'] or endpoint.last_data_received > health_status['last_data_received']:
                    health_status['last_data_received'] = endpoint.last_data_received
            else:
                health_status['unhealthy_endpoints'] += 1
        
        # Determine overall health
        if health_status['healthy_endpoints'] == health_status['total_endpoints']:
            health_status['overall_health'] = 'healthy'
        elif health_status['healthy_endpoints'] > 0:
            health_status['overall_health'] = 'degraded'
        else:
            health_status['overall_health'] = 'unhealthy'
        
        return health_status

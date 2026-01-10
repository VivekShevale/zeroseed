import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models.schemas import ServiceMetrics, IssueType, HealthStatus
from src.utils.logger import logger
from config.settings import config

class ServiceMonitor:
    """Service monitoring and metrics collection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Self-Healing-Agent/1.0"
        })
        self.session.timeout = (3, 10)  # Connect timeout, read timeout
        self.metrics_cache = {}
    
    def collect_metrics(self, service: Dict[str, Any]) -> Optional[ServiceMetrics]:
        """Collect metrics from a service"""
        service_id = service["service_id"]
        
        try:
            # Measure latency
            start_time = time.time()
            
            # Try health endpoint first
            health_url = f"{service['service_url'].rstrip('/')}{service.get('health_endpoint', '/health')}"
            health_response = self._make_request(health_url, method="GET")
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            if health_response is None:
                return ServiceMetrics(
                    service_id=service_id,
                    health=HealthStatus.DOWN,
                    latency=latency,
                    error_rate=1.0
                )
            
            # Parse health response
            health_data = health_response.json()
            health_status = self._parse_health_status(health_data)
            
            # Collect additional metrics if available
            metrics_url = service.get("metrics_url")
            additional_metrics = {}
            
            if metrics_url and metrics_url != health_url:
                metrics_response = self._make_request(metrics_url, method="GET")
                if metrics_response:
                    try:
                        additional_metrics = metrics_response.json()
                    except:
                        pass
            
            # Build metrics object
            metrics = ServiceMetrics(
                service_id=service_id,
                health=health_status,
                latency=latency,
                cpu=additional_metrics.get("cpu"),
                memory=additional_metrics.get("memory"),
                error_rate=additional_metrics.get("error_rate", 0.0),
                response_time=additional_metrics.get("response_time"),
                throughput=additional_metrics.get("throughput"),
                custom_metrics=additional_metrics.get("custom_metrics")
            )
            
            # Cache metrics
            self.metrics_cache[service_id] = {
                "metrics": metrics.dict(),
                "timestamp": datetime.utcnow()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_id}: {e}")
            return ServiceMetrics(
                service_id=service_id,
                health=HealthStatus.DOWN,
                error_rate=1.0
            )
    
    def detect_anomalies(self, metrics: ServiceMetrics, service: Dict[str, Any]) -> List[IssueType]:
        """Detect anomalies based on metrics and thresholds"""
        anomalies = []
        
        # Check basic health
        if metrics.health == HealthStatus.DOWN:
            anomalies.append(IssueType.SERVICE_DOWN)
        
        # Check thresholds
        if metrics.memory and metrics.memory > config.THRESHOLDS["memory"]:
            anomalies.append(IssueType.MEMORY_PRESSURE)
        
        if metrics.latency and metrics.latency > config.THRESHOLDS["latency"]:
            anomalies.append(IssueType.HIGH_LATENCY)
        
        if metrics.cpu and metrics.cpu > config.THRESHOLDS["cpu"]:
            anomalies.append(IssueType.HIGH_CPU)
        
        if metrics.error_rate and metrics.error_rate > config.THRESHOLDS["error_rate"]:
            anomalies.append(IssueType.HIGH_ERROR_RATE)
        
        # Check custom thresholds from service config
        custom_thresholds = service.get("custom_thresholds", {})
        for metric_name, threshold in custom_thresholds.items():
            metric_value = getattr(metrics, metric_name, None)
            if metric_value is not None and metric_value > threshold:
                anomalies.append(IssueType.CUSTOM)
        
        # Detect trends (e.g., increasing memory usage)
        trend_anomalies = self._detect_trend_anomalies(metrics, service)
        anomalies.extend(trend_anomalies)
        
        return anomalies
    
    def _detect_trend_anomalies(self, metrics: ServiceMetrics, service: Dict[str, Any]) -> List[IssueType]:
        """Detect anomalies based on trends"""
        service_id = service["service_id"]
        anomalies = []
        
        # Get historical metrics from cache/database
        historical_data = self._get_historical_metrics(service_id, window_minutes=15)
        
        if len(historical_data) < 5:  # Need minimum data points
            return anomalies
        
        # Check for rapid increase in memory
        if metrics.memory:
            recent_memory = [m.get("memory", 0) for m in historical_data[-5:]]
            if len(recent_memory) >= 3:
                memory_increase = recent_memory[-1] - recent_memory[0]
                if memory_increase > 20:  # 20% increase in last 5 checks
                    anomalies.append(IssueType.MEMORY_PRESSURE)
        
        # Check for increasing error rate
        if metrics.error_rate:
            recent_errors = [m.get("error_rate", 0) for m in historical_data[-5:]]
            if len(recent_errors) >= 3:
                error_increase = recent_errors[-1] - recent_errors[0]
                if error_increase > 0.1:  # 10% increase in error rate
                    anomalies.append(IssueType.HIGH_ERROR_RATE)
        
        return anomalies
    
    def _get_historical_metrics(self, service_id: str, window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis"""
        try:
            # Check cache first
            cache_key = f"{service_id}_history"
            if cache_key in self.metrics_cache:
                cached_data = self.metrics_cache[cache_key]
                if (datetime.utcnow() - cached_data["timestamp"]).seconds < 60:
                    return cached_data["data"]
            
            # Query database
            from src.models.database import db_instance
            metrics_col = db_instance.db.metrics_history
            
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            historical = list(metrics_col.find({
                "service_id": service_id,
                "timestamp": {"$gte": cutoff}
            }).sort("timestamp", 1))
            
            # Cache the result
            self.metrics_cache[cache_key] = {
                "data": historical,
                "timestamp": datetime.utcnow()
            }
            
            return historical
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []
    
    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.request(method, url, timeout=(3, 10), **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == config.MAX_RETRIES - 1:
                    logger.debug(f"Request failed after {config.MAX_RETRIES} attempts: {url}")
                    return None
                time.sleep(config.RETRY_DELAY)
        
        return None
    
    def _parse_health_status(self, health_data: Dict[str, Any]) -> HealthStatus:
        """Parse health status from response"""
        try:
            if isinstance(health_data, dict):
                status = health_data.get("status", "").upper()
                if status == "UP":
                    return HealthStatus.UP
                elif status == "DOWN":
                    return HealthStatus.DOWN
                elif status == "DEGRADED":
                    return HealthStatus.DEGRADED
            
            # Default to UP if we got a successful response
            return HealthStatus.UP
        except:
            return HealthStatus.DEGRADED
    
    def bulk_monitor(self, services: List[Dict[str, Any]]) -> Dict[str, ServiceMetrics]:
        """Monitor multiple services in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(10, len(services))) as executor:
            future_to_service = {
                executor.submit(self.collect_metrics, service): service
                for service in services
            }
            
            for future in as_completed(future_to_service):
                service = future_to_service[future]
                try:
                    metrics = future.result(timeout=15)
                    if metrics:
                        results[service["service_id"]] = metrics
                except Exception as e:
                    logger.error(f"Error monitoring {service['service_id']}: {e}")
        
        return results
"""
Metrics calculation utilities for statistical analysis.
"""
from typing import List, Optional, Dict, Any
import statistics
from datetime import datetime, timedelta
import numpy as np

def calculate_percentile(values: List[float], percentile: float) -> Optional[float]:
    """
    Calculate percentile from a list of values.
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
    
    Returns:
        Percentile value or None if insufficient data
    """
    if not values:
        return None
    
    try:
        if len(values) == 1:
            return values[0]
        
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower_index = int(index)
        upper_index = lower_index + 1
        
        if upper_index >= len(sorted_values):
            return sorted_values[lower_index]
        
        weight = index - lower_index
        return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
        
    except Exception:
        return None

def calculate_rate(success_count: int, total_count: int, window: int = 1) -> float:
    """
    Calculate success rate with smoothing.
    
    Args:
        success_count: Number of successful events
        total_count: Total number of events
        window: Smoothing window
    
    Returns:
        Success rate (0-1)
    """
    if total_count == 0:
        return 0.0
    
    # Apply Laplace smoothing to avoid extreme values
    alpha = 1  # Smoothing factor
    return (success_count + alpha) / (total_count + alpha * window)

def calculate_trend(values: List[float], window: int = 5) -> Dict[str, Any]:
    """
    Calculate trend metrics for a time series.
    
    Args:
        values: Time series values
        window: Window size for moving average
    
    Returns:
        Dictionary with trend metrics
    """
    if not values:
        return {
            "trend": "insufficient_data",
            "slope": 0,
            "moving_average": None,
            "volatility": 0
        }
    
    try:
        # Calculate linear regression slope
        n = len(values)
        x = list(range(n))
        
        if n > 1:
            # Simple linear regression
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(x[i] * values[i] for i in range(n))
            sum_x2 = sum(x_i * x_i for x_i in x)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Determine trend direction
            if slope > 0.1:
                trend = "increasing"
            elif slope < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Calculate moving average
            if n >= window:
                moving_avg = sum(values[-window:]) / window
            else:
                moving_avg = sum(values) / n
            
            # Calculate volatility (standard deviation)
            if n >= 2:
                volatility = statistics.stdev(values)
            else:
                volatility = 0
            
            return {
                "trend": trend,
                "slope": slope,
                "moving_average": moving_avg,
                "volatility": volatility,
                "current": values[-1],
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values)
            }
        else:
            return {
                "trend": "insufficient_data",
                "slope": 0,
                "moving_average": values[0],
                "volatility": 0,
                "current": values[0]
            }
            
    except Exception as e:
        return {
            "trend": "error",
            "error": str(e),
            "slope": 0,
            "moving_average": None
        }

def calculate_anomaly_score(current: float, historical: List[float], 
                           method: str = "zscore") -> Dict[str, Any]:
    """
    Calculate anomaly score for a value compared to historical data.
    
    Args:
        current: Current value
        historical: List of historical values
        method: Scoring method ('zscore', 'iqr', 'percentile')
    
    Returns:
        Anomaly score and metrics
    """
    if not historical or len(historical) < 5:
        return {
            "score": 0,
            "is_anomaly": False,
            "method": method,
            "reason": "insufficient_data"
        }
    
    try:
        if method == "zscore":
            mean = statistics.mean(historical)
            stdev = statistics.stdev(historical) if len(historical) > 1 else 0
            
            if stdev > 0:
                zscore = (current - mean) / stdev
                is_anomaly = abs(zscore) > 3  # 3 sigma rule
                return {
                    "score": zscore,
                    "is_anomaly": is_anomaly,
                    "method": method,
                    "mean": mean,
                    "stdev": stdev,
                    "threshold": 3
                }
        
        elif method == "iqr":
            q1 = calculate_percentile(historical, 25)
            q3 = calculate_percentile(historical, 75)
            
            if q1 is not None and q3 is not None:
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                is_anomaly = current < lower_bound or current > upper_bound
                
                return {
                    "score": (current - q1) / iqr if iqr > 0 else 0,
                    "is_anomaly": is_anomaly,
                    "method": method,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound
                }
        
        elif method == "percentile":
            percentile = sum(1 for v in historical if v <= current) / len(historical) * 100
            is_anomaly = percentile > 95 or percentile < 5
            
            return {
                "score": percentile,
                "is_anomaly": is_anomaly,
                "method": method,
                "percentile": percentile
            }
        
    except Exception as e:
        return {
            "score": 0,
            "is_anomaly": False,
            "method": method,
            "error": str(e)
        }
    
    # Default fallback
    return {
        "score": 0,
        "is_anomaly": False,
        "method": method,
        "reason": "calculation_failed"
    }

def calculate_composite_score(metrics: Dict[str, float], 
                            weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate composite score from multiple metrics.
    
    Args:
        metrics: Dictionary of metric names and values
        weights: Optional weights for each metric
    
    Returns:
        Composite score (0-1)
    """
    if not metrics:
        return 0.0
    
    # Default weights
    if weights is None:
        weights = {
            "health": 0.3,
            "latency": 0.2,
            "error_rate": 0.2,
            "cpu": 0.15,
            "memory": 0.15
        }
    
    try:
        score = 0
        total_weight = 0
        
        for metric, value in metrics.items():
            if metric in weights:
                # Normalize value to 0-1 scale
                if metric in ["health"]:
                    # Health: UP=1, DEGRADED=0.5, DOWN=0
                    normalized = {"UP": 1.0, "DEGRADED": 0.5, "DOWN": 0.0}.get(str(value).upper(), 0)
                elif metric in ["error_rate"]:
                    normalized = max(0, 1 - value)  # Lower error rate is better
                elif metric in ["latency", "cpu", "memory"]:
                    normalized = max(0, 1 - value / 100)  # Assume percentage
                else:
                    normalized = max(0, min(1, value))  # Clamp to 0-1
                
                score += normalized * weights[metric]
                total_weight += weights[metric]
        
        return score / total_weight if total_weight > 0 else 0
        
    except Exception:
        return 0.0

def calculate_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """
    Calculate correlation coefficient between two series.
    
    Args:
        x: First series
        y: Second series
    
    Returns:
        Correlation coefficient or None if insufficient data
    """
    if len(x) != len(y) or len(x) < 2:
        return None
    
    try:
        # Simple Pearson correlation
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        denominator_x = sum((xi - mean_x) ** 2 for xi in x)
        denominator_y = sum((yi - mean_y) ** 2 for yi in y)
        
        if denominator_x > 0 and denominator_y > 0:
            return numerator / (denominator_x * denominator_y) ** 0.5
        else:
            return 0.0
            
    except Exception:
        return None
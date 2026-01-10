"""
Validation utilities for input data and configurations.
"""
import re
from typing import Any, Dict, Optional, List, Union
from urllib.parse import urlparse
import ipaddress

def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        require_https: Require HTTPS scheme
    
    Returns:
        True if valid URL
    """
    try:
        result = urlparse(url)
        
        # Check scheme
        if require_https and result.scheme != 'https':
            return False
        
        if result.scheme not in ('http', 'https'):
            return False
        
        # Check netloc (domain)
        if not result.netloc:
            return False
        
        # Basic domain validation
        if '.' not in result.netloc:
            return False
        
        return True
        
    except Exception:
        return False

def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address.
    
    Args:
        ip: IP address to validate
    
    Returns:
        True if valid IP address
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port: Union[int, str]) -> bool:
    """
    Validate port number.
    
    Args:
        port: Port number
    
    Returns:
        True if valid port
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False

def validate_service_id(service_id: str) -> bool:
    """
    Validate service identifier.
    
    Args:
        service_id: Service ID
    
    Returns:
        True if valid service ID
    """
    if not service_id or not isinstance(service_id, str):
        return False
    
    # Allow alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, service_id))

def validate_metrics(metrics: Dict[str, Any]) -> List[str]:
    """
    Validate metrics dictionary.
    
    Args:
        metrics: Metrics dictionary
    
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(metrics, dict):
        return ["Metrics must be a dictionary"]
    
    # Validate health status if present
    if 'health' in metrics:
        health = str(metrics['health']).upper()
        if health not in ('UP', 'DOWN', 'DEGRADED'):
            errors.append(f"Invalid health status: {health}")
    
    # Validate numeric metrics
    numeric_fields = ['cpu', 'memory', 'latency', 'error_rate', 'response_time', 'throughput']
    
    for field in numeric_fields:
        if field in metrics:
            value = metrics[field]
            if value is not None:
                try:
                    float_value = float(value)
                    if field in ['cpu', 'memory'] and not (0 <= float_value <= 100):
                        errors.append(f"{field} must be between 0 and 100")
                    elif field == 'error_rate' and not (0 <= float_value <= 1):
                        errors.append("error_rate must be between 0 and 1")
                    elif field in ['latency', 'response_time'] and float_value < 0:
                        errors.append(f"{field} must be non-negative")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be a number")
    
    return errors

def validate_thresholds(thresholds: Dict[str, Any]) -> List[str]:
    """
    Validate threshold values.
    
    Args:
        thresholds: Thresholds dictionary
    
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(thresholds, dict):
        return ["Thresholds must be a dictionary"]
    
    for key, value in thresholds.items():
        if value is None:
            continue
        
        try:
            float_value = float(value)
            
            if key in ['memory', 'cpu']:
                if not (0 <= float_value <= 100):
                    errors.append(f"{key} threshold must be between 0 and 100")
            elif key == 'error_rate':
                if not (0 <= float_value <= 1):
                    errors.append("error_rate threshold must be between 0 and 1")
            elif key in ['latency', 'response_time']:
                if float_value < 0:
                    errors.append(f"{key} threshold must be non-negative")
            # Allow custom thresholds
                
        except (ValueError, TypeError):
            errors.append(f"{key} threshold must be a number")
    
    return errors

def validate_api_key(api_key: str, allowed_keys: List[str]) -> bool:
    """
    Validate API key.
    
    Args:
        api_key: API key to validate
        allowed_keys: List of allowed API keys
    
    Returns:
        True if valid API key
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Check if API key is in allowed list
    if api_key in allowed_keys:
        return True
    
    # Also check environment variable if provided as single string
    if ',' in api_key:
        provided_keys = [k.strip() for k in api_key.split(',')]
        return any(key in allowed_keys for key in provided_keys)
    
    return False

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address
    
    Returns:
        True if valid email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number
    
    Returns:
        True if valid phone number
    """
    # Simple validation for demonstration
    pattern = r'^\+?[0-9\s\-\(\)]{10,}$'
    return bool(re.match(pattern, phone.replace(' ', '')))

def validate_json_schema(data: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a simple JSON schema.
    
    Args:
        data: Data to validate
        schema: Schema definition
    
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(schema, dict):
        return ["Schema must be a dictionary"]
    
    for field, rules in schema.items():
        if rules.get('required', False) and field not in data:
            errors.append(f"Missing required field: {field}")
            continue
        
        if field in data:
            value = data[field]
            
            # Type validation
            expected_type = rules.get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"{field} must be a string")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"{field} must be a number")
                elif expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"{field} must be an integer")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"{field} must be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"{field} must be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"{field} must be an object")
            
            # Enum validation
            enum_values = rules.get('enum')
            if enum_values and value not in enum_values:
                errors.append(f"{field} must be one of {enum_values}")
            
            # Range validation for numbers
            if isinstance(value, (int, float)):
                min_val = rules.get('minimum')
                max_val = rules.get('maximum')
                
                if min_val is not None and value < min_val:
                    errors.append(f"{field} must be at least {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"{field} must be at most {max_val}")
            
            # String length validation
            if isinstance(value, str):
                min_length = rules.get('minLength')
                max_length = rules.get('maxLength')
                
                if min_length is not None and len(value) < min_length:
                    errors.append(f"{field} must be at least {min_length} characters")
                if max_length is not None and len(value) > max_length:
                    errors.append(f"{field} must be at most {max_length} characters")
                
                # Pattern validation
                pattern = rules.get('pattern')
                if pattern and not re.match(pattern, value):
                    errors.append(f"{field} does not match required pattern")
    
    return errors

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: Input string
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ''
    
    # Trim whitespace
    sanitized = input_str.strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove control characters (except newline and tab)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    return sanitized
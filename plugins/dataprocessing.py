# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Data Processing Plugin for SWARMZ

Provides data manipulation and processing capabilities.
"""

import json
import hashlib
from typing import Any, Dict, List


def register(executor):
    """Register data processing tasks with the executor."""
    
    def json_parse(json_string: str) -> Any:
        """Parse JSON string to Python object."""
        return json.loads(json_string)
    
    def json_stringify(obj: Any) -> str:
        """Convert Python object to JSON string."""
        return json.dumps(obj, indent=2)
    
    def hash_string(text: str, algorithm: str = "sha256") -> str:
        """Generate hash of a string."""
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(text.encode())
        return hash_func.hexdigest()
    
    def transform_data(data: List[Dict], operation: str) -> Any:
        """
        Transform data based on operation.
        Operations: count, sum, average, filter
        """
        if operation == "count":
            return len(data)
        elif operation == "sum" and data and isinstance(data[0], (int, float)):
            return sum(data)
        elif operation == "keys" and data and isinstance(data[0], dict):
            return list(data[0].keys())
        return data
    
    def encode_decode(text: str, operation: str = "base64_encode") -> str:
        """Encode or decode text."""
        import base64
        
        if operation == "base64_encode":
            return base64.b64encode(text.encode()).decode()
        elif operation == "base64_decode":
            return base64.b64decode(text.encode()).decode()
        return text
    
    # Register all tasks
    executor.register_task("data_json_parse", json_parse, {
        "description": "Parse JSON string",
        "params": {"json_string": "string"},
        "category": "data"
    })
    
    executor.register_task("data_json_stringify", json_stringify, {
        "description": "Convert object to JSON",
        "params": {"obj": "any"},
        "category": "data"
    })
    
    executor.register_task("data_hash", hash_string, {
        "description": "Generate hash of string",
        "params": {"text": "string", "algorithm": "string"},
        "category": "data"
    })
    
    executor.register_task("data_transform", transform_data, {
        "description": "Transform data collection",
        "params": {"data": "list", "operation": "string"},
        "category": "data"
    })
    
    executor.register_task("data_encode", encode_decode, {
        "description": "Encode or decode text",
        "params": {"text": "string", "operation": "string"},
        "category": "data"
    })


# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
File System Operations Plugin for SWARMZ

Provides file system manipulation capabilities while maintaining operator sovereignty.
"""

import os
from pathlib import Path
from typing import List, Dict, Any


def register(executor):
    """Register file system tasks with the executor."""
    
    def list_directory(path: str = ".") -> List[str]:
        """List contents of a directory."""
        return os.listdir(path)
    
    def read_file(filepath: str) -> str:
        """Read contents of a file."""
        with open(filepath, 'r') as f:
            return f.read()
    
    def write_file(filepath: str, content: str) -> str:
        """Write content to a file."""
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    
    def create_directory(path: str) -> str:
        """Create a directory."""
        os.makedirs(path, exist_ok=True)
        return f"Directory created: {path}"
    
    def file_info(filepath: str) -> Dict[str, Any]:
        """Get information about a file."""
        p = Path(filepath)
        return {
            "exists": p.exists(),
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "size": p.stat().st_size if p.exists() else 0,
            "absolute_path": str(p.absolute())
        }
    
    # Register all tasks
    executor.register_task("fs_list", list_directory, {
        "description": "List directory contents",
        "params": {"path": "string"},
        "category": "filesystem"
    })
    
    executor.register_task("fs_read", read_file, {
        "description": "Read file contents",
        "params": {"filepath": "string"},
        "category": "filesystem"
    })
    
    executor.register_task("fs_write", write_file, {
        "description": "Write content to file",
        "params": {"filepath": "string", "content": "string"},
        "category": "filesystem"
    })
    
    executor.register_task("fs_mkdir", create_directory, {
        "description": "Create a directory",
        "params": {"path": "string"},
        "category": "filesystem"
    })
    
    executor.register_task("fs_info", file_info, {
        "description": "Get file information",
        "params": {"filepath": "string"},
        "category": "filesystem"
    })


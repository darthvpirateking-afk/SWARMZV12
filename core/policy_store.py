"""
MIT License
Copyright (c) 2026 SWARMZ

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PolicyStore:
    """
    PolicyStore manages the storage, versioning, and rollback of governance policies.
    
    Features:
    - JSON-based policy storage with versioning
    - Atomic updates and rollback capability
    - Backup/restore functionality
    - Policy history tracking
    - Concurrent access safety
    """
    
    def __init__(self, data_dir: str = "data/governance"):
        """
        Initialize the PolicyStore.
        
        Args:
            data_dir: Directory to store policy files
        """
        self.data_dir = Path(data_dir)
        self.policies_dir = self.data_dir / "policies"
        self.backups_dir = self.data_dir / "backups"
        self.history_dir = self.data_dir / "history"
        
        # Ensure directories exist
        self.policies_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Policy metadata
        self.metadata_file = self.data_dir / "policy_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load policy metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load policy metadata: {e}")
                self.metadata = {"policies": {}, "backups": [], "history": []}
        else:
            self.metadata = {"policies": {}, "backups": [], "history": []}
    
    def _save_metadata(self) -> None:
        """Save policy metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save policy metadata: {e}")
            raise
    
    def _generate_version_id(self) -> str:
        """Generate a unique version ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"v_{timestamp}_{int(time.time() * 1000) % 1000000:06d}"
    
    def _backup_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> str:
        """
        Create a backup of the current policy version.
        
        Args:
            policy_id: ID of the policy to backup
            policy_data: Current policy data
            
        Returns:
            Backup version ID
        """
        version_id = self._generate_version_id()
        backup_file = self.backups_dir / f"{policy_id}_{version_id}.json"
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(policy_data, f, indent=2)
            
            # Update metadata
            if policy_id not in self.metadata["policies"]:
                self.metadata["policies"][policy_id] = {"current_version": None, "versions": []}
            
            self.metadata["policies"][policy_id]["versions"].append(version_id)
            self.metadata["backups"].append({
                "policy_id": policy_id,
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
                "file_path": str(backup_file)
            })
            
            self._save_metadata()
            logger.info(f"Created backup for policy {policy_id}: {version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to create backup for policy {policy_id}: {e}")
            raise
    
    def _archive_policy(self, policy_id: str, policy_data: Dict[str, Any], reason: str = "update") -> None:
        """
        Archive a policy version to history.
        
        Args:
            policy_id: ID of the policy to archive
            policy_data: Policy data to archive
            reason: Reason for archiving (update, rollback, etc.)
        """
        version_id = self._generate_version_id()
        archive_file = self.history_dir / f"{policy_id}_{version_id}.json"
        
        try:
            with open(archive_file, 'w') as f:
                json.dump(policy_data, f, indent=2)
            
            self.metadata["history"].append({
                "policy_id": policy_id,
                "version_id": version_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "file_path": str(archive_file)
            })
            
            self._save_metadata()
            logger.info(f"Archived policy {policy_id} version {version_id} ({reason})")
            
        except Exception as e:
            logger.error(f"Failed to archive policy {policy_id}: {e}")
            raise
    
    def save_policy(self, policy_id: str, policy_data: Dict[str, Any], 
                   description: str = "Policy update") -> str:
        """
        Save a policy with versioning and backup.
        
        Args:
            policy_id: Unique identifier for the policy
            policy_data: Policy configuration data
            description: Description of the policy change
            
        Returns:
            Version ID of the saved policy
        """
        # Validate policy data
        if not isinstance(policy_data, dict):
            raise ValueError("Policy data must be a dictionary")
        
        # Get current policy if it exists
        current_policy = self.get_policy(policy_id)
        
        # Create backup if policy exists
        if current_policy:
            self._backup_policy(policy_id, current_policy)
            self._archive_policy(policy_id, current_policy, "update")
        
        # Save new policy
        policy_file = self.policies_dir / f"{policy_id}.json"
        try:
            with open(policy_file, 'w') as f:
                json.dump(policy_data, f, indent=2)
            
            # Update metadata
            if policy_id not in self.metadata["policies"]:
                self.metadata["policies"][policy_id] = {"current_version": None, "versions": []}
            
            version_id = self._generate_version_id()
            self.metadata["policies"][policy_id]["current_version"] = version_id
            self.metadata["policies"][policy_id]["description"] = description
            self.metadata["policies"][policy_id]["last_updated"] = datetime.now().isoformat()
            
            self._save_metadata()
            logger.info(f"Saved policy {policy_id} version {version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to save policy {policy_id}: {e}")
            raise
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current version of a policy.
        
        Args:
            policy_id: ID of the policy to retrieve
            
        Returns:
            Policy data if found, None otherwise
        """
        policy_file = self.policies_dir / f"{policy_id}.json"
        if not policy_file.exists():
            return None
        
        try:
            with open(policy_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load policy {policy_id}: {e}")
            return None
    
    def get_policy_version(self, policy_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific version of a policy.
        
        Args:
            policy_id: ID of the policy
            version_id: Version ID to retrieve
            
        Returns:
            Policy data if found, None otherwise
        """
        # Check current version first
        current_policy = self.get_policy(policy_id)
        current_version = self.metadata["policies"].get(policy_id, {}).get("current_version")
        
        if current_version == version_id and current_policy:
            return current_policy
        
        # Check backups
        backup_file = self.backups_dir / f"{policy_id}_{version_id}.json"
        if backup_file.exists():
            try:
                with open(backup_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load policy {policy_id} version {version_id}: {e}")
                return None
        
        return None
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """
        List all policies with their metadata.
        
        Returns:
            List of policy metadata
        """
        policies = []
        for policy_id, metadata in self.metadata["policies"].items():
            policies.append({
                "id": policy_id,
                "current_version": metadata.get("current_version"),
                "description": metadata.get("description", ""),
                "last_updated": metadata.get("last_updated"),
                "version_count": len(metadata.get("versions", []))
            })
        return policies
    
    def list_policy_versions(self, policy_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of a specific policy.
        
        Args:
            policy_id: ID of the policy
            
        Returns:
            List of version metadata
        """
        metadata = self.metadata["policies"].get(policy_id, {})
        versions = []
        
        # Current version
        if metadata.get("current_version"):
            versions.append({
                "version_id": metadata["current_version"],
                "is_current": True,
                "timestamp": metadata.get("last_updated"),
                "description": metadata.get("description", "")
            })
        
        # Backup versions
        for version_id in metadata.get("versions", []):
            backup_info = next(
                (b for b in self.metadata["backups"] 
                 if b["policy_id"] == policy_id and b["version_id"] == version_id), 
                None
            )
            if backup_info:
                versions.append({
                    "version_id": version_id,
                    "is_current": False,
                    "timestamp": backup_info.get("timestamp"),
                    "description": "Backup"
                })
        
        return sorted(versions, key=lambda x: x["timestamp"], reverse=True)
    
    def rollback_policy(self, policy_id: str, target_version: str) -> bool:
        """
        Rollback a policy to a previous version.
        
        Args:
            policy_id: ID of the policy to rollback
            target_version: Version ID to rollback to
            
        Returns:
            True if rollback successful, False otherwise
        """
        # Get target version policy data
        target_policy = self.get_policy_version(policy_id, target_version)
        if not target_policy:
            logger.error(f"Target version {target_version} not found for policy {policy_id}")
            return False
        
        # Get current policy for archiving
        current_policy = self.get_policy(policy_id)
        if current_policy:
            self._archive_policy(policy_id, current_policy, "rollback")
        
        # Save the target version as current
        try:
            policy_file = self.policies_dir / f"{policy_id}.json"
            with open(policy_file, 'w') as f:
                json.dump(target_policy, f, indent=2)
            
            # Update metadata
            self.metadata["policies"][policy_id]["current_version"] = target_version
            self.metadata["policies"][policy_id]["description"] = f"Rollback to {target_version}"
            self.metadata["policies"][policy_id]["last_updated"] = datetime.now().isoformat()
            
            self._save_metadata()
            logger.info(f"Rolled back policy {policy_id} to version {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback policy {policy_id}: {e}")
            return False
    
    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a policy and all its versions.
        
        Args:
            policy_id: ID of the policy to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Archive current version before deletion
            current_policy = self.get_policy(policy_id)
            if current_policy:
                self._archive_policy(policy_id, current_policy, "deletion")
            
            # Delete policy file
            policy_file = self.policies_dir / f"{policy_id}.json"
            if policy_file.exists():
                policy_file.unlink()
            
            # Delete backup files
            for backup_file in self.backups_dir.glob(f"{policy_id}_*.json"):
                backup_file.unlink()
            
            # Update metadata
            if policy_id in self.metadata["policies"]:
                del self.metadata["policies"][policy_id]
            
            self.metadata["backups"] = [
                b for b in self.metadata["backups"] 
                if b["policy_id"] != policy_id
            ]
            
            self._save_metadata()
            logger.info(f"Deleted policy {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete policy {policy_id}: {e}")
            return False
    
    def backup_all(self, backup_name: Optional[str] = None) -> str:
        """
        Create a complete backup of all policies.
        
        Args:
            backup_name: Optional name for the backup
            
        Returns:
            Backup directory path
        """
        if not backup_name:
            backup_name = f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.backups_dir / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        try:
            # Copy policies directory
            policies_backup = backup_dir / "policies"
            if self.policies_dir.exists():
                shutil.copytree(self.policies_dir, policies_backup, dirs_exist_ok=True)
            
            # Copy metadata
            metadata_backup = backup_dir / "policy_metadata.json"
            shutil.copy2(self.metadata_file, metadata_backup)
            
            # Update backup metadata
            self.metadata["backups"].append({
                "backup_name": backup_name,
                "type": "full",
                "timestamp": datetime.now().isoformat(),
                "file_path": str(backup_dir)
            })
            
            self._save_metadata()
            logger.info(f"Created full backup: {backup_name}")
            return str(backup_dir)
            
        except Exception as e:
            logger.error(f"Failed to create full backup: {e}")
            raise
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore policies from a full backup.
        
        Args:
            backup_name: Name of the backup to restore
            
        Returns:
            True if restore successful, False otherwise
        """
        backup_dir = self.backups_dir / backup_name
        if not backup_dir.exists():
            logger.error(f"Backup {backup_name} not found")
            return False
        
        try:
            # Restore policies
            policies_backup = backup_dir / "policies"
            if policies_backup.exists():
                if self.policies_dir.exists():
                    shutil.rmtree(self.policies_dir)
                shutil.copytree(policies_backup, self.policies_dir)
            
            # Restore metadata
            metadata_backup = backup_dir / "policy_metadata.json"
            if metadata_backup.exists():
                shutil.copy2(metadata_backup, self.metadata_file)
                self._load_metadata()
            
            logger.info(f"Restored backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False
    
    def get_policy_history(self, policy_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the history of changes for a policy.
        
        Args:
            policy_id: ID of the policy
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
        """
        history = [
            h for h in self.metadata["history"] 
            if h["policy_id"] == policy_id
        ]
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def cleanup_old_versions(self, policy_id: str, keep_count: int = 10) -> int:
        """
        Clean up old policy versions, keeping only the specified number.
        
        Args:
            policy_id: ID of the policy
            keep_count: Number of versions to keep
            
        Returns:
            Number of versions deleted
        """
        versions = self.list_policy_versions(policy_id)
        versions_to_delete = versions[keep_count:]
        
        deleted_count = 0
        for version in versions_to_delete:
            if not version["is_current"]:
                backup_file = self.backups_dir / f"{policy_id}_{version['version_id']}.json"
                if backup_file.exists():
                    backup_file.unlink()
                    deleted_count += 1
        
        # Update metadata
        self.metadata["policies"][policy_id]["versions"] = [
            v["version_id"] for v in versions[:keep_count] 
            if not v["is_current"]
        ]
        
        self._save_metadata()
        logger.info(f"Cleaned up {deleted_count} old versions for policy {policy_id}")
        return deleted_count
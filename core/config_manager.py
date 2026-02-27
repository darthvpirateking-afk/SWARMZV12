"""
MIT License
Copyright (c) 2026 NEXUSMON

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
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from .policy_store import PolicyStore
from .policy_validator import PolicyValidator

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    ConfigurationManager provides hot-reload capabilities for governance policies.

    Features:
    - Hot-reload policies without restart
    - Integration with existing governance layers
    - Safety mechanisms and validation
    - Policy loading and caching
    - Change notification system
    """

    def __init__(
        self,
        data_dir: str = "data/governance",
        validator: Optional[PolicyValidator] = None,
    ):
        """
        Initialize the ConfigurationManager.

        Args:
            data_dir: Directory to store policy files
            validator: Policy validator instance
        """
        self.policy_store = PolicyStore(data_dir)
        self.validator = validator or PolicyValidator()

        # Policy cache
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._policy_locks: Dict[str, threading.Lock] = {}

        # Change notification
        self._change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._watcher_thread: Optional[threading.Thread] = None
        self._watcher_stop_event = threading.Event()

        # Configuration
        self._watch_interval = 5.0  # seconds
        self._auto_validate = True
        self._rollback_on_error = True

        # Load initial policies
        self._load_all_policies()

    def _get_policy_lock(self, policy_id: str) -> threading.Lock:
        """Get or create a lock for a specific policy."""
        if policy_id not in self._policy_locks:
            self._policy_locks[policy_id] = threading.Lock()
        return self._policy_locks[policy_id]

    def _load_all_policies(self) -> None:
        """Load all policies into cache."""
        try:
            policies = self.policy_store.list_policies()
            for policy_info in policies:
                policy_id = policy_info["id"]
                policy_data = self.policy_store.get_policy(policy_id)
                if policy_data:
                    self._policy_cache[policy_id] = policy_data
                    logger.info(f"Loaded policy {policy_id} into cache")
        except Exception as e:
            logger.error(f"Failed to load policies into cache: {e}")

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a policy from cache or storage.

        Args:
            policy_id: ID of the policy to retrieve

        Returns:
            Policy data if found, None otherwise
        """
        # Check cache first
        if policy_id in self._policy_cache:
            return self._policy_cache[policy_id]

        # Load from storage if not in cache
        policy_data = self.policy_store.get_policy(policy_id)
        if policy_data:
            self._policy_cache[policy_id] = policy_data
            logger.debug(f"Loaded policy {policy_id} from storage into cache")

        return policy_data

    def set_policy(
        self,
        policy_id: str,
        policy_data: Dict[str, Any],
        description: str = "Policy update",
    ) -> bool:
        """
        Set a policy with validation and caching.

        Args:
            policy_id: ID of the policy
            policy_data: Policy configuration data
            description: Description of the policy change

        Returns:
            True if policy was set successfully, False otherwise
        """
        lock = self._get_policy_lock(policy_id)
        with lock:
            try:
                # Validate policy if auto-validation is enabled
                if self._auto_validate:
                    validation_result = self.validator.validate(policy_data)
                    if not validation_result.is_valid:
                        logger.error(
                            f"Policy {policy_id} validation failed: {validation_result.errors}"
                        )
                        return False

                # Save to policy store
                version_id = self.policy_store.save_policy(
                    policy_id, policy_data, description
                )

                # Update cache
                self._policy_cache[policy_id] = policy_data

                # Notify change callbacks
                self._notify_policy_change(policy_id, policy_data)

                logger.info(f"Set policy {policy_id} version {version_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to set policy {policy_id}: {e}")
                return False

    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a policy and remove from cache.

        Args:
            policy_id: ID of the policy to delete

        Returns:
            True if policy was deleted successfully, False otherwise
        """
        lock = self._get_policy_lock(policy_id)
        with lock:
            try:
                # Delete from policy store
                success = self.policy_store.delete_policy(policy_id)

                # Remove from cache
                if policy_id in self._policy_cache:
                    del self._policy_cache[policy_id]

                if success:
                    logger.info(f"Deleted policy {policy_id}")

                return success

            except Exception as e:
                logger.error(f"Failed to delete policy {policy_id}: {e}")
                return False

    def rollback_policy(self, policy_id: str, target_version: str) -> bool:
        """
        Rollback a policy to a previous version.

        Args:
            policy_id: ID of the policy to rollback
            target_version: Version ID to rollback to

        Returns:
            True if rollback successful, False otherwise
        """
        lock = self._get_policy_lock(policy_id)
        with lock:
            try:
                # Get target version policy data
                target_policy = self.policy_store.get_policy_version(
                    policy_id, target_version
                )
                if not target_policy:
                    logger.error(
                        f"Target version {target_version} not found for policy {policy_id}"
                    )
                    return False

                # Validate policy if auto-validation is enabled
                if self._auto_validate:
                    validation_result = self.validator.validate(target_policy)
                    if not validation_result.is_valid:
                        logger.error(
                            f"Rollback policy {policy_id} validation failed: {validation_result.errors}"
                        )
                        return False

                # Rollback in policy store
                success = self.policy_store.rollback_policy(policy_id, target_version)

                if success:
                    # Update cache with rolled back policy
                    self._policy_cache[policy_id] = target_policy

                    # Notify change callbacks
                    self._notify_policy_change(policy_id, target_policy)

                    logger.info(
                        f"Rolled back policy {policy_id} to version {target_version}"
                    )

                return success

            except Exception as e:
                logger.error(f"Failed to rollback policy {policy_id}: {e}")
                return False

    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies with their metadata."""
        return self.policy_store.list_policies()

    def list_policy_versions(self, policy_id: str) -> List[Dict[str, Any]]:
        """List all versions of a specific policy."""
        return self.policy_store.list_policy_versions(policy_id)

    def get_policy_history(
        self, policy_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get the history of changes for a policy."""
        return self.policy_store.get_policy_history(policy_id, limit)

    def add_change_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Add a callback to be notified when policies change.

        Args:
            callback: Function to call when a policy changes
        """
        self._change_callbacks.append(callback)

    def remove_change_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Remove a change callback.

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def _notify_policy_change(
        self, policy_id: str, policy_data: Dict[str, Any]
    ) -> None:
        """Notify all registered callbacks of a policy change."""
        for callback in self._change_callbacks:
            try:
                callback(policy_id, policy_data)
            except Exception as e:
                logger.error(f"Error in policy change callback: {e}")

    def start_watcher(self) -> None:
        """Start the file system watcher for policy changes."""
        if self._watcher_thread is not None:
            logger.warning("Watcher is already running")
            return

        self._watcher_stop_event.clear()
        self._watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
        self._watcher_thread.start()
        logger.info("Started policy watcher")

    def stop_watcher(self) -> None:
        """Stop the file system watcher."""
        if self._watcher_thread is None:
            return

        self._watcher_stop_event.set()
        self._watcher_thread.join(timeout=10)
        self._watcher_thread = None
        logger.info("Stopped policy watcher")

    def _watcher_loop(self) -> None:
        """Main watcher loop to monitor policy file changes."""
        last_modified_times = {}

        while not self._watcher_stop_event.is_set():
            try:
                # Check policy files for changes
                policies_dir = self.policy_store.policies_dir
                if policies_dir.exists():
                    for policy_file in policies_dir.glob("*.json"):
                        try:
                            mtime = policy_file.stat().st_mtime
                            last_mtime = last_modified_times.get(str(policy_file))

                            if last_mtime is None or mtime > last_mtime:
                                # File has been modified
                                policy_id = policy_file.stem
                                policy_data = self.policy_store.get_policy(policy_id)

                                if policy_data:
                                    # Validate policy
                                    if self._auto_validate:
                                        validation_result = self.validator.validate(
                                            policy_data
                                        )
                                        if not validation_result.is_valid:
                                            logger.error(
                                                f"Modified policy {policy_id} validation failed: {validation_result.errors}"
                                            )
                                            if self._rollback_on_error:
                                                self._rollback_to_previous_version(
                                                    policy_id
                                                )
                                            continue

                                    # Update cache and notify
                                    self._policy_cache[policy_id] = policy_data
                                    self._notify_policy_change(policy_id, policy_data)

                                    last_modified_times[str(policy_file)] = mtime
                                    logger.info(f"Detected policy change: {policy_id}")

                        except Exception as e:
                            logger.error(
                                f"Error checking policy file {policy_file}: {e}"
                            )

                # Wait before next check
                self._watcher_stop_event.wait(self._watch_interval)

            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")
                self._watcher_stop_event.wait(self._watch_interval)

    def _rollback_to_previous_version(self, policy_id: str) -> None:
        """Rollback to the previous version of a policy."""
        try:
            versions = self.list_policy_versions(policy_id)
            if len(versions) > 1:
                # Get the second most recent version (previous version)
                previous_version = versions[1]["version_id"]
                self.rollback_policy(policy_id, previous_version)
                logger.info(f"Auto-rolled back policy {policy_id} to previous version")
        except Exception as e:
            logger.error(f"Failed to auto-rollback policy {policy_id}: {e}")

    def cleanup_old_versions(self, policy_id: str, keep_count: int = 10) -> int:
        """
        Clean up old policy versions, keeping only the specified number.

        Args:
            policy_id: ID of the policy
            keep_count: Number of versions to keep

        Returns:
            Number of versions deleted
        """
        return self.policy_store.cleanup_old_versions(policy_id, keep_count)

    def backup_all(self, backup_name: Optional[str] = None) -> str:
        """
        Create a complete backup of all policies.

        Args:
            backup_name: Optional name for the backup

        Returns:
            Backup directory path
        """
        return self.policy_store.backup_all(backup_name)

    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore policies from a full backup.

        Args:
            backup_name: Name of the backup to restore

        Returns:
            True if restore successful, False otherwise
        """
        success = self.policy_store.restore_backup(backup_name)
        if success:
            # Reload all policies into cache
            self._load_all_policies()
        return success

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the policy cache."""
        return {
            "cached_policies": len(self._policy_cache),
            "total_policies": len(self.policy_store.metadata["policies"]),
            "cache_size_mb": (
                sum(
                    len(json.dumps(policy).encode("utf-8"))
                    for policy in self._policy_cache.values()
                )
                / (1024 * 1024)
                if self._policy_cache
                else 0
            ),
        }

    def clear_cache(self) -> None:
        """Clear the policy cache."""
        self._policy_cache.clear()
        logger.info("Cleared policy cache")

    def reload_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Force reload a policy from storage into cache.

        Args:
            policy_id: ID of the policy to reload

        Returns:
            Policy data if found, None otherwise
        """
        lock = self._get_policy_lock(policy_id)
        with lock:
            policy_data = self.policy_store.get_policy(policy_id)
            if policy_data:
                self._policy_cache[policy_id] = policy_data
                logger.info(f"Reloaded policy {policy_id} from storage")
            return policy_data

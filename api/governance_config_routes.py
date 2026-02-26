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

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from core.config_manager import ConfigurationManager
from core.policy_validator import PolicyValidator, ValidationResult

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class PolicyCreateRequest(BaseModel):
    """Request model for creating a new policy."""
    policy_id: str = Field(..., description="Unique identifier for the policy")
    version: str = Field(..., description="Semantic version of the policy")
    description: str = Field(..., description="Description of the policy")
    rules: List[Dict[str, Any]] = Field(..., description="List of policy rules")
    enabled: bool = Field(True, description="Whether the policy is enabled")
    priority: int = Field(50, ge=0, le=100, description="Policy priority")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class PolicyUpdateRequest(BaseModel):
    """Request model for updating an existing policy."""
    version: Optional[str] = Field(None, description="New semantic version")
    description: Optional[str] = Field(None, description="Updated description")
    rules: Optional[List[Dict[str, Any]]] = Field(None, description="Updated rules")
    enabled: Optional[bool] = Field(None, description="Whether the policy is enabled")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Updated priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class PolicyResponse(BaseModel):
    """Response model for policy operations."""
    policy_id: str
    version: str
    description: str
    enabled: bool
    priority: int
    created_at: str
    updated_at: str
    rules_count: int
    size_bytes: int

class ValidationResultResponse(BaseModel):
    """Response model for validation results."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class PolicyHistoryResponse(BaseModel):
    """Response model for policy history."""
    policy_id: str
    version_id: str
    reason: str
    timestamp: str
    file_path: str

class PolicyVersionResponse(BaseModel):
    """Response model for policy versions."""
    version_id: str
    is_current: bool
    timestamp: str
    description: str

# Create router
router = APIRouter(
    prefix="/api/v1/governance/config",
    tags=["Governance Configuration"],
    responses={404: {"description": "Not found"}}
)

def get_config_manager() -> ConfigurationManager:
    """Dependency to get the ConfigurationManager instance."""
    return ConfigurationManager()

def get_policy_validator() -> PolicyValidator:
    """Dependency to get the PolicyValidator instance."""
    return PolicyValidator()

@router.post("/policies", response_model=Dict[str, Any])
async def create_policy(
    request: PolicyCreateRequest,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    validator: PolicyValidator = Depends(get_policy_validator)
):
    """
    Create a new governance policy.
    
    Validates the policy before saving and returns the created policy details.
    """
    try:
        # Convert request to policy data format
        policy_data = {
            "policy_id": request.policy_id,
            "version": request.version,
            "description": request.description,
            "rules": request.rules,
            "enabled": request.enabled,
            "priority": request.priority,
            "metadata": request.metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Validate policy
        validation_result = validator.validate(policy_data)
        
        if not validation_result.is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Policy validation failed",
                    "validation_result": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings
                    }
                }
            )
        
        # Save policy
        success = config_manager.set_policy(
            request.policy_id, 
            policy_data, 
            f"Created policy {request.policy_id}"
        )
        
        if success:
            logger.info(f"Created policy: {request.policy_id}")
            return {
                "success": True,
                "message": f"Policy {request.policy_id} created successfully",
                "policy_id": request.policy_id,
                "version": request.version,
                "validation_warnings": validation_result.warnings
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save policy")
    
    except Exception as e:
        logger.error(f"Error creating policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies", response_model=List[PolicyResponse])
async def list_policies(
    config_manager: ConfigurationManager = Depends(get_config_manager),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    priority_min: Optional[int] = Query(None, ge=0, le=100, description="Minimum priority"),
    priority_max: Optional[int] = Query(None, ge=0, le=100, description="Maximum priority")
):
    """
    List all governance policies with optional filtering.
    """
    try:
        policies = config_manager.list_policies()
        
        # Apply filters
        filtered_policies = []
        for policy in policies:
            policy_data = config_manager.get_policy(policy["id"])
            if not policy_data:
                continue
            
            # Apply enabled filter
            if enabled is not None and policy_data.get("enabled") != enabled:
                continue
            
            # Apply priority filters
            priority = policy_data.get("priority", 50)
            if priority_min is not None and priority < priority_min:
                continue
            if priority_max is not None and priority > priority_max:
                continue
            
            filtered_policies.append(policy)
        
        # Convert to response format
        response = []
        for policy in filtered_policies:
            policy_data = config_manager.get_policy(policy["id"])
            if policy_data:
                response.append(PolicyResponse(
                    policy_id=policy["id"],
                    version=policy["current_version"] or "unknown",
                    description=policy["description"],
                    enabled=policy_data.get("enabled", True),
                    priority=policy_data.get("priority", 50),
                    created_at=policy_data.get("created_at", ""),
                    updated_at=policy["last_updated"] or "",
                    rules_count=len(policy_data.get("rules", [])),
                    size_bytes=len(str(policy_data).encode('utf-8'))
                ))
        
        return response
    
    except Exception as e:
        logger.error(f"Error listing policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def get_policy(
    policy_id: str,
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Get a specific governance policy by ID.
    """
    try:
        policy_data = config_manager.get_policy(policy_id)
        
        if not policy_data:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        return {
            "success": True,
            "policy": policy_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(
    policy_id: str,
    request: PolicyUpdateRequest,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    validator: PolicyValidator = Depends(get_policy_validator)
):
    """
    Update an existing governance policy.
    
    Validates the policy update and applies changes atomically.
    """
    try:
        # Get current policy
        current_policy = config_manager.get_policy(policy_id)
        if not current_policy:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        # Build updated policy data
        updated_policy = current_policy.copy()
        
        if request.version is not None:
            updated_policy["version"] = request.version
        if request.description is not None:
            updated_policy["description"] = request.description
        if request.rules is not None:
            updated_policy["rules"] = request.rules
        if request.enabled is not None:
            updated_policy["enabled"] = request.enabled
        if request.priority is not None:
            updated_policy["priority"] = request.priority
        if request.metadata is not None:
            updated_policy["metadata"] = request.metadata
        
        updated_policy["updated_at"] = datetime.utcnow().isoformat()
        
        # Validate policy update
        validation_result = validator.validate_policy_update(current_policy, updated_policy)
        
        if not validation_result.is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Policy update validation failed",
                    "validation_result": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings
                    }
                }
            )
        
        # Apply update
        success = config_manager.set_policy(
            policy_id, 
            updated_policy, 
            f"Updated policy {policy_id}"
        )
        
        if success:
            logger.info(f"Updated policy: {policy_id}")
            return {
                "success": True,
                "message": f"Policy {policy_id} updated successfully",
                "policy_id": policy_id,
                "version": updated_policy.get("version"),
                "validation_warnings": validation_result.warnings
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update policy")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(
    policy_id: str,
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Delete a governance policy.
    """
    try:
        success = config_manager.delete_policy(policy_id)
        
        if success:
            logger.info(f"Deleted policy: {policy_id}")
            return {
                "success": True,
                "message": f"Policy {policy_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policies/{policy_id}/validate", response_model=ValidationResultResponse)
async def validate_policy(
    policy_id: str,
    policy_data: Dict[str, Any] = Body(..., description="Policy data to validate"),
    config_manager: ConfigurationManager = Depends(get_config_manager),
    validator: PolicyValidator = Depends(get_policy_validator)
):
    """
    Validate a policy without saving it.
    """
    try:
        # If policy_id is provided and policy exists, validate as update
        current_policy = config_manager.get_policy(policy_id)
        
        if current_policy:
            validation_result = validator.validate_policy_update(current_policy, policy_data)
        else:
            validation_result = validator.validate(policy_data)
        
        return ValidationResultResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings
        )
    
    except Exception as e:
        logger.error(f"Error validating policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}/versions", response_model=List[PolicyVersionResponse])
async def list_policy_versions(
    policy_id: str,
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    List all versions of a specific policy.
    """
    try:
        versions = config_manager.list_policy_versions(policy_id)
        
        if not versions:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        return [
            PolicyVersionResponse(
                version_id=v["version_id"],
                is_current=v["is_current"],
                timestamp=v["timestamp"],
                description=v["description"]
            ) for v in versions
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing policy versions for {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policies/{policy_id}/rollback", response_model=Dict[str, Any])
async def rollback_policy(
    policy_id: str,
    target_version: str = Body(..., embed=True, description="Version to rollback to"),
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Rollback a policy to a previous version.
    """
    try:
        success = config_manager.rollback_policy(policy_id, target_version)
        
        if success:
            logger.info(f"Rolled back policy {policy_id} to version {target_version}")
            return {
                "success": True,
                "message": f"Policy {policy_id} rolled back to version {target_version}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} or version {target_version} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}/history", response_model=List[PolicyHistoryResponse])
async def get_policy_history(
    policy_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of history entries"),
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Get the history of changes for a policy.
    """
    try:
        history = config_manager.get_policy_history(policy_id, limit)
        
        return [
            PolicyHistoryResponse(
                policy_id=h["policy_id"],
                version_id=h["version_id"],
                reason=h["reason"],
                timestamp=h["timestamp"],
                file_path=h["file_path"]
            ) for h in history
        ]
    
    except Exception as e:
        logger.error(f"Error getting policy history for {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}/summary", response_model=Dict[str, Any])
async def get_policy_summary(
    policy_id: str,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    validator: PolicyValidator = Depends(get_policy_validator)
):
    """
    Get a summary of policy characteristics and validation status.
    """
    try:
        policy_data = config_manager.get_policy(policy_id)
        
        if not policy_data:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        # Get policy summary
        summary = validator.get_policy_summary(policy_data)
        
        # Get validation status
        validation_result = validator.validate(policy_data)
        
        return {
            "success": True,
            "policy_id": policy_id,
            "summary": summary,
            "validation_status": {
                "is_valid": validation_result.is_valid,
                "error_count": len(validation_result.errors),
                "warning_count": len(validation_result.warnings)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy summary for {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policies/{policy_id}/compliance", response_model=Dict[str, Any])
async def validate_policy_compliance(
    policy_id: str,
    compliance_rules: List[Dict[str, Any]] = Body(..., description="List of compliance requirements"),
    config_manager: ConfigurationManager = Depends(get_config_manager),
    validator: PolicyValidator = Depends(get_policy_validator)
):
    """
    Validate a policy against compliance requirements.
    """
    try:
        policy_data = config_manager.get_policy(policy_id)
        
        if not policy_data:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        # Validate compliance
        compliance_result = validator.validate_policy_compliance(policy_data, compliance_rules)
        
        return {
            "success": True,
            "policy_id": policy_id,
            "compliance_status": {
                "is_compliant": compliance_result.is_valid,
                "errors": compliance_result.errors,
                "warnings": compliance_result.warnings
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating policy compliance for {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_config_stats(
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Get configuration management statistics.
    """
    try:
        cache_stats = config_manager.get_cache_stats()
        policies = config_manager.list_policies()
        
        # Calculate additional stats
        total_rules = 0
        enabled_policies = 0
        disabled_policies = 0
        
        for policy in policies:
            policy_data = config_manager.get_policy(policy["id"])
            if policy_data:
                total_rules += len(policy_data.get("rules", []))
                if policy_data.get("enabled", True):
                    enabled_policies += 1
                else:
                    disabled_policies += 1
        
        return {
            "success": True,
            "statistics": {
                "total_policies": len(policies),
                "enabled_policies": enabled_policies,
                "disabled_policies": disabled_policies,
                "total_rules": total_rules,
                "cache_stats": cache_stats
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting configuration stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    backup_name: Optional[str] = Body(None, description="Optional backup name"),
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Create a complete backup of all policies.
    """
    try:
        backup_path = config_manager.backup_all(backup_name)
        
        logger.info(f"Created backup: {backup_path}")
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_path": backup_path
        }
    
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore", response_model=Dict[str, Any])
async def restore_backup(
    backup_name: str = Body(..., embed=True, description="Name of the backup to restore"),
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Restore policies from a backup.
    """
    try:
        success = config_manager.restore_backup(backup_name)
        
        if success:
            logger.info(f"Restored backup: {backup_name}")
            return {
                "success": True,
                "message": f"Backup {backup_name} restored successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Backup {backup_name} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup {backup_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_versions(
    policy_id: Optional[str] = Body(None, description="Policy ID to cleanup (None for all)"),
    keep_count: int = Body(10, ge=1, le=100, description="Number of versions to keep"),
    config_manager: ConfigurationManager = Depends(get_config_manager)
):
    """
    Clean up old policy versions.
    """
    try:
        if policy_id:
            # Cleanup specific policy
            deleted_count = config_manager.cleanup_old_versions(policy_id, keep_count)
            message = f"Cleaned up {deleted_count} old versions for policy {policy_id}"
        else:
            # Cleanup all policies
            policies = config_manager.list_policies()
            total_deleted = 0
            for policy in policies:
                deleted = config_manager.cleanup_old_versions(policy["id"], keep_count)
                total_deleted += deleted
            deleted_count = total_deleted
            message = f"Cleaned up {total_deleted} old versions across all policies"
        
        logger.info(message)
        return {
            "success": True,
            "message": message,
            "deleted_versions": deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up old versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
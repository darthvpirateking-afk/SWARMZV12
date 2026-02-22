# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Operator Identity Layer — SWARMZ V3.0 API routes.

Exposes the operator charter, prime directive, system primitives,
and sovereignty status as REST endpoints.
"""

from fastapi import APIRouter

from swarmz_runtime.core.operator_charter import (
    FUTURE_CHANGE_VECTOR,
    OPERATOR_CHARTER_SECTIONS,
    OPERATOR_PRIME_DIRECTIVE,
    SWARMZ_OPERATING_MATRIX,
    SYSTEM_PRIMITIVES,
)

router = APIRouter(prefix="/v1/operator", tags=["operator-identity"])


@router.get("/identity")
def operator_identity():
    """Return the operator's sovereign identity and prime directive."""
    return {
        "identity": "SOVEREIGN_OPERATOR",
        "prime_directive": OPERATOR_PRIME_DIRECTIVE,
        "charter_sections": OPERATOR_CHARTER_SECTIONS,
        "status": "active",
    }


@router.get("/charter")
def operator_charter():
    """Return the full operator charter including primitives and operating matrix."""
    return {
        "prime_directive": OPERATOR_PRIME_DIRECTIVE,
        "sections": OPERATOR_CHARTER_SECTIONS,
        "system_primitives": SYSTEM_PRIMITIVES,
        "operating_matrix": SWARMZ_OPERATING_MATRIX,
    }


@router.get("/sovereignty")
def operator_sovereignty():
    """Return operator sovereignty status and future change vector."""
    return {
        "sovereignty": "full",
        "change_vector": FUTURE_CHANGE_VECTOR,
        "operating_matrix": SWARMZ_OPERATING_MATRIX,
        "status": "SOVEREIGN",
    }

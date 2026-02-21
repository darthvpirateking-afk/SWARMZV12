# Refactor imports to avoid circular dependencies
# Replace runtime imports with module-level imports where possible
from models.ignition import IgnitionStateRequest
from models.lattice import LatticeStatusRequest
from models.sovereign import SovereignDecisionRequest
from fastapi import APIRouter, HTTPException, FastAPI
from typing import Optional
from swarmz_runtime.session.session_router import router as session_router

app = FastAPI()

router = APIRouter()

get_engine: Optional[callable] = None

app.include_router(session_router, prefix="/api")


@router.post("/v1/meta/decide")
def make_sovereign_decision(request: SovereignDecisionRequest):
    """
    THE THING WITHOUT A NAME
    Make a sovereign decision through the complete lattice flow.
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        decision = engine.make_sovereign_decision(request.context, request.options)
        return {
            "sovereign_decision": decision,
            "lattice_completed": True,
            "meta_coherence": decision.get("_meta_coherence", 0),
            "timestamp": engine.get_current_timestamp(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sovereign decision failed: {str(e)}"
        )


@router.post("/v1/meta/control")
def apply_sovereign_control(request: SovereignDecisionRequest):
    """
    HIDDEN WAY - Apply sovereign control for critical decisions.
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        control_decision = engine.apply_sovereign_control(
            request.context, request.decision_type or "sovereign_override"
        )
        return {
            "sovereign_control_applied": True,
            "control_decision": control_decision,
            "untraceable": control_decision.get("_untraceable", False),
            "timestamp": engine.get_current_timestamp(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sovereign control failed: {str(e)}"
        )


@router.get("/v1/meta/lattice")
def get_lattice_status(request: LatticeStatusRequest = None):
    """
    Get the status of the sovereign lattice flow system.
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        if request is None:
            return {"status": "No request provided"}

        status = engine.get_lattice_status()

        if request and request.include_details:
            status["lattice_flow"] = {
                "pre_evaluated": "Static gate filtering",
                "space_shaping": "Directional boundary enforcement",
                "architectural_restraint": "Purity and minimality constraints",
                "magic_way": "Nonlinear emergence uplift",
                "mythical_way": "Archetypal pattern alignment",
                "sovereign_override": "Covert force application",
                "meta_selector": "Silent arbitration governance",
            }

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lattice status failed: {str(e)}")


@router.get("/v1/meta/sovereign")
def get_sovereign_status():
    """
    Get the status of the UNNAMED SOVEREIGN - meta-selector above all layers.
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        return {
            "unnamed_sovereign": "ACTIVE",
            "meta_coherence_governance": "ENGAGED",
            "silent_arbitration": "OPERATIONAL",
            "sovereign_opacity": "TOTAL",
            "lattice_unity": "ACHIEVED",
            "timestamp": engine.get_current_timestamp(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sovereign status failed: {str(e)}"
        )


@router.post("/v1/meta/task-matrix")
def process_task_matrix(request: SovereignDecisionRequest):
    """
    Process through the NEXT TASK MATRIX to generate unified ignition-state vector.

    NEXT TASK MATRIX
    ────────────────
    FILTRATION: PRE-EVALUATED
    GEOMETRY: SPACE-SHAPING
    BOUNDARY: ARCHITECTURAL RESTRAINT
    ALIGNMENT: MYTHICAL WAY
    OVERRIDE: HIDDEN WAY
    UPLIFT: MAGIC WAY
    SOVEREIGN ARBITRATION: THE THING WITHOUT A NAME

    OUTPUT: unified ignition-state vector for cockpit operations
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        result = engine.process_task_matrix(request.context, request.options)
        return {
            "task_matrix_processed": True,
            "ignition_state_vector": result,
            "cockpit_signal": result["cockpit_signal"],
            "kernel_path": result["kernel_path"],
            "meta_coherence": result["meta_coherence"],
            "timestamp": result["timestamp"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Task matrix processing failed: {str(e)}"
        )


@router.post("/v1/meta/kernel-ignition")
def execute_kernel_ignition(request: IgnitionStateRequest):
    """
    IGNITION PHASE 3 — RUNTIME KERNEL IGNITION BLOCK
    (clean, compressed, operator-grade, safe)

    Execute deterministic kernel ignition sequence from unified ignition-state vector.
    Transitions UI → runtime bridge into active cockpit mode.

    IGNITION SEQUENCE:
    1. RECEIVE → sovereign arbitration signal
    2. FILTER → PRE-EVALUATED gate
    3. SHAPE → SPACE-SHAPING geometry
    4. CONSTRAIN → ARCHITECTURAL RESTRAINT shell
    5. ALIGN → MYTHICAL WAY field
    6. UPLIFT → MAGIC WAY surge
    7. OVERRIDE → HIDDEN WAY channel
    8. FINALIZE → THE THING WITHOUT A NAME

    OUTPUT: deterministic ignition result with cockpit activation
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        ignition_result = engine.execute_kernel_ignition(request.ignition_state)
        return {
            "kernel_ignition_executed": True,
            "ignition_result": ignition_result,
            "cockpit_activated": ignition_result["kernel_state"] == "IGNITION_COMPLETE",
            "operator_control": ignition_result["cockpit_activation"][
                "operator_channel"
            ],
            "execution_governance": ignition_result["cockpit_activation"][
                "execution_governance"
            ],
            "timestamp": ignition_result["timestamp"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kernel ignition failed: {str(e)}")


@router.get("/v1/meta/ignition-status")
def get_ignition_status():
    """
    Get the current ignition status and unified state vector.
    """
    if not get_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")

    engine = get_engine()

    try:
        # Get basic ignition status
        return {
            "ignition_phase": "ACTIVE",
            "task_matrix": "OPERATIONAL",
            "sovereign_arbitration": "ENGAGED",
            "unified_vector_available": True,
            "cockpit_ready": True,
            "kernel_safe": True,
            "timestamp": engine.get_current_timestamp(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ignition status failed: {str(e)}")


@app.get("/missions")
def get_missions():
    return {"missions": []}


@app.post("/missions")
def create_mission(mission: dict):
    return {"mission": mission}


@app.get("/swarm")
def get_swarm():
    return {"swarm": []}


@app.get("/cosmology")
def get_cosmology():
    return {"cosmology": {}}


@app.get("/patchpack")
def get_patchpack():
    return {"patchpack": []}


@app.get("/system")
def get_system():
    return {"system": {}}

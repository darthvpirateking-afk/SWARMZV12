from fastapi import APIRouter

router = APIRouter()

@router.get("/cockpit/panels")
def get_cockpit_panels():
    return {
        "panels": [
            "Avatar Panel",
            "Mission Console",
            "Swarm Grid v2",
            "Cosmology Map v2",
            "Patchpack Timeline",
            "System Health + Governor Status",
            "Operator Session Panel",
            "Shadow-Ledger Alerts",
        ]
    }

@router.get("/cockpit/layout")
def get_cockpit_layout():
    return {
        "layout": {
            "top_bar": ["avatar presence", "operator rank", "session state"],
            "left_rail": ["missions", "swarm", "cosmology", "patchpack", "system"],
            "main_canvas": "dynamic panel",
            "right_rail": ["mission log", "swarm events", "patchpack events"],
        }
    }
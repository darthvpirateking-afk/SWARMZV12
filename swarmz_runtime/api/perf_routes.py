import cProfile
import pstats
import io
import time
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException

from swarmz_runtime.verify import provenance

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PERF_DIR = DATA_DIR / "perf"
PERF_DIR.mkdir(parents=True, exist_ok=True)


def _require_operator(request: Request):
    header_key = request.headers.get("X-Operator-Key")
    if not header_key:
        raise HTTPException(status_code=401, detail="operator key required")


@router.post("/v1/perf/snapshot")
def perf_snapshot(request: Request):
    _require_operator(request)
    prof_path = PERF_DIR / f"snapshot-{int(time.time())}.txt"
    pr = cProfile.Profile()
    pr.enable()
    time.sleep(0.05)
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)
    prof_path.write_text(s.getvalue())
    provenance.append_audit("perf_snapshot", {"file": str(prof_path)})
    return {"ok": True, "file": str(prof_path)}


@router.get("/v1/perf/bench")
def perf_bench():
    start = time.time()
    for _ in range(10000):
        pass
    dur = time.time() - start
    row = {"ok": True, "duration_sec": dur}
    bench_file = PERF_DIR / "bench.jsonl"
    with bench_file.open("a", encoding="utf-8") as f:
        f.write(str(row) + "\n")
    return row

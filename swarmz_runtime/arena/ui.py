"""
arena/ui.py – Minimal ARENA UI served as an HTML page.

Provides a simple form to start arena runs and displays ranked results.
Mounted at /arena in the FastAPI app.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_ARENA_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWARMZ Arena</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
background:#0d1117;color:#c9d1d9;padding:1.5rem;max-width:800px;margin:0 auto}
h1{color:#58a6ff;margin-bottom:.5rem;font-size:1.5rem}
.subtitle{color:#8b949e;margin-bottom:1.5rem;font-size:.85rem}
a{color:#58a6ff;text-decoration:none}
a:hover{text-decoration:underline}
.form-group{margin-bottom:1rem}
label{display:block;margin-bottom:.25rem;color:#8b949e;font-size:.85rem}
textarea,input,select{width:100%;padding:.6rem;border-radius:6px;border:1px solid #30363d;
background:#161b22;color:#c9d1d9;font-size:.9rem}
textarea{min-height:80px;resize:vertical}
button{padding:.6rem 1.5rem;border-radius:6px;border:none;cursor:pointer;font-size:.9rem;
background:#238636;color:#fff;margin-top:.5rem}
button:hover{background:#2ea043}
button:disabled{background:#30363d;cursor:not-allowed}
.results{margin-top:1.5rem}
.run-card{padding:1rem;border-radius:8px;background:#161b22;border:1px solid #30363d;
margin-bottom:.75rem}
.run-card h3{color:#58a6ff;font-size:.95rem;margin-bottom:.25rem}
.candidate{padding:.5rem;margin:.25rem 0;border-radius:4px;background:#0d1117;
border-left:3px solid #30363d;font-size:.85rem}
.candidate.winner{border-left-color:#238636;background:#0d1117}
.score{color:#f0883e;font-weight:bold}
.rank{color:#8b949e;font-size:.75rem}
.status{font-size:.75rem;padding:2px 6px;border-radius:3px;display:inline-block}
.status.completed{background:#238636;color:#fff}
.status.running{background:#1f6feb;color:#fff}
.status.failed{background:#da3633;color:#fff}
.spinner{display:none;margin:.5rem 0;color:#8b949e}
.spinner.active{display:block}
#error{color:#f85149;margin-top:.5rem;display:none}
.back{margin-bottom:1rem;display:inline-block}
</style>
</head>
<body>
<a class="back" href="/">&larr; Back to SWARMZ</a>
<h1>&#x1F3C6; SWARMZ Arena</h1>
<p class="subtitle">Run parallel candidates, rank deterministically, select winner</p>

<div class="form-group">
  <label for="prompt">Prompt</label>
  <textarea id="prompt" placeholder="Enter the prompt for all candidates..."></textarea>
</div>
<div class="form-group">
  <label for="num">Candidates (1-8)</label>
  <input id="num" type="number" min="1" max="8" value="3">
</div>
<div class="form-group">
  <label for="strategy">Scoring Strategy</label>
  <select id="strategy">
    <option value="length_quality">Length + Quality</option>
    <option value="length_only">Length Only</option>
  </select>
</div>
<button id="runBtn" onclick="startRun()">&#x1F680; Start Arena Run</button>
<div id="spinner" class="spinner">Running candidates...</div>
<div id="error"></div>

<div class="results" id="results">
  <h2 style="margin-bottom:.75rem;font-size:1.1rem">Recent Runs</h2>
  <div id="runsList"></div>
</div>

<script>
async function startRun() {
  const btn = document.getElementById('runBtn');
  const spinner = document.getElementById('spinner');
  const errDiv = document.getElementById('error');
  btn.disabled = true;
  spinner.className = 'spinner active';
  errDiv.style.display = 'none';

  try {
    const resp = await fetch('/v1/arena/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        prompt: document.getElementById('prompt').value,
        num_candidates: parseInt(document.getElementById('num').value),
        scoring_strategy: document.getElementById('strategy').value,
      })
    });
    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.detail || 'Run failed');
    }
    await loadRuns();
  } catch(e) {
    errDiv.textContent = e.message;
    errDiv.style.display = 'block';
  } finally {
    btn.disabled = false;
    spinner.className = 'spinner';
  }
}

async function loadRuns() {
  try {
    const resp = await fetch('/v1/arena/runs?limit=10');
    const data = await resp.json();
    const container = document.getElementById('runsList');
    container.innerHTML = '';
    const runs = (data.runs || []).reverse();
    for (const run of runs) {
      const card = document.createElement('div');
      card.className = 'run-card';
      let candsHtml = '';
      if (run.candidate_ids || run.candidates) {
        // Load full details
        try {
          const dr = await fetch('/v1/arena/runs/' + run.id);
          const details = await dr.json();
          const cands = details.candidate_details || [];
          cands.sort((a,b) => (a.rank||99) - (b.rank||99));
          for (const c of cands) {
            const isWinner = c.id === run.winner_id;
            candsHtml += '<div class="candidate ' + (isWinner ? 'winner' : '') + '">' +
              '<span class="rank">#' + (c.rank||'?') + '</span> ' +
              '<span class="score">' + (c.score||0).toFixed(4) + '</span> ' +
              (isWinner ? '&#x1F3C6; ' : '') +
              '<span style="color:#8b949e">' + (c.response||'').substring(0,100) + '...</span>' +
              '</div>';
          }
        } catch(e) {}
      }
      card.innerHTML = '<h3>' + run.id + ' <span class="status ' +
        (run.status||'') + '">' + (run.status||'unknown') + '</span></h3>' +
        '<p style="font-size:.8rem;color:#8b949e;margin-bottom:.5rem">' +
        (run.prompt||'').substring(0,120) + '</p>' +
        (run.winner_id ? '<p style="font-size:.85rem">Winner: <strong>' + run.winner_id + '</strong></p>' : '') +
        candsHtml;
      container.appendChild(card);
    }
  } catch(e) {
    console.error('Failed to load runs:', e);
  }
}

loadRuns();
</script>
</body>
</html>
"""


@router.get("/arena", response_class=HTMLResponse)
def arena_ui():
    """Serve the Arena UI page."""
    return _ARENA_HTML

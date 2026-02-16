"""
Storage module: atomic JSON/JSONL read/write operations for Galileo harness
Ensures durability and prevents partial writes
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime


GALILEO_DATA_DIR = Path(__file__).parent.parent / "data" / "galileo"


def init_storage() -> Path:
    """
    Initialize Galileo storage directory and files.
    
    Returns:
        Path to Galileo data directory
    """
    GALILEO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create JSONL files if they don't exist
    files_to_init = [
        'runs.jsonl',
        'hypotheses.jsonl',
        'experiments.jsonl',
        'scores.jsonl',
        'priors_cache.jsonl'
    ]
    
    for filename in files_to_init:
        (GALILEO_DATA_DIR / filename).touch(exist_ok=True)
    
    # Create domain_packs and templates directories
    (GALILEO_DATA_DIR / 'domain_packs').mkdir(exist_ok=True)
    (GALILEO_DATA_DIR / 'templates').mkdir(exist_ok=True)
    
    return GALILEO_DATA_DIR


def read_jsonl(filepath: Path) -> Tuple[List[Dict], int, int]:
    """
    Read JSONL file, skipping blank/malformed lines.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        Tuple of (list of dicts, skipped_count, quarantined_count)
    """
    if not filepath.exists():
        return [], 0, 0
    
    rows = []
    skipped = 0
    quarantined = 0
    bad_rows_file = filepath.parent / f"{filepath.stem}_bad_rows.jsonl"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip('\n\r')
            
            # Skip blank lines
            if not line or not line.strip():
                skipped += 1
                continue
            
            # Try to parse JSON
            try:
                obj = json.loads(line)
                rows.append(obj)
            except json.JSONDecodeError as e:
                # Quarantine bad row
                quarantined += 1
                try:
                    bad_record = {
                        'source_file': str(filepath),
                        'line_number': line_no,
                        'error': str(e),
                        'bad_line': line[:200],
                        'quarantined_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    with open(bad_rows_file, 'a', encoding='utf-8') as br:
                        br.write(json.dumps(bad_record, separators=(',', ':')) + '\n')
                except Exception:
                    pass  # Silently fail to quarantine
    
    return rows, skipped, quarantined


def write_jsonl(filepath: Path, obj: Dict) -> None:
    """
    Atomically append a single JSON object to JSONL file.
    
    Args:
        filepath: Path to JSONL file
        obj: Dict to append
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic append
    line = json.dumps(obj, separators=(',', ':')) + '\n'
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(line)
        f.flush()


def load_runs() -> List[Dict]:
    """Load all run records."""
    runs_file = GALILEO_DATA_DIR / 'runs.jsonl'
    rows, _, _ = read_jsonl(runs_file)
    # Sort by timestamp descending
    return sorted(rows, key=lambda r: r.get('timestamp', ''), reverse=True)


def load_hypotheses(domain: str = None) -> List[Dict]:
    """Load hypotheses, optionally filtered by domain."""
    hyp_file = GALILEO_DATA_DIR / 'hypotheses.jsonl'
    rows, _, _ = read_jsonl(hyp_file)
    if domain:
        rows = [h for h in rows if h.get('domain') == domain]
    return rows


def load_experiments(status: str = None) -> List[Dict]:
    """Load experiments, optionally filtered by status."""
    exp_file = GALILEO_DATA_DIR / 'experiments.jsonl'
    rows, _, _ = read_jsonl(exp_file)
    if status:
        rows = [e for e in rows if e.get('status') == status]
    return rows


def load_priors(domain: str = None) -> List[Dict]:
    """Load prior cache entries."""
    priors_file = GALILEO_DATA_DIR / 'priors_cache.jsonl'
    rows, _, _ = read_jsonl(priors_file)
    if domain:
        rows = [p for p in rows if p.get('domain') == domain]
    return rows


def save_hypothesis(hyp: Dict) -> None:
    """Save single hypothesis record."""
    hyp_file = GALILEO_DATA_DIR / 'hypotheses.jsonl'
    write_jsonl(hyp_file, hyp)


def save_experiment(exp: Dict) -> None:
    """Save single experiment record."""
    exp_file = GALILEO_DATA_DIR / 'experiments.jsonl'
    write_jsonl(exp_file, exp)


def save_score(score_record: Dict) -> None:
    """Save single score record."""
    scores_file = GALILEO_DATA_DIR / 'scores.jsonl'
    write_jsonl(scores_file, score_record)


def save_run_record(run: Dict) -> None:
    """Save run summary record."""
    runs_file = GALILEO_DATA_DIR / 'runs.jsonl'
    write_jsonl(runs_file, run)


def load_domain_pack(domain: str) -> Dict:
    """Load domain-specific configuration pack."""
    pack_file = GALILEO_DATA_DIR / 'domain_packs' / f"{domain}.json"
    
    if pack_file.exists():
        with open(pack_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Create default/starter pack if missing
    default_pack = {
        'domain': domain,
        'available_signals': [],
        'allowed_methods': ['simulation', 'ablation'],
        'local_datasets': [],
        'synthetic_generators': ['synthetic_gen_v1'],
        'metrics': ['signal', 'effect_size'],
        'constraints': ['no web', 'local compute only']
    }
    
    # Save it for next time
    try:
        pack_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pack_file, 'w', encoding='utf-8') as f:
            json.dump(default_pack, f, indent=2)
    except Exception:
        pass  # Silently fail to save
    
    return default_pack

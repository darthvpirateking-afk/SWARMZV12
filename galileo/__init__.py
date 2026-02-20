# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
GALILEO HARNESS v0.1
Deterministic hypothesis generation and testing system
Local-first, operator-gated, rule-based validation
"""

from .determinism import stableStringify, inputs_hash, generate_ids
from .similarity import check_similarity, compute_jaccard
from .gates import apply_gates
from .scorer import score_hypothesis, should_accept
from .storage import init_storage, load_runs, load_hypotheses, load_experiments, save_run_record
from .prompts import get_generator_prompt, get_critic_prompt, get_experimentalist_prompt, get_scorer_prompt

__all__ = [
    'stableStringify',
    'inputs_hash',
    'generate_ids',
    'check_similarity',
    'compute_jaccard',
    'apply_gates',
    'score_hypothesis',
    'should_accept',
    'init_storage',
    'load_runs',
    'load_hypotheses',
    'load_experiments',
    'save_run_record',
    'get_generator_prompt',
    'get_critic_prompt',
    'get_experimentalist_prompt',
    'get_scorer_prompt',
]


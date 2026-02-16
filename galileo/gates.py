"""
Gates module: hard rule-based filtering gates (deterministic, no LLM)
G0: Falsifiable - must have failure criteria
G1: Specific - predictions must include direction and metric name
G2: Testable locally - must reference local paths or synthetic generators
G3: Non-trivial - reject tautologies/definitions
G4: Novelty - local similarity threshold
"""

from typing import Dict, List, Tuple
import re


TAUTOLOGY_PATTERNS = [
    r'more\s+data',
    r'depends\s+on',
    r'in\s+general',
    r'could\s+be',
    r'may\s+be',
    r'by\s+definition',
    r'is\s+a',
    r'tends\s+to',
    r'sometimes',
]


def gate_g0_falsifiable(hypothesis: Dict) -> Tuple[bool, str]:
    """
    G0 FALSIFIABLE: must include at least one failure_criteria OR
    disconfirming observable in predictions/test_outline.
    
    Args:
        hypothesis: Hypothesis dict with predictions, test_outline, failure_criteria
        
    Returns:
        Tuple of (pass: bool, reason: str)
    """
    failure_criteria = hypothesis.get('failure_criteria', [])
    predictions = hypothesis.get('predictions', [])
    test_outline = hypothesis.get('test_outline', '')
    
    # Check for explicit failure criteria
    if failure_criteria and len(failure_criteria) > 0:
        return True, "Has explicit failure criteria"
    
    # Check for disconfirming language in test outline or predictions
    disconfirm_keywords = ['fail', 'reject', 'disprove', 'falsif', 'contrary', 'against', 'not ']
    test_text = (test_outline or '').lower()
    pred_text = ' '.join([str(p).lower() for p in predictions])
    combined = test_text + ' ' + pred_text
    
    if any(keyword in combined for keyword in disconfirm_keywords):
        return True, "Has disconfirming observable in test outline or predictions"
    
    return False, "No failure criteria or disconfirming observables found"


def gate_g1_specific(hypothesis: Dict) -> Tuple[bool, str]:
    """
    G1 SPECIFIC: predictions must include direction (+/-) AND metric name.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Tuple of (pass: bool, reason: str)
    """
    predictions = hypothesis.get('predictions', [])
    
    if not predictions:
        return False, "No predictions provided"
    
    pred_text = ' '.join([str(p).lower() for p in predictions])
    
    # Check for direction indicators
    has_direction = any(keyword in pred_text for keyword in [
        'increase', 'decrease', '+', '-',  'more', 'less', 'higher', 'lower',
        'improve', 'degrade', 'positive', 'negative'
    ])
    
    # Check for metric names (heuristic: capitalized words or domain-specific terms)
    has_metric = bool(re.search(r'[a-z]+_[a-z]+|[A-Z][a-z]+|accuracy|precision|recall|auc|rmse|mae', pred_text))
    
    if has_direction and has_metric:
        return True, "Has direction indicator AND metric name"
    elif not has_direction:
        return False, "Missing direction indicator"
    elif not has_metric:
        return False, "Missing metric name"
    else:
        return False, "Predictions not specific enough"


def gate_g2_testable_locally(hypothesis: Dict) -> Tuple[bool, str]:
    """
    G2 TESTABLE LOCALLY: experiment protocol must reference local path OR
    synthetic generator.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Tuple of (pass: bool, reason: str)
    """
    experiment = hypothesis.get('experiment', {})
    protocol = experiment.get('protocol', {})
    protocol_str = str(protocol).lower()
    
    # Check for local path references
    has_local_path = any(indicator in protocol_str for indicator in [
        'local', './data', '../../data', './experiments', 'file://',
        'csv', 'json', 'datasets', '.txt'
    ])
    
    # Check for synthetic generator
    has_synthetic = any(indicator in protocol_str for indicator in [
        'synthetic', 'simulation', 'monte carlo', 'generated', 'mock'
    ])
    
    if has_local_path or has_synthetic:
        return True, "References local data or synthetic generator"
    else:
        return False, "Must reference local paths or synthetic generators only"


def gate_g3_non_trivial(hypothesis: Dict) -> Tuple[bool, str]:
    """
    G3 NON-TRIVIAL: reject if claim matches tautology patterns.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Tuple of (pass: bool, reason: str)
    """
    claim = hypothesis.get('claim', '').lower()
    
    for pattern in TAUTOLOGY_PATTERNS:
        if re.search(pattern, claim):
            return False, f"Claim matches tautology pattern: {pattern}"
    
    return True, "Claim is substantive"


def gate_g4_novelty(
    hypothesis: Dict,
    closest_known: str = "",
    similarity_score: float = 0.0,
    threshold: float = 0.82
) -> Tuple[bool, str]:
    """
    G4 NOVELTY: must have novelty_anchor with similarity < threshold.
    
    Args:
        hypothesis: Hypothesis dict
        closest_known: Best matching prior/hypothesis title
        similarity_score: Jaccard similarity to closest match
        threshold: Similarity threshold (default 0.82)
        
    Returns:
        Tuple of (pass: bool, reason: str)
    """
    novelty_anchor = hypothesis.get('novelty_anchor', {})
    
    # Check structure
    if not novelty_anchor:
        return False, "Missing novelty_anchor field"
    
    if 'closest_known' not in novelty_anchor or 'difference' not in novelty_anchor:
        return False, "novelty_anchor missing required fields: closest_known, difference"
    
   # Check similarity threshold
    if similarity_score >= threshold:
        return False, f"Similarity {similarity_score:.2%} exceeds threshold {threshold:.0%}"
    
    return True, f"Novel (similarity {similarity_score:.2%}, below threshold {threshold:.0%})"


def apply_gates(hypothesis: Dict, similarity_score: float = 0.0, threshold: float = 0.82) -> Tuple[bool, List[str], List[str]]:
    """
    Apply all gates (G0..G4) to hypothesis.
    
    Args:
        hypothesis: Hypothesis dict
        similarity_score: Similarity to closest existing hypothesis/prior
        threshold: Similarity threshold for novelty gate
        
    Returns:
        Tuple of (all_pass: bool, passed_gate_names: list, failed_gate_names: list)
    """
    gates = [
        ("G0_FALSIFIABLE", lambda h: gate_g0_falsifiable(h)),
        ("G1_SPECIFIC", lambda h: gate_g1_specific(h)),
        ("G2_TESTABLE_LOCALLY", lambda h: gate_g2_testable_locally(h)),
        ("G3_NON_TRIVIAL", lambda h: gate_g3_non_trivial(h)),
        ("G4_NOVELTY", lambda h: gate_g4_novelty(h, similarity_score=similarity_score, threshold=threshold)),
    ]
    
    passed = []
    failed = []
    
    for gate_name, gate_func in gates:
        try:
            passes, reason = gate_func(hypothesis)
            if passes:
                passed.append(gate_name)
            else:
                failed.append(f"{gate_name}: {reason}")
        except Exception as e:
            failed.append(f"{gate_name}: Exception during evaluation: {str(e)}")
    
    all_pass = len(failed) == 0
    return all_pass, passed, failed

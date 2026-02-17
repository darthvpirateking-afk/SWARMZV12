# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Scorer module: numeric scoring and accept/reject decision logic
Rule-first scoring with deterministic heuristics
"""

from typing import Dict, Tuple, List


def score_novelty(similarity_score: float) -> float:
    """
    Score novelty as 1 - similarity.
    
    Args:
        similarity_score: Jaccard similarity (0..1)
        
    Returns:
        Novelty score (0..1)
    """
    return 1.0 - similarity_score


def score_falsifiability(hypothesis: Dict) -> float:
    """
    Score falsifiability based on presence of failure criteria.
    1.0 if crisp falsifier, else scaled 0..1 based on measurable criteria.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Falsifiability score (0..1)
    """
    failure_criteria = hypothesis.get('failure_criteria', [])
    predictions = hypothesis.get('predictions', [])
    
    # Crisp falsifier
    if failure_criteria and len(failure_criteria) > 0:
        return 1.0
    
    # Partial credit for measurable predictions
    if predictions:
        measurable_keywords = ['metric', 'value', 'threshold', 'significant', 'statistical']
        pred_text = ' '.join([str(p).lower() for p in predictions])
        if any(kw in pred_text for kw in measurable_keywords):
            return 0.7
        else:
            return 0.5
    
    return 0.0


def score_mechanistic_coherence(hypothesis: Dict) -> float:
    """
    Score mechanistic coherence based on explicit causal chain and linked variables.
    Heuristic: +points for causal keywords and explicit variable linking.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Coherence score (0..1)
    """
    mechanism = hypothesis.get('mechanism', '')
    predictions = hypothesis.get('predictions', [])
    
    if not mechanism:
        return 0.0
    
    mechanism_lower = mechanism.lower()
    
    # Causal chain indicators
    causal_keywords = [
        'causes', 'leads to', 'results in', 'affects', 'influences',
        'modulates', 'regulates', 'inhibits', 'activates', 'due to',
        'because', 'therefore', 'thus', 'consequently'
    ]
    
    score = 0.0
    causal_count = sum(1 for kw in causal_keywords if kw in mechanism_lower)
    score += min(0.5, causal_count * 0.1)  # Up to 0.5 for causal terms
    
    # Variable linking (mentions of variables in mechanism AND predictions)
    if predictions:
        pred_text = ' '.join([str(p) for p in predictions])
        # Simple heuristic: if mechanism and predictions share keywords
        mechanism_words = set(mechanism_lower.split())
        pred_words = set(pred_text.lower().split())
        overlap = len(mechanism_words & pred_words)
        score += min(0.5, overlap * 0.05)  # Up to 0.5 for overlaps
    
    return min(1.0, score)


def score_test_cost(hypothesis: Dict) -> float:
    """
    Score test cost: 1.0 if synthetic/local and few steps, else scaled down.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Test cost score (0..1), higher is better (lower cost)
    """
    experiment = hypothesis.get('experiment', {})
    protocol = experiment.get('protocol', {})
    steps = protocol.get('steps', [])
    
    # Check if synthetic/local
    protocol_str = str(experiment).lower()
    is_synthetic = any(kw in protocol_str for kw in ['synthetic', 'simulation', 'mock', 'local'])
    
    step_count = len(steps) if steps else 0
    
    if not is_synthetic:
        return 0.3  # Non-local experiments cost higher
    
    if step_count <= 5:
        return 1.0
    elif step_count <= 10:
        return 0.8
    elif step_count <= 20:
        return 0.6
    else:
        return 0.4


def score_reproducibility(hypothesis: Dict) -> float:
    """
    Score reproducibility: 1.0 if has seed + run_command + expected_artifacts, else 0..1.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Reproducibility score (0..1)
    """
    experiment = hypothesis.get('experiment', {})
    repro = experiment.get('repro', {})
    
    score = 0.0
    
    # Seed present
    if 'seed' in repro and repro['seed'] is not None:
        score += 0.33
    
    # Run command present
    if 'run_command' in repro and repro['run_command']:
        score += 0.33
    
    # Expected artifacts present
    if 'expected_artifacts' in repro and repro['expected_artifacts']:
        score += 0.34
    
    return min(1.0, score)


def score_risk(hypothesis: Dict) -> float:
    """
    Score risk (lower is better): 0.0 for safe, increases for risky operations.
    Default 0.0 (no risk). Increase if requests private data or disallowed actions.
    
    Args:
        hypothesis: Hypothesis dict
        
    Returns:
        Risk score (0..1)
    """
    experiment = hypothesis.get('experiment', {})
    protocol = experiment.get('protocol', {})
    protocol_str = str(protocol).lower()
    
    risk = 0.0
    
    # Check for risky keywords
    risky_keywords = [
        'private', 'personal', 'sensitive', 'secret', 'invasive',
        'tracking', 'monitoring', 'network call', 'api request', 'external',
        'database', 'production', 'delete', 'modify', 'write'
    ]
    
    for keyword in risky_keywords:
        if keyword in protocol_str:
            risk += 0.05
    
    # Ensure risk doesn't exceed 1.0
    return min(1.0, risk)


def score_hypothesis(
    hypothesis: Dict,
    similarity_score: float = 0.0,
    gate_failures: List[str] = None
) -> Dict[str, float]:
    """
    Compute all scores for a hypothesis.
    
    Args:
        hypothesis: Hypothesis dict
        similarity_score: Similarity to closest existing hypothesis
        gate_failures: List of failed gate names (if any)
        
    Returns:
        Dict of {score_name: score_value}
    """
    scores = {
        'novelty': score_novelty(similarity_score),
        'falsifiability': score_falsifiability(hypothesis),
        'mechanistic_coherence': score_mechanistic_coherence(hypothesis),
        'test_cost': score_test_cost(hypothesis),
        'reproducibility': score_reproducibility(hypothesis),
        'risk': score_risk(hypothesis)
    }
    
    return scores


def should_accept(
    scores: Dict[str, float],
    gate_failures: List[str] = None,
    novelty_threshold: float = 0.65,
    risk_threshold: float = 0.2
) -> Tuple[bool, str]:
    """
    Determine if hypothesis should be accepted based on scores and gates.
    
    ACCEPT if:
    - all gates pass (no failures)
    - avg(novelty, falsifiability, reproducibility) >= 0.65
    - risk <= 0.2
    
    Args:
        scores: Dict of scores from score_hypothesis
        gate_failures: List of failed gate names
        novelty_threshold: Minimum average threshold (default 0.65)
        risk_threshold: Maximum risk score (default 0.2)
        
    Returns:
        Tuple of (accept: bool, reason: str)
    """
    if gate_failures is None:
        gate_failures = []
    
    # Check gates
    if gate_failures:
        return False, f"Gates failed: {'; '.join(gate_failures)}"
    
    # Check risk
    risk = scores.get('risk', 1.0)
    if risk > risk_threshold:
        return False, f"Risk {risk:.2f} exceeds threshold {risk_threshold}"
    
    # Check average of key scores
    key_scores = [
        scores.get('novelty', 0.0),
        scores.get('falsifiability', 0.0),
        scores.get('reproducibility', 0.0)
    ]
    avg_score = sum(key_scores) / len(key_scores) if key_scores else 0.0
    
    if avg_score < novelty_threshold:
        return False, f"Average score {avg_score:.2f} below threshold {novelty_threshold}"
    
    return True, f"All criteria met. Avg score: {avg_score:.2f}, Risk: {risk:.2f}"


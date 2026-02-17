# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Similarity module: local-only duplicate detection via Jaccard similarity
Uses 3-gram shingles on normalized claim strings
"""

from typing import List, Tuple, Dict
import re


def normalize_claim(claim: str) -> str:
    """
    Normalize claim text for similarity comparison.
    Lowercase, remove punctuation, normalize whitespace.
    
    Args:
        claim: Raw claim text
        
    Returns:
        Normalized claim
    """
    # Lowercase
    text = claim.lower()
    # Remove punctuation but keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text


def get_3grams(text: str) -> set:
    """
    Extract 3-gram character shingles from text.
    
    Args:
        text: Input text
        
    Returns:
        Set of 3-gram shingles
    """
    text = normalize_claim(text)
    shingles = set()
    for i in range(len(text) - 2):
        shingles.add(text[i:i+3])
    return shingles


def compute_jaccard(claim1: str, claim2: str) -> float:
    """
    Compute Jaccard similarity between two claims.
    Similarity = |intersection| / |union|
    
    Args:
        claim1: First claim
        claim2: Second claim
        
    Returns:
        Jaccard similarity score (0..1)
    """
    shingles1 = get_3grams(claim1)
    shingles2 = get_3grams(claim2)
    
    if not shingles1 and not shingles2:
        return 1.0  # Both empty -> identical
    
    intersection = len(shingles1 & shingles2)
    union = len(shingles1 | shingles2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def check_similarity(
    claim: str,
    priors: List[Dict],
    hypotheses: List[Dict],
    similarity_threshold: float = 0.82
) -> Tuple[float, str, str]:
    """
    Check if claim is similar to existing priors or hypotheses.
    Returns best match and difference.
    
    Args:
        claim: New claim to check
        priors: List of prior entries (each has 'title', optional 'claim')
        hypotheses: List of hypothesis entries (each has 'claim', 'title', 'hypothesis_id')
        similarity_threshold: Threshold above which is considered duplicate (default 0.82)
        
    Returns:
        Tuple of (best_similarity_score, closest_known_ref, difference_text)
        closest_known_ref = "title (id)" or "title"
        difference_text = brief explanation of difference
    """
    best_score = 0.0
    best_match = None
    best_source = None
    
    # Check against priors
    for prior in priors:
        prior_claim = prior.get('claim', prior.get('title', ''))
        score = compute_jaccard(claim, prior_claim)
        if score > best_score:
            best_score = score
            best_match = prior.get('title', 'Unknown')
            best_source = 'prior'
    
    # Check against hypotheses
    for hyp in hypotheses:
        hyp_claim = hyp.get('claim', hyp.get('title', ''))
        score = compute_jaccard(claim, hyp_claim)
        if score > best_score:
            best_score = score
            best_match = hyp.get('title', 'Unknown')
            best_source = 'hypothesis'
            if 'hypothesis_id' in hyp:
                best_match = f"{best_match} ({hyp['hypothesis_id']})"
    
    # Compute difference if there's a match
    difference = ""
    if best_match:
        if best_score >= similarity_threshold:
            difference = f"Similarity: {best_score:.2%} (exceeds threshold {similarity_threshold:.0%})"
        else:
            difference = f"Similarity: {best_score:.2%}"
    else:
        difference = "No similar prior/hypothesis found"
    
    return best_score, best_match or "", difference


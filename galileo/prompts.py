# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Prompts module: LLM prompt templates for Galileo harness
Versioned, seeded, deterministic prompts for generator, critic, experimentalist, scorer
"""

from typing import Dict


def get_generator_prompt(
    domain: str, n_hypotheses: int, domain_pack: Dict = None, seed: int = 0
) -> str:
    """
    Prompt for hypothesis generator LLM.
    Must output STRICT JSON array of hypothesis objects.

    Args:
        domain: Domain name
        n_hypotheses: Number of hypotheses to generate
        domain_pack: Domain configuration
        seed: Random seed (for reproducibility note)

    Returns:
        Prompt string
    """
    if domain_pack is None:
        domain_pack = {}

    allowed_methods = ", ".join(
        domain_pack.get("allowed_methods", ["simulation", "ablation"])
    )
    avail_signals = ", ".join(domain_pack.get("available_signals", [""]))

    return f"""You are a scientific hypothesis generator. Your task is to generate {n_hypotheses} novel, falsifiable hypotheses for the domain: {domain}.

CONSTRAINTS:
- Domain: {domain}
- Allowed methods: {allowed_methods}
- Available signals: {avail_signals}
- Seed: {seed} (note for reproducibility)

For each hypothesis, output STRICT JSON (no markdown, no explanation) with this exact structure:
{{
  "title": "Hypothesis title (short, 5-10 words)",
  "claim": "Main claim (2-3 sentences)",
  "mechanism": "Causal mechanism explaining why this is true",
  "predictions": ["specific prediction 1", "specific prediction 2"],
  "novelty_anchor": {{"closest_known": "what existing idea is closest", "difference": "how this differs"}},
  "assumptions": ["assumption 1", "assumption 2"],
  "confounders": ["potential confounder 1"],
  "required_data": ["data 1"],
  "test_outline": "How would you test this at high level",
  "failure_criteria": ["what would disprove this"]
}}

Output EXACTLY {n_hypotheses} JSON objects, one per line (JSONL format). No markdown code blocks."""


def get_critic_prompt(hypothesis: Dict, domain: str = "") -> str:
    """
    Prompt for hypothesis critic LLM.
    Must output STRICT JSON critique object.

    Args:
        hypothesis: Hypothesis dict to critique
        domain: Domain (optional context)

    Returns:
        Prompt string
    """
    hyp_json = __import__("json").dumps(hypothesis, indent=2)

    return f"""You are a research methods critic. Evaluate this hypothesis for the domain: {domain}

HYPOTHESIS:
{hyp_json}

Output STRICT JSON critique (no markdown) with this structure:
{{
  "strengths": ["strength 1", "strength 2"],
  "confounders_additional": ["potential confounder not listed by author"],
  "strongest_counterargument": "Your most serious objection",
  "duplication_hints": "Is this similar to any well-known hypothesis? Briefly comment.",
  "testability_concerns": "Any issues with testing approach?",
  "reasoning": "Brief explanation of your critique"
}}

Output exactly one JSON object."""


def get_experimentalist_prompt(
    hypothesis: Dict, domain: str = "", seed: int = 0
) -> str:
    """
    Prompt for experiment design assistant (experimentalist).
    Must output STRICT JSON experiment protocol.

    Args:
        hypothesis: Hypothesis dict
        domain: Domain
        seed: Random seed

    Returns:
        Prompt string
    """
    hyp_json = __import__("json").dumps(hypothesis, indent=2)

    return f"""You are an experimental design expert for {domain}. Design a local, reproducible experiment to test this hypothesis:

HYPOTHESIS:
{hyp_json}

CONSTRAINTS:
- MUST use local/synthetic data only (no external APIs)
- MUST be runnable within 1-10 steps
- Include seed={seed} for reproducibility
- Target synthetic simulation or ablation study

Output STRICT JSON experiment protocol (no markdown):
{{
  "goal": "What this experiment aims to test",
  "protocol": {{
    "dataset": "What data source (local path or synthetic)",
    "variables": {{
      "independent": ["variable name"],
      "dependent": ["variable name"],
      "controls": ["control variable"]
    }},
    "method": "simulation|ablation|analysis",
    "steps": ["step 1", "step 2", ...],
    "stopping_rule": "When to stop experiment",
    "success_criteria": "Quantitative threshold for success",
    "failure_criteria": "Quantitative threshold for failure"
  }},
  "repro": {{
    "seed": {seed},
    "env": "local",
    "deps": ["numpy", "pandas"],
    "run_command": "python simulate_hypothesis.py --seed {seed}",
    "expected_artifacts": ["results.json", "metrics.txt"]
  }}
}}

Output exactly one JSON object."""


def get_scorer_prompt(hypothesis: Dict, scores_dict: Dict[str, float] = None) -> str:
    """
    Prompt for scoring reminder (auxiliary, still deterministic rule-based).
    Scorer module does the actual scoring; this is just a rubric reminder.

    Args:
        hypothesis: Hypothesis dict
        scores_dict: Scores computed by scorer module

    Returns:
        Prompt string (informational, not LLM decision)
    """
    scores_str = ""
    if scores_dict:
        scores_str = "\n".join([f"  {k}: {v:.2f}" for k, v in scores_dict.items()])
    else:
        scores_str = "(Scores not yet computed)"

    return f"""GALILEO SCORER RUBRIC (v0.1)

Hypothesis being scored:
Title: {hypothesis.get('title', 'N/A')}
Claim: {hypothesis.get('claim', 'N/A')}

DETERMINISTIC SCORING (by rule-engine, not LLM):
Scores:
{scores_str}

ACCEPTANCE CRITERIA:
- All gates G0-G4 must pass
- Average(novelty, falsifiability, reproducibility) >= 0.65
- Risk <= 0.2

If these criteria are met, STATUS=ACCEPTED.
Otherwise, STATUS=REJECTED with failure reasons.

This is computed deterministically by scorer.py, not by LLM."""

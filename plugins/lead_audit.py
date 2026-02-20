# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Lead Audit Plugin for SWARMZ

Decision Bottleneck product: "Who should I contact today?"
Provides deterministic lead scoring and prioritization.
"""

import csv
import io
import math
from typing import Dict, Any, List
from datetime import datetime


def parse_csv_data(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV content into list of lead dictionaries."""
    leads = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        leads.append(dict(row))
    
    return leads


def calculate_recency_score(last_contact: str) -> float:
    """
    Calculate recency score (0-100).
    More recent = higher score.
    """
    try:
        last_contact_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
        days_ago = (datetime.now() - last_contact_date).days
        
        # Exponential decay: score = 100 * e^(-days/30)
        # 0 days = 100, 30 days = 36.8, 60 days = 13.5, 90 days = 5.0
        score = 100 * math.exp(-days_ago / 30)
        return min(100, max(0, score))
    except:
        # If can't parse, assume very old
        return 10.0


def calculate_value_score(value: str) -> float:
    """
    Calculate value score (0-100).
    Higher value = higher score.
    """
    try:
        # Remove currency symbols and parse
        value_clean = value.replace('$', '').replace(',', '').replace('â‚¬', '').replace('Â£', '')
        value_num = float(value_clean)
        
        # Logarithmic scaling: small differences at low end matter more
        # $0 = 0, $100 = 33, $1000 = 56, $10000 = 78, $100000 = 100
        if value_num <= 0:
            return 0
        
        score = 20 * (value_num ** 0.3)
        return min(100, max(0, score))
    except:
        return 0.0


def calculate_engagement_score(engagement: str) -> float:
    """
    Calculate engagement score (0-100).
    Higher engagement = higher score.
    """
    engagement_map = {
        "cold": 10,
        "low": 25,
        "medium": 50,
        "warm": 75,
        "high": 90,
        "hot": 100
    }
    
    # Try direct mapping first
    engagement_lower = engagement.lower().strip()
    if engagement_lower in engagement_map:
        return float(engagement_map[engagement_lower])
    
    # Try numeric parse
    try:
        score = float(engagement)
        return min(100, max(0, score))
    except:
        # Default to medium
        return 50.0


def score_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single lead deterministically.
    
    Expected fields:
    - name: Lead name
    - last_contact: ISO date string
    - value: Dollar amount or number
    - engagement: Engagement level (cold/warm/hot or 0-100)
    
    Returns scored lead with priority score and reasoning.
    """
    # Extract fields with defaults
    name = lead.get("name", "Unknown")
    last_contact = lead.get("last_contact", "2020-01-01")
    value = lead.get("value", "0")
    engagement = lead.get("engagement", "medium")
    
    # Calculate component scores
    recency_score = calculate_recency_score(last_contact)
    value_score = calculate_value_score(str(value))
    engagement_score = calculate_engagement_score(str(engagement))
    
    # Weighted composite score
    # Engagement is most important (50%), then value (30%), then recency (20%)
    composite_score = (
        engagement_score * 0.5 +
        value_score * 0.3 +
        recency_score * 0.2
    )
    
    # Generate reasoning
    reasoning_parts = []
    
    if engagement_score >= 75:
        reasoning_parts.append("High engagement")
    elif engagement_score <= 25:
        reasoning_parts.append("Low engagement")
    
    if value_score >= 70:
        reasoning_parts.append("High value")
    elif value_score <= 30:
        reasoning_parts.append("Low value")
    
    if recency_score >= 70:
        reasoning_parts.append("Recently contacted")
    elif recency_score <= 30:
        reasoning_parts.append("Not contacted recently")
    
    if not reasoning_parts:
        reasoning_parts.append("Medium priority")
    
    reasoning = ", ".join(reasoning_parts)
    
    # Priority tier
    if composite_score >= 75:
        priority = "HIGH"
    elif composite_score >= 50:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    
    return {
        "name": name,
        "score": round(composite_score, 2),
        "priority": priority,
        "reasoning": reasoning,
        "components": {
            "recency": round(recency_score, 2),
            "value": round(value_score, 2),
            "engagement": round(engagement_score, 2)
        },
        "original_data": lead
    }


def audit_leads(csv_content: str) -> Dict[str, Any]:
    """
    Audit and prioritize leads from CSV data.
    
    Args:
        csv_content: CSV string with columns: name, last_contact, value, engagement
    
    Returns:
        Dictionary with:
        - leads: List of scored leads sorted by priority
        - summary: Statistics
        - recommendation: Top lead to contact
    """
    # Parse CSV
    leads = parse_csv_data(csv_content)
    
    if not leads:
        return {
            "leads": [],
            "summary": {"total": 0},
            "recommendation": None,
            "error": "No leads found in CSV"
        }
    
    # Score all leads
    scored_leads = [score_lead(lead) for lead in leads]
    
    # Sort by score descending
    scored_leads.sort(key=lambda x: x["score"], reverse=True)
    
    # Calculate summary statistics
    high_priority = sum(1 for lead in scored_leads if lead["priority"] == "HIGH")
    medium_priority = sum(1 for lead in scored_leads if lead["priority"] == "MEDIUM")
    low_priority = sum(1 for lead in scored_leads if lead["priority"] == "LOW")
    
    avg_score = sum(lead["score"] for lead in scored_leads) / len(scored_leads)
    
    summary = {
        "total": len(scored_leads),
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "average_score": round(avg_score, 2)
    }
    
    # Top recommendation
    recommendation = None
    if scored_leads:
        top_lead = scored_leads[0]
        recommendation = {
            "name": top_lead["name"],
            "score": top_lead["score"],
            "reasoning": f"Contact {top_lead['name']} first - {top_lead['reasoning']}"
        }
    
    return {
        "leads": scored_leads,
        "summary": summary,
        "recommendation": recommendation
    }


def register(executor):
    """Register Lead Audit tasks with SWARMZ executor."""
    
    def audit_leads_task(csv_content: str) -> Dict[str, Any]:
        """Audit and prioritize leads from CSV."""
        return audit_leads(csv_content)
    
    def score_single_lead(name: str, last_contact: str, value: str, engagement: str) -> Dict[str, Any]:
        """Score a single lead."""
        lead = {
            "name": name,
            "last_contact": last_contact,
            "value": value,
            "engagement": engagement
        }
        return score_lead(lead)
    
    # Register tasks
    executor.register_task("lead_audit", audit_leads_task, {
        "description": "Audit and prioritize leads from CSV data",
        "params": {"csv_content": "string"},
        "category": "lead_audit"
    })
    
    executor.register_task("lead_audit_score_single", score_single_lead, {
        "description": "Score a single lead",
        "params": {
            "name": "string",
            "last_contact": "string",
            "value": "string",
            "engagement": "string"
        },
        "category": "lead_audit"
    })


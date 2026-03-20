"""Utilities module"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional


def generate_processing_id() -> str:
    """Generate unique processing ID."""
    return str(uuid.uuid4())


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """Save dictionary to JSON file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file to dictionary."""
    with open(file_path, 'r') as f:
        return json.load(f)


def format_score_for_display(score: float, max_score: float = 10) -> str:
    """Format score with visual indicator."""
    percentage = (score / max_score) * 100
    bars = int(percentage / 10)
    return f"[{'█' * bars}{'░' * (10 - bars)}] {score:.1f}/{max_score}"


def get_risk_color(risk_level: str) -> str:
    """Get ANSI color code for risk level."""
    colors = {
        "low": "\033[92m",      # Green
        "medium": "\033[93m",   # Yellow
        "high": "\033[91m"      # Red
    }
    return colors.get(risk_level, "\033[0m")  # Default


def print_colored(text: str, color: str = "\033[0m") -> None:
    """Print colored text to terminal."""
    reset = "\033[0m"
    print(f"{color}{text}{reset}")


def summarize_output(output: Dict[str, Any]) -> str:
    """Generate a human-readable summary of ATS output."""
    
    summary = []
    summary.append(f"\n{'='*70}")
    summary.append(f"TRINITY ATS EVALUATION REPORT")
    summary.append(f"{'='*70}\n")
    
    # Candidate info
    candidate = output.get("candidate_profile", {})
    summary.append(f"CANDIDATE: {candidate.get('candidate_name', 'Unknown')}")
    summary.append(f"Role: {output.get('job_title', 'Unknown')}\n")
    
    # Overall result
    score = output.get("overall_match_score", 0)
    confidence = output.get("confidence_level", 0)
    recommendation = output.get("hiring_recommendation", "unknown")
    
    summary.append(f"MATCH SCORE: {format_score_for_display(score)}")
    summary.append(f"CONFIDENCE: {confidence*100:.1f}%")
    summary.append(f"RECOMMENDATION: {recommendation.upper()}\n")
    
    # Individual scores
    summary.append("COMPONENT SCORES:")
    for agent_name, score_data in output.get("individual_scores", {}).items():
        score = score_data.get("score", 0)
        confidence = score_data.get("confidence", 0)
        summary.append(f"  • {agent_name}: {score}/10 (confidence: {confidence*100:.0f}%)")
    
    # Bias analysis
    summary.append(f"\nBIAS ANALYSIS: {output.get('bias_analysis', {}).get('risk_level', 'unknown').upper()}")
    
    # Recommendations
    summary.append(f"\nRECOMMENDATIONS:")
    for rec in output.get("recommendations_for_hiring", [])[:3]:
        summary.append(f"  • {rec}")
    
    summary.append(f"\n{'='*70}\n")
    
    return "\n".join(summary)

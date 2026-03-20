"""
Pydantic models for typed state in the NARI ATS Framework.
These models ensure type safety and validation across all agents.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ExperienceEntry(BaseModel):
    """Represents a candidate's work experience."""
    job_title: str
    company: str
    duration_start: Optional[str] = None
    duration_end: Optional[str] = None
    duration_years: Optional[float] = None
    description: str
    key_achievements: Optional[List[str]] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """Represents a candidate's educational background."""
    degree: str
    institution: str
    field_of_study: str
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None
    relevant_coursework: Optional[List[str]] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    """Represents a candidate's project."""
    project_name: str
    description: str
    technologies: Optional[List[str]] = Field(default_factory=list)
    url: Optional[str] = None  # GitHub link, portfolio link, etc.
    date: Optional[str] = None


class SkillEntry(BaseModel):
    """Represents a candidate's skill with context."""
    skill_name: str
    proficiency_level: Optional[str] = None  # "junior", "intermediate", "senior", "expert"
    years_of_experience: Optional[float] = None
    context: Optional[str] = None  # Where/how they used this skill


class ExtractedResume(BaseModel):
    """
    Unified resume schema created by format extractors.
    This ensures all formats (PDF, DOCX, HTML, Images, Text) 
    produce the same structured output.
    """
    # Metadata
    format: str  # "PDF", "DOCX", "HTML", "TEXT", "IMAGE"
    extraction_confidence: float = Field(default=0.9, ge=0, le=1)
    extracted_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Raw content
    full_text: str
    
    # Structured fields (extracted by specialized agents)
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    candidate_location: Optional[str] = None
    professional_summary: Optional[str] = None
    achievements: Optional[Union[str, List[str]]] = None
    
    # Core data
    skills: Optional[List[SkillEntry]] = Field(default_factory=list)
    experience: Optional[List[ExperienceEntry]] = Field(default_factory=list)
    education: Optional[List[EducationEntry]] = Field(default_factory=list)
    projects: Optional[List[ProjectEntry]] = Field(default_factory=list)
    
    # Links and profiles
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobDescription(BaseModel):
    """Represents a job description with structured requirements."""
    job_title: str
    company: str
    description: str
    
    # Required fields
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    years_of_experience_min: Optional[int] = None
    years_of_experience_max: Optional[int] = None
    
    # Nice to have
    education_requirements: List[str] = Field(default_factory=list)
    preferred_certifications: List[str] = Field(default_factory=list)
    
    # Context
    level: str = Field(default="mid")  # "junior", "mid", "senior", "lead"
    department: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScoringResult(BaseModel):
    """Result from one scoring agent."""
    agent_name: str
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    key_factors: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)


class BiasFlag(BaseModel):
    """Represents a potential bias detected."""
    flag_type: str  # proxy_discriminator, biased_language, pattern_anomaly
    severity: str  # "low", "medium", "high"
    description: str
    recommendation: str


class BiasFlagsAnalysis(BaseModel):
    """Analysis of potential biases in hiring decision."""
    detected_biases: List[BiasFlag] = Field(default_factory=list)
    risk_level: str = Field(default="low")  # "low", "medium", "high"
    overall_assessment: str
    reasoning: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)


class PortfolioEvidence(BaseModel):
    """Evidence extracted from portfolio/GitHub/external sources."""
    source: str  # "github", "portfolio", "linkedin"
    profile_url: Optional[str] = None
    key_projects: List[ProjectEntry] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    verified_skills: List[str] = Field(default_factory=list)
    contribution_score: Optional[float] = None  # 0-10
    analysis: str


class ScoringRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AggregatedScore(BaseModel):
    """Final aggregated scoring (consensus)."""
    overall_match_score: float = Field(ge=0, le=10)
    component_scores: Dict[str, ScoringResult]  # agent_name -> ScoringResult
    confidence_level: float = Field(ge=0, le=1)
    scoring_note: str  # Explains the aggregation


class CandidateRecommendation(BaseModel):
    """Recommendations for the candidate."""
    strengths: List[str]
    areas_for_growth: List[str]
    personalized_feedback: str


class FinalATSOutput(BaseModel):
    """
    Final JSON output of the NARI ATS system.
    Includes candidate profile, scores, reasoning, bias analysis, and recommendations.
    """
    # Metadata
    processing_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Candidate and Resume
    candidate_profile: ExtractedResume
    resume_file_format: str
    
    # Matching Results
    job_title: str
    overall_match_score: float = Field(ge=0, le=10)
    individual_scores: Dict[str, ScoringResult]  # agent_name -> ScoringResult
    confidence_level: float = Field(ge=0, le=1)
    reasoning: str
    
    # Fairness & Bias Analysis
    bias_analysis: BiasFlagsAnalysis
    
    # External Evidence
    portfolio_evidence: Optional[PortfolioEvidence] = None
    
    # Recommendations
    hiring_recommendation: str  # "strong_yes", "yes", "maybe", "no", "strong_no"
    recommendations_for_hiring: List[str]
    feedback_for_candidate: List[str]
    
    # Explainability
    decision_factors: Dict[str, Any]


class NARIState(BaseModel):
    """
    Shared state passed through the LangGraph workflow.
    Updated by each agent, read by downstream agents.
    """
    # Input
    resume_file_path: str
    resume_file_format: Optional[str] = None
    job_description: JobDescription
    
    # Extracted Resume (produced by extractors)
    extracted_resume: Optional[ExtractedResume] = None
    extraction_errors: List[str] = Field(default_factory=list)
    
    # Format Validation (consistency check across formats)
    format_consistency_check: Optional[Dict[str, Any]] = None
    consistency_warnings: List[str] = Field(default_factory=list)
    
    # Scoring Results (from parallel agents)
    scoring_results: Dict[str, ScoringResult] = Field(default_factory=dict)
    aggregated_score: Optional[AggregatedScore] = None
    scoring_complete: bool = False
    
    # Bias Analysis
    bias_analysis: Optional[BiasFlagsAnalysis] = None
    
    # Portfolio/GitHub Evidence
    portfolio_evidence: Optional[PortfolioEvidence] = None
    
    # Final Output
    final_output: Optional[FinalATSOutput] = None
    
    # Processing metadata
    processing_id: str
    processing_start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_errors: List[str] = Field(default_factory=list)

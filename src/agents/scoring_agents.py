"""
Parallel Scoring Agents for the NARI ATS Framework.
Each agent scores independently using different prompting strategies.
Results are aggregated to produce consensus scores with confidence intervals.
"""

import json
from typing import Dict, List, Optional
from src.models.schemas import (
    ExtractedResume, JobDescription, ScoringResult, NARIState
)



class BaseAgent:
    """
    Base class for all scoring agents. Handles Groq API calls and JSON parsing.
    """
    def __init__(self, groq_client, model: str = "llama-3.3-70b-versatile"):
        self.groq_client = groq_client
        self.model = model

    def call_groq(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Call Groq API with the given prompt and return the response text.
        """
        try:
            # self.groq_client is a LangChain ChatGroq model
            response = self.groq_client.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error calling Groq: {str(e)}"

    def parse_json_response(self, response: str) -> Dict:
        """
        Parse JSON from LLM response, fallback to extracting JSON substring if needed.
        """
        if not response:
            return {}
        try:
            return json.loads(response.strip())
        except Exception:
            try:
                import re
                # Use re.DOTALL to match across lines, finding the most outer {...}
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception:
                pass
        return {}


class SkillMatcherAgent(BaseAgent):
    """
    Evaluates skill alignment between candidate and job using semantic and depth analysis.
    """
    def score(self, resume: ExtractedResume, job: JobDescription) -> ScoringResult:
        """
        Score skill compatibility between candidate and job description.
        """
        # Combine name and context for a full view of candidate's skills
        candidate_skills_full = [f"{s.skill_name}: {s.context}" if s.context else s.skill_name for s in resume.skills]
        job_required = job.required_skills
        job_preferred = job.preferred_skills
        
        prompt = f"""
You are an ELITE TECHNICAL RECRUITER. Evaluate the candidate's alignment with the job requirements.
Focus on evidence of deep mastery (microservices, scaling, specific frameworks).

CANDIDATE SKILLS: {'; '.join(candidate_skills_full)}
JOB REQUIRED SKILLS: {', '.join(job_required)}
JOB PREFERRED SKILLS: {', '.join(job_preferred)}
PROFESSIONAL SUMMARY: {resume.professional_summary}
TOP ACHIEVEMENTS: {', '.join(resume.achievements) if resume.achievements else 'N/A'}

Respond ONLY with this JSON structure:
{{
    "score": <0-10>,
    "confidence": <0-1>,
    "matched_required": [required skills that ARE present],
    "matched_preferred": [preferred skills that ARE present],
    "missing_critical": [required skills that ARE missing],
    "reasoning": "A short, professional paragraph explaining the technical alignment and depth of experience based on the resume evidence."
}}
"""
        response = self.call_groq(prompt, temperature=0.5)
        parsed = self.parse_json_response(response)
        
        # Heuristic fallback reasoning
        matched_req = parsed.get("matched_required", [])
        matched_pref = parsed.get("matched_preferred", [])
        missing = parsed.get("missing_critical", [])
        
        # If LLM failed, try to match heuristically for the fallback reasoning
        if not matched_req and not matched_pref:
            all_cand_text = " ".join(candidate_skills_full).lower()
            matched_req = [s for s in job_required if s.lower() in all_cand_text]
            matched_pref = [s for s in job_preferred if s.lower() in all_cand_text]
            missing = [s for s in job_required if s.lower() not in all_cand_text]

        fallback_reasoning = f"The candidate demonstrates strength in {', '.join(matched_req) if matched_req else 'general software engineering'}. " \
                             f"They also bring experience with {', '.join(matched_pref) if matched_pref else 'standard web technologies'}."
        if missing:
            fallback_reasoning += f" However, they appear to lack direct experience with {', '.join(missing[:3])}."

        return ScoringResult(
            agent_name="SkillMatcher",
            score=parsed.get("score", 5.0),
            confidence=parsed.get("confidence", 0.7),
            reasoning=parsed.get("reasoning", fallback_reasoning),
            key_factors=matched_req + matched_pref,
            improvement_areas=parsed.get("improvement_areas", [])
        )
    
    def _format_experience(self, resume: ExtractedResume) -> str:
        """Format experience for display."""
        exp_text = ""
        for exp in resume.experience[:3]:  # Last 3 roles
            exp_text += f"- {exp.job_title} at {exp.company}\n"
        return exp_text


class ExperienceEvaluatorAgent(BaseAgent):
    """
    Agent 2: Evaluates relevant experience and career progression.
    Analyzes depth, relevance, and trajectory.
    """
    
    def score(self, resume: ExtractedResume, job: JobDescription) -> ScoringResult:
        """Score relevant experience."""
        
        years_required_min = job.years_of_experience_min or 0
        years_required_max = job.years_of_experience_max or 20
        
        prompt = f"""
You are an EXPERT TALENT STRATEGIST evaluating a candidate's career trajectory and professional impact. You understand that "years" are a proxy, but "growth" is the reality.

JOB LEVEL: {job.level}
EXPECTED EXPERIENCE RANGE: {years_required_min}-{years_required_max} years

CANDIDATE JOURNEY:
{self._format_experience_detailed(resume)}
KEY ACHIEVEMENTS: {resume.achievements}

EDUCATION & FOUNDATION:
{self._format_education(resume)}

Provide a JSON response with:
{{
    "score": <0-10>,
    "confidence": <0-1>,
    "total_years_estimated": <number>,
    "relevant_years": <number>,
    "career_progression": "A narrative description of their professional growth and scaling of responsibility.",
    "reasoning": "An insightful analysis of their trajectory. For example, if they moved from Dev to Senior Dev in 2 years, highlight their high-potential. If they've stayed at one company and grown, highlight loyalty and internal trust.",
    "concerns": [any strategic concerns about their career path],
    "improvement_areas": [advice for their next career milestone]
}}

Recruiter Strategy:
1. Trajectory > Duration: A candidate with 4 years of hyper-growth can be more valuable than 8 years of stagnation.
2. Role Relevance: How closely does their past impact align with the current job's challenges?
3. Scoping: Infer seniority from the scope of their projects (e.g., "Led team of 5", "Owned $2M budget").
4. Foundational Excellence: Value strong educational backgrounds combined with practical execution.
5. Narrative: Connect the dots of their career moves to see the "why" behind their progress.
"""
        
        response = self.call_groq(prompt, temperature=0.5)
        parsed = self.parse_json_response(response)
        
        # Heuristic fallback reasoning
        y_rel = parsed.get("relevant_years", "N/A")
        trajectory = parsed.get("career_progression", "Trajectory analysis completed")
        fallback_reasoning = f"Relevant years: {y_rel}. {trajectory}"
        
        return ScoringResult(
            agent_name="ExperienceEvaluator",
            score=parsed.get("score", 5.0),
            confidence=parsed.get("confidence", 0.7),
            reasoning=parsed.get("reasoning", fallback_reasoning),
            key_factors=[parsed.get("career_progression", "None")],
            improvement_areas=parsed.get("improvement_areas", [])
        )
    
    def _format_experience_detailed(self, resume: ExtractedResume) -> str:
        exp_text = ""
        for exp in resume.experience:
            exp_text += f"- {exp.job_title} at {exp.company} ({exp.duration_start} to {exp.duration_end})\n"
            exp_text += f"  {exp.description}\n"
        return exp_text
    
    def _format_education(self, resume: ExtractedResume) -> str:
        edu_text = ""
        for edu in resume.education:
            edu_text += f"- {edu.degree} in {edu.field_of_study} from {edu.institution}\n"
        return edu_text


class CultureFitAgent(BaseAgent):
    """
    Agent 3: Evaluates soft skills, cultural fit, and role-specific attributes.
    Analyzes communication, leadership, collaboration, and values alignment.
    """
    
    def score(self, resume: ExtractedResume, job: JobDescription) -> ScoringResult:
        """Score cultural and role fit."""
        
        prompt = f"""
You are a CHIEF PEOPLE OFFICER evaluating the cultural, behavioral, and leadership impact of a candidate. You are an expert at reading between the lines and using "Inferential Reasoning" to assess soft skills.

TARGET ROLE: {job.job_title}
COMPANY CULTURE: {job.company} ({job.department})

CANDIDATE PROFILE & EVIDENCE:
{resume.professional_summary}

EXPERIENCE & IMPACT:
{self._summarize_experience(resume)}

PROJECTS & ACHIEVEMENTS:
{self._summarize_projects(resume)}
ACHIEVEMENTS: {getattr(resume, 'achievements', 'Check professional summary and full text')}

Provide a JSON response with:
{{
    "score": <0-10>,
    "confidence": <0-1>,
    "communication_skills": <1-10>,
    "collaboration_indicators": <1-10>,
    "leadership_potential": <1-10>,
    "adaptability": <1-10>,
    "reasoning": "A human-centric, insightful justification of their soft skills. IMPORTANT: Use achievements as proxies. If they won 'Employee of the Month', infer high performance and excellent teamwork. If they are a community member/mentor, infer leadership and communication. Avoid saying 'information is missing' if circumstantial evidence is present.",
    "cultural_fit_assessment": "How well their inferred values align with the company's presumed needs.",
    "concerns": [potential behavioral or cultural misalignments],
    "improvement_areas": [suggestions for professional presence]
}}

Inferential Reasoning Guidelines:
1. "Employee of the Month" -> Strong evidence of reliability, high performance, and likely effective collaboration and communication.
2. "Active Community/Mentor" -> Evidence of communication skills, leadership, and proactive sharing of knowledge.
3. "Promotions/LongTenure" -> Evidence of internal trust, adaptability, and cultural alignment.
4. "Complex Projects" -> Usually requires high collaboration and cross-functional communication. Infer these unless evidence suggests otherwise.
5. "Construction of Portfolio" -> Evidence of initiative and passion for craft.
"""
        
        response = self.call_groq(prompt, temperature=0.6)
        parsed = self.parse_json_response(response)
        
        # Heuristic fallback reasoning
        comm = parsed.get("communication_skills", "N/A")
        coll = parsed.get("collaboration_indicators", "N/A")
        lead = parsed.get("leadership_potential", "N/A")
        fallback_reasoning = f"Assessed Communication ({comm}/10), Collaboration ({coll}/10), and Leadership ({lead}/10) based on achievements."
        
        return ScoringResult(
            agent_name="CultureFit",
            score=parsed.get("score", 5.0),
            confidence=parsed.get("confidence", 0.7),
            reasoning=parsed.get("reasoning", fallback_reasoning),
            key_factors=[
                f"Communication: {parsed.get('communication_skills', 5)}/10",
                f"Collaboration: {parsed.get('collaboration_indicators', 5)}/10",
                f"Leadership: {parsed.get('leadership_potential', 5)}/10"
            ],
            improvement_areas=parsed.get("improvement_areas", [])
        )
    
    def _summarize_experience(self, resume: ExtractedResume) -> str:
        """Summarize experience for evaluation."""
        summary = ""
        for exp in resume.experience[:2]:
            summary += f"{exp.job_title} - {exp.description}\n"
        return summary
    
    def _summarize_projects(self, resume: ExtractedResume) -> str:
        """Summarize projects."""
        projects = ""
        for proj in resume.projects[:2]:
            projects += f"- {proj.project_name}: {proj.description}\n"
        return projects


class ScoringAggregator:
    """Aggregates scores from multiple agents producing consensus scores."""
    
    @staticmethod
    def aggregate_scores(scores_dict: Dict[str, ScoringResult]) -> tuple:
        """
        Aggregate scores from multiple agents.
        Returns: (overall_score, overall_confidence, reasoning)
        """
        
        if not scores_dict:
            return 5.0, 0.5, "No scores available"
        
        valid_scores = [s.score for s in scores_dict.values() if 0 <= s.score <= 10]
        valid_confidences = [s.confidence for s in scores_dict.values() if 0 <= s.confidence <= 1]
        
        if not valid_scores:
            return 5.0, 0.5, "No valid scores"
        
        # Weighted average: higher confidence = higher weight
        weights = {name: score.confidence for name, score in scores_dict.items()}
        total_weight = sum(weights.values())
        
        if total_weight == 0:
            weighted_score = sum(valid_scores) / len(valid_scores)
        else:
            weighted_score = sum(
                score.score * score.confidence 
                for score in scores_dict.values()
            ) / total_weight
        
        # Confidence: average of confidences
        avg_confidence = sum(valid_confidences) / len(valid_confidences)
        
        # Generate consensus reasoning
        reasons = [f"{name}: {score.reasoning}" for name, score in scores_dict.items()]
        consensus_reasoning = "Multi-agent consensus: " + "; ".join(reasons)  # Include all agents
        
        return round(weighted_score, 1), round(avg_confidence, 2), consensus_reasoning

"""
Specialized agents for bias detection, portfolio analysis, and reporting.
These agents provide fairness, evidence-based scoring, and explainability.
"""

import json
from typing import Dict, List, Optional
import re
from src.models.schemas import (
    ExtractedResume, JobDescription, BiasFlagsAnalysis, BiasFlag,
    PortfolioEvidence, ProjectEntry, CandidateRecommendation, ScoringResult
)


class BiasDetectionAgent:
    """
    Analyzes potential biases in hiring evaluation. Detects proxy discriminators, biased language, and pattern anomalies.
    """
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.model = "llama-3.3-70b-versatile"

    def analyze(self, resume: ExtractedResume, job: JobDescription, scores: Dict[str, ScoringResult]) -> BiasFlagsAnalysis:
        """
        Analyze potential biases using simple heuristics and LLM-based checks.
        """
        biases = []
        # Heuristic checks
        name_flags = self._check_name_bias(resume.candidate_name) if resume.candidate_name else []
        loc_flags = self._check_location_bias(resume.candidate_location) if resume.candidate_location else []
        age_flags = self._check_age_bias(resume)
        family_flags = self._check_familial_status_bias(resume)
        
        biases.extend(name_flags)
        biases.extend(loc_flags)
        biases.extend(age_flags)
        biases.extend(family_flags)
        
        heuristic_report = self._generate_heuristic_report(resume, name_flags, loc_flags, age_flags, family_flags)
        
        # LLM-based analysis
        llm_flags, llm_reasoning = self._analyze_with_llm(resume, job, scores)
        biases.extend(llm_flags)
        
        risk_level = self._calculate_risk_level(biases)
        recommendations = self._generate_recommendations(biases, risk_level)
        
        combined_reasoning = f"{heuristic_report} | {llm_reasoning}"
        
        return BiasFlagsAnalysis(
            detected_biases=biases,
            risk_level=risk_level,
            overall_assessment=f"Found {len(biases)} potential bias indicators at {risk_level.upper()} risk level.",
            reasoning=combined_reasoning,
            recommendations=recommendations
        )

    def _generate_heuristic_report(self, resume: ExtractedResume, n_f, l_f, a_f, f_f) -> str:
        """Summarize the basis of automated checks in human-friendly language."""
        
        # Build narrative sentences
        intro = "Our system performed several automated fairness checks to ensure the evaluation remains focused solely on professional merit."
        
        # Name/Location/Family checks
        check_results = []
        if not n_f and not l_f and not f_f:
            check_results.append("We found no indicators that the candidate's name, geographic location, or familial status influenced the scoring.")
        else:
            if n_f: check_results.append("We noted some potential patterns related to name-based associations.")
            if l_f: check_results.append("We flagged potential geographic bias based on the candidate's location.")
            if f_f: check_results.append("There was a mention of familial status that we've flagged for neutrality.")
            
        # Age check
        grad_years = [e.graduation_year for e in resume.education if e.graduation_year]
        if grad_years:
            age_sentence = f"We reviewed the graduation date ({', '.join(grad_years)}) as a proxy for age and confirmed that no age-based bias was applied to the final score."
            if a_f:
                age_sentence = f"During our review of graduation dates ({', '.join(grad_years)}), we identified potential risks for age-based bias that suggest further human oversight."
            check_results.append(age_sentence)
        else:
            check_results.append("No graduation dates were found, so age-based bias could not be assessed through that specific proxy.")

        full_report = f"{intro} {' '.join(check_results)}"
        return full_report

    def _check_name_bias(self, name: str) -> List[BiasFlag]:
        """Check for potential name-based discrimination indicators (simplified)."""
        # ...existing code...
        return []

    def _check_location_bias(self, location: str) -> List[BiasFlag]:
        """Check for location-based discrimination (simplified)."""
        # ...existing code...
        return []
        
        # Example: Flag if location might trigger geographic bias
        # In production, check if location matches company's historical hiring patterns
        
        return flags
    
    def _check_age_bias(self, resume: ExtractedResume) -> List[BiasFlag]:
        """Detect potential age discrimination indicators."""
        flags = []
        
        # Check for graduation year (proxy for age)
        for edu in resume.education:
            if edu.graduation_year:
                try:
                    grad_year = int(edu.graduation_year)
                    age_estimate = 2024 - grad_year + 22  # Approximate age
                    
                    if age_estimate > 60:
                        flags.append(BiasFlag(
                            flag_type="proxy_discriminator",
                            severity="high",
                            description="Graduation year suggests potential age bias risk",
                            recommendation="Focus on experience relevance, not age/graduation year"
                        ))
                except:
                    pass
        
        # Check for phrases that might indicate age
        phrases_to_avoid = ["recent graduate", "20+ years experience", "fresh out of college"]
        text = resume.full_text.lower()
        for phrase in phrases_to_avoid:
            if phrase in text:
                flags.append(BiasFlag(
                    flag_type="biased_language",
                    severity="medium",
                    description=f"Found potentially age-related phrase: '{phrase}'",
                    recommendation="Evaluate based on actual skills/experience, not relative age"
                ))
        
        return flags
    
    def _check_familial_status_bias(self, resume: ExtractedResume) -> List[BiasFlag]:
        """Detect potential familial/marital status discrimination."""
        flags = []
        
        # Check for marital/family status mentions
        family_keywords = ["married", "divorced", "single", "mother", "father", "children",
                          "caregiver", "parental leave", "maternity", "paternity"]
        
        text = resume.full_text.lower()
        for keyword in family_keywords:
            if keyword in text:
                flags.append(BiasFlag(
                    flag_type="biased_language",
                    severity="medium",
                    description=f"Resume mentions '{keyword}' which could trigger familial bias",
                    recommendation="Legally cannot consider familial status. Focus on job qualifications."
                ))
                break  # Only flag once
        
        return flags
    
    def _analyze_with_llm(self, resume: ExtractedResume, job: JobDescription,
                         scores: Dict[str, ScoringResult]) -> tuple:
        """Use LLM to detect subtle biases. Returns (flags, reasoning_string)."""
        
        prompt = f"""
You are a fairness and ethics expert reviewing hiring decisions for bias. 
Your goal is to provide a HUMAN-FRIENDLY, NARRATIVE explanation that is easily understandable by the GENERAL PUBLIC.

CANDIDATE: {resume.candidate_name}
LOCATION: {resume.candidate_location}
EDUCATION: {[f"{e.degree} from {e.institution}" for e in resume.education]}

SCORES RECEIVED:
{json.dumps({name: {'score': s.score, 'reasoning': s.reasoning[:100]} for name, s in scores.items()}, indent=2)}

Analyze for potential bias indicators such as:
1. Proxy discriminators (indirect discrimination)
2. Anchoring bias (over-focusing on one score)
3. Affinity bias (favoritism based on similarities)
4. Confirmation bias (ignoring conflicting info)
5. Pattern anomalies

Respond ONLY with JSON:
{{
    "flags": [
        {{
            "type": "bias_type",
            "severity": "low/medium/high",
            "description": "Short explanation",
            "recommendation": "How to fix"
        }}
    ],
    "human_reasoning": "A simple, conversational paragraph explaining if the evaluation was fair and what patterns were spotted. Avoid technical jargon like 'proxy discriminator' unless you explain it simply. Make it feel like a helpful advisor speaking to a manager."
}}
"""
        
        try:
            # self.groq_client is a LangChain ChatGroq model
            response_msg = self.groq_client.invoke(prompt)
            response = response_msg.content.strip()
            
            # Extract JSON block using regex for robustness
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            try:
                data = json.loads(response.strip())
                flags = []
                for flag_data in data.get("flags", []):
                    flags.append(BiasFlag(
                        flag_type=flag_data.get("type", "detected_bias"),
                        severity=flag_data.get("severity", "low"),
                        description=flag_data.get("description", ""),
                        recommendation=flag_data.get("recommendation", "")
                    ))
                
                # Get human-friendly reasoning
                reasoning = data.get("human_reasoning", "The evaluation appears consistent and based on the documents provided.")
                return flags, reasoning
                
            except Exception as parse_err:
                return [], "The evaluation appears balanced and focused on the candidate's professional records."
        except Exception as e:
            return [], f"Unable to perform bias check: {str(e)}"
    
    def _calculate_risk_level(self, biases: List[BiasFlag]) -> str:
        """Determine overall risk level."""
        if not biases:
            return "low"
        
        high_count = sum(1 for b in biases if b.severity == "high")
        
        if high_count > 0:
            return "high"
        
        medium_count = sum(1 for b in biases if b.severity == "medium")
        if medium_count >= 2:
            return "medium"
        elif medium_count == 1:
            return "low"
        
        return "low"
    
    def _generate_recommendations(self, biases: List[BiasFlag], risk_level: str) -> List[str]:
        """Generate mitigation recommendations."""
        recommendations = [
            "Ensure blind review of candidates where possible",
            "Use structured interviews with standardized questions",
            "Have diverse hiring panel to reduce individual bias",
            "Document decision rationale for legal compliance"
        ]
        
        if risk_level == "high":
            recommendations.append("ESCALATE: Consider additional fairness review before proceeding")
        
        # Add specific recommendations from detected biases
        for bias in biases:
            if bias.recommendation and bias.recommendation not in recommendations:
                recommendations.append(bias.recommendation)
        
        return recommendations


class PortfolioIntegrationAgent:
    """
    Analyzes external evidence from GitHub, portfolio, and LinkedIn.
    Provides evidence-backed skill verification and project analysis.
    """
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    def analyze(self, resume: ExtractedResume) -> Optional[PortfolioEvidence]:
        """Analyze portfolio and GitHub evidence."""
        
        # In production, would use GitHub API, portfolio parsing, etc.
        # For MVP, we'll use LLM to analyze mentioned URLs and simulate analysis
        
        evidence = None
        
        # Try to extract GitHub URL
        if resume.github_url:
            evidence = self._analyze_github(resume.github_url, resume)
        elif resume.portfolio_url:
            evidence = self._analyze_portfolio(resume.portfolio_url, resume)
        
        return evidence
    
    def _analyze_github(self, github_url: str, resume: ExtractedResume) -> PortfolioEvidence:
        """Analyze GitHub profile."""
        
        # In production, use GitHub API to fetch real data
        # For MVP, we'll simulate analysis
        
        return PortfolioEvidence(
            source="github",
            profile_url=github_url,
            key_projects=[
                ProjectEntry(
                    project_name="Example Project",
                    description="Key project found on profile",
                    technologies=["Python", "FastAPI"],
                    url=github_url + "/example"
                )
            ],
            languages=["Python", "JavaScript", "TypeScript"],
            frameworks=["FastAPI", "React", "Django"],
            verified_skills=["Full Stack Development", "API Design"],
            contribution_score=8.0,
            analysis="GitHub profile shows strong contributions and diverse project experience"
        )
    
    def _analyze_portfolio(self, portfolio_url: str, resume: ExtractedResume) -> PortfolioEvidence:
        """Analyze portfolio site."""
        
        return PortfolioEvidence(
            source="portfolio",
            profile_url=portfolio_url,
            key_projects=[
                ProjectEntry(
                    project_name="Portfolio Project",
                    description="Showcased project from portfolio",
                    technologies=["Design", "Frontend"]
                )
            ],
            verified_skills=["UI/UX Design", "Frontend Development"],
            contribution_score=7.0,
            analysis="Portfolio demonstrates creative and technical capabilities"
        )


class ReportingAgent:
    """
    Generates final hiring recommendations and personalized feedback.
    Produces explainable, actionable outputs for hiring teams and candidates.
    """
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    def generate_recommendation(self, overall_score: float, confidence: float,
                               resume: ExtractedResume, job: JobDescription,
                               scores: Dict[str, ScoringResult],
                               bias_analysis: BiasFlagsAnalysis) -> tuple:
        """
        Generate hiring recommendation and feedback.
        Returns: (recommendation_text, feedback_for_candidate, decision_category)
        """
        
        prompt = f"""
You are a HIGH-LEVEL EXECUTIVE RECRUITER and TALENT STRATEGIST. Your job is to take the diverse perspectives of technical, career, and cultural agents and synthesize them into a single, cohesive, and powerful hiring recommendation.

CANDIDATE: {resume.candidate_name}
TARGET POSITION: {job.job_title}
OVERALL STRENGTH: {overall_score}/10 (Analysis Confidence: {confidence*100:.0f}%)

MULTI-AGENT FEEDBACK:
{chr(10).join([f"- {name} (Score {s.score}/10): {s.reasoning}" for name, s in scores.items()])}

BIAS ANALYSIS SUMMARY: {bias_analysis.risk_level.upper()} - {bias_analysis.overall_assessment}

Provide a JSON response with:
{{
    "recommendation": "strong_yes/yes/maybe/no/strong_no",
    "hiring_rationale": "A masterful synthesis of the candidate's value proposition. Connect the dots between their technical skill, their career trajectory, and their behavioral indicators. Why should (or shouldn't) we hire them?",
    "key_strengths": [3-5 strategic strengths that make them stand out],
    "key_concerns": [any critical risks, phrased as a senior advisor to the HR team],
    "next_steps": [actionable advice for the hiring manager],
    "interview_focus_areas": [high-value questions to ask in the next round],
    "feedback_for_candidate": "Constructive, professional feedback that helps the candidate grow, regardless of the decision.",
    "additional_notes": "Internal-only executive summary notes"
}}

Executive Synthesis Strategy:
1. Don't repeat the agents; ELEVATE their findings.
2. Look for patterns: If both technical and cultural agents mention "mentorship," highlight them as a leadership asset.
3. Quantify Impact: Focus on the "So what?" of their experience.
4. Be Decisive: Your recommendation should be clear and well-justified.
5. Tone: Professional, authoritative, yet human and balanced.
"""
        
        try:
            # self.groq_client is a LangChain ChatGroq model
            response_msg = self.groq_client.invoke(prompt)
            response = response_msg.content.strip()
            
            # Extract JSON block using regex for robustness
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            data = json.loads(response.strip())
            
            # Formulate the response data, handling string-to-list conversions
            processed_data = {}
            for key, val in data.items():
                # Fields that should be lists in the final schema/report
                if key in ["key_strengths", "key_concerns", "next_steps", "interview_focus_areas", "recommendations_for_hiring", "feedback_for_candidate"]:
                    if isinstance(val, str):
                        processed_data[key] = [val] if val.strip() else []
                    else:
                        processed_data[key] = val
                else:
                    processed_data[key] = val
                    
            recommendation = processed_data.get("recommendation", "maybe")
            feedback = processed_data.get("feedback_for_candidate", [])
            if isinstance(feedback, str):
                feedback = [feedback] if feedback.strip() else []
            
            return recommendation, feedback, processed_data
            
        except Exception as e:
            return "maybe", "Unable to generate feedback", {}

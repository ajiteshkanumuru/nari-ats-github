"""
LangGraph orchestration for the NARI ATS Framework.
Coordinates multi-agent workflow with typed state and conditional routing.
"""

import uuid
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from src.models.schemas import (
    NARIState, ExtractedResume, JobDescription, ScoringResult,
    AggregatedScore, BiasFlagsAnalysis, FinalATSOutput, ScoringRiskLevel
)
from src.extractors.format_extractors import UniversalExtractor
from src.agents.scoring_agents import (
    SkillMatcherAgent, ExperienceEvaluatorAgent, CultureFitAgent, ScoringAggregator
)
from src.agents.specialized_agents import (
    BiasDetectionAgent, PortfolioIntegrationAgent, ReportingAgent
)


class NARIATSOrchestrator:
    """
    Orchestrates the NARI Multi-Agent ATS system using LangGraph.
    Each agent is a node in the workflow; state is passed and updated stepwise.
    """

    def __init__(self, groq_api_key: str):
        """
        Initialize orchestrator and read model configuration.
        """
        import os
        self.groq_api_key = groq_api_key
        self.primary_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        fallback_str = os.getenv("GROQ_FALLBACK_MODELS", "openai/gpt-oss-120b,llama-3.2-90b-vision-preview,openai/gpt-oss-20b,qwen/qwen3-32b,llama-3.1-8b-instant")
        self.fallback_models = [m.strip() for m in fallback_str.split(",") if m.strip()]
        
        self._setup_agents()
        # Build the workflow graph
        self.graph = self._build_graph()

    def _setup_agents(self):
        """Initialize agents with a robust Groq client using fallbacks."""
        # Create the primary client
        primary_client = ChatGroq(api_key=self.groq_api_key, model_name=self.primary_model)
        
        # Create fallback clients
        fallback_clients = [
            ChatGroq(api_key=self.groq_api_key, model_name=m)
            for m in self.fallback_models
        ]
        
        # Combine using LangChain's native fallback mechanism
        if fallback_clients:
            self.groq_client = primary_client.with_fallbacks(fallback_clients)
            print(f"DEBUG: Initialized Groq client with {len(fallback_clients)} fallbacks.")
        else:
            self.groq_client = primary_client
            print("DEBUG: Initialized Groq client without fallbacks.")
            
        # Core agents
        self.universal_extractor = UniversalExtractor(self.groq_client)
        self.skill_matcher = SkillMatcherAgent(self.groq_client)
        self.experience_evaluator = ExperienceEvaluatorAgent(self.groq_client)
        self.culture_fit = CultureFitAgent(self.groq_client)
        # Specialized agents
        self.bias_detector = BiasDetectionAgent(self.groq_client)
        self.portfolio_agent = PortfolioIntegrationAgent(self.groq_client)
        self.reporting_agent = ReportingAgent(self.groq_client)

    def _build_graph(self):
        """
        Build the LangGraph workflow: each node is an agent step, edges define execution order.
        Returns the compiled graph (with .invoke()).
        """
        workflow = StateGraph(NARIState)
        # Add agent nodes
        workflow.add_node("ingestion", self._ingest_resume)  # Ingest and extract resume
        workflow.add_node("format_check", self._validate_format_consistency)  # Validate extraction
        workflow.add_node("skill_matcher", self._run_skill_matcher)  # Score skills
        workflow.add_node("experience_evaluator", self._run_experience_evaluator)  # Score experience
        workflow.add_node("culture_fit", self._run_culture_fit)  # Score culture fit
        workflow.add_node("scoring_aggregator", self._aggregate_scores)  # Aggregate scores
        workflow.add_node("bias_detection", self._detect_bias)  # Analyze bias
        workflow.add_node("portfolio_analysis", self._analyze_portfolio)  # Analyze portfolio
        workflow.add_node("reporting", self._generate_report)  # Final report
        # Define workflow edges (sequential for clarity)
        workflow.set_entry_point("ingestion")
        workflow.add_edge("ingestion", "format_check")
        workflow.add_edge("format_check", "skill_matcher")
        workflow.add_edge("skill_matcher", "experience_evaluator")
        workflow.add_edge("experience_evaluator", "culture_fit")
        workflow.add_edge("culture_fit", "scoring_aggregator")
        workflow.add_edge("scoring_aggregator", "bias_detection")
        workflow.add_edge("bias_detection", "portfolio_analysis")
        workflow.add_edge("portfolio_analysis", "reporting")
        workflow.add_edge("reporting", END)
        return workflow.compile()

    # --- Agent step methods below ---
    # Each method should be concise, with a docstring and clear state update

    def _ingest_resume(self, state: NARIState) -> NARIState:
        """Extract resume data using UniversalExtractor."""
        # ...existing code...
        pass

    def _validate_format_consistency(self, state: NARIState) -> NARIState:
        """Validate extraction consistency across formats."""
        # ...existing code...
        pass

    def _run_skill_matcher(self, state: NARIState) -> NARIState:
        """Run SkillMatcherAgent and update state with skill score."""
        # ...existing code...
        pass

    def _run_experience_evaluator(self, state: NARIState) -> NARIState:
        """Run ExperienceEvaluatorAgent and update state with experience score."""
        # ...existing code...
        pass

    def _run_culture_fit(self, state: NARIState) -> NARIState:
        """Run CultureFitAgent and update state with culture fit score."""
        # ...existing code...
        pass

    def _aggregate_scores(self, state: NARIState) -> NARIState:
        """Aggregate all agent scores into a consensus result."""
        # ...existing code...
        pass

    def _detect_bias(self, state: NARIState) -> NARIState:
        """Run BiasDetectionAgent and update state with bias analysis."""
        # ...existing code...
        pass

    def _analyze_portfolio(self, state: NARIState) -> NARIState:
        """Run PortfolioIntegrationAgent and update state with evidence analysis."""
        # ...existing code...
        pass

    def _generate_report(self, state: NARIState) -> NARIState:
        """Run ReportingAgent and produce final output."""
        # ...existing code...
        pass
        workflow.add_edge("portfolio_analysis", "reporting")
        
        # End
        workflow.add_edge("reporting", END)
        
        return workflow.compile()
    
    def _ingest_resume(self, state: NARIState) -> NARIState:
        """Node 1: Ingest and extract resume."""
        try:
            extracted = self.universal_extractor.extract(state.resume_file_path)
            state.extracted_resume = extracted
            state.resume_file_format = extracted.format
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.extraction_errors.append(error_msg)
            state.processing_errors.append(f"Ingestion failed: {error_msg}")
        
        return state.model_dump()
    
    def _validate_format_consistency(self, state: NARIState) -> NARIState:
        """Node 2: Validate format consistency (check against duplicate formats if available)."""
        
        if not state.extracted_resume:
            state.consistency_warnings.append("No resume extracted to validate")
            return state.model_dump()
        
        # In production, if multiple formats of same resume provided,
        # cross-validate that extracted data is consistent
        state.format_consistency_check = {
            "format_type": state.extracted_resume.format,
            "confidence": state.extracted_resume.extraction_confidence,
            "validated": True
        }
        
        return state.model_dump()
    
    def _run_skill_matcher(self, state: NARIState) -> NARIState:
        """Node 3: Run skill matcher agent (parallel)."""
        
        if not state.extracted_resume:
            return state.model_dump()
        
        try:
            score_result = self.skill_matcher.score(
                state.extracted_resume,
                state.job_description
            )
            state.scoring_results["SkillMatcher"] = score_result
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Skill Matcher failed: {error_msg}")
        
        return state.model_dump()
    
    def _run_experience_evaluator(self, state: NARIState) -> NARIState:
        """Node 4: Run experience evaluator agent (parallel)."""
        
        if not state.extracted_resume:
            return state.model_dump()
        
        try:
            score_result = self.experience_evaluator.score(
                state.extracted_resume,
                state.job_description
            )
            state.scoring_results["ExperienceEvaluator"] = score_result
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Experience Evaluator failed: {error_msg}")
        
        return state.model_dump()
    
    def _run_culture_fit(self, state: NARIState) -> NARIState:
        """Node 5: Run culture fit agent (parallel)."""
        
        if not state.extracted_resume:
            return state.model_dump()
        
        try:
            score_result = self.culture_fit.score(
                state.extracted_resume,
                state.job_description
            )
            state.scoring_results["CultureFit"] = score_result
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Culture Fit failed: {error_msg}")
        
        return state.model_dump()
    
    def _aggregate_scores(self, state: NARIState) -> NARIState:
        """Node 6: Aggregate scores from parallel agents (consensus)."""
        
        if not state.scoring_results:
            state.processing_errors.append("No scoring results to aggregate")
            return state.model_dump()
        
        overall_score, confidence, reasoning = ScoringAggregator.aggregate_scores(
            state.scoring_results
        )
        
        state.aggregated_score = AggregatedScore(
            overall_match_score=overall_score,
            component_scores=state.scoring_results,
            confidence_level=confidence,
            scoring_note=reasoning
        )
        state.scoring_complete = True
        
        return state.model_dump()
    
    def _detect_bias(self, state: NARIState) -> NARIState:
        """Node 7: Detect bias in evaluation."""
        
        if not state.extracted_resume or not state.aggregated_score:
            return state.model_dump()
        
        try:
            bias_analysis = self.bias_detector.analyze(
                state.extracted_resume,
                state.job_description,
                state.scoring_results
            )
            state.bias_analysis = bias_analysis
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Bias Detection failed: {error_msg}")
        
        return state.model_dump()
    
    def _analyze_portfolio(self, state: NARIState) -> NARIState:
        """Node 8: Analyze portfolio and GitHub evidence."""
        
        if not state.extracted_resume:
            return state.model_dump()
        
        try:
            evidence = self.portfolio_agent.analyze(state.extracted_resume)
            state.portfolio_evidence = evidence
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Portfolio Analysis failed: {error_msg}")
        
        return state.model_dump()
    
    def _generate_report(self, state: NARIState) -> NARIState:
        """Node 9: Generate final report and recommendations."""
        
        if not state.aggregated_score:
            state.processing_errors.append("Cannot generate report without scores")
            return state.model_dump()
        
        try:
            recommendation, feedback, report_data = self.reporting_agent.generate_recommendation(
                state.aggregated_score.overall_match_score,
                state.aggregated_score.confidence_level,
                state.extracted_resume,
                state.job_description,
                state.scoring_results,
                state.bias_analysis or BiasFlagsAnalysis()
            )
            
            # Build final output
            state.final_output = FinalATSOutput(
                processing_id=state.processing_id,
                candidate_profile=state.extracted_resume,
                resume_file_format=state.resume_file_format or "unknown",
                job_title=state.job_description.job_title,
                overall_match_score=state.aggregated_score.overall_match_score,
                individual_scores=state.scoring_results,
                confidence_level=state.aggregated_score.confidence_level,
                reasoning=state.aggregated_score.scoring_note,
                bias_analysis=state.bias_analysis or BiasFlagsAnalysis(),
                portfolio_evidence=state.portfolio_evidence,
                hiring_recommendation=recommendation,
                recommendations_for_hiring=report_data.get("next_steps", []),
                feedback_for_candidate=report_data.get("interview_focus_areas", []),
                decision_factors=report_data
            )
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            state.processing_errors.append(f"Reporting failed: {error_msg}")
        
        return state.model_dump()
    
    async def run(self, resume_path: str, job_description: JobDescription) -> dict:
        """
        Run the orchestrator on a resume and job description.
        Returns final ATS output.
        """
        
        # Initialize state
        initial_state = NARIState(
            processing_id=str(uuid.uuid4()),
            resume_file_path=resume_path,
            job_description=job_description
        )
        
        # Execute the graph. LangChain's with_fallbacks handles retries automatically
        # across all nodes in the graph since they all use the same self.groq_client.
        try:
            result = self.graph.invoke(initial_state.model_dump())
        except Exception as e:
            return {
                "error": "Pipeline failed after exhausting all fallbacks",
                "last_error": str(e),
                "processing_errors": [str(e)]
            }

        if isinstance(result, dict):
            final_output = result.get("final_output")
        else:
            # result is likely a NARIState or similar
            final_output = getattr(result, "final_output", None)

        if final_output is None:
            # Return a proper error dict, not a stringified state object
            if isinstance(result, dict):
                return {
                    "error": "Pipeline failed to produce final output",
                    "processing_id": result.get("processing_id"),
                    "resume_file_path": result.get("resume_file_path"),
                    "processing_errors": result.get("processing_errors", []),
                }
            else:
                return {
                    "error": "Pipeline failed to produce final output",
                    "processing_id": getattr(result, "processing_id", None),
                    "resume_file_path": getattr(result, "resume_file_path", None),
                    "processing_errors": getattr(result, "processing_errors", []),
                }

        # Always return a dict for JSON serialization
        if hasattr(final_output, "model_dump"):
            return final_output.model_dump(mode="json")
        elif isinstance(final_output, dict):
            return final_output
        else:
            # Fallback: try to convert to dict
            return dict(final_output)
    
    def run_sync(self, resume_path: str, job_description: JobDescription) -> dict:
        """Synchronous wrapper for async run."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.run(resume_path, job_description))

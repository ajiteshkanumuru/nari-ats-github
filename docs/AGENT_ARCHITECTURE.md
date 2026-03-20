# System Workflow & Agent Architecture

The NARI system treats a resume not as a simple text file, but as a multi-dimensional evidence set that requires different "experts" to evaluate.

## The Multi-Agent Pipeline
The platform uses **LangGraph** to orchestrate independent AI agents. Below is the full vertical flow of the pipeline:

```mermaid
graph TD
    classDef stage fill:#f9f9f9,stroke:#333,stroke-width:2px;
    
    subgraph STAGE 1: INGESTION
    A["📄 Input Files<br/>(PDF, Word, Images, TXT)"]
    end
    
    subgraph STAGE 2: PARSING
    B["⚙️ Format-Agnostic Extraction<br/>(OCR & Semantic Mapping)"]
    end
    
    subgraph STAGE 3: EXPERT EVALUATION
    C1["🧠 Skill Matcher Agent"]
    C2["📈 Experience Evaluator"]
    C3["🤝 Culture Fit Agent"]
    end
    
    subgraph STAGE 4: QUALITY & FAIRNESS
    D["⚖️ Weighted Consensus<br/>(Confidence Aggregation)"]
    E["🛡️ Bias Audit Agent<br/>(Fairness Basis)"]
    end
    
    subgraph STAGE 5: REPORTING
    F["📝 Final Reports<br/>(JSON, PDF, DOCX)"]
    end
    
    A --> B
    B --> C1 & C2 & C3
    C1 & C2 & C3 --> D
    D --> E
    E --> F
    
    class A,B,C1,C2,C3,D,E,F stage;
```

---

## Who Does What? (The 7 Agents)
The system isolates responsibility across 7 specialized AI agents to ensure depth, explainability, and fairness.

### A. The Extraction Layer
**1. Universal Extractor Agent**: Instead of one generic parser, we use specialized logic for PDF, DOCX, HTML, and Images (OCR). This ensures that even "creative" or scanned resumes are interpreted accurately into a unified schema.

### B. The Scoring Trinity (Parallel Evaluators)
Three independent agents evaluate the candidate simultaneously from different perspectives:
**2. SkillMatcher Agent**: Focuses on the "What." It performs semantic matching between the candidate's skills and the JD requirements. It understands that "React.js" and "React" are the same thing and evaluates the depth and recency of use.
**3. ExperienceEvaluator Agent**: Focuses on the "How Long" and "How Big." It analyzes career trajectory, looking for progression, promotion velocity, and the relevance of past roles to the target position.
**4. CultureFit Agent**: Focuses on the "Soft Skills." It scans achievements and project descriptions for evidence of communication, leadership, cross-functional collaboration, and adaptability.

### C. The Intelligence & Fairness Layer
**5. BiasDetection Agent**: A dedicated fairness auditor. It scans for "proxy discriminators" (like graduation years suggesting age) and flags them. It provides a narrative "Fairness Assessment" to ensure the hiring manager is aware of potential biases before reviewing the score.
**6. PortfolioIntegration Agent**: A validation expert. It attempts to cross-reference resume claims with external links (like GitHub repositories or portfolio URLs) to see if external evidence supports the candidate's claims.

### D. The Synthesis Layer
**7. Reporting Agent (Chief Recruiter)**: This agent synthesizes the findings from all other agents into a single, cohesive recommendation (e.g., STRONG YES, MAYBE). It doesn't just repeat the scores; it "elevates" them into a strategic executive summary for the hiring manager, exactly as a Senior Recruiter would.

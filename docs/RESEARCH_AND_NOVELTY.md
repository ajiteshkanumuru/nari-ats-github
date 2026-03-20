# Research Context & System Novelty

## Why We Built NARI
Our research into existing Applicant Tracking Systems (ATS) platforms (like Greenhouse, Lever, and Workable) revealed several critical gaps in the industry:

- **Black-Box Scoring**: Traditional systems give a "match percentage" without any explanation. Hiring teams are forced to trust a number they don't objectively understand.
- **Keyword Brittleness**: Most systems search for exact keywords. A candidate with "Distributed Systems" might be rejected if the Job Description asks for "Scalable Architecture," even if the concepts are highly related.
- **Hidden Bias**: Existing tools lack proactive auditing for bias. Factors like candidate name, geographic location, or implied age (via graduation year) often unconsciously influence scoring in algorithmic models.
- **Single-Source Limitation**: Most systems only perform raw text parsing of the resume, completely ignoring external evidence like GitHub contributions or project portfolios.

---

## What Makes NARI Unique?
NARI is not merely a wrapper around a Large Language Model; it is a research-first architectural implementation that addresses documented failures in modern ATS technology.

### 1. The "Trinity" Multi-Agent Consensus Pattern
Unlike traditional systems that use a single "black-box" algorithm, NARI employs three independent "Expert Agents" (Skill, Experience, and Culture) that evaluate the candidate concurrently.
- **Weighted Confidence Integration**: Each agent self-reports a confidence score based on the clarity of the evidence. The final result is a **confidence-weighted average**, ensuring that the most "certain" agent has the greatest influence on the recommendation.
- **Conflict Resolution**: The system is designed to detect "Controversial Candidates"—those with high technical skill but low culture scores, or vice versa—flagging them for human review rather than giving a misleading flat average score.

### 2. Inferential Metric Mapping (Soft-Skill Extraction)
One of NARI's biggest innovations is its ability to perform **Inferential Logic**. Instead of just matching keywords like "Leadership," the system maps raw, factual achievements (e.g., *"Employee of the Month"* or *"Led architectural redesign"*) to high-level behavioral metrics including:
- **Reliability & Performance**: Inferred from awards and sustained tenure at previous companies.
- **Leadership Trajectory**: Inferred from mentorship and ownership of complex projects relative to years of experience.
- **Adaptability**: Inferred from transitions between different technology stacks, industries, or rapidly scaling environments.

### 3. Proactive Bias Logic (The "Verification Basis")
Most ATS systems attempt to "ignore" identifying details. NARI takes a proactive **Verification Basis** approach using a dedicated specialized AI Agent:
- It explicitly audits for **Proxy Discriminators** (e.g., graduation years acting as an implicit proxy for age).
- It provides a **Human-Centric Narrative Basis** for its fairness assessment, explaining exactly why it believes the evaluation was merit-based (e.g., *"No indicators that geographic location influenced the score"*).

### 4. Format-Agnostic State Persistence
NARI uses a custom **Unified Schema Architecture**. Whether a resume is a professional PDF, a Word document, or a scanned image (via OCR), it is transformed into a standardized, strongly-typed Pydantic state. This ensures that every candidate is evaluated solely on their objective merits, regardless of their resume's visual formatting.

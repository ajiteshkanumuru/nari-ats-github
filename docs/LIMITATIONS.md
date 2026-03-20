# Limitations of Traditional ATS Systems

Our foundational research identified severe limitations in current Applicant Tracking Systems (such as Greenhouse, Lever, Workable, and legacy parsers) that actively harm both recruiters and highly qualified candidates. These limitations directly motivated the architectural novelty of NARI.

## 1. Black-Box Algorithmic Scoring
Traditional machine learning parsers and keyword-matching systems often spit out a "Match Percentage" (e.g., "73% Match") with zero transparency.
- **The Problem:** Hiring teams are forced to blindly trust a number they don’t understand. Because the evaluation logic is hidden, recruiters cannot verify if a candidate was rejected for a valid reason or an algorithmic error.
- **The NARI Solution:** We implemented the *Reporting Synthesis Agent*, which provides full, human-readable narrative reasoning behind every generated score.

## 2. Keyword Brittleness & Lack of Semantic Depth
Legacy systems rely on hardcoded keyword matching rather than contextual understanding.
- **The Problem:** A candidate who writes they "Designed Distributed Systems for high traffic" might be automatically rejected if the Job Description specifically asks for "Scalable Architecture"—even though the concepts are functionally equivalent.
- **The NARI Solution:** Our *Skill Matcher Agent* relies on deep semantic evaluation via LLMs, allowing it to interpret equivalent technologies and evaluate the depth of skill rather than just binary keyword presence.

## 3. Propagation of Unconscious Bias
Current tools lack proactive auditing mechanisms to stop human or historical biases from influencing the pipeline.
- **The Problem:** Algorithmic models are easily swayed by "proxy discriminators." For example, a graduation year (like 1998) acts as an implicit proxy for age, and candidate names or zip codes often trigger structural systemic bias.
- **The NARI Solution:** We embedded a dedicated *Bias Audit Agent* that establishes a "Fairness Basis," actively scanning for and flagging language or proxies that could lead to discriminatory scoring.

## 4. Single-Dimensional Text Parsing
Traditional parsers look at a resume in a vacuum.
- **The Problem:** They purely parse the localized text of the uploaded PDF, completely ignoring the massive wealth of external evidence a candidate provides, such as GitHub repositories, technical blogs, or live portfolio websites.
- **The NARI Solution:** Our *Portfolio Integration Layer* is designed to cross-reference claims directly against external developer profiles to provide evidence-backed verification.

## 5. Failure to Understand Soft Skills (The "How" vs the "What")
Standard ATS systems only extract hard technical nouns ("Python", "AWS", "Docker").
- **The Problem:** They completely fail to measure critical behavioral metrics. They cannot determine if a candidate demonstrates leadership, cross-functional collaboration, or adaptability based on their career trajectory.
- **The NARI Solution:** We pioneered *Inferential Metric Mapping* via the *Culture Fit and Experience Evaluator Agents*, mapping tactical bullet points to high-level strategic soft skills.

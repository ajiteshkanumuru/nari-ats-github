# NARI Multi-Agent ATS System
## Namaah AI Research & Innovation (NARI)

**A Novel, Multi-Agent Applicant Tracking System with Explainability, Bias Detection, and Evidence-Based Scoring.**

---

## 📖 Complete Documentation Hub

We have broken down our research, architecture, and guides into dedicated documents. Please use these links to explore the specifics of our platform:

- 🏆 **[Official Research Paper (Deliverables)](NARI_RESEARCH_PAPER.md)**: The complete, formal 3-6 page document consolidating the existing ATS survey, NARI's novel approach, the LangGraph design flow, and the results/baseline comparisons required for submission. Start here for grading!
- 🚀 **[Setup & Run Guide](SETUP_AND_RUN_GUIDE.md)**: Absolute step-by-step commands for running the pipeline in your terminal **OR** via our premium React Web Application. Start here to test the code!
- 🧠 **[Research & Novelty](docs/RESEARCH_AND_NOVELTY.md)**: Why we built this, the flaws in existing ATS tools, and our novel approaches (like Inferential Metric Mapping and the Verification Basis).
- 🏗️ **[Agent Architecture](docs/AGENT_ARCHITECTURE.md)**: A complete block diagram of the workflow and an explanation of the 7 specialized AI Agents used in this platform.
- 📚 **[System Terminology](docs/TERMINOLOGY.md)**: What does an "Overall Match Score" or "Confidence Percentage" actually mean? This glossary explains our metrics.
- 🚧 **[Limitations of Current Systems](docs/LIMITATIONS.md)**: A breakdown of the black-box scoring, keyword brittleness, and hidden bias issues in traditional ATS platforms that drove us to build NARI.

---

## 🛠️ Quick Repository Structure

All necessary execution files are located safely in the root directory.

```bash
nari-ats-github/
├── src/
│   ├── agents/          # Specialized AI Agents (Scoring, Bias, Reporting)
│   ├── extractors/      # Multi-format Resume Extractors (OCR, PDF, DOCX)
│   ├── models/          # Type-safe object schemas (Pydantic)
│   └── orchestration.py # LangGraph Workflow Logic
├── frontend/            # React + Vite Graphical User Interface
├── samples/
│   ├── input/           # Place your Job Descriptions and Resumes here
│   └── output/          # Generated JSON, PDF, and DOCX reports
├── docs/                # Architectural deeper dives and research documents
├── SETUP_AND_RUN_GUIDE.md # 🚀 START HERE TO RUN THE APP
├── requirements.txt     # Python backend dependencies
└── main.py              # CLI Execution Entry Point
```

---

## नारी / ನಾರಿ / நாரி / நாரி / നാരി
**Built with a research-first focus and premium multi-agent collaboration for Namaah AI Research & Innovation (NARI).**

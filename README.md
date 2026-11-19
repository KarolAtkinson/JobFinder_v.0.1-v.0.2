# JobFinder v0.1 & v0.2 🎯

> **Job Discovery, CV Tailoring, and Application Automation**  
> Two parallel implementations exploring autonomous job hunting and CV optimization strategies

---

## 📋 Overview

This repository contains **two experimental versions** of an intelligent job application platform. Both approaches tackle the same core problem: automating the tedious job search and application process. Each version represents a different architectural philosophy.

### The Core Problem
Applying for tech jobs is repetitive and time-consuming:
- ❌ Manual job searching and filtering
- ❌ Generic, non-tailored applications get filtered by ATS
- ❌ Manual CV tailoring takes hours per application
- ⏱️ Spray-and-pray approach wastes time

### The Solution (Two Approaches)
Both versions aim to:
1. **Search for jobs** across multiple sources
2. **Filter opportunities** based on your resume/CV
3. **Tailor your CV/resume** for each specific role
4. **Submit applications** automatically with personalized outreach

---

## 🗂️ Project Structure

```
JobFinder_v.0.1-v.0.2/
├── JF_os_01/              # Version 1: ApplyAgent (Full-Stack with Server)
│   ├── README.md          # Comprehensive setup & documentation
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── [Backend + Frontend Code]
│
├── JSRE_01/               # Version 2: CV Optimiser (Local-First Desktop)
│   ├── README.md          # Feature & usage documentation
│   ├── requirements.txt    # Python dependencies
│   ├── desktop_app.py      # Standalone desktop application
│   └── run_cv_optimiser.bat
│
└── README.md              # This file - project overview & guidance
```

---

## 🔍 Version Comparison

| Feature | **JF_os_01 (ApplyAgent)** | **JSRE_01 (CV Optimiser)** |
|---------|---------------------------|---------------------------|
| **Architecture** | Full-stack web app | Local desktop app |
| **Backend** | FastAPI server | Standalone Python |
| **Frontend** | React 19 + TanStack | Desktop UI (Tkinter) |
| **Job Discovery** | DuckDuckGo, Google CSE, Bing | Manual job posting input |
| **CV Tailoring** | RAG + LLM-powered | Rule-based + optional Ollama |
| **Application Submission** | Automated via Resend API | Manual export to DOCX |
| **Email Tracking** | Webhooks + IMAP monitoring | N/A |
| **Database** | MongoDB + ChromaDB | Local JSON + app-data directory |
| **LLM Support** | Multi-provider fallback (Gemini → Groq → OpenRouter → Ollama) | Local Ollama only |
| **Privacy** | Requires API keys + server | Fully local, offline-capable |
| **Status** | Experimental (requires server) | Experimental (desktop standalone) |

---

## 🚀 Quick Start

### JF_os_01 - ApplyAgent (Full-Stack)
⚠️ **Note**: This version requires a backend server to function.

```bash
cd JF_os_01
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
# Configure .env with API keys
python main.py  # or run the FastAPI server
```

**See [JF_os_01/README.md](./JF_os_01/README.md) for detailed setup.**

---

### JSRE_01 - CV Optimiser (Local Desktop)
✅ **Local-first, no server required!**

```bash
cd JSRE_01
pip install -r requirements.txt
python desktop_app.py
```

Or simply double-click `run_cv_optimiser.bat` on Windows.

**See [JSRE_01/README.md](./JSRE_01/README.md) for detailed usage.**

---

## 📚 Documentation

Each version has its own detailed documentation:

- **[JF_os_01/README.md](./JF_os_01/README.md)** — ApplyAgent architecture, API reference, setup guide, multi-agent breakdown
- **[JSRE_01/README.md](./JSRE_01/README.md)** — CV Optimiser features, local AI setup, testing, usage guide

Additional resources in JF_os_01:
- `theory.md` — Conceptual overview and design decisions
- `context.md` — Project context and requirements
- `setup.md` — Detailed environment setup
- `UserJourney.md` — End-to-end user workflows

---

## ⚙️ System Requirements

### JF_os_01 (ApplyAgent)
- **Python 3.11+**
- **Node.js 18+** (for React frontend)
- **MongoDB** (or Atlas cloud instance)
- **API keys**: Google, Groq, OpenRouter, Resend, etc.
- **Docker** (optional, for containerized deployment)

### JSRE_01 (CV Optimiser)
- **Python 3.11+**
- **Ollama** (optional, for local AI drafting)
- **~5GB disk space** (for model weights, if using Ollama)

---

## 🎓 Learning Resources

Both versions demonstrate:
- **LLM Integration**: Multi-provider LLM chains, fallback strategies, prompt engineering
- **Resume/CV Parsing**: PDF extraction, semantic analysis, embeddings (ChromaDB/RAG)
- **Job Discovery**: Web scraping, search API integration, anti-bot resilience
- **Email Automation**: SMTP, HTML templating, webhook handling
- **Desktop Applications**: Tkinter UI, local data persistence
- **Full-Stack Development**: FastAPI, React, real-time updates

---

## ⚠️ Project Status

**Status**: Experimental / Abandoned (as of project completion)

**Reason**: The full-stack version (JF_os_01) requires backend infrastructure to function, which became impractical for standalone deployment. The local-first approach (JSRE_01) is more practical for personal use.

**Lessons Learned**:
- Server-based job applications require complex infrastructure and maintenance
- Local-first desktop apps are more practical for personal automation
- Privacy-first design (keeping CV data local) is preferred by most users

---

## 📝 License & Attribution

Both versions were developed as experimental projects to explore automation strategies for job applications.

---

## 🤝 Contributing

This is an archived experimental project. It is provided as-is for educational reference.

---

## ❓ FAQ

**Q: Can I use these to submit applications automatically?**  
A: JF_os_01 (ApplyAgent) can automate submissions via email + Resend API. JSRE_01 exports tailored CVs for manual submission.

**Q: Which version should I use?**  
A: Use **JSRE_01 (CV Optimiser)** if you prefer a local, standalone desktop app. Use **JF_os_01** if you want to explore full-stack architecture and automation.

**Q: Do I need to run Ollama?**  
A: Optional. JSRE_01 can work without Ollama (rule-based tailoring). JF_os_01 uses cloud LLMs by default and falls back to Ollama if configured.

**Q: Is my CV data sent to the cloud?**  
A: **JF_os_01**: Yes, to configured LLM providers. **JSRE_01**: No, everything stays local unless you explicitly enable Ollama (which also runs locally).

---

## 📞 Support

For detailed information on each version, see their respective README files.

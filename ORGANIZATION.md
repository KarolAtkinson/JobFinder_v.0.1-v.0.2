# Project Organization Overview 📁

A comprehensive guide to the JobFinder repository structure and how the two versions are organized.

---

## 📂 Repository Structure

```
JobFinder_v.0.1-v.0.2/                    Root project folder
│
├── 📄 README.md                          Main project overview (this contains architecture overview & quick start)
├── 📄 VERSIONS_GUIDE.md                  Comparison & decision guide for choosing between versions
├── 📄 ORGANIZATION.md                    This file - detailed structure explanation
│
├── 📂 JF_os_01/                          Version 1: ApplyAgent (Full-Stack Web Application)
│   ├── 📄 README.md                      ⭐ START HERE - Full setup & architecture guide
│   ├── 📄 theory.md                      Conceptual framework & design philosophy
│   ├── 📄 context.md                     Project requirements & context
│   ├── 📄 setup.md                       Detailed environment & dependency setup
│   ├── 📄 UserJourney.md                 End-to-end user workflows & interactions
│   │
│   ├── 📄 requirements.txt                Python dependencies (FastAPI, ChromaDB, LangChain, etc.)
│   ├── 📄 .env.example                   Template for required environment variables
│   ├── 📄 .env                           Actual environment config (DO NOT COMMIT)
│   ├── 📄 .gitignore                     Git ignore patterns
│   │
│   ├── 🐍 main.py                       Entry point for FastAPI backend
│   ├── 🐍 [Backend source code]          FastAPI routes, LLM orchestration, database models
│   ├── 🌐 [Frontend source code]         React 19 + TanStack Start components
│   │
│   ├── 🔧 run-applyagent.ps1            PowerShell startup script
│   ├── 🔧 start.bat                      Windows batch startup script
│   │
│   ├── 📄 test.pdf                       Sample resume for testing
│   │
│   └── 📂 .venv/                         Python virtual environment (auto-generated)
│
├── 📂 JSRE_01/                           Version 2: CV Optimiser (Local Desktop App)
│   ├── 📄 README.md                      ⭐ START HERE - Features, usage & local AI setup
│   │
│   ├── 📄 requirements.txt                Python dependencies (Tkinter, Ollama, etc.)
│   ├── 📄 .gitignore                     Git ignore patterns
│   │
│   ├── 🐍 desktop_app.py                 Main desktop application entry point
│   ├── 🐍 [Application source code]      Tkinter UI, CV processing, tailoring logic
│   │
│   ├── 🔧 run_cv_optimiser.bat           Windows batch launcher
│   │
│   └── 📂 .venv/                         Python virtual environment (auto-generated)
│
└── 📂 .git/                              Git repository metadata

```

---

## 📋 Documentation Map

### For Project Overview
- **[README.md](./README.md)** ← Start here for overview
- **[VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)** ← How to choose between versions

### For Version 1: ApplyAgent (JF_os_01)
| Document | Purpose | Audience |
|----------|---------|----------|
| [JF_os_01/README.md](./JF_os_01/README.md) | Complete setup & architecture | Everyone |
| [JF_os_01/theory.md](./JF_os_01/theory.md) | Design philosophy & concepts | Developers |
| [JF_os_01/context.md](./JF_os_01/context.md) | Requirements & constraints | Project owners |
| [JF_os_01/setup.md](./JF_os_01/setup.md) | Environment & dependency setup | DevOps/Setup |
| [JF_os_01/UserJourney.md](./JF_os_01/UserJourney.md) | End-to-end workflows | Product/UX |

### For Version 2: CV Optimiser (JSRE_01)
| Document | Purpose | Audience |
|----------|---------|----------|
| [JSRE_01/README.md](./JSRE_01/README.md) | Features, usage & local AI | Everyone |

---

## 🎯 Directory Purpose Breakdown

### JF_os_01 - ApplyAgent
**Type**: Full-stack web application  
**Purpose**: Autonomous job discovery, CV tailoring, and application submission  

**Key Components**:
- **Backend**: FastAPI server for job discovery, CV processing, and email sending
- **Frontend**: React 19 + TanStack Start for user interface
- **Database**: MongoDB for storing jobs, applications, and user data
- **Vector DB**: ChromaDB for semantic search and RAG
- **LLM Orchestration**: Multi-provider LLM chain (Gemini → Groq → OpenRouter → Ollama)
- **Email Service**: Resend API for sending applications with tracking
- **Webhooks**: Svix for email open/click tracking and reply detection

**Documentation Hierarchy**:
1. Start: `README.md` - Setup instructions and overview
2. Understand: `theory.md` - Design and conceptual framework
3. Configure: `setup.md` - Detailed environment setup
4. Learn: `UserJourney.md` - See it in action
5. Reference: `context.md` - Requirements details

### JSRE_01 - CV Optimiser
**Type**: Local-first desktop application  
**Purpose**: Local CV tailoring with optional AI assistance  

**Key Components**:
- **Desktop UI**: Tkinter-based interface
- **Local Data**: JSON-based CV and blueprint storage
- **CV Processing**: PDF import, text extraction, field parsing
- **Tailoring**: Rule-based matching + optional Ollama AI
- **Export**: DOCX document generation
- **Local Model**: Optional Ollama integration for Qwen3 AI

**Documentation**:
1. Start: `README.md` - Features, setup, and usage

---

## 🚀 Quick Navigation

### "I want to get started quickly"
→ Read [README.md](./README.md) → Choose version using [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md) → Go to version folder and read its README.md

### "I want to understand the architecture"
→ Read [JF_os_01/theory.md](./JF_os_01/theory.md) → Browse [JF_os_01/README.md](./JF_os_01/README.md) → Look at code structure

### "I want to understand workflows"
→ Read [JF_os_01/UserJourney.md](./JF_os_01/UserJourney.md) → Review [JF_os_01/README.md](./JF_os_01/README.md) API section

### "I want to set up locally"
→ [JF_os_01/setup.md](./JF_os_01/setup.md) (for ApplyAgent) OR [JSRE_01/README.md](./JSRE_01/README.md) (for CV Optimiser)

### "I want to understand requirements"
→ Read [JF_os_01/context.md](./JF_os_01/context.md)

---

## 📊 Version Feature Comparison

### JF_os_01 (ApplyAgent)
- ✅ Automated job discovery
- ✅ Multi-provider LLM support
- ✅ Email automation
- ✅ Full-stack architecture learning
- ✅ Complex system design
- ❌ Requires server
- ❌ Requires multiple API keys

### JSRE_01 (CV Optimiser)
- ✅ Local-first, no server needed
- ✅ Privacy-focused
- ✅ Standalone desktop app
- ✅ Optional local AI
- ✅ Simple setup
- ❌ Manual job input
- ❌ No auto-submission

---

## 🔄 How They Relate

Both versions solve the same problem but with different approaches:

```
Problem: Tedious job application process
         ↓
        / \
       /   \
      ↙     ↘
  
Version 1          Version 2
(JF_os_01)        (JSRE_01)
  
Full-Stack         Desktop App
Server-based       Local-first
Automated          Manual
Cloud LLMs         Local Ollama
Complex            Simple
Production         Personal
  ↓                 ↓
Both teach         Both solve
AI patterns        the same problem
```

---

## 💾 Configuration Files

### .env Files
- **JF_os_01/.env.example** → Template for required API keys
- **JF_os_01/.env** → Actual configuration (Git ignored, never commit)

### .gitignore Files
Both versions have `.gitignore` to exclude:
- Virtual environments (`.venv/`)
- Environment files (`.env`)
- Cache files
- Dependencies (node_modules, etc.)

### requirements.txt
- **JF_os_01/requirements.txt** → Backend Python dependencies
- **JSRE_01/requirements.txt** → Desktop app dependencies

---

## 🛠️ Common Tasks

### Setup Version 1 (ApplyAgent)
```bash
cd JF_os_01
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

### Setup Version 2 (CV Optimiser)
```bash
cd JSRE_01
pip install -r requirements.txt
python desktop_app.py
```

### Run Tests (JSRE_01)
```bash
cd JSRE_01
pip install -r requirements.txt
python -m pytest -q
```

---

## 📚 Learning Path

### Beginner
1. Read main [README.md](./README.md)
2. Read [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)
3. Choose a version
4. Follow the Quick Start

### Intermediate
1. Read version-specific README.md
2. Review theory/context docs (for ApplyAgent)
3. Examine code structure
4. Run tests or deploy locally

### Advanced
1. Study [JF_os_01/theory.md](./JF_os_01/theory.md)
2. Review [JF_os_01/UserJourney.md](./JF_os_01/UserJourney.md)
3. Examine architecture diagrams
4. Modify and extend the code

---

## ✨ Key Takeaways

| Aspect | ApplyAgent (JF_os_01) | CV Optimiser (JSRE_01) |
|--------|----------------------|------------------------|
| **Main Doc** | README.md | README.md |
| **Learning Docs** | theory.md, context.md, setup.md, UserJourney.md | README.md |
| **Complexity** | High | Low |
| **Setup Time** | 30+ mins | 5 mins |
| **Learning Value** | Full-stack AI | Desktop app development |
| **Best For** | Understanding AI architecture | Personal productivity |

---

## 🗺️ Navigation Tips

1. **For first-time visitors**: Start with [README.md](./README.md)
2. **To choose a version**: Use [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)
3. **For detailed setup**: Go to version folder and read its README.md
4. **For architecture deep-dive**: Read JF_os_01's theory.md and context.md
5. **For quick start**: Use Quick Start section in main README.md

---

## 📞 Still Lost?

Each version has its own README - that's your best starting point for that version!

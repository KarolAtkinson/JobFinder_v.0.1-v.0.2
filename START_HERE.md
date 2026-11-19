# 👋 START HERE - JobFinder v0.1 & v0.2

Welcome to **JobFinder**, a repository containing two parallel implementations of an intelligent job application automation platform.

---

## 🎯 What Is This Project?

This project contains **two experimental versions** of an automated job application system:

1. **JSRE_01** - Local desktop app for CV tailoring ✅ Recommended for most users
2. **JF_os_01** - Full-stack web server for complete automation (learning project)

Both aim to solve: *"How can we automate the tedious job search and application process?"*

---

## 🗺️ Documentation Map

### 🚀 Just Want to Get Started? (5 minutes)
→ Read: **[QUICKSTART.md](./QUICKSTART.md)** ← Copy/paste commands and go

### 📚 Want to Understand Your Options?
→ Read: **[VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)** ← Comparison and decision matrix

### 📁 Want to Understand the Structure?
→ Read: **[ORGANIZATION.md](./ORGANIZATION.md)** ← Full directory breakdown and navigation

### 🔍 Want Complete Overview?
→ Read: **[README.md](./README.md)** ← Comprehensive project overview

### 📖 Version-Specific Docs
- **[JF_os_01/README.md](./JF_os_01/README.md)** - Full-stack version setup
- **[JSRE_01/README.md](./JSRE_01/README.md)** - Desktop version setup

---

## ⚡ Quick Decision: Which Version for You?

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  Want a simple standalone desktop app?                        ║
║  → Use JSRE_01 ✅ (Read: JSRE_01/README.md)                   ║
║                                                                ║
║  Want to learn full-stack AI architecture?                    ║
║  → Use JF_os_01 (Read: JF_os_01/README.md)                    ║
║                                                                ║
║  Not sure? → Read VERSIONS_GUIDE.md                           ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🚀 Quick Start (60 seconds)

### Desktop App (JSRE_01) - Local & Offline
```bash
cd JSRE_01
pip install -r requirements.txt
python desktop_app.py
```

### Web App (JF_os_01) - Full-Stack & Automated
```bash
cd JF_os_01
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Add your API keys here
python main.py
```

---

## 📊 Version Comparison at a Glance

| Feature | JSRE_01 | JF_os_01 |
|---------|---------|----------|
| **Type** | Desktop App | Web Server |
| **Privacy** | ✅ Fully Local | ⚠️ Uses Cloud LLMs |
| **Auto Job Search** | ❌ Manual | ✅ Automatic |
| **Difficulty** | Easy | Hard |
| **Setup Time** | 5 min | 30+ min |
| **Best For** | Daily Use | Learning |
| **Status** | Usable | Experimental |

---

## 📚 Documentation Guide

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[QUICKSTART.md](./QUICKSTART.md)** | Copy/paste commands to get started | 2 min |
| **[VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)** | Detailed comparison and decision help | 5 min |
| **[ORGANIZATION.md](./ORGANIZATION.md)** | Understand folder structure | 5 min |
| **[README.md](./README.md)** | Complete project overview | 10 min |
| **[JF_os_01/README.md](./JF_os_01/README.md)** | Full-stack version details | 20 min |
| **[JF_os_01/theory.md](./JF_os_01/theory.md)** | Architecture & design philosophy | 15 min |
| **[JF_os_01/setup.md](./JF_os_01/setup.md)** | Detailed environment setup | 10 min |
| **[JF_os_01/UserJourney.md](./JF_os_01/UserJourney.md)** | End-to-end workflows | 10 min |
| **[JSRE_01/README.md](./JSRE_01/README.md)** | Desktop version details | 10 min |

---

## 💡 What You'll Learn

### From JSRE_01 (Desktop App)
- Building standalone desktop applications with Tkinter
- Local-first data architecture
- PDF parsing and text processing
- Rule-based text algorithms
- Optional Ollama LLM integration

### From JF_os_01 (Web App)
- FastAPI backend patterns
- React 19 + TypeScript frontend
- LLM orchestration and fallback strategies
- Retrieval-Augmented Generation (RAG)
- Email API and webhook integration
- Multi-stage data processing pipelines

---

## 🎓 Recommended Learning Path

### For Beginners (New to AI/Python)
1. Start with **[QUICKSTART.md](./QUICKSTART.md)**
2. Try **JSRE_01** (simpler, works offline)
3. Read **[JSRE_01/README.md](./JSRE_01/README.md)**
4. Explore the code

### For Intermediate (Python experience)
1. Read **[VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md)**
2. Choose based on learning goals
3. Read chosen version's README
4. Follow setup instructions
5. Study the code and architecture

### For Advanced (Backend/AI experience)
1. Read **[JF_os_01/theory.md](./JF_os_01/theory.md)**
2. Study **[JF_os_01/README.md](./JF_os_01/README.md)**
3. Review **[JF_os_01/UserJourney.md](./JF_os_01/UserJourney.md)**
4. Examine the source code
5. Extend or modify as needed

---

## ✨ Key Features

### JSRE_01 (CV Optimiser)
- ✅ Local-first, no server needed
- ✅ 100% private - CV stays on your machine
- ✅ Offline capable
- ✅ Optional Ollama for local AI
- ✅ Fast setup (5 minutes)
- ✅ Works great for personal use

### JF_os_01 (ApplyAgent)
- ✅ Automated job discovery
- ✅ Multi-provider LLM support
- ✅ Email automation
- ✅ Full-stack architecture
- ✅ Learning-focused design
- ⚠️ Requires backend infrastructure

---

## 🔥 Quick Links

**Getting Started:**
- 🚀 [Quick Start Guide](./QUICKSTART.md)
- 🎯 [Version Selection](./VERSIONS_GUIDE.md)
- 📁 [Project Organization](./ORGANIZATION.md)

**Version 1 (Full-Stack):**
- 📖 [ApplyAgent README](./JF_os_01/README.md)
- 🏗️ [Architecture & Theory](./JF_os_01/theory.md)
- 📋 [Setup Instructions](./JF_os_01/setup.md)
- 👥 [User Workflows](./JF_os_01/UserJourney.md)
- 📝 [Requirements & Context](./JF_os_01/context.md)

**Version 2 (Desktop):**
- 📖 [CV Optimiser README](./JSRE_01/README.md)

---

## ❓ Common Questions

**Q: Which version should I use?**  
A: Use **JSRE_01** unless you specifically want to learn full-stack architecture. See [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md).

**Q: Do I need to run a server?**  
A: Only for JF_os_01. JSRE_01 is completely standalone and local.

**Q: Is my CV data private?**  
A: **JSRE_01** keeps everything local. **JF_os_01** sends data to configured LLM providers.

**Q: What if I get stuck?**  
A: Read the version-specific README.md file, check the troubleshooting section, or review the detailed guides.

**Q: Can I use these for real job applications?**  
A: JSRE_01 is usable for personal CV tailoring. JF_os_01 is experimental and learning-focused.

---

## 🛠️ System Requirements

### Minimum (for JSRE_01)
- Python 3.11+
- ~100MB disk space
- Tkinter (usually pre-installed)

### Recommended (for JF_os_01)
- Python 3.11+
- Node.js 18+
- 2GB+ disk space
- MongoDB or MongoDB Atlas account
- API keys from various LLM providers

---

## 🎬 Next Steps

1. **Pick your version** using the comparison table above
2. **Read [QUICKSTART.md](./QUICKSTART.md)** for setup commands
3. **Go to the version folder** (JF_os_01 or JSRE_01)
4. **Follow the README.md** in that folder
5. **Explore the code** to learn more

---

## 📞 Still Need Help?

| I want to... | Go to... |
|-------------|----------|
| Get started immediately | [QUICKSTART.md](./QUICKSTART.md) |
| Choose between versions | [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md) |
| Understand structure | [ORGANIZATION.md](./ORGANIZATION.md) |
| Learn about ApplyAgent | [JF_os_01/README.md](./JF_os_01/README.md) |
| Learn about CV Optimiser | [JSRE_01/README.md](./JSRE_01/README.md) |
| Deep dive into architecture | [JF_os_01/theory.md](./JF_os_01/theory.md) |

---

## 🎉 You're All Set!

Pick a version, follow [QUICKSTART.md](./QUICKSTART.md), and start exploring! 🚀

**Ready? Go to [QUICKSTART.md](./QUICKSTART.md) →**

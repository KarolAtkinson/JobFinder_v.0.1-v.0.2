# Quick Start Guide 🚀

Get started in 5 minutes with the right version for you.

---

## 🎯 Choose Your Version

### Option 1: Desktop App (Recommended for most users)
📦 **JSRE_01 - CV Optimiser** (Local, Offline, Private)

```bash
cd JSRE_01
pip install -r requirements.txt
python desktop_app.py
```

**What you get**:
- 🖥️ Standalone desktop application
- 🔒 100% local data - no servers, no cloud
- 🤖 Optional local AI with Ollama
- 📊 Rule-based CV tailoring
- ⚡ Works offline

**Setup time**: ~5 minutes

---

### Option 2: Full-Stack Web App (For learning)
🌐 **JF_os_01 - ApplyAgent** (Server-based, Automated, Full-Stack)

```bash
cd JF_os_01
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

**What you get**:
- 🔍 Automated job discovery
- 🤖 Multi-provider LLM support
- 📧 Email automation with tracking
- 🌐 Web UI with React
- 📚 Full-stack architecture learning

**Setup time**: ~30 minutes  
**Requirements**: 
- Python 3.11+
- Node.js 18+
- API keys (Google, Groq, Resend, etc.)
- MongoDB database

---

## 📚 Detailed Guides

| Want to... | Read this |
|-----------|-----------|
| Understand both versions | [VERSIONS_GUIDE.md](./VERSIONS_GUIDE.md) |
| Explore repository structure | [ORGANIZATION.md](./ORGANIZATION.md) |
| Learn ApplyAgent architecture | [JF_os_01/README.md](./JF_os_01/README.md) + [JF_os_01/theory.md](./JF_os_01/theory.md) |
| Use CV Optimiser | [JSRE_01/README.md](./JSRE_01/README.md) |
| Understand all features | [README.md](./README.md) |

---

## ⚡ 2-Minute Summary

**JobFinder** = Two experimental job application automation tools

| | JSRE_01 | JF_os_01 |
|---|---------|---------|
| **Type** | Desktop App | Web Server |
| **Privacy** | ✅ Local | ⚠️ Cloud LLMs |
| **Auto Discovery** | ❌ Manual | ✅ Automatic |
| **Difficulty** | ⭐ Easy | ⭐⭐⭐ Hard |
| **Setup** | 5 mins | 30 mins |
| **For** | Daily use | Learning |

---

## 🎓 What You'll Learn

### From JSRE_01 (Desktop App)
- Building Tkinter desktop applications
- Local data persistence with JSON
- PDF parsing and text extraction
- Text-based CV tailoring algorithms
- Optional Ollama integration

### From JF_os_01 (Web App)
- FastAPI backend architecture
- React 19 + TypeScript frontend
- LLM orchestration patterns
- RAG (Retrieval-Augmented Generation)
- Email API integration
- Webhook handling
- Multi-provider LLM fallback chains

---

## 🆘 Troubleshooting

### "I don't know which version to use"
→ Run this in your head:
- Do I want a desktop app? → Use JSRE_01
- Do I want to learn architecture? → Use JF_os_01
- Do I want something that just works? → Use JSRE_01

### "I'm getting dependency errors"
→ Make sure you:
1. Created a virtual environment
2. Activated it
3. Ran `pip install -r requirements.txt`
4. Used Python 3.11+

### "The desktop app won't start"
→ Try:
```bash
# Make sure tkinter is installed
# On Linux: sudo apt-get install python3-tk
# Then: pip install -r requirements.txt
python desktop_app.py
```

### "I can't set up the web app"
→ Check [JF_os_01/setup.md](./JF_os_01/setup.md) for detailed troubleshooting

---

## 📋 Checklist Before Starting

### For JSRE_01
- ✅ Python 3.11+ installed
- ✅ Tkinter available (Windows/macOS included, Linux needs: `sudo apt-get install python3-tk`)
- ✅ ~100MB free disk space

### For JF_os_01
- ✅ Python 3.11+ installed
- ✅ Node.js 18+ installed
- ✅ 2GB+ free disk space
- ✅ MongoDB account or local instance
- ✅ API keys ready (Groq, Google, OpenRouter, Resend)

---

## 🎬 Next Steps

1. **Choose a version** (use the matrix above)
2. **Copy the Quick Start command** from above
3. **Run it in your terminal**
4. **Read the version's README.md** when you need help
5. **Explore the code** to learn more

---

## 💡 Pro Tips

- **Start small**: Try JSRE_01 first (simpler)
- **Learn architecture**: Then explore JF_os_01
- **Read the docs**: Each version has detailed README.md files
- **Check requirements.txt**: Shows all dependencies
- **Use virtual environments**: Keeps your Python clean

---

**Ready? Go to [JSRE_01/](./JSRE_01/) or [JF_os_01/](./JF_os_01/) and start coding! 🚀**

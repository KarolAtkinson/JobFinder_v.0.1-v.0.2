# Version Selection Guide 🎯

Confused about which version to use? This guide will help you choose.

---

## 🏃 **Quick Decision Tree**

```
Do you want a standalone desktop app that works offline?
  ├─ YES → Use JSRE_01 (CV Optimiser) ✅
  └─ NO  → Continue...

Do you want to explore full-stack architecture?
  ├─ YES → Use JF_os_01 (ApplyAgent) ✅
  └─ NO  → Go back to JSRE_01

Do you have API keys and can run a backend server?
  ├─ YES → Use JF_os_01 (ApplyAgent) ✅
  └─ NO  → Use JSRE_01 (CV Optimiser) ✅
```

---

## 📌 Choose **JSRE_01** (CV Optimiser) If You Want:

✅ A **standalone desktop application**  
✅ **Fully local** data (no cloud servers needed)  
✅ **Privacy-first**: CV data stays on your machine  
✅ Simple, **rule-based CV tailoring**  
✅ Optional **local AI** (Ollama) for drafting  
✅ **Quick setup** (~5 minutes)  
✅ Works **offline** completely  
✅ Manual, **verified application control**  

### Quick Start (JSRE_01)
```bash
cd JSRE_01
pip install -r requirements.txt
python desktop_app.py
```

📖 **Full guide**: [JSRE_01/README.md](./JSRE_01/README.md)

---

## 📌 Choose **JF_os_01** (ApplyAgent) If You Want:

✅ **Fully automated** job discovery  
✅ **Multi-source job searching** (DuckDuckGo, Google CSE, Bing)  
✅ **Advanced LLM tailoring** via RAG  
✅ **Automated email submission** with tracking  
✅ **Reply detection** via IMAP monitoring  
✅ **Full-stack web app** with React frontend  
✅ **Cloud LLM integration** (Gemini, Groq, OpenRouter)  
✅ **Webhook email tracking** (Resend API)  
✅ Explore **AI orchestration patterns**  

### Prerequisites (JF_os_01)
- ⚠️ **Backend server** (required)
- 🔑 **API keys** for LLMs and email service
- 🗄️ **MongoDB** database
- 📚 **Learning goal**: Full-stack AI architecture

📖 **Full guide**: [JF_os_01/README.md](./JF_os_01/README.md)

---

## 🔄 Comparison Matrix

| Feature | JSRE_01 | JF_os_01 |
|---------|---------|----------|
| **Local Desktop App** | ✅ | ❌ |
| **Standalone (no server)** | ✅ | ❌ |
| **Offline capable** | ✅ | ❌ |
| **Privacy (data stays local)** | ✅ | ⚠️ (needs LLM keys) |
| **Auto job discovery** | ❌ | ✅ |
| **Email tracking** | ❌ | ✅ |
| **Web UI** | ❌ | ✅ |
| **Learning complexity** | ⭐ Low | ⭐⭐⭐ High |
| **Setup time** | 5 mins | 30+ mins |
| **Learning value** | AI drafting | Full-stack AI |

---

## 🎓 Learning Path

### For Beginners
Start with **JSRE_01**:
1. Understand local data persistence (JSON)
2. Learn about rule-based text processing
3. Experiment with optional Ollama integration
4. See how to build a complete desktop application

### For Intermediate Developers
Explore **JF_os_01**:
1. FastAPI backend architecture
2. React 19 + TanStack frontend patterns
3. LLM orchestration and fallback strategies
4. Email automation and webhook handling
5. Multi-stage RAG pipeline

---

## 💡 Real-World Usage

### Scenario 1: "I just want to tailor my CV faster"
→ **Use JSRE_01**  
- Import your CV
- Get rule-based or AI-assisted tailoring
- Export tailored DOCX
- Apply manually

### Scenario 2: "I want to automate everything"
→ **Use JF_os_01**  
- Set up all API keys
- Configure email tracking
- Let it discover, tailor, and submit automatically
- Monitor applications via dashboard

### Scenario 3: "I'm learning AI and want production patterns"
→ **Use JF_os_01**  
- Study multi-provider LLM fallback
- Learn RAG with ChromaDB + LangChain
- Understand async FastAPI patterns
- See real webhook/email integration

---

## ⚠️ Important Notes

### JSRE_01 (CV Optimiser)
- Output is **hardcoded to Polish** currently (easy to change)
- Uses **Qwen3 4B model** for local AI
- **No automatic job discovery** (you provide job postings)
- Fully **rule-based** without AI selected
- **~5GB** disk space for model weights

### JF_os_01 (ApplyAgent)
- **Project abandoned** - requires backend to function
- Multiple **API keys** required (Gemini, Groq, OpenRouter, Resend, etc.)
- **MongoDB** database required
- Complex **infrastructure setup**
- Good for **learning, not production**

---

## 🚀 Next Steps

1. **Decide**: Which version fits your needs?
2. **Navigate**: Go to the chosen version's directory
3. **Read**: Read its README.md thoroughly
4. **Setup**: Follow the setup instructions
5. **Explore**: Check the documentation files
6. **Learn**: Examine the code and understand the patterns

---

## 📞 Questions?

- **For JSRE_01 questions**: See [JSRE_01/README.md](./JSRE_01/README.md)
- **For JF_os_01 questions**: See [JF_os_01/README.md](./JF_os_01/README.md)
- **General questions**: Check the main [README.md](./README.md)

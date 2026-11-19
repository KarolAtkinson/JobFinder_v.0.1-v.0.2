# CV Optimiser

A local-first application for tailoring CVs to individual job applications while keeping a verified career blueprint as the source of truth.

## Current features

The application provides typed Python data models, validated JSON load/save functions, job-requirement extraction, an evidence-matching report, and evidence-grounded DOCX drafts.

Completed, text-based CV PDFs can be imported from the desktop window. The app extracts selectable PDF text locally and drafts profile, employment, skills, education, certification, and language fields for review. Imported records remain unverified and are not used in tailored CV exports until reviewed. Import changes only the editable draft; it does not replace the saved master until you explicitly save. Image-only/scanned PDFs need OCR before import.

The blueprint can store contact details, career history, achievements with evidence and verification status, skills, education, certifications, languages, and application preferences. The blueprint is stored outside the source workspace in the user's operating-system application-data directory (`%LOCALAPPDATA%\cv-optimiser\master_cv.json` on Windows), so it is not accidentally committed with the code.

The baseline analyser and tailoring are rule-based. Optional local AI drafting uses the local Ollama runtime with the Hugging Face Qwen3 4B GGUF model. The app now builds a **new CV draft from scratch** using two blueprint layers:

1. your saved master blueprint as the factual source of truth;
2. a blank canvas file you import yourself: the same layout as the master (JSON, or a CV PDF), with some sections left empty. The agent fills only the empty sections, section by section, from the master and the job; sections that already have text are kept as written.

The model writes only selected sections (summary, experience bullets, grouped skills, and project bullets). Education, certifications, and languages are copied unchanged from the master blueprint. Output is validated for language and unsupported numeric claims, repair is attempted once, and unresolved items fall back to source wording with review notes. You must review and confirm before export. AI output does not modify the master blueprint.

Language is currently hardcoded to Polish for generated CV output. Non-Polish source wording can be translated during drafting where the model can do so without changing factual meaning.

The model runs locally. Downloading its weights contacts Hugging Face through Ollama; CV and job-posting text are sent only to the local Ollama service on your computer, not to a hosted inference API. This application is designed for truthful, conventional, ATS-readable tailoring. It does not insert hidden text or promise to bypass hiring systems or guarantee interviews. Its score is an internal comparison indicator, not an ATS score or hiring probability.

## Run the desktop application

Install the Python dependencies once, then double-click `run_cv_optimiser.bat` or run:

```powershell
python -m pip install -r requirements.txt
python desktop_app.py
```

The app stores your master blueprint in the local application-data directory shown in the desktop window. Review the generated document before each application.

### Enable optional local AI drafting

1. In **Local AI CV builder**, choose **Install Ollama** if the local runtime is missing. You can also install [Ollama for Windows](https://ollama.com/download/windows) directly. Leave Ollama running.
2. Choose **Download local AI model** to download `hf.co/Qwen/Qwen3-4B-GGUF:Q4_K_M` from Hugging Face into Ollama. The model weights occupy several GB.
3. Import your two files: the master blueprint (Blueprint tab, **Import master blueprint (.json)…** or **Import CV from PDF…**, then Save) and the blank canvas (**Import blank canvas…**; it is remembered as `canvas_cv.json` next to the master). Canvas entries are matched to master entries by employer/role or project name; unmatched entries are reported, never guessed. Education, certifications and languages are copied from the master when the canvas leaves them empty.
4. Analyse a job, then choose **Build new CV with AI**.
5. Review/edit the generated draft in the **New CV draft - review, edit and export** panel.
6. Tick **I reviewed this CV and confirm everything in it is accurate**, then use **Export new CV (.docx)**.

The app also saves the reviewed draft JSON to `%LOCALAPPDATA%\cv-optimiser\draft_cv.json`.

The Qwen model is a general instruction model rather than a CV-only fine-tune. The application supplies the job-specific instructions and evidence checks. A machine with limited GPU memory may run inference on the CPU and respond more slowly.

## Test

From the project directory, run:

```powershell
python -m pytest -q
```

Tests mock the local model where needed and do not require downloading model weights or running Ollama. Application dependencies are listed in `requirements.txt`.

## Not implemented yet

Controlled external industry research, application outcome tracking, and broader section-level AI editing controls are future steps.

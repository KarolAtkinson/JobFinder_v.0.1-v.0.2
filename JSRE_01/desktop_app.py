"""Native desktop interface for the local CV Optimiser."""

from __future__ import annotations

import importlib
import importlib.util
import json
import py_compile
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from cv_optimiser.attestation import attest_skills, mark_all_verified
from cv_optimiser.cv_draft import (
    CVDraft,
    DraftSkillGroup,
    default_draft_path,
    fill_draft,
    render_draft_docx,
    save_draft,
    split_lines,
)
from cv_optimiser.job_analysis import JobAnalysis, JobAnalysisError, analyze_job_description
from cv_optimiser.job_import import JobImportError, load_job_posting
from cv_optimiser.local_ai import (
    MODEL_ID,
    LocalModelError,
    OllamaClient,
)
from cv_optimiser.models import BlueprintValidationError, MasterBlueprint
from cv_optimiser.pdf_import import PDFImportError, draft_blueprint_from_pdf_path
from cv_optimiser.storage import default_blueprint_path, load_blueprint, save_blueprint
from cv_optimiser.tailoring import TailoredCV, build_tailored_cv, render_docx

# The program writes every CV in Polish; anything in another language is translated.
CV_LANGUAGE = "pl"


APP_DIR = Path(__file__).resolve().parent
# Dependency order matters when reloading.
RELOAD_ORDER = (
    "models", "storage", "job_analysis", "attestation", "tailoring", "pdf_import", "job_import", "local_ai",
    "cv_draft",
)


def _watched_files() -> list[Path]:
    return [APP_DIR / "desktop_app.py", *sorted((APP_DIR / "cv_optimiser").glob("*.py"))]


def _snapshot() -> dict[str, float]:
    result: dict[str, float] = {}
    for path in _watched_files():
        try:
            result[str(path)] = path.stat().st_mtime
        except OSError:
            continue
    return result


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


class ScrollableFrame(ttk.Frame):
    """A frame that fills its parent, tracks its width, and scrolls vertically when content is taller."""

    MIN_CONTENT_HEIGHT = 620

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.content = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", self._resize)
        self.content.bind("<Configure>", self._resize)

    def _resize(self, _event: tk.Event | None = None) -> None:
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        self._rewrap(self.content, max(200, width - 60))
        needed = max(self.content.winfo_reqheight(), self.MIN_CONTENT_HEIGHT)
        self.canvas.itemconfigure(self._window, width=width, height=max(height, needed))
        self.canvas.configure(scrollregion=(0, 0, width, max(height, needed)))

    def _rewrap(self, widget: tk.Misc, limit: int) -> None:
        for child in widget.winfo_children():
            if isinstance(child, ttk.Label) and int(str(child.cget("wraplength")) or 0) > 0:
                if int(str(child.cget("wraplength"))) != limit:
                    child.configure(wraplength=limit)
            self._rewrap(child, limit)

    def scroll(self, units: int) -> None:
        if self.content.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(units * 3, "units")


class CVOptimiserWindow:
    def __init__(self, root: tk.Tk, restore_state: dict[str, str] | None = None) -> None:
        self.root = root
        self.root.title("CV Optimiser")
        if restore_state is None:
            screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
            width, height = min(1180, int(screen_w * 0.92)), min(840, int(screen_h * 0.88))
            self.root.geometry(f"{width}x{height}+{(screen_w - width) // 2}+{max(0, (screen_h - height) // 3)}")
        self.root.minsize(640, 480)
        icon_path = APP_DIR / "assets" / "cv_optimiser.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass
        self.root.configure(background="#f3f5f8")
        self._closed = False
        self._progress_anchor: tuple[float, int] | None = None
        self._code_snapshot = _snapshot()

        self.blueprint_path = default_blueprint_path()
        self.client = OllamaClient()
        self.worker_events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.analysis: JobAnalysis | None = None
        self.analysis_blueprint_text: str | None = None
        self.blueprint: MasterBlueprint | None = None
        self.tailored_cv: TailoredCV | None = None
        self.draft_view: dict[str, Any] | None = None
        self.draft_analysis: JobAnalysis | None = None
        self.canvas_path = self.blueprint_path.parent / "canvas_cv.json"
        self.canvas: MasterBlueprint | None = None
        self.canvas_text = tk.StringVar(value="Blank canvas: not imported")
        self._step_info = (0, 1)
        self._build_window()
        self._load_blueprint()
        self._load_saved_canvas()
        if restore_state:
            self._restore_state(restore_state)
        self._poll_worker_events()
        self._watch_code()
        self._check_model_status()

    def _language_code(self) -> str:
        return CV_LANGUAGE

    def _capture_state(self) -> dict[str, str]:
        return {
            "blueprint": self.blueprint_editor.get("1.0", "end-1c"),
            "job_description": self.job_description.get("1.0", "end-1c"),
            "job_title": self.job_title_var.get(),
            "industry": self.industry_var.get(),
            "tab": str(self.notebook.index(self.notebook.select())),
        }

    def _restore_state(self, state: dict[str, str]) -> None:
        self.blueprint_editor.delete("1.0", "end")
        self.blueprint_editor.insert("1.0", state["blueprint"])
        self.job_description.delete("1.0", "end")
        self.job_description.insert("1.0", state["job_description"])
        self.job_title_var.set(state["job_title"])
        self.industry_var.set(state["industry"])
        self.notebook.select(int(state["tab"]))
        self.status_text.set("Code refreshed; your unsaved text was kept. Run Analyse again.")

    def _watch_code(self) -> None:
        if self._closed:
            return
        if _snapshot() != self._code_snapshot:
            self.refresh_button.configure(text="Refresh code (changes found)", style="Primary.TButton")
        self.root.after(2000, self._watch_code)

    def _reload_code(self) -> None:
        if self.progress.winfo_ismapped():
            messagebox.showwarning(
                "Busy", "Wait for the running download or AI task to finish, then refresh.", parent=self.root
            )
            return
        files = _watched_files()
        try:
            for path in files:
                py_compile.compile(str(path), doraise=True, cfile=str(Path(__file__).with_suffix(".check.pyc")))
        except py_compile.PyCompileError as error:
            messagebox.showerror("Refresh cancelled", f"The new code has an error:\n\n{error.msg}", parent=self.root)
            return
        finally:
            Path(__file__).with_suffix(".check.pyc").unlink(missing_ok=True)
        try:
            for name in RELOAD_ORDER:
                module = sys.modules.get(f"cv_optimiser.{name}")
                if module is not None:
                    importlib.reload(module)
            spec = importlib.util.spec_from_file_location("desktop_app_live", APP_DIR / "desktop_app.py")
            if spec is None or spec.loader is None:
                raise ImportError("Cannot load desktop_app.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules["desktop_app_live"] = module
            spec.loader.exec_module(module)
        except Exception as error:  # noqa: BLE001 - keep the running window usable
            messagebox.showerror("Refresh failed", f"{type(error).__name__}: {error}", parent=self.root)
            return
        state = self._capture_state()
        root = self.root
        self._closed = True
        root.unbind_all("<MouseWheel>")
        for child in root.winfo_children():
            child.destroy()
        root.live_window = module.CVOptimiserWindow(root, restore_state=state)  # type: ignore[attr-defined]

    def _build_window(self) -> None:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), background="#f3f5f8")
        style.configure("Subheader.TLabel", font=("Segoe UI", 11), background="#f3f5f8")
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

        header = ttk.Frame(self.root, padding=(20, 16, 20, 10))
        header.pack(fill="x")
        ttk.Label(header, text="CV Optimiser", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Tailor a reviewable CV draft using your verified experience. Your data and AI inference stay on this PC.",
            style="Subheader.TLabel",
            wraplength=1050,
        ).pack(anchor="w", pady=(4, 0))
        self.refresh_button = ttk.Button(header, text="Refresh code", command=self._reload_code)
        self.refresh_button.place(relx=1.0, x=0, y=0, anchor="ne")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(4, 10))
        blueprint_scroll = ScrollableFrame(self.notebook)
        job_scroll = ScrollableFrame(self.notebook)
        self.blueprint_tab = blueprint_scroll.content
        self.job_tab = job_scroll.content
        self.blueprint_tab.configure(padding=14)
        self.job_tab.configure(padding=14)
        self.notebook.add(blueprint_scroll, text="  Career blueprint  ")
        self.notebook.add(job_scroll, text="  Job application  ")
        self._build_blueprint_tab()
        self._build_job_tab()
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        footer = ttk.Frame(self.root, padding=(20, 4, 20, 14))
        footer.pack(fill="x")
        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(footer, textvariable=self.status_text).pack(side="left")
        ttk.Label(
            footer,
            text=f"Blueprint: {self.blueprint_path}",
            foreground="#555",
        ).pack(side="right")

    def _on_mousewheel(self, event: tk.Event) -> None:
        widget = event.widget
        # Text boxes and tables scroll themselves.
        if isinstance(widget, (tk.Text, ttk.Treeview, tk.Listbox)):
            return
        selected = self.notebook.nametowidget(self.notebook.select())
        if isinstance(selected, ScrollableFrame):
            selected.scroll(-1 if event.delta > 0 else 1)

    def _build_blueprint_tab(self) -> None:
        self.blueprint_tab.columnconfigure(0, weight=1)
        self.blueprint_tab.rowconfigure(2, weight=1)
        ttk.Label(
            self.blueprint_tab,
            text="Master career blueprint",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.blueprint_tab,
            text=(
                "Edit the JSON below. Add verified achievements with supporting evidence. "
                "Unverified details are excluded from AI prompts and tailored exports."
            ),
            wraplength=1060,
        ).grid(row=1, column=0, sticky="w", pady=(4, 9))

        editor_frame = ttk.Frame(self.blueprint_tab)
        editor_frame.grid(row=2, column=0, sticky="nsew")
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)
        self.blueprint_editor = tk.Text(
            editor_frame,
            wrap="none",
            undo=True,
            font=("Cascadia Code", 10),
            padx=10,
            pady=10,
        )
        vertical = ttk.Scrollbar(editor_frame, orient="vertical", command=self.blueprint_editor.yview)
        horizontal = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.blueprint_editor.xview)
        self.blueprint_editor.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.blueprint_editor.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        buttons = ttk.Frame(self.blueprint_tab)
        buttons.grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Button(buttons, text="Import CV from PDF…", command=self._import_pdf).pack(side="left")
        ttk.Button(buttons, text="Import master blueprint (.json)…", command=self._import_master_json).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Confirm imported items as mine", command=self._confirm_imported).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Validate blueprint", command=self._validate_blueprint).pack(side="left")
        ttk.Button(
            buttons,
            text="Save blueprint",
            style="Primary.TButton",
            command=self._save_blueprint,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Load saved blueprint", command=self._load_blueprint).pack(
            side="left", padx=(8, 0)
        )

    def _build_job_tab(self) -> None:
        self.job_tab.columnconfigure(0, weight=1)
        self.job_tab.rowconfigure(2, weight=1)
        self.job_tab.rowconfigure(5, weight=2)

        details = ttk.Frame(self.job_tab)
        details.grid(row=0, column=0, sticky="ew")
        details.columnconfigure(1, weight=1)
        details.columnconfigure(3, weight=1)
        ttk.Label(details, text="Target job title").grid(row=0, column=0, sticky="w", padx=(0, 7))
        self.job_title_var = tk.StringVar()
        ttk.Entry(details, textvariable=self.job_title_var).grid(row=0, column=1, sticky="ew", padx=(0, 18))
        ttk.Label(details, text="Industry (optional)").grid(row=0, column=2, sticky="w", padx=(0, 7))
        self.industry_var = tk.StringVar()
        ttk.Entry(details, textvariable=self.industry_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(self.job_tab, text="Paste the complete job description", style="Section.TLabel").grid(
            row=1, column=0, sticky="w", pady=(16, 5)
        )
        job_text_frame = ttk.Frame(self.job_tab)
        job_text_frame.grid(row=2, column=0, sticky="nsew")
        job_text_frame.rowconfigure(0, weight=1)
        job_text_frame.columnconfigure(0, weight=1)
        self.job_description = tk.Text(job_text_frame, wrap="word", height=8, undo=True, padx=8, pady=8)
        job_scroll = ttk.Scrollbar(job_text_frame, orient="vertical", command=self.job_description.yview)
        self.job_description.configure(yscrollcommand=job_scroll.set)
        self.job_description.grid(row=0, column=0, sticky="nsew")
        job_scroll.grid(row=0, column=1, sticky="ns")

        actions = ttk.Frame(self.job_tab)
        actions.grid(row=3, column=0, sticky="nw", pady=10)
        self.analyse_button = ttk.Button(
            actions,
            text="Analyse job and match evidence",
            style="Primary.TButton",
            command=self._analyse_job,
        )
        self.analyse_button.pack(side="left")
        ttk.Button(actions, text="Import job from .txt…", command=self._import_job_txt).pack(
            side="left", padx=(10, 0)
        )

        ttk.Label(self.job_tab, text="Requirements and evidence", style="Section.TLabel").grid(
            row=4, column=0, sticky="w", pady=(3, 5)
        )
        result_frame = ttk.Frame(self.job_tab)
        result_frame.grid(row=5, column=0, sticky="nsew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        columns = ("priority", "status", "requirement", "evidence")
        self.results = ttk.Treeview(result_frame, columns=columns, show="headings", height=7)
        for column, label, width in (
            ("priority", "Priority", 90),
            ("status", "Evidence", 95),
            ("requirement", "Job requirement", 390),
            ("evidence", "Blueprint source", 330),
        ):
            self.results.heading(column, text=label)
            self.results.column(column, width=width, minwidth=70, stretch=column in {"requirement", "evidence"})
        results_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.results.yview)
        self.results.configure(yscrollcommand=results_scroll.set)
        self.results.grid(row=0, column=0, sticky="nsew")
        results_scroll.grid(row=0, column=1, sticky="ns")

        self.score_label = ttk.Label(self.job_tab, text="Internal evidence alignment: not analysed")
        self.score_label.grid(row=6, column=0, sticky="w", pady=(7, 5))
        export_row = ttk.Frame(self.job_tab)
        export_row.grid(row=7, column=0, sticky="w")
        ttk.Button(export_row, text="Export verified CV (.docx)", command=self._export_verified_cv).pack(
            side="left"
        )
        ttk.Button(export_row, text="Export analysis report (.json)", command=self._export_report).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            export_row, text="Confirm missing requirements as my skills…", command=self._confirm_missing
        ).pack(side="left", padx=(8, 0))
        self.include_missing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.job_tab,
            text=(
                "Add missing job requirements to the new CV (I confirm I have done them; "
                "my imported CV items count as confirmed). Re-run Analyse after changing."
            ),
            variable=self.include_missing_var,
        ).grid(row=10, column=0, sticky="w", pady=(6, 0))

        ai_frame = ttk.LabelFrame(self.job_tab, text="Local AI CV builder", padding=10)
        ai_frame.grid(row=8, column=0, sticky="ew", pady=(12, 0))
        ai_frame.columnconfigure(0, weight=1)
        ttk.Label(
            ai_frame,
            text=(
                f"Model: {MODEL_ID}. Model downloads come from Hugging Face; prompts are sent only "
                "to the Ollama service running on this computer."
            ),
            wraplength=1000,
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        self.model_status = tk.StringVar(value="Checking local Ollama...")
        ttk.Label(ai_frame, textvariable=self.model_status).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.download_model_button = ttk.Button(
            ai_frame,
            text="Download local AI model",
            command=self._download_model,
        )
        self.download_model_button.grid(row=1, column=1, padx=8, pady=(5, 0))
        self.install_ollama_button = ttk.Button(
            ai_frame,
            text="Install Ollama",
            command=self._install_ollama,
        )
        self.install_ollama_button.grid(row=1, column=2, pady=(5, 0))
        self.generate_button = ttk.Button(
            ai_frame,
            text="Build new CV with AI",
            command=self._generate_draft,
        )
        self.generate_button.grid(row=1, column=3, padx=(8, 0), pady=(5, 0))

        canvas_row = ttk.Frame(ai_frame)
        canvas_row.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(7, 0))
        ttk.Button(canvas_row, text="Import blank canvas…", command=self._import_canvas).pack(side="left")
        ttk.Label(canvas_row, textvariable=self.canvas_text, wraplength=800).pack(side="left", padx=(10, 0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(ai_frame, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(7, 0))
        self.progress.grid_remove()
        self.progress_text = tk.StringVar(value="")
        ttk.Label(ai_frame, textvariable=self.progress_text).grid(row=3, column=0, columnspan=3, sticky="w")

        self.draft_frame = ttk.LabelFrame(
            self.job_tab,
            text="New CV draft - review, edit and export",
            padding=10,
        )
        self.draft_frame.grid(row=9, column=0, sticky="ew", pady=(10, 0))
        self.draft_frame.columnconfigure(0, weight=1)
        self.draft_frame.grid_remove()
        self.export_draft_button = ttk.Button(
            self.draft_frame,
            text="Export new CV (.docx)",
            style="Primary.TButton",
            command=self._export_draft_cv,
        )
        self.export_draft_button.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.job_tab.rowconfigure(2, weight=1)
        self.job_tab.rowconfigure(5, weight=1)

    def _load_blueprint(self) -> None:
        try:
            blueprint = load_blueprint(self.blueprint_path) if self.blueprint_path.exists() else MasterBlueprint()
            text = json.dumps(blueprint.to_dict(), indent=2, ensure_ascii=False)
        except (OSError, BlueprintValidationError) as error:
            messagebox.showerror("Blueprint load failed", str(error), parent=self.root)
            return
        self.blueprint_editor.delete("1.0", "end")
        self.blueprint_editor.insert("1.0", text)
        self.analysis = None
        self.analysis_blueprint_text = None
        self.blueprint = blueprint
        self._clear_analysis()
        self.status_text.set("Blueprint loaded")

    def _import_master_json(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.root, title="Select the master blueprint", filetypes=[("Blueprint JSON", "*.json")]
        )
        if not filename:
            return
        try:
            blueprint = load_blueprint(filename)
        except (OSError, BlueprintValidationError) as error:
            messagebox.showerror("Master blueprint import failed", str(error), parent=self.root)
            return
        self.blueprint_editor.delete("1.0", "end")
        self.blueprint_editor.insert("1.0", json.dumps(blueprint.to_dict(), indent=2, ensure_ascii=False))
        self.blueprint = blueprint
        self.analysis = None
        self.analysis_blueprint_text = None
        self._clear_analysis()
        self.status_text.set("Master blueprint imported; choose Save blueprint to keep it")

    def _load_saved_canvas(self) -> None:
        if not self.canvas_path.exists():
            return
        try:
            self.canvas = load_blueprint(self.canvas_path)
        except (OSError, BlueprintValidationError):
            return
        self.canvas_text.set(f"Blank canvas: {self.canvas_path.name} (saved)")

    def _import_canvas(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select the blank canvas (same layout as the master, some sections empty)",
            filetypes=[("Blueprint JSON or CV PDF", "*.json *.pdf")],
        )
        if not filename:
            return
        try:
            if filename.lower().endswith(".pdf"):
                canvas = draft_blueprint_from_pdf_path(filename)
            else:
                canvas = load_blueprint(filename)
            save_blueprint(canvas, self.canvas_path)
        except (OSError, BlueprintValidationError, PDFImportError) as error:
            messagebox.showerror("Blank canvas import failed", str(error), parent=self.root)
            return
        self.canvas = canvas
        self.canvas_text.set(f"Blank canvas: {Path(filename).name}")
        self._clear_draft()
        self.status_text.set("Blank canvas imported")

    def _import_pdf(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select a completed CV PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not filename:
            return
        if not messagebox.askyesno(
            "Import PDF as a draft",
            (
                "The PDF text will be extracted locally and used to replace the blueprint editor contents. "
                "The saved master blueprint will not change until you review the draft and choose Save blueprint. "
                "Extracted details are marked unverified. Continue?"
            ),
            parent=self.root,
        ):
            return
        try:
            draft = draft_blueprint_from_pdf_path(filename)
        except PDFImportError as error:
            messagebox.showerror("PDF import failed", str(error), parent=self.root)
            self.status_text.set("PDF import failed")
            return
        except OSError as error:
            messagebox.showerror("PDF import failed", f"Could not read the selected PDF: {error}", parent=self.root)
            self.status_text.set("PDF import failed")
            return

        self.blueprint_editor.delete("1.0", "end")
        self.blueprint_editor.insert("1.0", json.dumps(draft.to_dict(), indent=2, ensure_ascii=False))
        self.blueprint = draft
        self.analysis = None
        self.analysis_blueprint_text = None
        self._clear_analysis()
        self.notebook.select(self.blueprint_tab)
        self.status_text.set("PDF extracted into an unverified draft; review before saving")
        messagebox.showinfo(
            "PDF draft imported",
            (
                f"Extracted text from {len(draft.imported_cv_text)} characters in the PDF. "
                f"Found {len(draft.experience)} work-history block(s), {len(draft.skills)} skill(s), "
                f"{len(draft.education)} education record(s), and {len(draft.certifications)} certification(s).\n\n"
                "Review the JSON, correct any fields, and mark details verified only after checking the original CV. "
                "The saved master blueprint has not been changed."
            ),
            parent=self.root,
        )

    def _import_job_txt(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select a job application text file",
            filetypes=[("Text files", "*.txt")],
        )
        if not filename:
            return
        try:
            posting = load_job_posting(filename)
        except JobImportError as error:
            messagebox.showerror("Job import failed", str(error), parent=self.root)
            self.status_text.set("Job import failed")
            return

        self.job_title_var.set(posting.title)
        self.industry_var.set(posting.industry)
        self.job_description.delete("1.0", "end")
        self.job_description.insert("1.0", posting.description)
        self.analysis = None
        self.analysis_blueprint_text = None
        self._clear_analysis()
        self.status_text.set("Job imported; check the title and industry, then analyse")

    def _confirm_imported(self) -> None:
        try:
            blueprint, _ = self._blueprint_from_editor()
        except BlueprintValidationError as error:
            messagebox.showerror("Blueprint validation failed", str(error), parent=self.root)
            return
        if not messagebox.askyesno(
            "Confirm imported items",
            "By continuing you confirm that the imported experience, achievements, skills, education, "
            "certifications and languages are accurate and yours. They can then be used in tailored CVs. Continue?",
            parent=self.root,
        ):
            return
        changed = mark_all_verified(blueprint)
        self.blueprint_editor.delete("1.0", "end")
        self.blueprint_editor.insert("1.0", json.dumps(blueprint.to_dict(), indent=2, ensure_ascii=False))
        self.status_text.set(f"{changed} item(s) confirmed; click Save blueprint to keep them")

    def _confirm_missing(self) -> None:
        if self.analysis is None:
            messagebox.showwarning("Analyse a job first", "Analyse a job first.", parent=self.root)
            return
        missing = [match.requirement.text for match in self.analysis.matches if match.status == "missing"]
        if not missing:
            messagebox.showinfo("Nothing missing", "Every requirement already has supporting evidence.", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm missing requirements")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(
            dialog,
            text=(
                "Tick only the requirements you have genuinely done. They are added to your blueprint as "
                "skills you personally confirmed. Anything you untick stays out of the CV."
            ),
            wraplength=640,
            padding=10,
        ).pack(anchor="w")
        body = ttk.Frame(dialog, padding=(10, 0))
        body.pack(fill="both", expand=True)
        choices: list[tuple[tk.BooleanVar, str]] = []
        for text in missing:
            variable = tk.BooleanVar(value=True)
            ttk.Checkbutton(body, text=text[:110], variable=variable).pack(anchor="w")
            choices.append((variable, text))

        def apply() -> None:
            selected = [text for variable, text in choices if variable.get()]
            dialog.destroy()
            if not selected:
                return
            try:
                blueprint, _ = self._blueprint_from_editor()
            except BlueprintValidationError as error:
                messagebox.showerror("Blueprint validation failed", str(error), parent=self.root)
                return
            added = attest_skills(blueprint, selected, self.job_title_var.get())
            self.blueprint_editor.delete("1.0", "end")
            self.blueprint_editor.insert("1.0", json.dumps(blueprint.to_dict(), indent=2, ensure_ascii=False))
            self._analyse_job()
            self.status_text.set(f"{added} confirmed skill(s) added and job re-analysed; save the blueprint to keep them")

        buttons = ttk.Frame(dialog, padding=10)
        buttons.pack(anchor="e")
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="left")
        ttk.Button(buttons, text="I confirm these", style="Primary.TButton", command=apply).pack(
            side="left", padx=(8, 0)
        )

    def _blueprint_from_editor(self) -> tuple[MasterBlueprint, str]:
        text = self.blueprint_editor.get("1.0", "end-1c")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise BlueprintValidationError(
                f"Blueprint is not valid JSON at line {error.lineno}, column {error.colno}: {error.msg}."
            ) from error
        return MasterBlueprint.from_dict(data), text

    def _validate_blueprint(self) -> None:
        try:
            blueprint, _ = self._blueprint_from_editor()
        except BlueprintValidationError as error:
            messagebox.showerror("Blueprint validation failed", str(error), parent=self.root)
            self.status_text.set("Blueprint validation failed")
            return
        self.blueprint = blueprint
        self.status_text.set("Blueprint is valid")
        messagebox.showinfo("Blueprint valid", "Your career blueprint passed validation.", parent=self.root)

    def _save_blueprint(self) -> None:
        try:
            blueprint, _ = self._blueprint_from_editor()
            save_blueprint(blueprint, self.blueprint_path)
        except (BlueprintValidationError, OSError) as error:
            messagebox.showerror("Blueprint save failed", str(error), parent=self.root)
            self.status_text.set("Blueprint was not saved")
            return
        self.blueprint = blueprint
        self.status_text.set(f"Blueprint saved to {self.blueprint_path}")
        messagebox.showinfo("Blueprint saved", f"Saved locally to:\n{self.blueprint_path}", parent=self.root)

    def _analyse_job(self) -> None:
        try:
            blueprint, text = self._blueprint_from_editor()
            analysis = analyze_job_description(
                self.job_description.get("1.0", "end-1c"),
                blueprint,
                job_title=self.job_title_var.get(),
                industry=self.industry_var.get(),
            )
        except (BlueprintValidationError, JobAnalysisError) as error:
            messagebox.showerror("Cannot analyse job", str(error), parent=self.root)
            self.status_text.set("Job analysis failed")
            return

        self.blueprint = blueprint
        self.analysis = analysis
        self.analysis_blueprint_text = text
        cv_blueprint, cv_analysis = blueprint, analysis
        if self.include_missing_var.get():
            # Work on a copy so the editor and saved blueprint are untouched.
            cv_blueprint = MasterBlueprint.from_dict(blueprint.to_dict())
            mark_all_verified(cv_blueprint)
            missing = [m.requirement.text for m in analysis.matches if m.status == "missing"]
            attest_skills(cv_blueprint, missing, self.job_title_var.get())
            cv_analysis = analyze_job_description(
                self.job_description.get("1.0", "end-1c"),
                cv_blueprint,
                job_title=self.job_title_var.get(),
                industry=self.industry_var.get(),
            )
            self.blueprint = cv_blueprint
        self.blueprint = cv_blueprint if self.include_missing_var.get() else blueprint
        self.draft_analysis = cv_analysis
        self.tailored_cv = build_tailored_cv(cv_blueprint, cv_analysis)
        self._clear_results()
        self._clear_draft()
        for match in analysis.matches:
            self.results.insert(
                "",
                "end",
                values=(
                    match.requirement.priority.title(),
                    match.status.title(),
                    match.requirement.text,
                    "; ".join(match.evidence) or "No supporting evidence found",
                ),
            )
        self.score_label.configure(
            text=(
                f"Internal evidence alignment: {analysis.alignment_score}% "
                "(not an ATS score or hiring probability)"
            )
        )
        self.status_text.set(f"Analysed {len(analysis.requirements)} job requirements")
        self._check_model_status()

    def _clear_analysis(self) -> None:
        self._clear_results()
        self.score_label.configure(text="Internal evidence alignment: not analysed")
        self._clear_draft()

    def _clear_results(self) -> None:
        for item in self.results.get_children():
            self.results.delete(item)

    def _clear_draft(self) -> None:
        for child in self.draft_frame.winfo_children():
            if child is not self.export_draft_button:
                child.destroy()
        self.draft_view = None
        self.export_draft_button.configure(state="disabled")
        self.draft_frame.grid_remove()

    def _current_blueprint_is_unchanged(self) -> bool:
        if self.analysis_blueprint_text is None:
            return False
        return self.blueprint_editor.get("1.0", "end-1c") == self.analysis_blueprint_text

    def _require_current_analysis(self) -> bool:
        if self.analysis is None or self.blueprint is None or self.tailored_cv is None:
            messagebox.showwarning("Analyse a job first", "Analyse a job before generating or exporting a CV.")
            return False
        if not self._current_blueprint_is_unchanged():
            messagebox.showwarning(
                "Blueprint changed",
                "The blueprint has changed since analysis. Analyse the job again before generating or exporting.",
                parent=self.root,
            )
            return False
        return True

    def _export_verified_cv(self) -> None:
        if not self._require_current_analysis() or self.tailored_cv is None:
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save verified CV draft",
            defaultextension=".docx",
            initialfile="tailored_cv.docx",
            filetypes=[("Word document", "*.docx")],
        )
        if not filename:
            return
        try:
            Path(filename).write_bytes(render_docx(self.tailored_cv, language=self._language_code()))
        except OSError as error:
            messagebox.showerror("CV export failed", str(error), parent=self.root)
            return
        self.status_text.set(f"CV draft saved to {filename}")
        messagebox.showinfo("CV exported", f"Saved draft to:\n{filename}", parent=self.root)

    def _export_report(self) -> None:
        if self.analysis is None:
            messagebox.showwarning("Analyse a job first", "Analyse a job before exporting its report.")
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save job analysis report",
            defaultextension=".json",
            initialfile="job_analysis_report.json",
            filetypes=[("JSON report", "*.json")],
        )
        if not filename:
            return
        report = {
            "job_title": self.analysis.job_title,
            "industry": self.analysis.industry,
            "alignment_score": self.analysis.alignment_score,
            "score_note": "Internal evidence comparison only; not an ATS score or hiring probability.",
            "requirements": [
                {
                    "text": match.requirement.text,
                    "priority": match.requirement.priority,
                    "category": match.requirement.category,
                    "evidence_status": match.status,
                    "blueprint_evidence": list(match.evidence),
                }
                for match in self.analysis.matches
            ],
        }
        try:
            Path(filename).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Report export failed", str(error), parent=self.root)
            return
        self.status_text.set(f"Analysis report saved to {filename}")

    def _refresh_model_status(self) -> None:
        try:
            installed = self.client.is_model_installed()
        except LocalModelError:
            self._set_model_status(False, "Ollama is not available. Install it to enable local AI.")
            return
        self._set_model_status(installed, None)

    def _set_model_status(self, installed: bool, error: str | None) -> None:
        if error:
            self.model_status.set(error)
            self.download_model_button.configure(state="disabled")
            self.generate_button.configure(state="disabled")
            self.install_ollama_button.configure(state="normal")
            return
        self.install_ollama_button.configure(state="disabled")
        if installed:
            self.model_status.set("Ollama is ready; model is installed locally.")
            self.download_model_button.configure(state="disabled")
            self.generate_button.configure(state="normal" if self.analysis else "disabled")
        else:
            self.model_status.set("Ollama is ready; the local model has not been downloaded.")
            self.download_model_button.configure(state="normal")
            self.generate_button.configure(state="disabled")

    def _check_model_status(self) -> None:
        if self._closed:
            return

        def check() -> None:
            try:
                installed = self.client.is_model_installed()
            except LocalModelError as error:
                self.worker_events.put(("model_status", (False, str(error))))
            else:
                self.worker_events.put(("model_status", (installed, None)))

        threading.Thread(target=check, daemon=True).start()

    def _install_ollama(self) -> None:
        self.install_ollama_button.configure(state="disabled")

        def install() -> None:
            try:
                process = subprocess.Popen(
                    [
                        "winget",
                        "install",
                        "--id",
                        "Ollama.Ollama",
                        "--exact",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                        "--disable-interactivity",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                output, _ = process.communicate()
            except OSError as error:
                self.worker_events.put(("install_error", str(error)))
                return
            if process.returncode != 0:
                self.worker_events.put(("install_error", output.strip() or "winget installation failed."))
            else:
                self.worker_events.put(("ollama_installed", output.strip()))

        threading.Thread(target=install, daemon=True).start()

    def _download_model(self) -> None:
        self.download_model_button.configure(state="disabled")
        self.progress.configure(mode="determinate")
        self.progress_var.set(0)
        self.progress.grid()
        self._progress_anchor = None
        self.progress_text.set("Connecting to local Ollama...")

        def download() -> None:
            try:
                self.client.pull_model(
                    lambda status, percent: self.worker_events.put(("progress", (status, percent)))
                )
            except LocalModelError as error:
                self.worker_events.put(("error", str(error)))
            else:
                self.worker_events.put(("downloaded", None))

        threading.Thread(target=download, daemon=True).start()

    def _progress_message(self, status: str, percent: int | None) -> str:
        if percent is None:
            return status
        now = time.monotonic()
        if self._progress_anchor is None or percent < self._progress_anchor[1]:
            self._progress_anchor = (now, percent)
        start_time, start_percent = self._progress_anchor
        message = f"{status}: {percent}%"
        gained = percent - start_percent
        if gained > 0 and now - start_time >= 1.5:
            remaining = (now - start_time) * (100 - percent) / gained
            message += f" - about {_format_duration(remaining)} left"
        return message

    def _generate_draft(self) -> None:
        if not self._require_current_analysis() or self.draft_analysis is None or self.blueprint is None:
            return
        if self.canvas is None:
            messagebox.showwarning(
                "Blank canvas missing", "Import the blank canvas file first (Import blank canvas…).", parent=self.root
            )
            return
        self.generate_button.configure(state="disabled")
        self.progress.configure(mode="determinate")
        self.progress_var.set(0)
        self.progress.grid()
        self._progress_anchor = None
        self._step_info = (0, 1)
        self.progress_text.set("Loading the local model and reading your evidence (this can take a minute)...")
        blueprint, analysis = self.blueprint, self.draft_analysis
        canvas = self.canvas
        language = self._language_code()

        def percent(fraction: float) -> int:
            done, total = self._step_info
            return min(99, round((done + fraction) / total * 100))

        def on_chunk(count: int) -> None:
            self.worker_events.put(("progress", (self._step_label, percent(min(0.95, count / 220)))))

        def on_step(label: str, done: int, total: int) -> None:
            self._step_info = (done, total)
            self._step_label = label
            self.worker_events.put(("progress", (label, percent(0))))

        self._step_label = "Writing the new CV"
        self.client.on_progress = on_chunk

        def generate() -> None:
            try:
                result = fill_draft(blueprint, canvas, analysis, self.client, language, on_step)
            except LocalModelError as error:
                self.worker_events.put(("error", str(error)))
            else:
                self.worker_events.put(("draft", result))
            finally:
                self.client.on_progress = None

        threading.Thread(target=generate, daemon=True).start()

    def _show_draft(self, draft: CVDraft, warnings: list[str]) -> None:
        self._clear_draft()
        frame = self.draft_frame
        row = 0

        def label(text: str, bold: bool = False) -> None:
            nonlocal row
            ttk.Label(
                frame, text=text, wraplength=1000, font=("Segoe UI", 10, "bold") if bold else None
            ).grid(row=row, column=0, sticky="w", pady=(8 if bold else 2, 0))
            row += 1

        def box(text: str, height: int) -> tk.Text:
            nonlocal row
            widget = tk.Text(frame, height=height, wrap="word", font=("Segoe UI", 10), undo=True)
            widget.insert("1.0", text)
            widget.grid(row=row, column=0, sticky="ew", pady=(2, 0))
            row += 1
            return widget

        label(
            "The agent filled the empty sections of your blank canvas from your master blueprint. Edit anything below (one bullet per line), "
            "then confirm and export.",
        )
        for warning in warnings:
            label(f"Note: {warning}")
        label("Professional summary", bold=True)
        view: dict[str, Any] = {"draft": draft, "summary": box(draft.summary, 7), "experience": [], "projects": []}
        for item in draft.experience:
            dates = " - ".join(value for value in (item.start_date, item.end_date) if value)
            label(" | ".join(part for part in (item.role, item.employer, dates) if part) or "Experience", bold=True)
            view["experience"].append(box("\n".join(item.bullets), max(3, len(item.bullets) + 1)))
        label("Skills (one group per line: Group: skill; skill)", bold=True)
        skill_lines = [f"{group.label}: {'; '.join(group.skills)}" for group in draft.skills]
        view["skills"] = box("\n".join(skill_lines), max(3, len(skill_lines) + 1))
        for project in draft.projects:
            label(f"Project: {project.name}", bold=True)
            view["projects"].append(box("\n".join(project.bullets), max(3, len(project.bullets) + 1)))
        label("Education, certifications and languages are copied unchanged from your blueprint.")
        view["approved"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="I reviewed this CV and confirm everything in it is accurate",
            variable=view["approved"],
            command=self._refresh_approval_state,
        ).grid(row=row, column=0, sticky="w", pady=(8, 0))
        self.export_draft_button.grid(row=row + 1, column=0, sticky="w", pady=(8, 0))
        self.draft_view = view
        frame.grid()
        self._refresh_approval_state()

    def _refresh_approval_state(self) -> None:
        ready = (
            self.draft_view is not None
            and self.draft_view["approved"].get()
            and self._current_blueprint_is_unchanged()
        )
        self.export_draft_button.configure(state="normal" if ready else "disabled")

    def _collect_draft(self) -> CVDraft:
        assert self.draft_view is not None
        view = self.draft_view
        base: CVDraft = view["draft"]
        draft = CVDraft.from_dict(base.to_dict())
        draft.summary = view["summary"].get("1.0", "end-1c").strip()
        for item, widget in zip(draft.experience, view["experience"]):
            item.bullets = split_lines(widget.get("1.0", "end-1c"))
        for item, widget in zip(draft.projects, view["projects"]):
            item.bullets = split_lines(widget.get("1.0", "end-1c"))
        groups: list[DraftSkillGroup] = []
        for line in split_lines(view["skills"].get("1.0", "end-1c")):
            name, _, rest = line.partition(":")
            skills = [part.strip() for part in rest.split(";") if part.strip()]
            if rest and skills:
                groups.append(DraftSkillGroup(label=name.strip(), skills=skills))
            elif line:
                groups.append(DraftSkillGroup(label="", skills=[line]))
        draft.skills = groups
        return draft

    def _export_draft_cv(self) -> None:
        if not self._require_current_analysis() or self.draft_view is None:
            return
        if not self.draft_view["approved"].get():
            messagebox.showwarning("Review required", "Confirm that you reviewed the CV first.")
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save new CV",
            defaultextension=".docx",
            initialfile="CV.docx",
            filetypes=[("Word document", "*.docx")],
        )
        if not filename:
            return
        draft = self._collect_draft()
        try:
            Path(filename).write_bytes(render_draft_docx(draft, self._language_code()))
            save_draft(draft, default_draft_path(self.blueprint_path))
        except OSError as error:
            messagebox.showerror("CV export failed", str(error), parent=self.root)
            return
        self.status_text.set(f"New CV saved to {filename}")
        messagebox.showinfo("CV exported", f"Saved CV to:\n{filename}", parent=self.root)

    def _poll_worker_events(self) -> None:
        while True:
            try:
                event, payload = self.worker_events.get_nowait()
            except queue.Empty:
                break
            if event == "progress":
                status, percent = payload
                self.progress_text.set(self._progress_message(status, percent))
                if percent is not None:
                    self.progress_var.set(percent)
            elif event == "downloaded":
                self.progress.stop()
                self.progress.grid_remove()
                self.progress_text.set("Model downloaded successfully.")
                self.status_text.set("Local AI model is ready")
                self._refresh_model_status()
                messagebox.showinfo(
                    "Model ready",
                    f"{MODEL_ID} has been downloaded to Ollama on this PC.",
                    parent=self.root,
                )
            elif event == "draft":
                self.progress.stop()
                self.progress.grid_remove()
                self.progress_text.set("The new CV is ready for your review.")
                self._show_draft(*payload)
                self.status_text.set("Review and edit the new CV before export")
            elif event == "error":
                self.progress.stop()
                self.progress.grid_remove()
                self.progress_text.set("")
                self.status_text.set("Local AI operation failed")
                self._refresh_model_status()
                messagebox.showerror("Local AI error", payload, parent=self.root)
            elif event == "model_status":
                self._set_model_status(*payload)
            elif event == "install_error":
                self.install_ollama_button.configure(state="normal")
                self.model_status.set("Ollama installation failed.")
                messagebox.showerror("Ollama installation failed", payload, parent=self.root)
            elif event == "ollama_installed":
                self.model_status.set("Ollama installed. Waiting for the local service to start...")
                self.status_text.set("Ollama installed")
                self.root.after(4000, self._check_model_status)
        if not self._closed:
            self.root.after(100, self._poll_worker_events)


def main() -> None:
    root = tk.Tk()
    CVOptimiserWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
render_resume.py - Compile a resume .tex to PDF and render preview images.

This powers the "view" half of the loop: after a surgical edit to the .tex, compile it
and produce PNG previews so the result can be shown inline, plus surface compile errors
clearly (with a log tail) when the LaTeX doesn't build.

Usage:
    python render_resume.py resume.tex [--outdir DIR] [--dpi 150]

Prints JSON: { ok, pdf, previews: [...png], engine, log_tail (on failure) }.
Requires a LaTeX engine (latexmk/pdflatex/xelatex) and pdftoppm (poppler) for previews.
Standard library only.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def have(cmd):
    return shutil.which(cmd) is not None


def compile_tex(tex_path, outdir):
    tex_path = Path(tex_path).resolve()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    jobname = tex_path.stem

    # Prefer latexmk (handles reruns/bib), fall back to raw pdflatex twice.
    attempts = []
    if have("latexmk"):
        attempts.append((["latexmk", "-pdf", "-interaction=nonstopmode",
                          "-halt-on-error", f"-outdir={outdir}", str(tex_path)], "latexmk+pdflatex"))
    if have("pdflatex"):
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={outdir}", str(tex_path)]
        attempts.append((cmd, "pdflatex"))  # will run twice below

    last_log = ""
    for cmd, engine in attempts:
        runs = 2 if cmd[0] == "pdflatex" else 1
        ok = False
        for _ in range(runs):
            proc = subprocess.run(cmd, cwd=tex_path.parent, capture_output=True, text=True, timeout=120)
            last_log = proc.stdout + proc.stderr
            ok = proc.returncode == 0
        pdf = outdir / f"{jobname}.pdf"
        if ok and pdf.exists():
            return {"ok": True, "pdf": str(pdf), "engine": engine}
    # find the log file for a better tail
    log_file = outdir / f"{jobname}.log"
    if log_file.exists():
        last_log = log_file.read_text(encoding="utf-8", errors="ignore")
    tail = "\n".join(last_log.splitlines()[-30:])
    return {"ok": False, "log_tail": tail}


def render_previews(pdf_path, outdir, dpi):
    if not have("pdftoppm"):
        return []
    stem = Path(pdf_path).stem
    prefix = Path(outdir) / f"{stem}_preview"
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
                   capture_output=True, text=True, timeout=60)
    return sorted(str(p) for p in Path(outdir).glob(f"{stem}_preview*.png"))


def main():
    ap = argparse.ArgumentParser(description="Compile resume .tex and render previews.")
    ap.add_argument("tex", help="Path to resume .tex")
    ap.add_argument("--outdir", default="build", help="Build/output directory")
    ap.add_argument("--dpi", type=int, default=150, help="Preview render DPI")
    args = ap.parse_args()

    if not have("pdflatex") and not have("latexmk"):
        print(json.dumps({"ok": False, "error":
              "No LaTeX engine found. Install TeX (e.g. `brew install --cask mactex-no-gui` "
              "or `apt install texlive-latex-recommended`) or use tectonic."}))
        sys.exit(1)

    result = compile_tex(args.tex, args.outdir)
    if result.get("ok"):
        result["previews"] = render_previews(result["pdf"], args.outdir, args.dpi)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
render_resume.py - Compile a resume .tex to PDF and render preview images.

This powers the "view" half of the loop: after a surgical edit to the .tex, compile it
and produce PNG previews so the result can be shown inline, plus surface compile errors
clearly (with a log tail) when the LaTeX doesn't build.

Usage:
    python render_resume.py resume.tex [--outdir DIR] [--dpi 150] [--engine auto|latexmk|pdflatex|tectonic]

Prints JSON: { ok, pdf, pages, previews: [...png], engine, warnings, log_tail (on failure) }.
--outdir defaults to a build/ folder next to the .tex. Paths are resolved from the
directory you run it in, so it works from anywhere.

Engines, in order of preference: latexmk, pdflatex, tectonic. With tectonic, fontawesome5
(which crashes tectonic on some machines) is swapped out of a temporary copy and
\\faExternalLink* becomes an arrow; your .tex is never modified. Compile on Overleaf for
the final PDF with real icons. Previews use pdftoppm (poppler), or sips on macOS.
Standard library only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TECTONIC_SANITIZE = [
    (re.compile(r"\\faExternalLink\*?"), r"$\\nearrow$"),
    (re.compile(r"^(\s*\\usepackage(?:\[[^\]]*\])?\{fontawesome5\})", re.M), r"%\1"),
    (re.compile(r"^(\s*\\input\{glyphtounicode\})", re.M), r"%\1"),
    (re.compile(r"^(\s*\\pdfgentounicode\s*=\s*1)", re.M), r"%\1"),
]


def have(cmd):
    return shutil.which(cmd) is not None


def tail(text, n=25):
    return "\n".join(text.splitlines()[-n:])


def run(cmd, cwd):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
        return proc.returncode == 0, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return False, f"{cmd[0]} timed out after 180s"


def compile_latex(tex, outdir, engine):
    if engine == "latexmk":
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
               f"-outdir={outdir}", tex.name]
        ok, log = run(cmd, tex.parent)
    else:  # pdflatex, twice for references
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={outdir}", tex.name]
        ok, log = run(cmd, tex.parent)
        if ok:
            ok, log = run(cmd, tex.parent)
    pdf = outdir / f"{tex.stem}.pdf"
    if not ok:
        log_file = outdir / f"{tex.stem}.log"
        if log_file.exists():
            log = log_file.read_text(encoding="utf-8", errors="ignore")
    return ok and pdf.exists(), pdf, log, []


def compile_tectonic(tex, outdir):
    source = tex.read_text(encoding="utf-8", errors="ignore")
    sanitized, warnings = source, []
    for pat, repl in TECTONIC_SANITIZE:
        sanitized = pat.sub(repl, sanitized)
    if sanitized != source:
        warnings.append("Compiled a copy without fontawesome5/glyphtounicode for tectonic; "
                        "icons show as arrows. Use Overleaf for the final PDF.")
    # The copy sits next to the original so relative \includegraphics / \input paths resolve.
    tmp = tex.parent / f".{tex.stem}.r2r-tectonic.tex"
    tmp.write_text(sanitized, encoding="utf-8")
    try:
        ok, log = run(["tectonic", "--keep-logs", "--outdir", str(outdir), tmp.name], tex.parent)
    finally:
        tmp.unlink(missing_ok=True)
    built = outdir / f"{tmp.stem}.pdf"
    pdf = outdir / f"{tex.stem}.pdf"
    if ok and built.exists():
        built.replace(pdf)
    built_log = outdir / f"{tmp.stem}.log"
    if built_log.exists():
        built_log.replace(outdir / f"{tex.stem}.log")
    return ok and pdf.exists(), pdf, log, warnings


def page_count(pdf):
    if have("pdfinfo"):
        ok, out = run(["pdfinfo", str(pdf)], pdf.parent)
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        if ok and m:
            return int(m.group(1))
    try:
        data = pdf.read_bytes()
    except OSError:
        return None
    n = len(re.findall(rb"/Type\s*/Page(?!s)", data))
    return n or None


def render_previews(pdf, outdir, dpi):
    stem = pdf.stem
    for old in outdir.glob(f"{stem}_preview*.png"):
        old.unlink()
    if have("pdftoppm"):
        run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(outdir / f"{stem}_preview")], outdir)
    elif have("sips"):  # macOS; renders page 1 only
        run(["sips", "-s", "format", "png", "--resampleWidth", str(int(8.5 * dpi)),
             str(pdf), "--out", str(outdir / f"{stem}_preview-1.png")], outdir)
    return sorted(str(p) for p in outdir.glob(f"{stem}_preview*.png"))


def pick_engines(choice):
    order = ["latexmk", "pdflatex", "tectonic"] if choice == "auto" else [choice]
    return [e for e in order if have(e)]


def main():
    ap = argparse.ArgumentParser(description="Compile resume .tex and render previews.")
    ap.add_argument("tex", help="Path to resume .tex")
    ap.add_argument("--outdir", help="Output directory (default: build/ next to the .tex)")
    ap.add_argument("--dpi", type=int, default=150, help="Preview render DPI")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "latexmk", "pdflatex", "tectonic"])
    args = ap.parse_args()

    tex = Path(args.tex).expanduser().resolve()
    if not tex.is_file():
        print(json.dumps({"ok": False, "error": f"not a file: {tex}"}))
        sys.exit(1)
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else tex.parent / "build"
    outdir.mkdir(parents=True, exist_ok=True)

    engines = pick_engines(args.engine)
    if not engines:
        print(json.dumps({"ok": False, "error":
              "No LaTeX engine found. The lightest option is tectonic, one binary "
              "(`brew install tectonic`, or see tectonic-typesetting.github.io). MacTeX / "
              "TeX Live also work. Or compile on Overleaf."}))
        sys.exit(1)

    failures = []
    for engine in engines:
        if engine == "tectonic":
            ok, pdf, log, warnings = compile_tectonic(tex, outdir)
        else:
            ok, pdf, log, warnings = compile_latex(tex, outdir, engine)
        if ok:
            pages = page_count(pdf)
            if pages and pages > 1:
                warnings.append(f"Resume is {pages} pages; most resumes should be one.")
            result = {"ok": True, "pdf": str(pdf), "pages": pages, "engine": engine,
                      "previews": render_previews(pdf, outdir, args.dpi), "warnings": warnings}
            print(json.dumps(result, indent=2))
            return
        failures.append({"engine": engine, "log_tail": tail(log)})

    print(json.dumps({"ok": False, "engines_tried": [f["engine"] for f in failures],
                      "log_tail": failures[-1]["log_tail"]}, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()

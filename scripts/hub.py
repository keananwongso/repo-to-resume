#!/usr/bin/env python3
"""
hub.py - Create and find your resume hub: the folder that holds YOUR data.

The skill is installed once, globally. Your resume, CONTEXT.md, job postings and session
logs live in a separate folder (the "hub", default ~/resume) so updating the skill never
touches them. This script scaffolds that folder and finds it again from any directory.

Usage:
    python hub.py init [PATH] [--resume FILE] [--example]
    python hub.py locate [--from DIR]

init    Creates PATH (default ~/resume) with CONTEXT.md, jobs/, logs/, inspo/, build/, and
        remembers it in ~/.config/repo-to-resume/config.json. Never overwrites a file.
        --resume FILE copies your existing resume in; --example copies the sample resume.
locate  Prints JSON describing the hub: it checks DIR (default: cwd) and its parents for a
        CONTEXT.md first, then the remembered hub path. Lists resumes and job postings found.

Standard library only.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HUB = Path.home() / "resume"
RESUME_EXTS = {".tex", ".pdf", ".docx"}
TEXT_EXTS = {".md", ".txt"}  # counted as a resume only when "resume" is in the name
SUBDIRS = {
    "jobs": "Job postings you're targeting, one file each (e.g. google-swe-2027.md).",
    "logs": "Session logs: what changed, what was decided, what's still open.",
    "inspo": "Resumes you admire, for voice and density. Keep other people's resumes private.",
}
GITIGNORE = "build/\ninspo/\n.DS_Store\n"


def config_path():
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "repo-to-resume" / "config.json"


def read_config():
    try:
        return json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_config(data):
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def describe(hub):
    hub = Path(hub)
    resumes = sorted(str(p) for p in hub.iterdir() if p.is_file() and (
        p.suffix.lower() in RESUME_EXTS
        or (p.suffix.lower() in TEXT_EXTS and "resume" in p.name.lower())))
    jobs_dir = hub / "jobs"
    jobs = sorted(str(p) for p in jobs_dir.iterdir()
                  if p.is_file() and p.name != "README.md") if jobs_dir.is_dir() else []
    context = hub / "CONTEXT.md"
    return {
        "hub": str(hub),
        "context_md": str(context) if context.exists() else None,
        "resumes": resumes,
        "jobs": jobs,
        "logs_dir": str(hub / "logs"),
        "build_dir": str(hub / "build"),
    }


def cmd_init(args):
    hub = Path(args.path).expanduser().resolve() if args.path else DEFAULT_HUB
    hub.mkdir(parents=True, exist_ok=True)
    created, kept = [], []

    def place(dest, write):
        if dest.exists():
            kept.append(str(dest))
        else:
            write(dest)
            created.append(str(dest))

    for name, blurb in SUBDIRS.items():
        (hub / name).mkdir(exist_ok=True)
        place(hub / name / "README.md", lambda d, b=blurb: d.write_text(b + "\n", encoding="utf-8"))
    (hub / "build").mkdir(exist_ok=True)

    place(hub / "CONTEXT.md", lambda d: shutil.copyfile(SKILL_DIR / "templates" / "CONTEXT.md", d))
    place(hub / ".gitignore", lambda d: d.write_text(GITIGNORE, encoding="utf-8"))

    if args.resume:
        src = Path(args.resume).expanduser().resolve()
        if not src.is_file():
            print(json.dumps({"ok": False, "error": f"resume not found: {src}"}))
            sys.exit(1)
        place(hub / src.name, lambda d: shutil.copyfile(src, d))
    elif args.example:
        place(hub / "resume.tex", lambda d: shutil.copyfile(SKILL_DIR / "examples" / "resume.tex", d))

    cfg = read_config()
    cfg["hub"] = str(hub)
    write_config(cfg)

    out = {"ok": True, "created": created, "kept_existing": kept,
           "config": str(config_path()), **describe(hub)}
    print(json.dumps(out, indent=2))


def find_upwards(start):
    """Nearest directory at or above `start` holding a CONTEXT.md, stopping at $HOME."""
    home = Path.home().resolve()
    cur = Path(start).resolve()
    while True:
        if (cur / "CONTEXT.md").is_file():
            return cur
        if cur == home or cur.parent == cur:
            return None
        cur = cur.parent


def cmd_locate(args):
    start = Path(args.from_dir or os.getcwd())
    found = find_upwards(start)
    if found:
        print(json.dumps({"found": True, "source": "current directory", **describe(found)}, indent=2))
        return
    hub = read_config().get("hub")
    if hub and Path(hub).is_dir():
        print(json.dumps({"found": True, "source": "config", **describe(hub)}, indent=2))
        return
    print(json.dumps({
        "found": False,
        "config": str(config_path()),
        "hint": "No resume hub yet. Run `hub.py init [PATH] [--resume FILE]` to create one "
                "(default ~/resume), or have the user paste their resume.",
    }, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Create or find your resume hub.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init", help="Create a resume hub folder")
    p_init.add_argument("path", nargs="?", help=f"Hub folder (default {DEFAULT_HUB})")
    p_init.add_argument("--resume", help="Copy this existing resume file into the hub")
    p_init.add_argument("--example", action="store_true", help="Start from the sample resume.tex")
    p_loc = sub.add_parser("locate", help="Find the hub from the current directory or config")
    p_loc.add_argument("--from", dest="from_dir", help="Directory to search from (default cwd)")
    args = ap.parse_args()
    {"init": cmd_init, "locate": cmd_locate}[args.cmd](args)


if __name__ == "__main__":
    main()

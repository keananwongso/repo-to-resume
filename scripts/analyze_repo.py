#!/usr/bin/env python3
"""
analyze_repo.py - Extract EVIDENCED, non-hallucinated facts from a code repository
so that resume bullets can be grounded in what the code actually shows.

Design principle: this script never guesses at impact. It reports only things that
are literally present in the repo (languages by line count, dependencies declared in
manifests, endpoint counts by pattern match, git history, README claims). The
judgment call of "what's resume-worthy" is left to the model reading this JSON.

Usage:
    python analyze_repo.py [PATH_OR_URL] [--author "Name or email substring"] [--json-only]

If PATH_OR_URL is omitted, the current working directory is analyzed (the common case:
"I'm standing inside the repo"). A GitHub URL is shallow-cloned to a temp dir.

Standard library only. No pip installs. Degrades gracefully when git/README/manifests
are missing.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config: what to ignore, how to map extensions, which deps signal what
# ---------------------------------------------------------------------------

IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", "out",
    "venv", ".venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    "vendor", "target", "coverage", ".expo", ".turbo", ".cache", ".parcel-cache",
    "bower_components", ".gradle", ".idea", ".vscode", "Pods", ".dart_tool",
    "migrations/versions", ".terraform", "site-packages",
}

# extension -> language label
EXT_LANG = {
    ".py": "Python", ".ipynb": "Jupyter Notebook",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++",
    ".hpp": "C++", ".cs": "C#", ".swift": "Swift", ".m": "Objective-C",
    ".scala": "Scala", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sass": "SCSS",
    ".vue": "Vue", ".svelte": "Svelte", ".r": "R", ".jl": "Julia",
    ".sol": "Solidity", ".lua": "Lua",
}

# Extensions we treat as "real code" for scale metrics (excludes markup/style/config)
CODE_LANGS = {
    "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "Kotlin", "Ruby",
    "PHP", "C", "C++", "C#", "Swift", "Objective-C", "Scala", "Dart", "Elixir",
    "Vue", "Svelte", "R", "Julia", "Solidity", "Lua", "SQL",
}

# npm / pip package name -> human framework label. Presence means "declared dependency".
DEP_LABELS = {
    # JS / TS
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt",
    "svelte": "Svelte", "@angular/core": "Angular",
    "react-native": "React Native", "expo": "Expo",
    "express": "Express", "fastify": "Fastify", "koa": "Koa", "@nestjs/core": "NestJS",
    "socket.io": "WebSockets (Socket.IO)", "ws": "WebSockets",
    "graphql": "GraphQL", "@apollo/client": "Apollo", "trpc": "tRPC", "@trpc/server": "tRPC",
    "prisma": "Prisma", "@prisma/client": "Prisma", "mongoose": "MongoDB (Mongoose)",
    "pg": "PostgreSQL", "mysql2": "MySQL", "redis": "Redis", "ioredis": "Redis",
    "@supabase/supabase-js": "Supabase", "firebase": "Firebase", "firebase-admin": "Firebase",
    "drizzle-orm": "Drizzle", "typeorm": "TypeORM", "sequelize": "Sequelize",
    "tailwindcss": "Tailwind CSS", "vite": "Vite", "webpack": "Webpack",
    "zustand": "Zustand", "redux": "Redux", "@reduxjs/toolkit": "Redux Toolkit",
    "@tanstack/react-query": "React Query", "react-query": "React Query",
    "stripe": "Stripe", "openai": "OpenAI API", "@anthropic-ai/sdk": "Anthropic API",
    "@google/generative-ai": "Google Gemini API", "langchain": "LangChain",
    "jest": "Jest", "vitest": "Vitest", "@playwright/test": "Playwright", "cypress": "Cypress",
    "electron": "Electron", "three": "Three.js", "d3": "D3.js",
    # Python
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django", "starlette": "Starlette",
    "uvicorn": "Uvicorn", "gunicorn": "Gunicorn",
    "pandas": "pandas", "numpy": "NumPy", "scipy": "SciPy",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "keras": "Keras",
    "transformers": "Hugging Face Transformers", "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn", "sqlalchemy": "SQLAlchemy", "alembic": "Alembic",
    "celery": "Celery", "pydantic": "Pydantic", "psycopg2": "PostgreSQL",
    "psycopg2-binary": "PostgreSQL", "pymongo": "MongoDB", "redis-py": "Redis",
    "pytesseract": "Tesseract OCR", "opencv-python": "OpenCV", "pillow": "Pillow",
    "requests": "requests", "httpx": "httpx", "anthropic": "Anthropic API",
    "google-generativeai": "Google Gemini API",
}

MANIFESTS = [
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Gemfile", "composer.json",
]

MAX_FILE_BYTES = 1_500_000  # skip files larger than this for LOC (likely vendored/minified)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_git(args, cwd):
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def is_url(s):
    return s.startswith(("http://", "https://", "git@")) or s.endswith(".git")


def read_text(path, limit=None):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_text(encoding="utf-8", errors="ignore")
        return data[:limit] if limit else data
    except (OSError, ValueError):
        return None


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs in place
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".") or d in {".github"}]
        rel = os.path.relpath(dirpath, root)
        if any(part in IGNORE_DIRS for part in rel.split(os.sep)):
            continue
        for fn in filenames:
            yield Path(dirpath) / fn


# ---------------------------------------------------------------------------
# Analysis passes
# ---------------------------------------------------------------------------

def analyze_languages(root):
    loc_by_lang = Counter()
    files_by_lang = Counter()
    total_code_files = 0
    total_code_loc = 0
    for f in iter_files(root):
        lang = EXT_LANG.get(f.suffix.lower())
        if not lang:
            continue
        text = read_text(f)
        if text is None:
            continue
        loc = sum(1 for line in text.splitlines() if line.strip())
        loc_by_lang[lang] += loc
        files_by_lang[lang] += 1
        if lang in CODE_LANGS:
            total_code_files += 1
            total_code_loc += loc
    ranked = []
    total_loc = sum(loc_by_lang.values()) or 1
    for lang, loc in loc_by_lang.most_common():
        ranked.append({
            "language": lang,
            "loc": loc,
            "files": files_by_lang[lang],
            "pct": round(100 * loc / total_loc, 1),
        })
    return {
        "ranked": ranked,
        "total_code_files": total_code_files,
        "total_code_loc": total_code_loc,
    }


def parse_package_json(path):
    text = read_text(path)
    if not text:
        return {}, {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}, {}
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    meta = {
        "name": data.get("name"),
        "description": data.get("description"),
        "scripts": list((data.get("scripts") or {}).keys()),
    }
    return deps, meta


def parse_python_deps(root):
    names = set()
    req = root / "requirements.txt"
    if req.exists():
        for line in (read_text(req) or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~\[ ]", line)[0].strip().lower()
            if name:
                names.add(name)
    pyproj = root / "pyproject.toml"
    if pyproj.exists():
        text = read_text(pyproj) or ""
        for m in re.findall(r'"([A-Za-z0-9_.\-]+)(?:[<>=!~].*?)?"', text):
            names.add(m.lower())
        # simple `name = "..."` style deps
        for m in re.findall(r'^\s*([A-Za-z0-9_.\-]+)\s*=\s*["\^~><]', text, re.M):
            names.add(m.lower())
    return names


def detect_frameworks(root):
    labels = []
    seen = set()

    def add(label):
        if label and label not in seen:
            seen.add(label)
            labels.append(label)

    pkg_meta = {}
    pkg = root / "package.json"
    if pkg.exists():
        deps, pkg_meta = parse_package_json(pkg)
        for dep in deps:
            if dep in DEP_LABELS:
                add(DEP_LABELS[dep])

    for name in parse_python_deps(root):
        if name in DEP_LABELS:
            add(DEP_LABELS[name])

    # ecosystem markers that aren't in the label map
    if (root / "go.mod").exists():
        add("Go modules")
    if (root / "Cargo.toml").exists():
        add("Cargo (Rust)")

    return labels, pkg_meta


def detect_infra(root):
    infra = {}
    checks = {
        "docker": ["Dockerfile", "dockerfile"],
        "docker_compose": ["docker-compose.yml", "docker-compose.yaml", "compose.yaml"],
        "vercel": ["vercel.json"],
        "netlify": ["netlify.toml"],
        "fly": ["fly.toml"],
        "heroku": ["Procfile"],
        "terraform": ["main.tf"],
    }
    for key, files in checks.items():
        infra[key] = any((root / f).exists() for f in files)

    gh_workflows = root / ".github" / "workflows"
    infra["github_actions"] = gh_workflows.is_dir() and any(gh_workflows.iterdir())

    # database signals
    db = []
    if (root / "prisma" / "schema.prisma").exists():
        db.append("Prisma schema")
    if (root / "supabase").is_dir():
        db.append("Supabase")
    for name in ("migrations", "alembic"):
        if (root / name).is_dir():
            db.append("DB migrations")
            break
    infra["database_signals"] = db
    return infra


def count_endpoints(root):
    """Heuristic endpoint count. Reports method used so the model can caveat it."""
    # Next.js style API routes as files
    file_route_dirs = [
        root / "app" / "api", root / "pages" / "api",
        root / "src" / "app" / "api", root / "src" / "pages" / "api",
    ]
    file_routes = 0
    for d in file_route_dirs:
        if d.is_dir():
            for f in iter_files(d):
                if f.name.startswith(("route.", "index.")) or f.suffix in {".ts", ".js", ".tsx", ".jsx"}:
                    file_routes += 1

    # Pattern-based routes (express / fastapi / flask)
    patterns = [
        r"\b(?:app|router)\.(?:get|post|put|patch|delete)\s*\(",   # express/fastify
        r"@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(",     # fastapi
        r"@(?:app|blueprint)\.route\s*\(",                            # flask
    ]
    pattern_routes = 0
    compiled = [re.compile(p) for p in patterns]
    for f in iter_files(root):
        if f.suffix.lower() not in {".py", ".js", ".ts", ".mjs", ".cjs"}:
            continue
        text = read_text(f)
        if not text:
            continue
        for c in compiled:
            pattern_routes += len(c.findall(text))

    method = None
    total = 0
    if file_routes:
        method = "file-based API routes (Next.js style)"
        total = file_routes
    if pattern_routes:
        method = "route handler declarations" if not file_routes else method + " + route handlers"
        total += pattern_routes
    return {"count": total, "method": method}


def count_tests(root):
    test_files = 0
    frameworks = set()
    for f in iter_files(root):
        n = f.name.lower()
        if (".test." in n or ".spec." in n or n.endswith("_test.py")
                or n.startswith("test_") or "tests" in f.parts):
            if f.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs"}:
                test_files += 1
    return {"test_files": test_files}


def git_analysis(root, author_hint=None):
    if not (root / ".git").exists():
        return {"available": False}
    count = run_git(["rev-list", "--count", "HEAD"], root)
    first = run_git(["log", "--reverse", "--format=%ai", "--max-parents=0"], root)
    last = run_git(["log", "-1", "--format=%ai"], root)
    shortlog = run_git(["shortlog", "-sne", "HEAD"], root)

    contributors = []
    if shortlog:
        for line in shortlog.splitlines():
            m = re.match(r"\s*(\d+)\s+(.*)", line)
            if m:
                contributors.append({"commits": int(m.group(1)), "who": m.group(2).strip()})

    first_date = (first or "").splitlines()[0][:10] if first else None
    last_date = (last or "")[:10] if last else None
    duration_days = None
    if first_date and last_date:
        try:
            from datetime import date
            y1, m1, d1 = map(int, first_date.split("-"))
            y2, m2, d2 = map(int, last_date.split("-"))
            duration_days = (date(y2, m2, d2) - date(y1, m1, d1)).days
        except ValueError:
            pass

    author_share = None
    if author_hint and contributors:
        total = sum(c["commits"] for c in contributors) or 1
        mine = sum(c["commits"] for c in contributors
                   if author_hint.lower() in c["who"].lower())
        if mine:
            author_share = {"commits": mine, "pct": round(100 * mine / total, 1)}

    return {
        "available": True,
        "commits": int(count) if count and count.isdigit() else None,
        "first_commit": first_date,
        "last_commit": last_date,
        "duration_days": duration_days,
        "contributors": contributors[:10],
        "contributor_count": len(contributors),
        "author_share": author_share,
    }


def parse_readme(root):
    for name in ("README.md", "readme.md", "Readme.md", "README.MD", "README.rst", "README.txt"):
        p = root / name
        if p.exists():
            text = read_text(p, limit=20000)
            if not text:
                continue
            title = None
            m = re.search(r"^#\s+(.+)$", text, re.M)
            if m:
                title = m.group(1).strip()
            # first substantial paragraph
            desc = None
            for para in re.split(r"\n\s*\n", text):
                clean = para.strip()
                if clean and not clean.startswith(("#", "!", "[![", "<", "|")) and len(clean) > 40:
                    desc = re.sub(r"\s+", " ", clean)[:400]
                    break
            # feature-ish bullets
            bullets = re.findall(r"^[-*]\s+(.{6,140})$", text, re.M)
            bullets = [re.sub(r"\s+", " ", b).strip() for b in bullets[:15]]
            # links (prefer likely live/demo), excluding badges and CI/shield hosts
            BADGE_HOSTS = ("shields.io", "codecov.io", "coveralls", "travis-ci",
                           "circleci.com", "badge", ".svg", "app.netlify.com/start")
            links = [l for l in re.findall(r"https?://[^\s)>\]]+", text)
                     if not any(b in l.lower() for b in BADGE_HOSTS)]
            live = [l for l in links if any(k in l.lower() for k in
                    ("vercel.app", "netlify.app", "herokuapp", "fly.dev", "onrender",
                     "demo", "live", ".co", ".io", ".app")) and "github.com" not in l]
            # claimed numeric metrics -> must be human-verified, never trusted as fact
            raw_claims = re.findall(r"[^.\n]*?\b\d[\d,]*\+?\s?(?:%|k\b|users|requests|conversations|"
                                    r"items|endpoints|ms|seconds|daily|players|downloads)[^.\n]*",
                                    text, re.I)
            NOISE = ("collected", "passed", "failed", "[", "]", "coverage:", "====",
                     "pytest", "|", "shield", "badge")
            claims = []
            for c in raw_claims:
                c = re.sub(r"\s+", " ", c).strip()[:160]
                if len(c) < 12 or any(n in c.lower() for n in NOISE):
                    continue
                claims.append(c)
            claims = claims[:12]
            return {
                "found": True, "title": title, "description": desc,
                "feature_bullets": bullets, "live_links": live[:5],
                "claimed_metrics_UNVERIFIED": claims,
            }
    return {"found": False}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Extract evidenced facts from a repo for resume generation.")
    ap.add_argument("target", nargs="?", default=".", help="Local path or GitHub URL (default: current dir)")
    ap.add_argument("--author", help="Substring of your git name/email to compute your commit share")
    ap.add_argument("--json-only", action="store_true", help="Print only JSON, no summary")
    args = ap.parse_args()

    tmp = None
    target = args.target
    url_name = None
    if is_url(target):
        url_name = re.sub(r"\.git$", "", target.rstrip("/").split("/")[-1]) or None
        tmp = tempfile.mkdtemp(prefix="repo2resume_")
        clone = subprocess.run(
            ["git", "clone", "--depth", "200", target, tmp],
            capture_output=True, text=True
        )
        if clone.returncode != 0:
            print(json.dumps({"error": "git clone failed", "detail": clone.stderr[:500]}))
            sys.exit(1)
        root = Path(tmp)
    else:
        root = Path(target).resolve()
        if not root.is_dir():
            print(json.dumps({"error": f"not a directory: {root}"}))
            sys.exit(1)

    langs = analyze_languages(root)
    frameworks, pkg_meta = detect_frameworks(root)
    infra = detect_infra(root)
    endpoints = count_endpoints(root)
    tests = count_tests(root)
    git = git_analysis(root, args.author)
    readme = parse_readme(root)

    result = {
        "repo_name": pkg_meta.get("name") or readme.get("title") or url_name or root.name,
        "package_description": pkg_meta.get("description"),
        "languages": langs,
        "frameworks_and_libraries": frameworks,
        "infrastructure": infra,
        "api_surface": endpoints,
        "testing": tests,
        "git": git,
        "readme": readme,
        "_notes": (
            "Everything here is EVIDENCED from the repo. 'claimed_metrics_UNVERIFIED' "
            "and README text are the project's own claims and must be human-confirmed "
            "before appearing on a resume. Do NOT invent usage/impact numbers not present here."
        ),
    }

    print(json.dumps(result, indent=2))

    if tmp:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

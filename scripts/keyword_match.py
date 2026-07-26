#!/usr/bin/env python3
"""
keyword_match.py - Compute JD-vs-resume keyword coverage, the way Simplify's panel does.

Given a job description and a resume, report which target keywords the resume already
covers, which are missing, split into high vs low priority, with an overall match %.
This is deterministic and taxonomy-driven so it doesn't hallucinate keywords.

Usage:
    python keyword_match.py --jd JD.txt --resume resume.tex [--repo-json repo.json]

Resume may be .tex, .txt, .md, or .pdf (needs `pdftotext` for PDF).
If --repo-json (output of analyze_repo.py) is passed, each MISSING keyword is annotated
with whether the analyzed repo could truthfully support it, so you know which gaps are
closable with real evidence versus which you simply don't have.

Standard library only.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Skill taxonomy: canonical -> aliases (all matched case-insensitively, word-bounded).
# Deliberately skill-focused. Brand mentions like "Google Ads" are intentionally NOT
# here: they show up in JDs as prose ("from Google Ads to Chrome") and aren't things a
# candidate can truthfully add, so chasing them is noise.
# ---------------------------------------------------------------------------

TAXONOMY = {
    # languages
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java"],
    "C": [r"\bc\b(?![+#])"],
    "C++": [r"c\+\+", "cpp"],
    "C#": [r"c#", "c-sharp", "csharp"],
    "Go": ["golang", r"\bgo\b"],
    "Rust": ["rust"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "Scala": ["scala"],
    "SQL": ["sql"],
    "R": [r"\br\b"],
    # frameworks / libs
    "React": ["react"],
    "React Native": ["react native"],
    "Next.js": ["next.js", "nextjs"],
    "Node.js": ["node.js", "nodejs", r"\bnode\b"],
    "Express": ["express"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Spring": ["spring boot", "spring"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "Tailwind CSS": ["tailwind"],
    # infra / cloud / tools
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Azure": ["azure"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery", "github actions"],
    "Git": [r"\bgit\b"],
    "Linux": ["linux"],
    "Unix": ["unix"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "GraphQL": ["graphql"],
    "REST": ["rest api", "restful", r"\brest\b"],
    "Kafka": ["kafka"],
    "Spark": ["spark"],
    # concepts
    "data structures": ["data structures"],
    "algorithms": ["algorithms"],
    "machine learning": ["machine learning", r"\bml\b"],
    "AI": ["artificial intelligence", r"\bai\b"],
    "natural language processing": ["natural language processing", "nlp"],
    "distributed systems": ["distributed", "parallel systems", "distributed and parallel"],
    "web application development": ["web application", "web app development", "web development"],
    "mobile application development": ["mobile application", "mobile app development"],
    "information retrieval": ["information retrieval"],
    "networking": ["networking"],
    "security": ["security software", r"\bsecurity\b"],
    "troubleshooting": ["troubleshooting", "debugging", "code-level troubleshooting"],
    "automation": ["automate", "automation"],
    "scalability": ["scalable", "scalability", "massive scale"],
    "system design": ["system design", "large software systems", "large-scale"],
}


def compile_aliases(aliases):
    pats = []
    for a in aliases:
        if a.startswith(r"\b") or "\\" in a or a in {r"c\+\+", r"c#"}:
            pats.append(re.compile(a, re.I))
        else:
            pats.append(re.compile(r"\b" + re.escape(a) + r"\b", re.I))
    return pats


CANON_PATTERNS = {canon: compile_aliases(al) for canon, al in TAXONOMY.items()}


def present_in(text, canon):
    return any(p.search(text) for p in CANON_PATTERNS[canon])


def count_in(text, canon):
    return sum(len(p.findall(text)) for p in CANON_PATTERNS[canon])


# ---------------------------------------------------------------------------
# Resume text extraction
# ---------------------------------------------------------------------------

def strip_latex(tex):
    tex = re.sub(r"%.*", "", tex)                         # comments
    tex = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", tex)  # commands + optional args
    tex = re.sub(r"[{}$&~^\\]", " ", tex)                 # residual latex chars
    return re.sub(r"\s+", " ", tex)


def read_resume(path):
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        try:
            out = subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True, timeout=30)
            return out.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(json.dumps({"error": "pdftotext not available; pass a .tex/.txt resume"}))
            sys.exit(1)
    text = p.read_text(encoding="utf-8", errors="ignore")
    return strip_latex(text) if suffix == ".tex" else text


# ---------------------------------------------------------------------------
# Priority: high if it appears in a required/minimum region OR is emphasized (>=2x).
# ---------------------------------------------------------------------------

def split_required_preferred(jd):
    lower = jd.lower()
    pref_idx = None
    for marker in ("preferred qualifications", "nice to have", "bonus", "preferred:"):
        i = lower.find(marker)
        if i != -1:
            pref_idx = i
            break
    if pref_idx is None:
        return jd, ""
    return jd[:pref_idx], jd[pref_idx:]


def repo_supports(canon, repo):
    """Does the analyzed repo contain truthful evidence for this keyword?"""
    if not repo:
        return None
    hay = " ".join([
        json.dumps(repo.get("frameworks_and_libraries", [])),
        " ".join(l.get("language", "") for l in repo.get("languages", {}).get("ranked", [])),
        json.dumps(repo.get("infrastructure", {})),
        json.dumps(repo.get("api_surface", {})),
    ]).lower()
    return present_in(hay, canon)


def main():
    ap = argparse.ArgumentParser(description="JD vs resume keyword coverage.")
    ap.add_argument("--jd", required=True, help="Path to job description text file")
    ap.add_argument("--resume", required=True, help="Path to resume (.tex/.txt/.md/.pdf)")
    ap.add_argument("--repo-json", help="Optional analyze_repo.py JSON to check gap closability")
    args = ap.parse_args()

    jd = Path(args.jd).read_text(encoding="utf-8", errors="ignore")
    resume = read_resume(args.resume)
    repo = None
    if args.repo_json:
        try:
            repo = json.loads(Path(args.repo_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            repo = None

    required_region, preferred_region = split_required_preferred(jd)

    covered, missing_high, missing_low = [], [], []
    for canon in TAXONOMY:
        if not present_in(jd, canon):
            continue  # not a target keyword for this JD
        in_required = present_in(required_region, canon)
        emphasized = count_in(jd, canon) >= 2
        priority = "high" if (in_required or emphasized) else "low"
        if present_in(resume, canon):
            covered.append({"keyword": canon, "priority": priority})
        else:
            entry = {"keyword": canon, "priority": priority}
            sup = repo_supports(canon, repo)
            if sup is not None:
                entry["repo_can_support"] = sup
            (missing_high if priority == "high" else missing_low).append(entry)

    total = len(covered) + len(missing_high) + len(missing_low)
    high_total = len([c for c in covered if c["priority"] == "high"]) + len(missing_high)
    high_covered = len([c for c in covered if c["priority"] == "high"])
    low_total = len([c for c in covered if c["priority"] == "low"]) + len(missing_low)
    low_covered = len([c for c in covered if c["priority"] == "low"])

    result = {
        "match_pct": round(100 * len(covered) / total, 0) if total else 0,
        "high_priority": {"covered": high_covered, "total": high_total},
        "low_priority": {"covered": low_covered, "total": low_total},
        "covered": [c["keyword"] for c in covered],
        "missing_high_priority": missing_high,
        "missing_low_priority": missing_low,
        "_notes": (
            "Only add a missing keyword to the resume if it is TRUTHFUL. When --repo-json "
            "is provided, 'repo_can_support': true means the analyzed repo contains real "
            "evidence for that keyword, so the gap is honestly closable. Never keyword-stuff."
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

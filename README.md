# repo-to-resume

Turn a codebase into **honest, ATS-aware resume content** — bullets grounded in what the code
actually shows, never invented metrics. Paste a job description to see keyword coverage, and
optionally have your LaTeX resume surgically edited and previewed in place.

It works as a [Claude Code](https://claude.com/claude-code) skill **and** as standalone Python
scripts you can run yourself.

## Why it's different: the honesty contract

A resume tool that fabricates is actively harmful — you have to defend every line in an
interview. So this one:

- **Grounds every bullet in evidence** pulled from the repo (stack, endpoints, git history,
  tests, infra) rather than guessing.
- **Never invents a number.** README claims and unprovable figures are flagged for you to
  confirm, not silently asserted.
- **Distinguishes "built" from "contributed to"** using your real share of commits.
- **Flags honest gaps** instead of keyword-stuffing: if a JD wants a language none of your
  repos show, it says so and asks whether you have another repo or coursework for it.

## What's in here

```
scripts/
  analyze_repo.py     # pull evidenced facts from a repo (stack, endpoints, git, tests)
  keyword_match.py    # JD-vs-resume keyword coverage (match %, high/low priority, gaps)
  render_resume.py    # compile a .tex resume to PDF + preview PNG
references/
  latex-editing.md    # the surgical in-place .tex editing method
guides/
  phrasing-guide.md   # the bullet register (the 8 rules) — strong defaults
  industry-vocab.md   # worked example: build a role-specific vocabulary guide
CONTEXT.template.md   # scaffold for your persistent working memory (copy → CONTEXT.md)
inputs/               # drop your resume.tex + job-description.md here (gitignored)
  resume.example.tex          # runnable fictional sample
  job-description.example.md  # runnable fictional sample
inspo/                # drop resume PDFs you admire (gitignored)
build.sh              # compile a resume: ./build.sh inputs/resume.tex
SKILL.md              # the Claude Code skill definition
```

## Requirements

- **Python 3** (standard library only — no `pip install`).
- For compiling/previewing a LaTeX resume: a TeX engine
  ([`tectonic`](https://tectonic-typesetting.github.io/) is a single binary and the lightest;
  MacTeX / TeX Live also work), plus `pdftoppm` (from poppler) or macOS `sips` for PNG previews.
- Optional: `pdftotext` (poppler) so `keyword_match.py` can read a `.pdf` resume directly.

## Use it as a Claude Code skill

Copy the skill into your skills directory and invoke it by name:

```bash
mkdir -p ~/.claude/skills/repo-to-resume
cp -R SKILL.md scripts references ~/.claude/skills/repo-to-resume/
```

Then, standing inside any repo, ask Claude Code:

- `/repo-resume` — or "turn this repo into resume bullets"
- "how well does my resume match this JD" (paste the JD)
- "tailor my resume to this role and preview it" (point at your `.tex`)

## Use it standalone (no Claude Code)

From a clone of this repo:

```bash
# 1. What does a repo actually show? (evidenced facts as JSON)
python3 scripts/analyze_repo.py /path/to/your/repo --author "Your Name" > repo.json

# 2. How well does a resume cover a job description?
python3 scripts/keyword_match.py \
    --jd inputs/job-description.example.md \
    --resume inputs/resume.example.tex \
    --repo-json repo.json

# 3. Compile a LaTeX resume to PDF + preview PNG
./build.sh inputs/resume.example.tex
#   or:  python3 scripts/render_resume.py inputs/resume.example.tex --outdir build
```

The three commands above run against the **shipped example files**, so you can see the whole
loop work before adding any of your own data.

## Make it yours

1. `cp CONTEXT.template.md CONTEXT.md` and fill in your standing preferences and hard facts.
   The skill reads this first each session, and it overrides the default style rules.
2. Put your real resume at `inputs/resume.tex` and a target posting at
   `inputs/job-description.md`.
3. Drop resumes you admire into `inspo/`.

All of those (`CONTEXT.md`, your real `resume.tex`/`job-description.md`, `inspo/*.pdf`, and the
`build/` output) are **gitignored** — so if you work inside this repo, your personal data is
never committed. Only the `.example.` files are tracked.

## License

MIT — see [LICENSE](LICENSE).

# repo-to-resume

Your code already proves what you built. This turns it into resume bullets that are actually
true — you just ask Claude, in plain English.

No made-up metrics. Every bullet traces back to real evidence in your repo, and anything it
can't prove gets flagged for you to confirm. Because you have to defend every line in an
interview.

## Get started

**1. Install it (one time).** Clone it straight into your Claude Code skills folder — the
skill has to live under `~/.claude/skills/` to be discovered, so clone it right there:

```bash
git clone https://github.com/keananwongso/repo-to-resume.git \
  ~/.claude/skills/repo-to-resume
```

Restart Claude Code once and it picks up the `/repo-resume` skill automatically. (No
`pip install` — the scripts use only the Python standard library.)

<sub>Prefer to keep the repo in your normal projects folder? Clone it anywhere, then either
symlink it in (`ln -s /path/to/repo-to-resume ~/.claude/skills/repo-to-resume`) or launch
with `claude --add-dir /path/to/repo-to-resume`.</sub>

**2. Give it your resume.** Drop your resume into the skill's `inputs/` folder — `.tex`,
`.pdf`, or `.md`, whatever you have. (Or just paste it into the chat.) Same for a job posting
you're targeting.

**3. Talk to Claude.** Open Claude Code inside any project and say what you want:

> "turn this repo into resume bullets"
>
> "how well does my resume match this job?" *(paste the posting)*
>
> "tailor my resume to this role and show me the preview"
>
> "what keywords am I missing for this job?"

That's it. It reads your code, checks it against the job, and writes honest bullets you can
actually stand behind.

---

## Not using Claude Code?

The same thing runs as plain Python scripts (standard library, nothing to install). From a
clone of the repo:

```bash
# Turn a repo into evidenced facts
python3 scripts/analyze_repo.py /path/to/your/project --author "Your Name"

# How well does a resume match a job posting?
python3 scripts/keyword_match.py --jd inputs/job-description.md --resume inputs/resume.tex

# Compile a LaTeX resume to PDF + preview
./build.sh inputs/resume.tex
```

Want to see it work first? The repo ships a fictional resume + job posting, so this runs out
of the box:

```bash
python3 scripts/keyword_match.py \
    --jd inputs/job-description.example.md \
    --resume inputs/resume.example.tex
```

## What's inside

```
scripts/
  analyze_repo.py     # evidenced facts from a repo (stack, endpoints, git, tests)
  keyword_match.py    # JD-vs-resume keyword coverage (match %, priority, gaps)
  render_resume.py    # compile a .tex resume to PDF + preview PNG
guides/
  phrasing-guide.md   # how to write bullets that land (the 8 rules)
  industry-vocab.md   # example: build a vocabulary guide for a target industry
references/
  latex-editing.md    # the surgical in-place .tex editing method
CONTEXT.template.md   # scaffold for your persistent notes → copy to CONTEXT.md
inputs/               # your resume + job posting go here (gitignored)
inspo/                # resumes you admire go here (gitignored)
```

Your real files (`resume.tex`, `job-description.md`, anything in `inspo/`) are gitignored, so
working inside the repo never commits your personal data.

## Requirements

- **Python 3** — standard library only, nothing to `pip install`.
- To compile a LaTeX resume: a TeX engine ([`tectonic`](https://tectonic-typesetting.github.io/)
  is the lightest — one binary; MacTeX / TeX Live also work), plus `pdftoppm` (poppler) or
  macOS `sips` for the PNG preview.
- Optional: `pdftotext` (poppler) so keyword matching can read a `.pdf` resume directly.

## Why "honest" is the whole point

- Bullets are grounded in repo evidence, not guesses.
- It never states a usage, latency, or adoption number that isn't proven or confirmed by you.
- It tells "built" from "contributed to" using your real share of commits.
- If a job wants a skill none of your repos show, it says so — instead of keyword-stuffing.

Make it yours: copy `CONTEXT.template.md` to `CONTEXT.md` and jot your standing preferences and
hard facts. Claude reads it first each session, and it overrides the defaults.

## License

MIT — see [LICENSE](LICENSE).

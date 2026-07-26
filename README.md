# repo-to-resume

Point it at a codebase, get resume bullets that are actually true — grounded in what the
code shows, with no made-up metrics. Paste a job description and it tells you which keywords
you hit and which you're missing. It can even edit your LaTeX resume in place and show you the
result.

The whole idea: **never fabricate.** Every bullet traces back to real evidence, and anything
it can't prove gets flagged for you to confirm — not silently invented. Because you have to
defend every line in an interview.

## Try it in 30 seconds

Clone it and run the example (a fictional resume + job posting ship with the repo):

```bash
git clone https://github.com/keananwongso/repo-to-resume.git
cd repo-to-resume

# How well does this resume match this job?
python3 scripts/keyword_match.py \
    --jd inputs/job-description.example.md \
    --resume inputs/resume.example.tex
```

You'll get a match %, the keywords you cover, and the ones you're missing (high vs low
priority). That's the core loop.

## Use it on your own stuff

1. **Turn a repo into bullets:**
   ```bash
   python3 scripts/analyze_repo.py /path/to/your/project --author "Your Name"
   ```
   It reads your stack, endpoints, tests, and git history, then you (or Claude) write honest
   bullets from that — never from thin air.

2. **Check your resume against a real job:** drop the posting in `inputs/job-description.md`
   and your resume in `inputs/resume.tex`, then run `keyword_match.py` like above.

3. **Compile + preview a LaTeX resume:**
   ```bash
   ./build.sh inputs/resume.tex
   ```

Your real files (`resume.tex`, `job-description.md`, anything in `inspo/`) are gitignored, so
working inside the repo never commits your personal data.

## Using Claude Code? Even easier

Install it as a skill and just talk to it:

```bash
mkdir -p ~/.claude/skills/repo-to-resume
cp -R SKILL.md scripts references ~/.claude/skills/repo-to-resume/
```

Then, standing in any repo: *"turn this repo into resume bullets"*, *"how well does my resume
match this JD?"*, or *"tailor my resume to this role and preview it."*

---

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
inputs/               # your resume.tex + job-description.md go here (gitignored)
inspo/                # resumes you admire go here (gitignored)
```

## Requirements

- **Python 3** — standard library only, nothing to `pip install`.
- To compile a LaTeX resume: a TeX engine ([`tectonic`](https://tectonic-typesetting.github.io/)
  is the lightest — one binary; MacTeX / TeX Live also work), plus `pdftoppm` (poppler) or
  macOS `sips` for the PNG preview.
- Optional: `pdftotext` (poppler) so keyword matching can read a `.pdf` resume directly.

## The honesty contract

This is the part that makes it worth using:

- Bullets are grounded in repo evidence, not guesses.
- It never states a usage, latency, or adoption number that isn't proven or confirmed by you.
- It tells "built" from "contributed to" using your real share of commits.
- If a job wants a skill none of your repos show, it says so — instead of keyword-stuffing.

Make it yours: copy `CONTEXT.template.md` to `CONTEXT.md` and jot your standing preferences and
hard facts. The skill reads it first each session and it overrides the defaults.

## License

MIT — see [LICENSE](LICENSE).

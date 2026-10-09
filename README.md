# repo-to-resume

Your code already proves what you built. This turns it into resume bullets you can defend
in an interview.

A Claude Code skill. Point it at a repo and it reads what's actually there: the stack, the
endpoints, the tests, the git history, how much of it you wrote. Then it writes bullets
from that evidence, checks them against the job you want, and edits your LaTeX resume in
place.

**Honest by construction.** Every bullet traces back to something in the repo. Numbers
the code can't prove get flagged for you to confirm, never invented.

---

## Install

Once, globally. It works in every project after that.

```
/plugin install repo-to-resume --marketplace keananwongso/repo-to-resume
```

Or clone it straight into your skills folder:

```bash
git clone https://github.com/keananwongso/repo-to-resume.git ~/.claude/skills/repo-to-resume
```

Restart Claude Code. Nothing to `pip install`, the scripts are plain Python.

## Set up your hub

The skill is the tool. Your resume lives somewhere else, in a folder that's yours:

```
~/resume/
  resume.tex       your resume
  CONTEXT.md       your rules and hard facts, read every session
  jobs/            postings you're targeting
  logs/            what changed each session, and what's still open
  inspo/           resumes you admire
  build/           compiled PDFs and previews
```

Ask Claude to *"set up my resume hub"* and point it at your current resume. It creates the
folder and remembers where it is. Updating the skill never touches it.

## Use it

Open Claude Code anywhere and say what you want.

> "turn this repo into resume bullets"
>
> "how well does my resume match this job?" *(paste the posting)*
>
> "tailor my resume to this role and show me the preview"
>
> "what keywords am I missing?"

Inside a code repo it pulls evidence from that repo. Inside your hub it works on your
resume. Either way it reads your `CONTEXT.md` first.

---

## Why it exists

Most resume tools write what sounds good. Then you're in an interview defending a 40%
number you never measured.

This one works the other way round. It starts from what the code shows and only claims
that. It tells "built" from "contributed to" using your real share of commits. If a job
wants a skill none of your repos show, it says so instead of stuffing the keyword in.

`CONTEXT.md` is where it gets good. Every correction you make ("never say containment",
"that number was disproven") goes in there, and it holds you to it next time. After a few
sessions it writes like you.

---

## Shape

```
SKILL.md                  what Claude follows
scripts/
  analyze_repo.py         evidence from a repo: stack, endpoints, git, tests
  keyword_match.py        resume vs job posting: match %, priority, gaps
  render_resume.py        .tex to PDF, page count, preview PNG
  hub.py                  creates and finds your hub
guides/
  phrasing-guide.md       the register strong resumes write in
  industry-vocab.md       example of a vocabulary guide for one industry
references/
  latex-editing.md        the surgical in-place edit method
templates/CONTEXT.md      starting point for your rules
examples/                 a fictional resume and job posting
```

## Requirements

- **Python 3.** Standard library only.
- **A TeX engine** to compile a LaTeX resume. [`tectonic`](https://tectonic-typesetting.github.io/)
  is the lightest, one binary (`brew install tectonic`). MacTeX and TeX Live work too.
- **poppler** (`pdftoppm`, `pdftotext`) for previews and reading PDF resumes. On macOS,
  `sips` covers the preview if poppler isn't there.

## Without Claude Code

The scripts run on their own from a clone:

```bash
python3 scripts/analyze_repo.py /path/to/project --author "Your Name"
python3 scripts/keyword_match.py --jd examples/job-description.md --resume examples/resume.tex
python3 scripts/render_resume.py examples/resume.tex
```

## License

MIT. See [LICENSE](LICENSE).

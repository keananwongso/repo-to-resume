---
name: repo-to-resume
description: >
  Turn a codebase into tailored, honest, ATS-aware resume content, and optionally edit
  and preview a LaTeX resume in place. Use this whenever the user is inside (or points
  at) a GitHub repo and wants resume bullets, a projects entry, or experience bullets
  generated from what the code actually shows. Also use when the user pastes a job
  description and wants a keyword-coverage match (which target keywords their resume
  hits and misses, high vs low priority, like Simplify), or wants their .tex resume
  surgically edited to close gaps and then compiled to a PDF preview. Triggers:
  "/repo-resume", "turn this repo into resume bullets", "generate resume content from
  this project", "how well does my resume match this JD", "tailor my resume to this job",
  "edit my latex resume for this role", "what keywords am I missing". Prefer this skill
  over free-handing bullets or eyeballing keyword match, because it grounds every claim
  in evidence pulled from the repo and computes coverage deterministically instead of
  guessing.
allowed-tools: Bash(python3 *) Bash(latexmk *) Bash(pdflatex *) Bash(pdftoppm *)
---

# Repo to Resume

Generate resume-ready project and experience bullets from a real codebase, tailored to
a target job and deduped against an existing resume. The whole point is to be **honest
and specific**: bullets are grounded in evidence the analyzer pulls from the repo, and
anything that needs a real-world number the code can't prove is flagged for the user to
fill in rather than invented.

This skill assumes the common case: the user is standing inside the repo and pastes in
some subset of {job description, target role(s), current resume}. Any of those can be
missing. Use whatever is provided; do not block on the rest.

## Running the bundled scripts

The three scripts live in this skill's own directory, not the user's project. The
working directory is the user's repo, so always invoke them by their skill-directory
path. In Claude Code and plugin installs this is `${CLAUDE_SKILL_DIR}/scripts/<name>.py`;
that variable expands to wherever the skill is installed. All examples below use it.
Scripts are Python 3, standard library only, so no install step is needed.

Not on Claude Code? The same scripts run standalone from a clone of this repo — just
call `python3 scripts/<name>.py ...` from the repo root instead of the
`${CLAUDE_SKILL_DIR}` path. See the README for the standalone quickstart.

## The three tools

- `scripts/analyze_repo.py` — pulls evidenced facts from a repo (stack, endpoints, git
  history, README claims). The grounding for bullets.
- `scripts/keyword_match.py` — computes JD-vs-resume keyword coverage (match %, high/low
  priority, covered/missing), and flags which missing keywords a repo can truthfully
  support. The targeting lens and the "Simplify-style" view.
- `scripts/render_resume.py` — compiles a `.tex` resume to PDF and renders preview PNGs.
  The "view."

Bullet generation (below) uses the first. If the user has a job description and/or a
`.tex` resume and wants matching or in-place editing, run the full tailoring loop in the
section "Tailoring loop with keyword match and LaTeX editing."

## Workflow (bullet generation)

### 1. Run the analyzer

Run the bundled script against the repo. Default to the current directory (the user is
usually already in the repo); accept a path or a GitHub URL if they gave one.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_repo.py [PATH_OR_URL] [--author "their name or email"]
```

Pass `--author` with a substring of the user's git identity when known (e.g. their
GitHub name or email). It computes their share of commits, which is what separates an
honest "built X solo" from "contributed to X" on a team repo. If you don't know it,
run without it and note that solo-vs-team is unconfirmed.

The script prints JSON. Read it fully. Everything in it is evidenced from the repo
**except** the `readme.*` fields and `claimed_metrics_UNVERIFIED`, which are the
project's own claims and must be human-confirmed before they land on a resume.

### 2. Gather targeting context

Look at what the user pasted:

- **Job description present** → extract the role's priorities: required stack, the
  verbs and nouns it repeats, the kind of impact it rewards (scale, reliability,
  velocity, ownership, ML depth, etc.). These become the lens. Mirror its exact keyword
  spellings where they're truthful for the repo (this is the ATS surface).
- **Target role(s) present** but no full JD → use the role to decide emphasis (e.g.
  FDSE rewards customer-facing systems + breadth + shipping; ML roles reward the
  training/eval loop; infra roles reward reliability and scale).
- **Current resume present** → read it to (a) match the user's existing bullet voice
  and tense, (b) avoid repeating stack lines or phrasing already there, and (c) find
  the strongest *new* angle this repo adds that the resume doesn't already cover.
- **Nothing pasted** → produce strong general-purpose bullets and then ask the 2-3
  highest-leverage questions (see step 4) to sharpen them.

### 3. Synthesize bullets from evidence

Write 2-4 bullets for the project. Each bullet must trace back to something in the JSON
or to a metric the user confirms. Follow the style rules below.

Map evidence to bullets like this:

- `frameworks_and_libraries` + `languages.ranked` → the honest stack line and the
  technical nouns. Lead with the languages/frameworks the JD actually asks for.
- `api_surface.count` → "N endpoints/routes" only when method is credible; caveat that
  it's a heuristic if the user asks.
- `git.commits`, `git.duration_days`, `git.author_share` → scope and ownership. A 24hr
  hackathon with 200 commits is a velocity story; a solo repo over months is an
  ownership story. Use `author_share` to choose "built" vs "contributed to" honestly.
- `git.contributor_count` → team size ("lead on a team of 4"), if the user confirms
  their role.
- `testing.test_files`, `infrastructure` (Docker, CI, deploy target) → engineering
  maturity signals (deployed, tested, CI'd) when present.
- `readme.claimed_metrics_UNVERIFIED` + `readme.live_links` → candidate impact
  numbers and proof-of-shipping, but ONLY after the user confirms them.

### 4. Output: bullets + a verification block

Present, in this order:

1. **Project line** — `Name | one-line what-it-is | stack line (JD-relevant first)`.
   Include the live link if the repo has one.
2. **Bullets** — 2-4, ready to paste.
3. **Grounding** — a short list mapping each bullet to its evidence, so the user can
   trust it (e.g. "endpoints: 40 route handlers detected"; "solo: 91% of commits").
4. **Confirm before using** — any number that came from the README or that the code
   can't prove, listed as things to verify.
5. **Questions to unlock stronger bullets** — at most 3, only for impact numbers the
   user alone knows (real users, conversion, latency in prod, adoption). Never fill
   these with guesses.

## Style rules (match these exactly)

These are strong defaults for resume writing, distilled from resumes that landed offers
(see `guides/phrasing-guide.md`). Hold to them by default, and adapt them to any standing
preferences the user records in their own `CONTEXT.md` — that file, when present, wins over
these defaults.

- **Nouns describe systems, verbs describe the engineer.** "Architected a real-time
  sync layer" not "worked on real-time features." The system is the noun; what the
  engineer did to it is the verb.
- **Impact over effort.** What the system does or enables, not how hard it was. Not
  "spent weeks debugging the payment flow" but "hardened the payment flow, eliminating
  the class of double-charge failures."
- **No vendor-specific or internal jargon.** Prefer the general capability over a
  product name a reader won't know. Name a specific technology only when it is a real
  keyword for the target role.
- **Every bullet earns its number, but no invented numbers.** Prefer an evidenced
  count (endpoints, commits, contributors, LOC scale, dataset size) over a vague
  adjective. If there's no honest number, lead with the system and its function
  instead of padding with a fake percentage.
- **One to two lines each.** Tight. Cut throat-clearing ("responsible for",
  "helped with", "worked on").
- **Match the tense and voice of the existing resume** when one is provided.
- Avoid em dashes and hyphenated connectors in the bullet text; write clean sentences.

**Before → after examples (the target register):**

Weak: "Made a mobile app for a hackathon using React Native."
Strong: "Built Lockout, a React Native focus app with a five-state Zustand state
machine and on-device Gemini Vision verification, shipped end to end in a 24-hour
build as team lead."

Weak: "Worked on backend API with lots of endpoints."
Strong: "Designed a 40-route FastAPI service backed by PostgreSQL, with a 23-file test
suite and containerized deploy, exposing auth, profiles, and content feeds."

## Tailoring logic

When a job description is present, the ranking of what to surface changes. Decide
emphasis from the JD, not from what's most impressive in the abstract:

- Pull the JD's required and preferred stack. If the repo genuinely uses it, that stack
  leads the project line and appears verbatim (ATS).
- Echo the JD's framing of value. A JD centered on "customer-facing" and "ownership"
  (e.g. Palantir FDSE) rewards bullets about shipping a working system to real use and
  owning it end to end. A JD centered on "scale" and "reliability" rewards throughput,
  uptime, and test/CI signals.
- Do not claim a technology the JD wants that the repo does not contain. If it's
  missing, say so in the questions block so the user can decide whether they have
  another repo that shows it.

This skill produces the raw, grounded bullets. If you have other resume skills installed
(for ATS/format passes, section placement, metric-finding, or final line polish), compose
with them: this skill supplies the honest, evidence-backed bullets; those refine and place
them.

## Tailoring loop with keyword match and LaTeX editing

When the user has a job description and wants coverage analysis, and especially when they
have a `.tex` resume they want edited in place and previewed, run this loop:

1. **Match.** Run the keyword analyzer:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/keyword_match.py --jd JD.txt --resume resume.tex --repo-json repo.json
   ```
   (`repo.json` is saved analyze_repo.py output; omit if not analyzing a repo.) Present
   the result the way the user expects to see it: overall match %, high-priority X/Y,
   low-priority X/Y, then covered vs missing. For each missing keyword, note whether the
   repo can truthfully support it (`repo_can_support`). Brand-name mentions in a JD (e.g.
   "Google Ads") are intentionally not chased; they aren't truthfully addable.

2. **Decide honest edits.** Missing keywords with `repo_can_support: true`, or that the
   user confirms from real experience, are the closable gaps. Missing keywords nothing
   can back (e.g. a JD wanting C/C++/Java/DSA when every repo is JS/TS web work) get
   named plainly, with a question about whether the user has another repo, coursework, or
   experience that shows them. Never keyword-stuff.

3. **Edit the `.tex` surgically.** Apply changes as minimal string replacements to
   individual content lines only, never a rewrite and never the preamble. Read
   `references/latex-editing.md` for the exact method: locating anchors, which macros
   hold editable content, escaping LaTeX special characters, and page-fit awareness.

4. **View.** Compile and preview:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/render_resume.py resume.tex --outdir build
   ```
   Show the returned preview PNG inline. If it overflowed one page, tighten. If compile
   failed, read `log_tail`, fix the offending line, recompile.

5. **Re-score and report.** Re-run `keyword_match.py` on the edited resume and show
   before to after coverage, what changed, what's still missing and why, and any numbers
   still needing confirmation.

Full details of the LaTeX editing method and the compile/view step live in
`references/latex-editing.md`.

## The honesty contract (do not break)

A resume tool that fabricates is actively harmful to the user, who has to defend every
line in an interview. So:

- Never state a usage, revenue, conversion, latency, or adoption number that is not
  either in the analyzer output as evidence or explicitly confirmed by the user.
- README numbers are claims, not facts. Route them through "Confirm before using."
- If ownership is ambiguous (no `--author` share), write "contributed to" and flag it,
  rather than defaulting to "built."
- It is better to ship a bullet with a real system and no percentage than a bullet with
  an invented percentage. The user can always add a true number in step 5.

## Edge cases

- **Bare repo / thin README / no git** → still generate from languages, frameworks, and
  file structure; lean harder on the questions block for impact.
- **Monorepo or many services** → summarize the whole, then offer one bullet per major
  service if the user wants.
- **Fork or tutorial-heavy repo** → check `git.author_share`; if the user's share is
  tiny, say so honestly and suggest it may not be resume-worthy on its own.
- **Huge repo** → the analyzer prunes vendored dirs and caps large files; trust its
  ranked languages over raw impressions.

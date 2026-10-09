# CONTEXT.md — persistent memory for your resume hub

This file lives in your resume hub and is the hub's working memory. The skill reads it first
each session so it doesn't re-ask what you've already decided, and adds to it when you state
a new rule. Delete the guidance in each section as you replace it with your own.

Whatever you record here **overrides the skill's default style rules**.

Last updated: <date>

## Standing style preferences

Your personal resume-writing rules — the corrections you find yourself repeating. Examples of
the *kind* of thing that lives here (replace with your own):

1. Bullet length: e.g. "max two lines, mostly one; one focus per bullet."
2. Numbers policy: which numbers are worth including, and the rule that unknown numbers become
   `[FILL: ...]` placeholders rather than invented ones.
3. Stack in bullets vs. skills line: e.g. "no stack parentheticals in bullets; the skills
   section carries the stack."
4. Bolding convention, vendor-name handling, opener verbs you like/dislike, etc.

## Hard facts (do not violate)

The non-negotiable truth of your background — the guardrails against fabrication. For example:

- Languages you can honestly claim (and will interview in). List the ones you can NOT claim, so
  they never get added to close a keyword gap.
- Which repos/projects are solo vs. team, and your rough commit share on each — this decides
  "built" vs. "contributed to" honestly.
- Metrics you have personally confirmed as real (and the source/definition of each), plus any
  numbers that were disproven and must never come back.

## Target + strategy

- Target role(s) / companies for this cycle.
- Which guide(s) apply (e.g. a role-specific vocab guide like `guides/industry-vocab.md`).
- Any known gaps to close before applying (a missing language, a project you still need).

## Toolchain

- How you compile: e.g. `render_resume.py resume.tex` → `build/resume.pdf` + preview PNG.
- Where the final application PDF is produced (e.g. Overleaf for real icons).
- What "show me the resume" should do.

## Open items

- [ ] Track decisions still pending, numbers awaiting confirmation, and TODOs for the next
      session here so nothing gets silently dropped.

# Phrasing guide — the register to hold every bullet to

Distilled from strong software-engineering resumes (offers at top companies) plus recruiter
research. These are defaults; if your own `CONTEXT.md` records different preferences, those
win. The point of every rule below is the same: sound specific and true, never inflated.

## The 8 rules

1. **Outcome first, metric in the first ~6 words.** `[Result verb] + [metric] + by/with + [system] + [stack]`.
   > "Reduced on-call escalations by 80% with a Java Spring service orchestrating MCP workflows via Python."
2. **Two numbers per bullet: the improvement AND the arena.** The arena number proves it wasn't a toy.
   > "Reduced compute costs by up to 90% ... across a platform serving 200M+ functions."
3. **Name the architecture pattern, not the app.** "sidecar", "container runtime", "write-ahead logging",
   "ingestion pipeline" — the noun proves you know what you built. Never "a tool" or "a system".
4. **Enumerate the specific toil deleted, in domain vocabulary.**
   > "eliminating manual service key fetching, endpoint polling, and base64 decoding" — cheapest authenticity signal.
5. **Narrate the diagnosis: symptom → root cause → intervention → result.**
   > "Diagnosed poor site performance (LCP) caused by eager loading of large components, improving page speed 10x by introducing server-side rendering..."
6. **Denominate in money or human time when possible.** $ > % > nothing. "saving 6,000 hours/week".
7. **Show the raw arithmetic behind one percentage.** "by 26%, reducing build time from 34 minutes to 25 minutes" — vaccinates the whole resume against made-up-number suspicion.
8. **No metric? Substitute concrete artifact counts / named deliverables — never adjectives.**
   > "Authored a 44-page design document", "wrote DynamoDB migration scripts to port registration data".

## Verb tiers
- **Result verbs** lead metric bullets: Reduced, Cut, Saved, Accelerated, Scaled, Slashed.
- **Craft verbs** lead system bullets: Architected, Engineered, Built, Implemented, Diagnosed, Authored.
- Never: Worked on, Helped, Assisted, Responsible for, Participated in.

## The AI framing rule
AI terms (LLM, RAG, embeddings, NLP) sit in the **instrument slot** of the sentence; the
**subject/outcome slot** holds an ops/business metric. Nobody writes "AI-powered" about their
own work. Example of the register:
> "Automated backporting of 100+ Android and Linux kernel CVEs monthly using Python, Git, and LLMs."
(LLMs = third item in a tool list.) The engineering claim is the guarantee around the model
("structured output validation, retry/fallback handling"), never the model itself. "Built a
LangChain chatbot" hurts; "NLP ingestion pipeline with retry/fallback holding a high
automated-completion rate" reads as engineering.

## Anti-patterns (absent from strong resumes)
No summary/objective section. No soft-skill claims. No buzzword adjectives (robust, seamless,
cutting-edge). No responsibility-listing. No proficiency levels in skills. No hedging
("helped improve", "aimed to"). No claiming the whole product — scope narrowed honestly
("key components of", "solo developed").

## How resumes actually get screened (recruiter research)
- ATS checks baseline quals (degree, location, grad date); then a **human recruiter reads it**
  in ~6–15 seconds. Third-party "match %" scores are that tool's scraper, not the employer's.
- A durable formula: **"Accomplished X as measured by Y, by doing Z"** (Laszlo Bock, Google).
- Brand-name keywords in a JD (e.g. a specific ad product) are often scraping artifacts of JD
  boilerplate — don't chase them.
- Never list a language you can't interview in; you get interviewed in what you claim.
- For interns: real production experience > projects > GPA; the transcript is uploaded anyway,
  so listing GPA is fine.
- AI-heavy work helps **only** framed as engineering: shipped systems, evals, cost/latency
  awareness, fallback handling.

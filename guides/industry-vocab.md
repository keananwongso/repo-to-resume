# Building a role-specific vocabulary guide (worked example: conversational / agentic AI)

Recruiters and hiring managers in a given space read for *their* vocabulary. Phrasing true
work in the target industry's exact terms is a cheap, honest ATS-and-human win — as long as
every term has a real referent in your work.

**This file is an example, not a fixed rulebook.** It shows how to build a vocab guide for
one space (conversational / agentic customer-experience AI, as used by companies like Decagon
and Sierra). To target a different space (infra, ML platform, fintech, data), research that
industry's product pages, engineering blogs, and live job posts, and build your own version
the same way. Then apply the **honesty guard** at the bottom.

## The core nouns (this space)
- **AI agent / customer-facing agent** — never "chatbot" (the legacy thing they replace)
- **Agent builds** — the unit of forward-deployed work: "end-to-end execution of AI agent builds"
- **Agentic logic** — "the core agentic logic governing agent behavior"
- **Orchestration** — "routing, execution logic, tool orchestration, and control-plane systems"
- **Goals and guardrails** — "layered guardrails" (brand voice, escalations, hallucinations)
- **Escalation / handoff** — routing a conversation to a human when needed
- **Grounding** — RAG framed as knowledge: "integrate proprietary knowledge — FAQs, policies, catalogs"
- **Tool calling / secure actions** — agent "pulls live data and triggers workflows" via APIs
- **Multi-step workflows** — actions completed "within a single conversation"
- **Evals / regression testing** — "validate agent behavior against ground truth and guard against drift"
- **Simulations** — testing agents against simulated conversations and mock APIs
- **Execution traces / root-cause analysis** — "diagnose failures through root-cause analysis of execution traces"
- **Non-deterministic** — the defining challenge: "impose determinism on a fundamentally non-deterministic technology"
- **Pilot → production** — "complete ownership from initial pilot through deployment and iteration"

## The metrics (exact industry naming)
| Metric | Meaning | Notes |
|---|---|---|
| **Resolution rate** | Issue actually solved by the agent | Often THE billing/impact metric |
| **Containment rate** | % of conversations handled without reaching a human | Industry standard |
| **Deflection rate** | % of contacts never reaching a human | Related to containment |
| **CSAT** | Quality counterweight, always paired with resolution | — |
| **Handle time / cost per resolution** | The $ a resolution replaces | Case-study framing |

Typical real-world numbers for calibration: resolution 65–95%, CSAT 4.5–4.8/5. Use these to
sanity-check your own numbers, not to borrow them.

## Verbatim register samples (from live job posts / blogs)
- "Own end-to-end architecture and execution of AI agent builds for enterprise customers, from systems design and initial scoping through implementation, evaluation, and production deployment."
- "Design and engineer the core agentic logic governing agent behavior, applying engineering principles to optimize quality, reliability, and correctness across non-deterministic model outputs."
- "Partnering directly with customers to build and ship AI agents that handle thousands of conversations a day."
- "Design evaluation and regression-testing frameworks to validate agent behavior against ground truth and guard against performance drift."
- "Diagnose, debug, and resolve both probabilistic and technical failures through root-cause analysis of execution traces, error logs, and model behavior."

## Verb pairs the space favors
"build and ship" · "design, build, and deploy" · "productionize" · "hone agent performance" ·
"own from pilot through launch" · "ground responses in"

## Honesty guard (applies to ANY vocab guide you build)
Only use a term if your actual work had that thing. Guardrails, escalation/handoff, eval
suites, simulations, resolution/containment rates each need a real referent — a system you
built, a number you can defend, an outcome you can point to. If you can prove containment but
not a resolved-outcome number, claim containment and leave resolution off until you have the
figure. A term you can't back is exactly the term an interviewer will probe.

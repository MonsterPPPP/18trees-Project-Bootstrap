<p align="center">
  <img src="./assets/banner.webp" alt="十八木" width="100%" />
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong>
</p>

# 18trees-Project-Bootstrap

**The human states requirements while looking at the project map; the Agent opens branches, changes code, and passes independent review, by the rules.**

A **personally customized Bootstrap**: it integrates a four-layer semantic map, sub-agent collaboration discipline, and four proven upstream skill specs into one usable project initialization.

For Coding Agents that support skills (Codex / Claude Code). The human describes only the goal; the Agent handles installation, understanding, modification, testing, independent review, and queue-based merging.

> A personal Bootstrap that integrates a four-layer semantic map, a review-gated sub-agent workflow, and four proven upstream skills into one initialization. Installed non-invasively into existing codebases.

---

## What Problem It Solves

You have a project you've been writing for a long time. You want to let an AI Agent help you change things, but:

- **It doesn't know what your project looks like** — it re-reads the code every time, and you still have to talk to it in file paths and class names
- **It changes places it shouldn't** — you want to say "just change this part," but you can't articulate what "this part" corresponds to in the code
- **No one checks independently after the change** — it says "done," and you can't tell whether it's right
- (Incidentally: many tools also stuff files into your repo — skills directories and config files all become part of your commit history)

Project Bootstrap does three things about that:

1. **Draws a semantic map of the project** — four layers: Product / Feature / Capability / System. You point at the map and say "change this," and the Agent maps it to the implementation
2. **Sets a discipline for collaboration** — one branch per task, automatically launched independent review, serialized queue-based merging, role boundaries put in writing
3. **Brings in good specs** — the interaction, coding, and engineering specs each come from four proven upstream skills; it does not invent another set

Then you just talk:

> Change the login failure message so users know how to retry.

---

## Our Contributions

### 1. Humans drive code changes by looking at the map

**This is the project's most central interaction paradigm.**

Most Agent tools make people issue commands in engineering language: file paths, function names, module structure. You have to know what the code looks like before you can say clearly what to change — and that is exactly the reason you wanted to hand the work to AI.

This project projects the codebase into a **four-layer semantic map**:

```text
Product  →  Feature / User Flow  →  Capability  →  System / Technical Layer
    ↑ Human speaks here                             ↑ Agent maps it to the implementation
```

The map's first entry point is the **Product / Feature Workflow**, not a file tree and not a conventional architecture diagram. **Humans mainly operate the top three layers**, saying "modify Auth / Session Management" or "change the login failure message"; the Agent locates the technical path.

This has several direct consequences:

- **No need to remember file paths or class names.** You speak at the product semantic layer; the Agent finds the landing point at the technical layer.
- **Boundaries are pointable.** Saying "only modify NODE:X" is a hard boundary — the Agent must not cross it; if other nodes need to be involved, it must stop and explain, and wait for you to redefine. This is far more executable than saying "don't change too much."
- **One manifest, two readers.** Rendered as offline, browsable HTML for humans, and at the same time an index for the Agent to locate the implementation.
- **The source-of-truth chain is one-directional.** `Codebase → Semantic Project Manifest → HTML Project Map`. Paths and class names go only into metadata; they never pollute the layer humans read.

### 2. Agent collaboration discipline: one branch per task + mandatory independent review

This is the project's main output on the **engineering process** side, and the biggest thing that separates it from "just add an AGENTS.md for your Agent."

**The full chain for one task:**

```text
Human issues the task
      │
      ▼
Coding Agent ── create Task Branch off latest main ── implement + test
      │
      ▼
Automatically launch Review Subagent (no human trigger needed)
      │
      ├── PASS ──────────────► Merge Queue
      │                              │
      └── REQUEST_CHANGES            Serialized in Ready order
              │                     sync latest main → integration check → Merge → delete branch
              ▼
   Coder fixes → retests → re-Review in a fresh context
```

**Every change gets its own branch.** `feat/<task>`, `fix/<task>`, `refactor/<task>`, `chore/<task>` — one branch, one clear task, deleted after merging. **The Coding Agent is forbidden from directly modifying, committing to, or pushing `main`.**

**Review is the default action, not an optional step.** Every development task automatically launches a Review Subagent, and **Coder self-review cannot substitute for it**.

**The Reviewer works in an independent, clean context** and inherits none of the Coding Agent's chat, reasoning, or prior conclusions. It receives only five kinds of material:

| Delivered to the Reviewer | Content |
| --- | --- |
| Original task and acceptance goals | Verbatim text and success criteria |
| Semantic Node and change boundary | Node, normal / Strict, allowed behavior, shared impact |
| Current code diff | Bound to base / head SHA |
| Test results | Command, exit code, results for the corresponding head, **unverified items** |
| Specs | ponytail and Project Bootstrap specs |

**The Reviewer is read-only.** It does not change code, resolve conflicts, commit, or merge. It outputs only two verdicts:

```text
PASS
Reason: <evidence for requirements, boundary, minimal implementation, tests/regression, sync judgment>
Change requests: none
```

```text
REQUEST_CHANGES
Reason: <specific non-conformities and evidence; "there is risk" alone is not acceptable>
Change requests: <verifiable fix or supplementary-evidence requirements; does not authorize widening the boundary>
```

**When evidence is insufficient, REQUEST_CHANGES is the only option; guessing approval is not allowed.** Writing "don't let the AI say 'looks fine'" into a protocol is more reliable than putting it in a prompt.

**Five review items**: original requirements and scope (including Strict Node Boundary) → ponytail minimal implementation → STS behavior guard → tests and regression → semantic sync.

**The Merge Queue serializes.** Queue order is "first Ready, first queued" — **not by branch creation time**. Ready = development complete + this branch's tests pass + Review PASS. Anything queued later must be re-verified against the latest `main`; **that earlier Review PASS is not grounds for unconditional merging**.

**Conflicts are not handed to the Reviewer to fix.** When integration fails: `Queue FAIL → remove from queue → return to the original Coding Agent → re-adapt against latest main → test → re-Review → re-queue`. The Review Agent must not modify anything directly.

**Role boundaries, set in stone:**

| Role | Responsible for | Not responsible for |
| --- | --- | --- |
| Coding Agent | Implementation, tests, fixes, conflict resolution | Approving its own review, directly modifying / pushing `main` |
| Review Agent | Independent review, `PASS` / `REQUEST_CHANGES` | Modifying code, adapting conflicts, executing merges |
| Merge Queue | Serialization, syncing latest main, final integration verification, merging and cleaning up branches | Fixing failed implementations in place of the Coder, bypassing Review |
| Human | Issuing tasks, setting boundaries; final Merge when explicitly requested | Repeated Review or Merge by default |

**By default, the human does not carry the repetitive Review and Merge work.** To merge yourself, just add `require human merge` — this switch only changes who owns the final merge; it does not exempt anything from independent review, testing, or the serialization requirement.

The full ten-section spec, the contract the Reviewer can execute independently, and synthetic `PASS` / `REQUEST_CHANGES` examples are in the [interface spec](docs/interface-spec.md).

**This is not a spec on paper — this repository's own history ran on exactly this process.** Every feature landing completed "task branch → independent review → merge":

```text
*   4351362 merge: land Gateway Flow after independent review
|\
| * 21a051a docs: record Gateway Flow acceptance and isolate reviewer context
|/
*   d3dbb27 merge: land deployment policy after independent review
|\
| * 69cd7ee docs: record deployment policy acceptance evidence
|/
*   172cca4 merge: land STS and local-only bootstrap after review
|\
| * 44e8c73 fix: reject shared-worktree local exclusions before writes
|/
*   1381c53 merge: land agent-first bootstrap after independent review
|\
| * 936ed07 fix: atomically preserve rules and Git config on failed install
|/
```

All four merges are annotated with independent review; each one has its own task branch and its own set of commits.

> Note: what this project delivers is a **behavioral spec**. It does not automatically configure branch protection, permissions, or CI / queue services on your hosting platform. Server-side enforcement must be configured by you on the remote — this is listed among the weaknesses below.

### 3. Bringing in proven specs (as an integrator)

This project **does not invent new specs**. It selects four proven upstreams and orchestrates them into one set that works together:

| Layer | Upstream | What this layer governs |
|---|---|---|
| **Interaction spec** | [i-have-adhd](https://github.com/ayghri/i-have-adhd) | How each reply is organized: actions first, numbered steps, progress every turn, concrete times, visible results |
| **Coding spec** | [ponytail](https://github.com/DietrichGebert/ponytail) | How to implement as small as possible: new code, new abstractions, new dependencies and blast radius |
| **Engineering spec** | [Stop That Shit](https://github.com/lennney/stop-that-shit) | When to stop adding more: scope creep, useless defense, intent overreach, going in circles on a task |
| **Visualization** | [archify](https://github.com/tt-a1i/archify) | Rendering and validation of the four-layer semantic map |

**Integration itself is the work.** These four upstreams are independent of each other, have different interfaces, and never reference one another in their text. Making them work together within one process — where each one's applicable boundary lies, which standard the Reviewer reviews against, what to do when an upstream is missing, whose word wins on conflict — and freezing those conclusions into initialization templates, is this project's main output.

What initialization produces is not a few placeholder files but a collaboration environment you can start working in immediately:

| Category | What gets installed |
|---|---|
| **Coding spec** | ponytail's minimal-implementation principles, thresholds for new dependencies and new abstractions, blast-radius judgment |
| **Interaction spec** | i-have-adhd's output structure: actions first, numbered steps, progress restated every turn, concrete times, visible results |
| **Engineering spec** | Stop That Shit's four S/H/I/T categories and their judgment order; Strict Node Boundary; the Reviewer's review items |
| **Configuration conventions** | Git workflow (branch naming, Review Gate, Merge Queue, `require human merge`), Deployment Mode, thin entry point and loading mechanism |

All of these conclusions are written into the target project's `AGENTS.md` and project skill, loaded directly by new sessions, so **you don't have to re-explain the rules**.

So this project **deliberately adds no competing coding spec**: it defines no code style, no test spec, no directory conventions. When good specs already exist, use the ones that exist; this project's job is to make them work together.

### 4. Accompanying feature: non-invasive, reversible installation

The previous three are active capabilities; this one is the precondition that lets them **cost you nothing**.

Tracked / staged diff is unchanged before and after installation; a plain `git status` shows no added Bootstrap entries. **Git conditional configuration** confines the effect to the workspace where it was installed — **it does not change the shared `info/exclude`, the global Git config, or `.gitignore`**. To commit the specs along with the project, explicitly choose Standard mode.

And it is **reversible**: `deinit` restores the original exclude bytes, restores the thin entry point's original content, and keeps your task changes. For existing files, the thin entry point only **appends its own marked block**; it does not modify tracked `AGENTS.md` / `CLAUDE.md`.

### What It Doesn't Do (by design)

- **No code generation.** It builds the collaboration environment; it does not write business implementations for you.
- **No server-side configuration.** It installs no CI, configures no branch protection, and stands up no Merge Queue service.
- **No multi-agent orchestration.** That is ruflo's territory.
- **No spec generator.** That is spec-kit / OpenSpec's territory.

### Weaknesses (brief)

- **Claude Code client behavior acceptance is not complete** — only Codex's new-session loading has actually been verified. This is "untested", not "passed".
- **Server side and semantic layer unverified**: no remote configuration, branch protection and hosted Merge Queue have not been tested in practice; semantic facts such as Strict Node Boundary and map sync are still judged by the Agent, and the tooling does not prove them automatically.
- **Full acceptance was done only on Windows** (Python 3.12.7 / Node.js 24.12.0 / archify 2.15.0).
- **Git exclude is not an enforced commit blocker**; `git add -f` bypasses it. It also depends on the four upstream skills.
- **0 stars, a new project**, with few real-machine usage cases so far.

The complete boundaries are recorded item by item in [docs/verification.md](docs/verification.md) — it explicitly marks which items were not verified and which were synthetic walkthroughs.

---

## Installation

Send this in the target project's Coding Agent chat:

> Using this repository, initialize Project Bootstrap in the current project: `https://github.com/MonsterPPPP/18trees-Project-Bootstrap`. Make it local-only, do not bring Bootstrap files into Git; preserve the project's existing rules; when done, tell me how to use it.

The Agent will read [INSTALL.md](INSTALL.md) and run the whole flow — prepare dependencies, understand the project, generate the map, validate the installation.

### Prerequisites

Python 3.12+, Node.js 22+, Git, and [archify](https://github.com/tt-a1i/archify). When dependencies are missing, the Agent prepares an isolated environment in a cache directory outside the project — **nothing is written into your project**.

### ⚠️ Web-based chatbots cannot use this project

**It executes commands on your machine**: cloning source, creating a venv, running `bootstrap.py init`, modifying the workspace's local Git configuration, generating map files. Web-based ChatGPT / Gemini / DeepSeek / Kimi / Doubao have no tool capability and cannot do any of this.

What you need is a **Coding Agent that can execute shell commands and read/write files** (Codex / Claude Code, or equivalent).

To judge whether a project can be used by pasting, look at whether it **needs to execute commands or access the filesystem**:

| Type | Examples | Paste into a web-based chatbot |
|---|---|---|
| Pure text transformation | Writing, translation, review | ✅ Works |
| Needs to execute commands / access the filesystem | This project, deployment, running tests | ❌ Doesn't work; tool capability is required |

The same organization's [18trees-AI-writing-skill](https://github.com/MonsterPPPP/18trees-AI-writing-skill) is the former and can be used by pasting; this project is the latter and cannot.

---

## Usage

After installation, continue in the same chat:

1. **Understand the project** — "Tell me what this project can do and open the project map."
2. **Request a change** — "Change the login failure message so users know how to retry."
3. **Bound the scope** — "Only modify NODE:X; if other nodes need to be involved, stop and explain first."
4. **Check the result** — "Tell me what was done and how to verify it." By default it queues for merge after independent Review passes; to merge yourself, add `require human merge`.
5. **Exit** — "Remove the Bootstrap from the current project, keeping my task changes."

See the [human manual](MANUAL.md) for details.

**Default is Local-only + Local-first**: the Bootstrap stays on this machine; production release requires explicit authorization.

---

## Repository Structure

```text
.
├── README.md / MANUAL.md / INSTALL.md / AGENTS.md   Entry documentation
├── bootstrap.py                     CLI: init / map / validate / verify-install / deinit
├── docs/
│   ├── interface-spec.md            Interface spec (four-layer map, source-of-truth chain, Gateway Flow, Deployment)
│   ├── toolchain.md                 Tool contract: schema, conflict policy, validation boundaries
│   └── verification.md              Acceptance records and verification boundaries
├── schema/                          JSON Schema for the manifest
├── templates/                       Templates written into the target project at initialization
├── skills/project-interface/        Project skill installed into the target project along with initialization
├── examples/synthetic.manifest.json Synthetic four-layer example (no business implementation)
└── tests/                           Toolchain tests, `python -m unittest discover -s tests -v`
```

This repository delivers only specs, templates, the skill, and the toolchain; **all examples are synthetic data with no business implementation**.

---

## Development

```bash
python -m unittest discover -s tests -v
```

The engineering follows ponytail, and the development process follows the Gateway Flow defined in this repository's [AGENTS.md](AGENTS.md). Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.

---

## Comparison with Similar Projects

This ecosystem is already very mature; we are very small. Here is the full picture, so you can judge which one to use.

**Data as of 2026-09-20; stars are a snapshot from that day.**

| Project | Stars | What it is |
|---|---:|---|
| [github/spec-kit](https://github.com/github/spec-kit) | **138,043** | Structured process and reusable templates for coding agents (spec / plan / tasks / implement) |
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (formerly claude-flow) | 72,908 | Agent orchestration: multi-agent swarms and autonomous coordination |
| [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 69,643 | Spec-driven development, advocating fluid not rigid, iterative not waterfall |
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53,267 | Agile AI Driven Development, covering the whole path from an idea or change request to running software |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 11,590 | Human-in-the-loop approval in complex codebases |
| [steipete/agent-rules](https://github.com/steipete/agent-rules) | 5,686 | A collection of rules and knowledge for Claude Code / Cursor |
| [buildermethods/agent-os](https://github.com/buildermethods/agent-os) | 5,430 | Extracts existing standards from a codebase and injects them on demand |
| [michaelshimeles/skills](https://github.com/michaelshimeles/skills) | 1,032 | AGENTS.md workflow templates + worktree isolation + evidence chain |
| **This project** | **0** | Map-driven interaction + collaboration discipline + integration of proven specs, installed into **existing projects** without leaving a trace |

### How to Choose

| Your situation | Recommendation |
|---|---|
| You want to add a spec layer before the generation flow, so the Agent writes things out clearly before acting | spec-kit / OpenSpec |
| You want a complete agile methodology with role division (PM / architecture / dev / QA) | BMAD |
| You want multi-agent swarm orchestration | ruflo |
| You want the Agent to learn the standards and conventions your codebase already has | agent-os |
| You want to insert human approval at key points | humanlayer |
| **You want to command changes by looking at the map even without understanding the code structure, and you want mandatory independent review** | **This project** |
| You are still building a brand-new project with no legacy baggage | Any of the above; probably all more suitable than this project |

**In one sentence**: most of them answer "how to give the Agent better specs"; this project answers "**how a human commands changes without reading the code, and why every change must pass independent review**".

## License

[MIT](LICENSE) © 2026 十八木

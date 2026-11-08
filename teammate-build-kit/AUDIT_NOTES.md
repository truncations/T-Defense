# AUDIT_NOTES

Checked on 2026-11-07. **Verified** means confirmed in an official or primary source. **Rejected** means the source contradicts the claim, or we dropped it from the plan. **Unverified** means we couldn't confirm it; the plan has a fallback.

Inputs audited: `scam_defense_handoff_for_claude_code_pro.md` (teammate handoff, called **TH**), the build-kit prompt (**BK**, which replaces the planner's earlier handoff), and the T-Mobile brief pasted by the planner (**TM**). T-Mobile's actual starter files were **not available**, so every fact about them is Assumed until Stage 0.

## Event and track

| ID | Claim | Source of claim | Status | Evidence |
|---|---|---|---|---|
| C1 | Track is T-Mobile "Safe Signal"; criteria are creativity, impact, usability, security and privacy, detection accuracy | TM, TH | Verified | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C2 | T-Mobile provides a synthetic message set, a taxonomy and a baseline classifier | TM | Verified (stated on the track page); contents Unverified | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C3 | Hacking 12:00 pm Sat Nov 7; Devpost draft 11:00 pm; submissions due 12:00 pm Sun Nov 8; judging 1–4 pm | — | Verified (the page says times may change) | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C4 | Teams may enter up to three sponsor tracks plus one HackUTD track | — | Verified via a search summary of the Devpost page; we couldn't open the rules page (HTTP 403) | [hackutd-zeroday.devpost.com](https://hackutd-zeroday.devpost.com/) |
| C5 | No general event rule restricts AI tools or LLMs; Safe Signal only requires synthetic data | BK question | Unverified (Devpost rules returned 403; the event page lists none) | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C6 | Using sponsor tools doesn't affect Safe Signal prize eligibility | BK question | Verified that the track page lists no tool requirement; Unverified for the general rules | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C7 | Judging is in person, about 2 minutes per team | Assumed | Unverified for 2026; 2025 reportedly used in-person judging | Search summary of 2025 coverage; confirm with organizers |
| C8 | Judge said extensions add friction; prefers in-network or background | BK, TH | Team-stated (not verifiable) | — |

## Product honesty

| ID | Claim | Source | Status | Evidence |
|---|---|---|---|---|
| C10 | A carrier can't read end-to-end encrypted messages; don't claim carrier-level visibility | TH, BK | Verified as a design constraint by definition of end-to-end encryption; kept as a hard pitch rule | TH section 9; BK |
| C11 | Scam pages may behave differently for automated browsers, so a clean scan isn't proof of safety | TH section 7 | Unverified as a measured fact; adopted as a conservative design rule ("No warning signs found", never "safe") | TH section 7 |
| C12 | Forwarding a scam text to 7726 (SPAM) reports it to the carrier | Planner add | Verified (carrier and state court pages) | [AT&T support](https://www.att.com/support/article/my-account/KM1212535/), [Texas courts](https://txcourts.gov/media/how-to-report-scam-text-messages/) |
| C13 | Card `4242 4242 4242 4242` is a widely published test number; SSN `000-00-0000` is never issued | Planner add | Assumed (common knowledge); used only as an obviously fake canary on our own pages | — |

## Browser automation

| ID | Claim | Source | Status | Evidence |
|---|---|---|---|---|
| C20 | Playwright browser contexts are isolated (own cookies, local storage, session storage), "incognito-like" | TH | Verified | [Playwright: browser contexts](https://playwright.dev/python/docs/browser-contexts) |
| C21 | Contexts are not a security sandbox | TH section 7 | Verified (the docs present them as test isolation and never call them a sandbox), so we added the allowlist and network block | Same as C20 |
| C22 | Install: `pip install playwright` / `pytest-playwright`, then `playwright install` (one browser can be named) | TH | Verified for pip and `playwright install`; Chromium-only install is Verified via a third-party guide | [Playwright intro](https://playwright.dev/python/docs/intro) |
| C23 | Playwright OS support: Windows 11+, macOS 14+, Debian 12/13, Ubuntu 22.04/24.04 | — | Verified | [Playwright intro](https://playwright.dev/python/docs/intro) |
| C24 | Playwright's async API inside Uvicorn on Windows can fail with subprocess `NotImplementedError` (event-loop type) | Planner add | Unverified (known community issue); the plan avoids it with the sync API in a worker thread | — |
| C25 | `localhost` and `127.0.0.1` count as different origins | Planner add | Assumed (standard same-origin definition: scheme + host + port) | — |

## Codex tooling

| ID | Claim | Source | Status | Evidence |
|---|---|---|---|---|
| C30 | Codex reads `AGENTS.md` (checking `AGENTS.override.md` first), from the project root down to the current folder; default combined limit 32 KiB | BK | Verified | [Codex: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |
| C31 | Codex skills are folders with `SKILL.md` in `.agents/skills` (repo) or `~/.agents/skills` | BK | Verified (the kit ships 7 project skills) | [Codex customization](https://learn.chatgpt.com/docs/customization/overview.md) |
| C32 | Add an MCP server with `codex mcp add <name> -- <command>`; list with `codex mcp list`; config in `~/.codex/config.toml` under `[mcp_servers.<name>]` | BK | Verified | [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp) |
| C33 | Context7 MCP: `codex mcp add context7 -- npx -y @upstash/context7-mcp` | — | Verified (the Codex docs' own example) | [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp) |
| C34 | `SKILL.md` must have `name` and `description` frontmatter; repo skills go in `.agents/skills`; invoke with `$name` or `/skills`; implicit invocation when the description matches; bundled `$skill-creator` | ADE request | Verified | [Codex: build skills](https://learn.chatgpt.com/docs/build-skills) |
| C35 | Custom subagents are standalone TOML files in `.codex/agents/` with required `name`, `description`, `developer_instructions`; they inherit sandbox and approval settings; parallel write-heavy work can conflict | ADE request | Verified | [Codex: subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) |
| C36 | `--sandbox workspace-write --ask-for-approval on-request` is the lower-risk local automation preset; the modes are read-only, workspace-write, danger-full-access; native Windows sandbox in PowerShell | ADE request | Verified | [Codex: sandboxing](https://learn.chatgpt.com/docs/sandboxing.md) |
| C37 | Workspace-write blocks network by default, so installs trigger an approval | — | Unverified (stated only by secondary sources); the plan works either way, because installs are approval points | [Secondary: Codex approval modes blog](https://codex.danielvaughan.com/2026/03/26/codex-cli-approval-modes-sandbox-security) |
| C38 | Playwright MCP add command: `codex mcp add playwright -- npx @playwright/mcp@latest` | — | Unverified (third-party guides; the Codex docs only link the package). Optional, with a fallback | [Playwright MCP listing](https://github.com/mcp/microsoft/playwright-mcp) |
| C39 | Codex loads `AGENTS.md` once at session start, so a restart is needed after the bootstrap; skills are probably loaded the same way | — | Verified for AGENTS.md; Assumed for skills and agents | [Codex: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |

## Stack and libraries

| ID | Claim | Source | Status | Evidence |
|---|---|---|---|---|
| C40 | React + TS + Vite + FastAPI + SQLite + Playwright is a reasonable stack | TH section 5.2 | **Rejected for this team and timeline** (too many tools for beginners in about 24 hours); replaced with FastAPI + plain HTML + Playwright | Decision in BUILD_OVERVIEW section 2 |
| C41 | FastAPI is current and maintained | — | Verified (PyPI shows releases in 2026). **No version pinned in the kit**: Codex records the installed versions | [pepy.tech/fastapi](https://pepy.tech/projects/fastapi) |
| C42 | FastAPI `TestClient` needs `httpx` | Planner | Unverified here; Codex confirms during setup | — |
| C43 | Python `venv` is built in, so no `uv` is needed | Planner | Assumed (standard library) | — |

## Scope items we dropped

| ID | Claim | Source | Status | Note |
|---|---|---|---|---|
| C50 | MutationObserver watches DOM changes and is event-driven; extensions use content scripts and a service worker | TH sections 3.2, 4 | Not re-checked: **Rejected from scope** (extension cut) | TH links MDN and Chrome docs; re-verify if the extension comes back |
| C51 | Discord message content needs a privileged intent; scraping private chats isn't acceptable | TH section 3.3 | Unverified (Discord support page returned 403); **Rejected from scope** | [Discord privileged intents](https://support-dev.discord.com/hc/en-us/articles/6207308062871-What-are-Privileged-Intents) |
| C52 | Local proxy, DNS filtering, CDP and Native Messaging are out of scope | TH section 4 | Agreed: Rejected from scope | — |

## Credits and sponsor tools

| ID | Claim | Source | Status | Evidence |
|---|---|---|---|---|
| C60 | Maritime is an event sponsor | BK | Verified | [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C61 | Maritime is a managed cloud for AI agents (isolated persistent VMs, CLI, SDKs; hosting from $1 per agent per month) | — | Verified via the YC launch page; maritime.sh couldn't be reached from here | [YC launch](https://www.ycombinator.com/launches/VQm-maritime-fully-managed-cloud-for-running-ai-agents-at-scale) |
| C62 | Each of us has $500 of Maritime credit, and what it covers | BK | **Unverified** (not on the event page) | Planner to ask the sponsor booth |
| C63 | Lovable credits: Plan mode 1 credit per message; Build mode varies (about 0.5–2 credits per edit) | — | Verified | [Lovable plans and credits](https://docs.lovable.dev/introduction/plans-and-credits) |
| C64 | Lovable syncs two-way with GitHub (one branch), and exported apps are React-based | — | GitHub sync Verified; React export Unverified (third-party) | [Lovable GitHub](https://docs.lovable.dev/integrations/github) |
| C65 | NVIDIA Brev rents GPU instances, billed per use; Brev credits are NVIDIA-track prizes | — | Verified | [Brev pricing](https://www.nvidia.com/en-us/launchables/pricing), [zeroday.hackutd.co](https://zeroday.hackutd.co/) |
| C66 | Our demo needs no GPU | Planner | Assumed until Stage 0 shows the baseline's size | — |

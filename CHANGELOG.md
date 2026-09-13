# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- `.cursor/environment.json` — minimal Cloud Agent install check (docs archive; no runtime services)
- `.gitignore` — exclude local env/secret and editor noise
- `LICENSE` — MIT License (copyright 2026 Andrew Pappas / smtp.eth)
- `CLAUDE.md` — agent routing matrix and repo-specific instructions
- `CONTRIBUTING.md` — contribution guidelines for ecosystem agents and humans
- `SECURITY.md` — vulnerability reporting and security standards
- `CHANGELOG.md` — this file
- `docs/agent-hydration.md` — Phase 1–6 hydration findings report
- `.github/ISSUE_TEMPLATE/` — bug, feature, and agent-task issue templates
- `.github/pull_request_template.md` — structured PR template
- `agentic_flows/scratchpad.txt` — agent coordination state machine
- `postmortem.md` — incident and decision log (initialized)
- `.github/workflows/ci.yml` — markdown lint and link check CI pipeline

### Changed

- CI `pull_request` trigger targets `alpha` (default branch), not `main`
- `CONTRIBUTING.md` branch strategy aligned with live default branch `alpha`

---

## [0.1.0] — 2025-12-13

### Added

- `README.md` — public archive description
- `AGENTS-v2.2.md` — agent constitution with quantum-blockchain sections
- `AGENT-PROMPTS.md` — specialist agent system prompts (4 agents)
- `GOOSE-RECIPES.md` — Goose YAML recipe templates
- `IMPLEMENTATION-GUIDE.md` — step-by-step setup guide
- `EXECUTION-SUMMARY.md` — implementation summary

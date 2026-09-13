# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- Expanded packaging validators: schema meta-check, packaging inventory,
  issue-template + Dependabot schemas, recipe/agent lock (no invented agents),
  cross-doc agent presence, CI job presence, Cursor install path refs,
  `goose run` path consistency
- `schemas/packaging-inventory.json` (+ schema), `github-issue-template.schema.json`,
  `dependabot-v2.schema.json`
- `pyproject.toml` — pytest / ruff / coverage config for validation tooling
- CI: Python 3.11/3.12 matrix, ruff, coverage gate, actionlint, JSON validation report artifact
- `schemas/` + `scripts/validate_manifests.py` + `tests/` — structural validation for documented Goose recipes, Cursor `environment.json`, GitHub custom-agent frontmatter, and known YAML configs
- `requirements-dev.txt` — jsonschema / PyYAML / pytest / pytest-cov / ruff for local + CI validation
- CI job `manifest-validate` (pytest + `scripts/validate_manifests.py`) in `.github/workflows/ci.yml`
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

- Expanded CI workflow: Python matrix, ruff, coverage, actionlint, validation artifacts
- Aligned `GOOSE-RECIPES.md` master `goose run` path with declared recipe **File**
- CI workflow renamed to cover manifest validation in addition to markdown lint/link check
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

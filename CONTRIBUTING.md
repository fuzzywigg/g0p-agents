# Contributing to g0p-agents

Status: ACTIVE | Tier: 1 | Created: 2026-04-13
Edit policy: Agent-editable; structural changes require Andrew approval

---

## Who Can Contribute

This repo is part of the FUZZYWIGG multi-agent ecosystem. Contributions come from:

- **Agent surfaces** (copilot, geryon, claude-cowork, browser-claude, playwright) — automated contributions via structured issues and PRs
- **Andrew Pappas** (owner) — architectural decisions, branch protection changes, licensing, financial decisions
- **Ecosystem collaborators** — invited contributors working on PikoClaw or related projects

## Branch Strategy

| Branch | Purpose |
| --- | --- |
| `alpha` | Default / protected. Merges require PR + review. Never push directly. |
| `copilot/<task>` | Copilot agent work — CI fixes, single-file edits |
| `geryon/<task>` | Geryon agent work — multi-file scaffolding, deep code changes |
| `claude/<task>` | claude-cowork strategic work — docs, Notion-linked content |
| `cursor/<task>` | Cursor cloud-agent work — thin docs/CI/hygiene |

## PR Requirements

1. Branch off from `alpha` using the naming convention above
2. Reference the issue number in the PR title when one exists: `Fix #12: Add LICENSE file`
3. Fill in the PR template completely
4. All CI checks must pass before merge (markdown lint, link check, actionlint, and
   manifest validate on Python 3.11/3.12/3.13)
5. One approval required (Andrew or designated reviewer)

## Local validation (docs packaging)

```bash
python -m pip install -r requirements-dev.txt
ruff check scripts tests
python scripts/validate_manifests.py --list-validators
python scripts/validate_manifests.py
python -m pytest --cov=scripts --cov-report=term-missing
```

Do not invent new specialist agents in PRs; CI locks the documented set in
`AGENT-PROMPTS.md` / `GOOSE-RECIPES.md` / `AGENTS-v2.2.md` (four agents only).
Packaging inventory v31 + `scripts/validate_manifests.py` refuse invented recipes,
orphan on-disk YAML, and unknown `*Agent` tokens.

## Issue Reporting

Use the appropriate issue template:

- **Bug** — something broken in existing files or workflows
- **Feature** — new capability needed
- **Agent Task** — structured work for a specific agent surface

All issues must include the metadata header defined in CLAUDE.md.

## Governance

Structural changes (directory reorganization, agent routing changes, license changes) require Andrew approval before merging, regardless of CI status.

See [CLAUDE.md](CLAUDE.md) for agent routing matrix and negative constraints.

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
|---|---|
| `main` | Protected. Merges require PR + review. Never push directly. |
| `copilot/<task>` | Copilot agent work — CI fixes, single-file edits |
| `geryon/<task>` | Geryon agent work — multi-file scaffolding, deep code changes |
| `claude/<task>` | claude-cowork strategic work — docs, Notion-linked content |

## PR Requirements

1. Branch off from `main` using the naming convention above
2. Reference the issue number in the PR title: `Fix #12: Add LICENSE file`
3. Fill in the PR template completely
4. All CI checks must pass before merge
5. One approval required (Andrew or designated reviewer)

## Issue Reporting

Use the appropriate issue template:
- **Bug** — something broken in existing files or workflows
- **Feature** — new capability needed
- **Agent Task** — structured work for a specific agent surface

All issues must include the metadata header defined in CLAUDE.md.

## Governance

Structural changes (directory reorganization, agent routing changes, license changes) require Andrew approval before merging, regardless of CI status.

See [CLAUDE.md](CLAUDE.md) for agent routing matrix and negative constraints.

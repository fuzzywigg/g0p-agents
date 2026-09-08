# CLAUDE.md — g0p-agents Repo Agent Instructions

Status: ACTIVE | Tier: 1 | Owner: claude-cowork
Created: 2026-04-13 | Edit policy: Agent-editable; structural changes require Andrew approval
Canonical source: This file (GitHub is truth for code/config)

---

## Repo Identity

**Repo**: fuzzywigg/g0p-agents
**Purpose**: Quantum-Blockchain agentic protocols archive (v2.2, Dec 2025).
Contains agent system prompts, Goose YAML recipe templates, and implementation
guide for the FUZZYWIGG four-agent swarm (QuantumArchitectAgent,
BlockchainArchitectAgent, EdgeSecurityAgent, OrchestrationAgent).
**North Star**: PikoClaw demo at Panathenea (Athens), May 27–29, 2026
**Status**: Documentation archive — activation into working codebase is a
pending architectural decision (see LIST B in docs/agent-hydration.md)

---

## Agent Routing Matrix

| Task | Surface | Rationale |
| ------ | --------- | ----------- |
| CI/CD fixes, linting, dependabot | copilot | Single-repo, syntax-level work |
| Multi-file code scaffolding (agentic_flows/, contracts/, quantum_circuits/) | geryon | Deep coding, long-running, 60–90 min |
| Strategic planning, Notion updates, cross-platform coordination | claude-cowork | Cross-system state, Notion truth |
| GitHub Settings, branch protection | browser-claude | UI-only settings |
| Automated E2E verification | playwright | Test automation |
| Financial transactions, repo visibility changes | human | Non-automatable |

---

## State Residency Rules

| Content Type | Owner | Others do |
| --- | --- | --- |
| Code, config, workflows | This GitHub repo | Link only |
| Policies, decisions, rollouts | Notion Tier 1 | Link only |
| Agent operating rules | Notion Tier 0 | Link only |
| Ephemeral execution context | Slack/Discord threads | Link, don't canonize |
| Reusable prompts/snippets | repo /docs/ or Gist | Notion links to it |

---

## Key Files

| File | Purpose |
| ------ | --------- |
| `AGENTS-v2.2.md` | Constitution — full agent rules and quantum-blockchain standards |
| `AGENT-PROMPTS.md` | System prompts for all 4 specialist agents |
| `GOOSE-RECIPES.md` | Goose YAML recipe templates for orchestration |
| `IMPLEMENTATION-GUIDE.md` | Step-by-step WSL2 setup guide |
| `EXECUTION-SUMMARY.md` | Dec 2025 status snapshot |
| `docs/agent-hydration.md` | Hydration findings report (this run) |
| `agentic_flows/` | Live recipe YAML files + scratchpad.txt (to be scaffolded) |

---

## Negative Constraints (no agent may autonomously)

- Push to `main` branch
- Merge own PRs on protected repos
- Delete files or repositories without human approval
- Initiate financial transactions or alter billing
- Change repo visibility (private/public)
- Modify branch protection rules
- Create public gists containing secrets or PII

---

## Escalation Format

When blocked, use this format in PR comments or Slack:

```text
🚨 ESCALATION REQUIRED
From Agent: [surface name]
Conflict: [What constraint am I hitting?]
Recommendation: [How should we resolve this?]
Timeline: [How long until decision needed?]
```

---

## Quarterly Review Triggers

- [ ] Risk tolerance update (AGENTS-v2.2.md Section 12.4.1)
- [ ] Agent success metrics audit
- [ ] Notion Master Index sync
- [ ] postmortem.md incident review

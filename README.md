# g0p-agents (archived reference)

[![CI](https://github.com/fuzzywigg/g0p-agents/actions/workflows/ci.yml/badge.svg?branch=alpha)](https://github.com/fuzzywigg/g0p-agents/actions/workflows/ci.yml)
[![link-check](https://img.shields.io/github/actions/workflow/status/fuzzywigg/g0p-agents/ci.yml?branch=alpha&label=link-check)](https://github.com/fuzzywigg/g0p-agents/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/fuzzywigg/g0p-agents)](LICENSE)

Docs-only archive of 2025 "Quantum-Blockchain" agent prompts (v2.2, Dec 2025).

**This is not a live hive, runtime, or production swarm.** The "Oracle-Style
Quantum Hive Mind" language in the historic copy below is prompt fiction. There
is no running hive mind in this tree. For current operational standards, see
[fuzzywigg/agents-standard](https://github.com/fuzzywigg/agents-standard).

## Historic prompt set

This repository contains the "Quantum-Blockchain" agentic protocols v2.2 (Dec 2025). The files describe an **Oracle-Style Quantum Hive Mind** architecture *on paper*, featuring:

1. **QuantumArchitectAgent**: Designing quantum-safe algorithms.
2. **BlockchainArchitectAgent**: Implementing multi-chain, quantum-resistant contracts.
3. **EdgeSecurityAgent**: Creating "walled garden" mobile security.
4. **OrchestrationAgent**: Managing conflicts via stimgery and YAML recipes.

## Contents

* **AGENT-PROMPTS.md**: Full system prompts for the 4 specialist agents.
* **GOOSE-RECIPES.md**: YAML-based orchestration logic (Goose Framework).
* **IMPLEMENTATION-GUIDE.md**: Step-by-step setup for a quantum-dev environment.
* **AGENTS-v2.2.md**: Historic snapshot of the agent constitution.
* **CLAUDE.md** / **CONTRIBUTING.md** / **SECURITY.md**: Repo routing, contribution, and reporting policy.

> **Note**: This is an archived reference implementation, not a live hive. For current operational standards, see the main `agents-standard` repository.

## Cloud agents

Docs-only bootstrap lives in [`.cursor/environment.json`](.cursor/environment.json) (`install` verifies key archive files; no `start` services).

## Manifest validation

This archive has no runtime agent code. CI still enforces structural checks on
documented packaging (Goose recipes, Cursor env, GitHub agent/issue frontmatter,
Dependabot, markdownlint, scratchpad, pyproject tooling, inventory v43 locks
(coverage gate 99%), PR/license/requirements/security/contributing/changelog/
postmortem/gitignore/hydration/execution-summary/implementation-guide/claude/
recipe-titles/ci-actions/issue-names/readme-badges/quarterly-review/link-check/
ci-job-names/github-agent-desc/ci-runs-on/ci-artifacts/
actionlint-shell/ci-setup-python/ci-ruff/license-mit/ci-pip-install/ci-pip-check/
ci-pytest/state-residency/key-files/pr-routing/routing-matrix/repo-identity/
escalation-format/routing-rationales/claude-metadata/escalation-usage/
security-supported/security-reporting/security-standards/
security-header/security-fips/security-known-non-issues/
changelog-format/changelog-unreleased/changelog-release/
constitution-crypto/constitution-handoff/constitution-escalation-matrix/
constitution-on-device/constitution-multichain/constitution-escalation-format/
implementation-quickstart/execution-specialists/hydration-list-b/hydration-phase1/hydration-list-a/hydration-resolved/hydration-phase4/hydration-deferred/hydration-meta/hydration-identity-detail/hydration-git-detail/hydration-phase2/hydration-phase5/
postmortem-intro/postmortem-fields/postmortem-next-steps/
scratchpad-intro/scratchpad-format/scratchpad-task-meta/
issue-metadata/issue-routing/bug-repro/
contributing-who/contributing-branches/contributing-pr/
contributing-issues/contributing-local/contributing-governance/
contributing-metadata/contributing-surfaces/contributing-ci-honesty/
pr-summary/pr-acceptance/pr-notes/
readme-honesty/readme-historic/readme-contents/
goose-howto/goose-state-machine/goose-naming/goose-recipe-headers/goose-instruction-agents/goose-extensions/goose-orchestration/goose-conflicts/goose-quantum-task,
prompt-roles/prompt-sections/prompt-usage,
implementation-phases/implementation-tools/implementation-success/
execution-timeline/execution-technologies/execution-workflow/execution-ide/execution-innovations/execution-next48, constitution
and routing and negative-constraint surfaces,
bug/feature/agent-task template headings and name/about locks, prompt
escalation locks, CI matrix permissions/fail-fast/artifact naming/action
pins/workflow name/job display names/lychee args, and locked four-agent
cross-doc consistency):

```bash
python -m pip install -r requirements-dev.txt
ruff check scripts tests
python scripts/validate_manifests.py --list-validators
python scripts/validate_manifests.py
python -m pytest --cov=scripts --cov-report=term-missing
```

Schemas and the packaging inventory live under [`schemas/`](schemas/). The
validator reads Goose recipe YAML from [`GOOSE-RECIPES.md`](GOOSE-RECIPES.md)
and does **not** invent specialist agents beyond the historic four.

## License

MIT — see [LICENSE](LICENSE).

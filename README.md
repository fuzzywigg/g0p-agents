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

This archive has no runtime agent code. CI still enforces structural checks on documented packaging:

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_manifests.py
python -m pytest -q
```

Schemas live under [`schemas/`](schemas/). The validator reads Goose recipe YAML
from [`GOOSE-RECIPES.md`](GOOSE-RECIPES.md), plus `.cursor/environment.json`,
`.github/agents/*.agent.md` frontmatter, and known YAML configs.

## License

MIT — see [LICENSE](LICENSE).

#!/usr/bin/env python3
"""Validate documented agent packaging manifests in this docs-only archive.

Checks structural correctness of:
- Goose recipe YAML fenced in GOOSE-RECIPES.md (and any agentic_flows/*.yaml)
- Locked recipe inventory (names + declared file paths + bindings; no invented workflows)
- Historic Goose settings / extension locks (no drift from archive recipes)
- Recipe name ↔ declared file bindings; orphan on-disk recipe refusal
- Documented specialist agents only (no invented agents / *Agent tokens)
- Prompt fence headers + escalation markers for historic four agents
- AGENTS-v2.2.md constitution headings for documented agents only
- AGENTS-v2.2.md constitution crypto / handoff / escalation-matrix locks
- AGENTS-v2.2.md §22.2 on-device / §22.3 multichain / §22.4.3 escalation-format locks
- AGENTS-v2.2.md §22.5 recipe-orchestration / §22.6 scratchpad-state / §22.7 conflict-matrix locks
- CONTRIBUTING.md metadata / surface-duty / CI-honesty leftover locks
- CLAUDE.md routing surfaces (packaging surfaces; not specialist agents)
- SECURITY.md / CONTRIBUTING.md packaging honesty locks
- Agent-task / bug / feature issue template headings
- Orchestration recipe must reference all documented specialists
- .cursor/environment.json (+ install path refs + locked name)
- .github/agents/*.agent.md frontmatter + locked file/name + non-empty body
- .github/ISSUE_TEMPLATE/*.md frontmatter + locked file set + non-empty body
- .github/pull_request_template.md required headings
- .github/dependabot.yml (ecosystem set + weekly schedule; no version bumps)
- .markdownlint.yaml (default + MD013 line_length locks)
- requirements-dev.txt required validation packages
- LICENSE MIT + copyright holder; README packaging / honesty phrases
- CHANGELOG / postmortem / .gitignore / CLAUDE negative-constraint locks
- CHANGELOG.md Keep a Changelog format / Unreleased / 0.1.0 release locks
- GOOSE-RECIPES.md recipe headers / instruction-agent / extension locks
- GOOSE-RECIPES.md master orchestration / conflicts / quantum-task locks
- AGENT-PROMPTS.md constraints / escalation-triggers / related-docs locks
- EXECUTION-SUMMARY.md IDE setup / innovations / next-48-hours locks
- agentic_flows/scratchpad.txt coordination markers (+ allowed file set)
- pyproject.toml validation tooling keys (+ coverage / requires-python / ruff)
- CI workflow job/step/matrix/concurrency/permissions/artifact-if presence
- Packaging inventory lock + internal consistency + schema meta-validation
- Parseability of known YAML config files
- Historic Goose recipe version lock (1.0.0)
- CLAUDE.md required sections / identity / escalation-format phrases
- Historic Goose recipe title locks (four recipes only)
- CI required GitHub Actions pins + workflow name + actionlint markers
- CI link-check lychee args/fail + markdown-lint globs/config + job display names
- CI runs-on ubuntu-latest + artifact paths/if-no-files-found + actionlint shell/id locks
- CI setup-python cache: pip + ruff check scripts/tests command locks
- CI pip install / pip check / pytest cov+junitxml command marker locks
- CLAUDE.md state-residency / key-files table locks (archive governance)
- PR template Agent Surface Routing field locks (Surface/Issue/Branch/Priority)
- CLAUDE.md Agent Routing Matrix task-row locks (six surfaces)
- CLAUDE.md Repo Identity north-star / purpose locks
- CLAUDE.md Escalation Format block field locks (banner + four fields)
- CLAUDE.md routing-matrix rationale column locks (six surfaces)
- CLAUDE.md header metadata locks (Status/Tier/Owner/Created/Edit/Canonical)
- CLAUDE.md escalation usage intro + fenced placeholder field locks
- SECURITY.md Supported Versions / Reporting / Standards domain locks
- SECURITY.md header / FIPS standards-row / Known Non-Issues rename locks
- SECURITY.md scope / reporting-channel / compliance-detail leftover locks
- AGENTS-v2.2.md §22.1 crypto / §22.4.1 handoff / §22.4.2 escalation-matrix locks
- AGENTS-v2.2.md §22.2 on-device / §22.3 multichain / §22.4.3 escalation-format locks
- IMPLEMENTATION-GUIDE Quick Start / EXECUTION-SUMMARY specialist table /
  hydration LIST B HITL question locks (Dec 2025 archive snapshot slice)
- docs/agent-hydration.md PHASE 1 / LIST A / PHASE 3 resolved /
- AGENTS-v2.2.md §23 IDE stack / install / VS Code /
  §24 hard-constraints / §25 risk-tolerance leftover locks
- CHANGELOG.md preamble / Changed / 0.1.0 initial leftover locks
- AGENT-PROMPTS.md expertise / principles / metrics leftover locks
- AGENT-PROMPTS.md tools / communication / escalation-identity leftover locks
- AGENT-PROMPTS.md orchestration-matrix / monthly / usage-example leftover locks
- AGENT-PROMPTS.md context / decision-authority / escalation-authority leftover locks
- AGENT-PROMPTS.md responsibilities / cannot-delegate / human-escalation leftover locks
  PHASE 4 issues / LIST B deferred leftover locks
- postmortem.md intro / Decision field / Next Steps surface locks
- agentic_flows/scratchpad.txt intro / format-legend / task-meta locks
- GitHub issue template metadata / routing-field / bug-repro locks
- pyproject project name + version/license/description/readme +
  ruff line-length/src/lint select locks
- coverage show_missing/skip_empty/source + exact fail_under +
  pytest addopts/testpaths/pythonpath locks
- LICENSE MIT required phrase locks (header / grant / AS IS)
- Dependabot directory set inventory lock (file untouched)
- Issue template frontmatter name/about locks
- README badge phrase locks
- README honesty / historic prompt set / contents section locks
- README lead / contents-blurbs / bootstrap-closing leftover locks
- CLAUDE.md quarterly-review trigger phrase locks
- markdownlint MD025/MD033/MD024 siblings_only + MD013 tables/code_blocks locks
- GitHub agent description lock
- Expanded Cursor install refs matching live environment.json

Does not invent agents or scaffold new specialist definitions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = REPO_ROOT / "schemas"

# Locked historic specialist set — validators must not invent beyond these.
DOCUMENTED_AGENTS: tuple[str, ...] = (
    "QuantumArchitectAgent",
    "BlockchainArchitectAgent",
    "EdgeSecurityAgent",
    "OrchestrationAgent",
)

EXPECTED_RECIPE_NAMES: frozenset[str] = frozenset(
    {
        "quantum_algorithm_design_workflow",
        "blockchain_contract_design_workflow",
        "edge_security_implementation_workflow",
        "quantum_nft_mint_full_orchestration",
    }
)

EXPECTED_RECIPE_FILES: tuple[str, ...] = (
    "agentic_flows/quantum_algorithm_design.yaml",
    "agentic_flows/blockchain_contract_design.yaml",
    "agentic_flows/edge_security_implementation.yaml",
    "agentic_flows/quantum_nft_mint_orchestration.yaml",
)

EXPECTED_RECIPE_BINDINGS: dict[str, str] = {
    "quantum_algorithm_design_workflow": "agentic_flows/quantum_algorithm_design.yaml",
    "blockchain_contract_design_workflow": "agentic_flows/blockchain_contract_design.yaml",
    "edge_security_implementation_workflow": "agentic_flows/edge_security_implementation.yaml",
    "quantum_nft_mint_full_orchestration": "agentic_flows/quantum_nft_mint_orchestration.yaml",
}

RECIPE_PRIMARY_AGENT: dict[str, str] = {
    "quantum_algorithm_design_workflow": "QuantumArchitectAgent",
    "blockchain_contract_design_workflow": "BlockchainArchitectAgent",
    "edge_security_implementation_workflow": "EdgeSecurityAgent",
    "quantum_nft_mint_full_orchestration": "OrchestrationAgent",
}

HISTORIC_GOOSE_PROVIDER = "anthropic"
HISTORIC_GOOSE_MODEL = "claude-opus-4"
HISTORIC_EXTENSION_TYPE = "builtin"
HISTORIC_EXTENSION_NAME = "developer"
HISTORIC_RECIPE_VERSION = "1.0.0"

AGENT_TOKEN_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*Agent)\b")
PROMPT_HEADING_RE = re.compile(
    r"^##\s+\d+\.\s+([A-Z][A-Za-z0-9]*Agent)\s+Prompt Template\s*$",
    re.MULTILINE,
)
GOOSE_RUN_PATH_RE = re.compile(
    r"goose\s+run\s+(\./agentic_flows/[A-Za-z0-9_\-]+\.ya?ml)"
)
INSTALL_TEST_F_RE = re.compile(r"test\s+-f\s+(\S+)")
CHECKBOX_RE = re.compile(r"^[\t ]*- \[[ x~!]\]", re.MULTILINE)
REQUIREMENTS_PKG_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._+-]*)")
PR_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SCHEMA_DRAFT_URI = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID_PREFIX = "https://github.com/fuzzywigg/g0p-agents/schemas/"

KNOWN_YAML_CONFIGS = (
    Path(".github/workflows/ci.yml"),
    Path(".github/dependabot.yml"),
    Path(".markdownlint.yaml"),
)

KNOWN_YAML_CONFIG_RELS: tuple[str, ...] = tuple(str(path) for path in KNOWN_YAML_CONFIGS)

REQUIRED_ARCHIVE_DOCS = (
    "AGENT-PROMPTS.md",
    "AGENTS-v2.2.md",
    "CLAUDE.md",
    "GOOSE-RECIPES.md",
    "README.md",
)

INVENTORY_VERSION = 50
CURSOR_ENVIRONMENT_NAME = "g0p-agents"
DEPENDABOT_SCHEDULE_INTERVAL = "weekly"
DEPENDABOT_DIRECTORIES: frozenset[str] = frozenset({"/"})
DEPENDABOT_ECOSYSTEMS: frozenset[str] = frozenset({"github-actions", "pip"})
DEPENDABOT_GROUP_NAMES: frozenset[str] = frozenset({"github_actions", "python_dev"})
CI_PERMISSIONS_CONTENTS = "read"
CI_ARTIFACT_NAME_PREFIX = "manifest-validate-py"
CI_PULL_REQUEST_BRANCH = "alpha"
CI_CONCURRENCY_GROUP_PREFIX = "ci-"
CI_ARTIFACT_UPLOAD_IF = "always()"
CI_CANCEL_IN_PROGRESS = True
CI_FAIL_FAST = False
CI_WORKFLOW_NAME = "CI — Lint, Links & Manifests"
CI_REQUIRED_ACTIONS: tuple[str, ...] = (
    "actions/checkout@v7",
    "actions/setup-python@v7",
    "actions/upload-artifact@v7",
    "DavidAnson/markdownlint-cli2-action@v24",
    "lycheeverse/lychee-action@v2",
)
CI_REQUIRED_TEXT_MARKERS: tuple[str, ...] = (
    "download-actionlint.bash",
    "actionlint",
    "cache: pip",
)
CI_LINK_CHECK_ARGS = "--verbose --no-progress '**/*.md'"
CI_LINK_CHECK_FAIL = True
CI_MARKDOWN_LINT_GLOBS = "**/*.md"
CI_MARKDOWN_LINT_CONFIG = ".markdownlint.yaml"
CI_CACHE_DEPENDENCY_PATH = "requirements-dev.txt"
CI_JOB_DISPLAY_NAMES: dict[str, str] = {
    "markdown-lint": "Markdown Lint",
    "link-check": "Link Check",
    "actionlint": "Actionlint",
    "manifest-validate": "Manifest Validate (Py ${{ matrix.python-version }})",
}
CI_RUNS_ON = "ubuntu-latest"
CI_ARTIFACT_IF_NO_FILES_FOUND = "warn"
CI_ARTIFACT_PATHS: tuple[str, ...] = (
    "manifest-findings.json",
    "validators.txt",
    "coverage.xml",
    "pytest-junit.xml",
)
CI_ACTIONLINT_SHELL = "bash"
CI_ACTIONLINT_STEP_ID = "get_actionlint"
CI_SETUP_PYTHON_CACHE = "pip"
CI_RUFF_CHECK_COMMAND = "ruff check scripts tests"
CI_PIP_INSTALL_COMMAND = "python -m pip install -r requirements-dev.txt"
CI_PIP_CHECK_COMMAND = "python -m pip check"
CI_PYTEST_REQUIRED_MARKERS: tuple[str, ...] = (
    "--cov=scripts",
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--junitxml=pytest-junit.xml",
)
STATE_RESIDENCY_REQUIRED_PHRASES: tuple[str, ...] = (
    "Code, config, workflows",
    "Policies, decisions, rollouts",
    "Agent operating rules",
    "Ephemeral execution context",
    "Reusable prompts/snippets",
    "This GitHub repo",
    "Notion Tier 1",
    "Notion Tier 0",
    "Slack/Discord threads",
    "Link, don't canonize",
)
KEY_FILES_REQUIRED_ENTRIES: tuple[str, ...] = (
    "AGENTS-v2.2.md",
    "AGENT-PROMPTS.md",
    "GOOSE-RECIPES.md",
    "IMPLEMENTATION-GUIDE.md",
    "EXECUTION-SUMMARY.md",
    "docs/agent-hydration.md",
    "agentic_flows/",
)
PR_ROUTING_REQUIRED_FIELDS: tuple[str, ...] = (
    "Surface",
    "Issue",
    "Branch",
    "Priority",
)
ROUTING_MATRIX_REQUIRED_PHRASES: tuple[str, ...] = (
    "CI/CD fixes, linting, dependabot",
    "Multi-file code scaffolding (agentic_flows/, contracts/, quantum_circuits/)",
    "Strategic planning, Notion updates, cross-platform coordination",
    "GitHub Settings, branch protection",
    "Automated E2E verification",
    "Financial transactions, repo visibility changes",
)
REPO_IDENTITY_REQUIRED_PHRASES: tuple[str, ...] = (
    "fuzzywigg/g0p-agents",
    "Quantum-Blockchain agentic protocols archive",
    "FUZZYWIGG four-agent swarm",
    "PikoClaw demo at Panathenea",
    "Documentation archive",
    "LIST B",
)
ESCALATION_BLOCK_REQUIRED_PHRASES: tuple[str, ...] = (
    "ESCALATION REQUIRED",
    "From Agent:",
    "Conflict:",
    "Recommendation:",
    "Timeline:",
)
ROUTING_MATRIX_RATIONALE_PHRASES: tuple[str, ...] = (
    "Single-repo, syntax-level work",
    "Deep coding, long-running, 60–90 min",
    "Cross-system state, Notion truth",
    "UI-only settings",
    "Test automation",
    "Non-automatable",
)
CLAUDE_METADATA_REQUIRED_PHRASES: tuple[str, ...] = (
    "Status: ACTIVE",
    "Tier: 1",
    "Owner: claude-cowork",
    "Created: 2026-04-13",
    "Edit policy: Agent-editable",
    "Canonical source: This file",
)
ESCALATION_USAGE_REQUIRED_PHRASES: tuple[str, ...] = (
    "When blocked, use this format in PR comments or Slack:",
    "```text",
    "From Agent: [surface name]",
    "Conflict: [What constraint am I hitting?]",
    "Recommendation: [How should we resolve this?]",
    "Timeline: [How long until decision needed?]",
)
SECURITY_SUPPORTED_REQUIRED_PHRASES: tuple[str, ...] = (
    "This repository is a documentation archive",
    "No executable code is deployed",
    "YAML recipe templates",
    "Agent system prompts",
    "Future: Solidity contracts",
)
SECURITY_REPORTING_REQUIRED_PHRASES: tuple[str, ...] = (
    "Do NOT open a public GitHub issue for security vulnerabilities",
    "To report a vulnerability:",
    "Email:",
    "Include: description, affected files, reproduction steps, suggested fix",
    "acknowledgment within 48 hours",
)
SECURITY_STANDARDS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Cryptography",
    "Smart contracts",
    "Mobile",
    "Secrets",
    "Keys",
    "NIST post-quantum standards",
    "Slither audit pass",
    "Never commit secrets",
    "Never expose plaintext keys",
)
SECURITY_HEADER_REQUIRED_PHRASES: tuple[str, ...] = (
    "# Security Policy",
    "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
    "Edit policy: Structural changes require Andrew approval",
)
SECURITY_FIPS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Security Standards for This Ecosystem",
    "ML-KEM/FIPS 203",
    "ML-DSA/FIPS 204",
    "SLH-DSA/FIPS 205",
    "0 critical vulnerabilities",
    "Apple/Google security guidelines compliance",
    "use `.env` files excluded by `.gitignore`",
)
SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Known Non-Issues",
    "CRYSTALS-Kyber",
    "CRYSTALS-Dilithium",
    "ML-KEM (FIPS 203)",
    "ML-DSA (FIPS 204)",
    "pre-finalization names",
    "The underlying algorithms are correct",
)
SECURITY_SCOPE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Supported Versions",
    "Security policy applies to:",
    "potential injection risks if values are interpolated without sanitization",
    "potential prompt injection surface",
    "Python quantum circuits",
    "React Native mobile code (when scaffolded)",
)
SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Reporting a Vulnerability",
    "Andrew Pappas — contact via smtp.eth ENS or GitHub @fuzzywigg",
    "Expected response:",
    "smtp.eth ENS",
    "GitHub @fuzzywigg",
)
SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES: tuple[str, ...] = (
    "When code is scaffolded into this repo, it must comply with:",
    "| Domain | Standard |",
    "in RAM, logs, or code",
    "AGENTS-v2.2.md references",
    "updated in a future issue",
)
CHANGELOG_FORMAT_REQUIRED_PHRASES: tuple[str, ...] = (
    "# Changelog",
    "All notable changes to this project will be documented in this file.",
    "Keep a Changelog",
    "## [Unreleased]",
    "### Added",
)
CHANGELOG_UNRELEASED_REQUIRED_PHRASES: tuple[str, ...] = (
    "## [Unreleased]",
    "Packaging inventory",
    "historic four",
    "or Dependabot",
    "validators",
)
CHANGELOG_RELEASE_REQUIRED_PHRASES: tuple[str, ...] = (
    "### Changed",
    "## [0.1.0] — 2025-12-13",
    "`AGENTS-v2.2.md` — agent constitution",
    "`AGENT-PROMPTS.md` — specialist agent system prompts (4 agents)",
    "`GOOSE-RECIPES.md` — Goose YAML recipe templates",
)
CONSTITUTION_CRYPTO_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.1 Quantum-Safe Cryptography Requirements",
    "CRYSTALS-Kyber",
    "CRYSTALS-Dilithium",
    "SPHINCS+",
    "liboqs",
    "Never use classical RSA/ECDSA for new implementations",
    "Hybrid approach during transition",
)
CONSTITUTION_HANDOFF_REQUIRED_PHRASES: tuple[str, ...] = (
    "#### 22.4.1 Handoff Sequence",
    "**Phase 1: Algorithm Design**",
    "**Phase 2: Contract Design**",
    "**Phase 3: Implementation**",
    "**Phase 4: Orchestration Decision**",
    "QuantumArchitectAgent → BlockchainArchitectAgent",
    "Logs decision in postmortem.md",
)
CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES: tuple[str, ...] = (
    "#### 22.4.2 Escalation Triggers",
    "**QuantumArchitectAgent escalates when**:",
    "Circuit depth exceeds device constraints by >20%",
    "**BlockchainArchitectAgent escalates when**:",
    "Gas cost exceeds 10M",
    "**EdgeSecurityAgent escalates when**:",
    "Crypto operations > 500ms",
    "**OrchestrationAgent escalates to user when**:",
)

CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.2 On-Device Quantum Logic Execution",
    "MUST use Cirq circuits compiled for mobile constraints",
    "MUST have deterministic fallback to classical simulation (Qualtran)",
    "MUST NOT block UI thread",
    "Circuit execution: < 500ms",
    "Memory footprint: < 2MB",
    "Cirq-sim (classical validation)",
)
CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.3 Multi-Chain State Consistency",
    "State Commitment Protocol",
    "Operation state committed to blockchain (hash)",
    "Result cryptographically signed (post-quantum signature)",
    "Failure Recovery",
    "Maximum pending duration: 24 hours",
    "Rollback MUST be executable by user without third-party approval",
)
CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES: tuple[str, ...] = (
    "#### 22.4.3 Escalation Format (All Agents)",
    "🚨 ESCALATION REQUIRED",
    "From Agent: [Agent Name]",
    "Mode: [Transformative/Operational]",
    "Conflict: [What constraint am I hitting?]",
    "Recommendation: [How should we resolve this?]",
    "Awaiting approval before proceeding.",
)
CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.5 Recipe-Based Orchestration Structure",
    "All agent workflows use YAML recipes in `./agentic_flows/` directory.",
    "#### Example: NFT Mint with Quantum Validation",
    "name: quantum_nft_mint_workflow",
    "Execute NFT Mint with Quantum Validation",
    "QuantumArchitectAgent validates cryptographic randomness",
    "All three agents sign off before mainnet deployment",
)
CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.6 Scratchpad State Machine",
    "All agent coordination state lives in `./agentic_flows/scratchpad.txt`",
    "Checkbox state is source of truth",
    "Only append, never overwrite",
    "Each agent owns its section",
    "Deadline must be set before work begins",
    "If deadline passes without completion → escalate to user",
)
CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 22.7 Conflict Resolution Matrix",
    "When agents disagree on a design decision",
    "**Quantum Algorithm Complexity**",
    "**Smart Contract Gas Cost**",
    "**Crypto Algorithm Choice**",
    "**Deployment Timeline**",
    "**Final Decision Maker**: OrchestrationAgent",
)
IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Quick Start (30 minutes)",
    "mkdir -p agentic_flows",
    "mkdir -p quantum_circuits",
    "mkdir -p contracts",
    "touch agentic_flows/scratchpad.txt",
    "AGENTS-v2.2.md",
    "AGENT-PROMPTS.md",
    "GOOSE-RECIPES.md",
    "Python 3.11",
)
EXECUTION_SPECIALISTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Four Specialist Agents",
    "QuantumArchitectAgent",
    "BlockchainArchitectAgent",
    "EdgeSecurityAgent",
    "OrchestrationAgent",
    "Quantum Computing",
    "Blockchain Dev",
    "On-Device Security",
    "YAML recipes, Docker Compose",
)

HYDRATION_META_REQUIRED_PHRASES: tuple[str, ...] = (
    "# Agent Hydration Report — g0p-agents",
    "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
    "Owner: copilot (hydration run) | Edit policy: Agent-editable",
)
HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES: tuple[str, ...] = (
    "**LICENSE file absent**",
    "No package.json, requirements.txt, pyproject.toml, Cargo.toml",
    "No executable source code",
    "Purpose statement is thin; no badges, no quick-start",
    "Goose (referenced in YAML templates)",
)
HYDRATION_GIT_DETAIL_REQUIRED_PHRASES: tuple[str, ...] = (
    "`main` (protected), `copilot/hydrate` (this run)",
    "2 commits total (shallow clone)",
    "main protected (push blocked)",
    "copilot/hydrate: no protection",
    "Feature branches per issue",
    "Full history",
)
HYDRATION_PHASE2_REQUIRED_PHRASES: tuple[str, ...] = (
    "## PHASE 2: QUESTIONS",
    "Determines if crypto recommendations are current",
    "Determines scaffolding language for quantum_circuits/",
    "Andrew's head",
    "Andrew / Notion North Star",
    "Notion Master Index",
    "Web/docs",
    "OQS project",
    "Codebase read",
)
HYDRATION_PHASE5_REQUIRED_PHRASES: tuple[str, ...] = (
    "## PHASE 5: Roadmap",
    "See GitHub Issue: [claude] g0p-agents Roadmap — Development Timeline & Issue Tracker",
)
HYDRATION_PHASE1_REQUIRED_PHRASES: tuple[str, ...] = (
    "### Identity",
    "### Source Architecture",
    "### Dependencies",
    "### Tests",
    "### CI/CD",
    "### Documentation",
    "### Governance",
    "### Templates",
    "### Security",
    "### Error Handling",
    "### Observability",
    "### Deployment",
    "### Git State",
    "Public archive of Quantum-Blockchain agentic protocols v2.2",
    "Markdown only (documentation archive)",
)
HYDRATION_LIST_A_REQUIRED_PHRASES: tuple[str, ...] = (
    "### LIST A — Researchable",
    "What is the Goose framework?",
    "What are CRYSTALS-Kyber and CRYSTALS-Dilithium?",
    "What is `liboqs`?",
    "What is `stimgery`",
    "Determines if recipe files can be scaffolded correctly",
    "NIST PQC docs",
    "Clarify if typo or intentional term",
)
HYDRATION_RESOLVED_REQUIRED_PHRASES: tuple[str, ...] = (
    "Goose is Block's open-source AI agent framework",
    "CRYSTALS-Kyber (now ML-KEM, FIPS 203)",
    "CRYSTALS-Dilithium (now ML-DSA, FIPS 204)",
    "liboqs (Open Quantum Safe)",
    "colloquial portmanteau of \"strategy\" + \"imagery\"",
    "LIST B items B1–B5 are deferred to Andrew",
    "No scaffolding issues marked P1 until B1/B2 are answered",
)
HYDRATION_PHASE4_REQUIRED_PHRASES: tuple[str, ...] = (
    "## PHASE 4: ISSUES GENERATED",
    "Add LICENSE file",
    "Create .github/workflows/ CI pipeline (markdown lint + link check)",
    "Add CONTRIBUTING.md",
    "Add SECURITY.md",
    "Create GitHub issue templates (bug, feature, agent-task)",
    "Create PR template",
    "Scaffold agentic_flows/ with actual Goose recipe YAML files",
    "Create agentic_flows/scratchpad.txt and postmortem.md",
    "Scaffold quantum_circuits/ with sample Cirq implementation",
    "Scaffold contracts/ with sample Solidity ERC-721 contract",
    "Scaffold mobile/ with React Native QuantumValidator skeleton",
)
HYDRATION_DEFERRED_REQUIRED_PHRASES: tuple[str, ...] = (
    "## LIST B — Deferred to Andrew",
    "Before Phase 3 scaffolding issues should be prioritized",
    "remain a reference archive",
    "What specific PikoClaw features depend on g0p-agents by May 27, 2026?",
    "Which of the 4 agents (Quantum/Blockchain/Edge/Orchestration) is highest priority",
    "should g0p-agents merge into it or stay separate?",
    "Does a Notion page for g0p-agents exist?",
)
HYDRATION_LIST_B_REQUIRED_PHRASES: tuple[str, ...] = (
    "### LIST B — Requires Andrew (HITL)",
    "Is g0p-agents meant to be activated into a runnable codebase",
    "What is PikoClaw exactly",
    "Should actual Solidity, Python (Cirq), and React Native code be implemented",
    "What is the `agents-standard` repo",
    "Is there a Notion page for g0p-agents",
)

CONSTITUTION_IDE_STACK_REQUIRED_PHRASES: tuple[str, ...] = (
    "## 23. Quantum-Blockchain Development IDE Setup",
    "### 23.1 Required Software Stack",
    "#### Tier 1: Foundation (All Developers)",
    "#### Tier 2: Quantum Computing",
    "#### Tier 3: Blockchain Development",
    "#### Tier 4: On-Device Security",
    "#### Tier 5: Container Orchestration",
    "Git + GitHub",
    "VS Code + Remote WSL2 extension",
    "Cirq (Google quantum circuits)",
    "Qualtran (quantum algorithm abstractions)",
    "Hardhat (smart contract environment)",
    "React Native + Expo (cross-platform)",
    "Docker Desktop (WSL2 backend)",
)

CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 23.2 Installation Script (WSL2 Ubuntu 22.04)",
    "setup-quantum-blockchain-dev.sh",
    "Setting up Quantum-Blockchain Development Environment...",
    "source ~/quantum-blockchain-env/bin/activate",
    "mkdir -p ~/fuzzywigg-ai/quantum_circuits",
    "mkdir -p ~/fuzzywigg-ai/agentic_flows",
    "pip install liboqs",
    "\u2705 Quantum-Blockchain development environment ready!",
)

CONSTITUTION_VSCODE_REQUIRED_PHRASES: tuple[str, ...] = (
    "### 23.3 VS Code Extensions (Required)",
    "Install these extensions in VS Code:",
    "ms-python.python",
    "ms-toolsai.jupyter",
    "JuanBlanco.solidity",
    "Hardhat.hardhat-solidity",
    "ms-azuretools.vscode-docker",
    "ms-vscode-remote.remote-wsl",
    "GitHub.copilot",
)

CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## 24. Hard Constraints \u2014 Quantum-Blockchain Additions",
    "Add to Section 3 (Hard Constraints):",
    "Agents must **NEVER**:",
    "Design quantum algorithms without validating against known quantum-resistant properties",
    "Deploy smart contracts without post-quantum cryptography threat modeling",
    "Implement on-device crypto without HSM/secure enclave consideration",
    "Claim quantum-safe without formal verification",
    "NIST-standardized algorithms (Kyber, Dilithium, SPHINCS+)",
)

CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## 25. Quarterly Risk Tolerance Review (Section 12.4.1)",
    "### 12.4.1 Risk Tolerance Evolution Protocol",
    "Every 90 days (or after 500+ successful transactions), conduct a formal risk tolerance review:",  # noqa: E501
    "Success rate > 99.5% (at current tier)",
    "Time since last critical incident > 60 days",
    "Review incident log (postmortem.md)",
    "Test new tier on testnet (10 transactions minimum)",
    "If failure rate > 2% in new tier, immediately revert to previous tier.",
)

CHANGELOG_PREAMBLE_REQUIRED_PHRASES: tuple[str, ...] = (
    "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).",
    "https://keepachangelog.com/en/1.0.0/",
    "All notable changes to this project will be documented in this file.",
    "---",
)

CHANGELOG_CHANGED_REQUIRED_PHRASES: tuple[str, ...] = (
    "### Changed",
    "Inventory schema minimum version is **7**",
    "CI validator-count gate raised to \u226534",
    "coverage gate **99%**",
    "Dependabot now tracks pip (`requirements-dev.txt`)",
    "CI `pull_request` trigger targets `alpha`",
    "`CONTRIBUTING.md` branch strategy aligned with live default branch `alpha`",
)

CHANGELOG_INITIAL_REQUIRED_PHRASES: tuple[str, ...] = (
    "## [0.1.0] \u2014 2025-12-13",
    "`README.md` \u2014 public archive description",
    "`IMPLEMENTATION-GUIDE.md` \u2014 step-by-step setup guide",
    "`EXECUTION-SUMMARY.md` \u2014 implementation summary",
)

POSTMORTEM_INTRO_REQUIRED_PHRASES: tuple[str, ...] = (
    "Decision & Incident Log",
    "Every significant decision, conflict, and resolution is logged here",
    "Agents MUST log decisions after each workflow",
    "Andrew reviews quarterly",
)
POSTMORTEM_FIELD_REQUIRED_PHRASES: tuple[str, ...] = (
    "**Date**:",
    "**Decision**:",
    "**Agent**:",
    "**Context**:",
    "**LIST B Deferred**:",
    "**Risk Level**:",
    "**Files Created**:",
    "**Blocked**:",
    "**Next Steps**:",
)
POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Andrew answers LIST B (B1–B5) in docs/agent-hydration.md",
    "browser-claude or claude-cowork creates GitHub issues",
    "claude-cowork creates/updates Notion page under Active Sprint Work",
    "geryon scaffolds agentic_flows/ once B1 is answered",
)
SCRATCHPAD_INTRO_REQUIRED_PHRASES: tuple[str, ...] = (
    "Agent Coordination Scratchpad",
    "Updated by each agent after completing their task",
    "mark them complete",
)
SCRATCHPAD_FORMAT_REQUIRED_PHRASES: tuple[str, ...] = (
    "[x] = DONE",
    "[ ] = PENDING",
    "[~] = IN_PROGRESS",
    "[!] = BLOCKED/ESCALATED",
)
SCRATCHPAD_TASK_META_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Task: Repo Hydration",
    "Status:",
    "Created:",
    "Owner:",
    "Current blocker:",
)
ISSUE_METADATA_REQUIRED_PHRASES: tuple[str, ...] = (
    "Status: ACTIVE",
    "Tier: 1",
    "Created: YYYY-MM-DD",
    "Owner:",
    "Edit policy: Agent-editable; structural changes require Andrew approval",
)
ISSUE_ROUTING_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Agent Surface Routing",
    "| Surface |",
    "| Rationale |",
    "| Priority |",
    "| Branch |",
    "| Dependencies |",
)
BUG_REPRO_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Steps to Reproduce",
    "## Expected Behavior",
    "## Actual Behavior",
)
CONTRIBUTING_WHO_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Who Can Contribute",
    "FUZZYWIGG multi-agent ecosystem",
    "Agent surfaces",
    "Andrew Pappas",
    "Ecosystem collaborators",
)
CONTRIBUTING_BRANCH_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Branch Strategy",
    "`alpha`",
    "Default / protected",
    "`copilot/<task>`",
    "`geryon/<task>`",
    "`claude/<task>`",
    "`cursor/<task>`",
)
CONTRIBUTING_PR_REQUIRED_PHRASES: tuple[str, ...] = (
    "## PR Requirements",
    "Branch off from `alpha`",
    "Fill in the PR template completely",
    "All CI checks must pass before merge",
    "One approval required",
    "## Governance",
    "require Andrew approval",
)
CONTRIBUTING_ISSUES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Issue Reporting",
    "Use the appropriate issue template",
    "**Bug** — something broken",
    "**Feature** — new capability needed",
    "**Agent Task** — structured work",
    "metadata header defined in CLAUDE.md",
)
CONTRIBUTING_LOCAL_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Local validation (docs packaging)",
    "python -m pip install -r requirements-dev.txt",
    "ruff check scripts tests",
    "python scripts/validate_manifests.py --list-validators",
    "python scripts/validate_manifests.py",
    "python -m pytest --cov=scripts --cov-report=term-missing",
)
CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Governance",
    "Structural changes",
    "directory reorganization",
    "agent routing changes",
    "license changes",
    "require Andrew approval before merging",
    "regardless of CI status",
    "See [CLAUDE.md](CLAUDE.md)",
    "agent routing matrix and negative constraints",
)

CONTRIBUTING_METADATA_REQUIRED_PHRASES: tuple[str, ...] = (
    "# Contributing to g0p-agents",
    "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
    "Edit policy: Agent-editable; structural changes require Andrew approval",
)
CONTRIBUTING_SURFACES_REQUIRED_PHRASES: tuple[str, ...] = (
    "copilot, geryon, claude-cowork, browser-claude, playwright",
    "automated contributions via structured issues and PRs",
    "architectural decisions, branch protection changes, licensing, financial decisions",
    "invited contributors working on PikoClaw or related projects",
    "Never push directly",
    "CI fixes, single-file edits",
    "multi-file scaffolding, deep code changes",
    "docs, Notion-linked content",
    "thin docs/CI/hygiene",
)
CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES: tuple[str, ...] = (
    "Reference the issue number in the PR title when one exists",
    "Fix #12: Add LICENSE file",
    "markdown lint, link check, actionlint",
    "manifest validate on Python 3.11/3.12/3.13",
    "Andrew or designated reviewer",
    "Packaging inventory v50",
    "refuse invented recipes",
    "orphan on-disk YAML",
    "unknown `*Agent` tokens",
    "`AGENT-PROMPTS.md` / `GOOSE-RECIPES.md` / `AGENTS-v2.2.md`",
)
PR_SUMMARY_REQUIRED_PHRASES: tuple[str, ...] = (
    "# Summary",
    "One sentence: what does this PR accomplish?",
    "## Problem",
    "Closes #N",
)
PR_ACCEPTANCE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Changes",
    "List of files changed and what was done",
    "## Acceptance Criteria",
    "Copy from the linked issue",
    "- [ ]",
)
PR_NOTES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Notes for Reviewer",
    "Anything Andrew or the reviewing agent should know",
    "[agent-surface]",
    "#[issue-number]",
    "[P1/P2/P3]",
)
README_HONESTY_REQUIRED_PHRASES: tuple[str, ...] = (
    "(archived reference)",
    "This is not a live hive, runtime, or production swarm",
    "prompt fiction",
    "no running hive mind in this tree",
    "fuzzywigg/agents-standard",
)
README_HISTORIC_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Historic prompt set",
    "Designing quantum-safe algorithms",
    "Implementing multi-chain, quantum-resistant contracts",
    'Creating "walled garden" mobile security',
    "Managing conflicts via stimgery and YAML recipes",
)
README_CONTENTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Contents",
    "**AGENT-PROMPTS.md**",
    "**GOOSE-RECIPES.md**",
    "**IMPLEMENTATION-GUIDE.md**",
    "**AGENTS-v2.2.md**",
    "## Cloud agents",
    ".cursor/environment.json",
    "## Manifest validation",
    "## License",
)

README_LEAD_REQUIRED_PHRASES: tuple[str, ...] = (
    'Docs-only archive of 2025 "Quantum-Blockchain" agent prompts (v2.2, Dec 2025).',
    '"Oracle-Style',
    'Quantum Hive Mind" language in the historic copy below is prompt fiction.',
    'This repository contains the "Quantum-Blockchain" agentic protocols v2.2 (Dec 2025).',
    'architecture *on paper*',
)
README_BLURBS_REQUIRED_PHRASES: tuple[str, ...] = (
    'Full system prompts for the 4 specialist agents.',
    'YAML-based orchestration logic (Goose Framework).',
    'Step-by-step setup for a quantum-dev environment.',
    'Historic snapshot of the agent constitution.',
    'Repo routing, contribution, and reporting policy.',
)
README_BOOTSTRAP_REQUIRED_PHRASES: tuple[str, ...] = (
    'This is an archived reference implementation, not a live hive.',
    'Docs-only bootstrap lives in',
    '(`install` verifies key archive files; no `start` services).',
    'This archive has no runtime agent code.',
    'Schemas and the packaging inventory live under',
    'does **not** invent specialist agents beyond the historic four',
    'MIT — see [LICENSE](LICENSE).',
)

PROMPT_EXPERTISE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Expertise",
    "Quantum mechanics (gates, superposition, entanglement)",
    "Quantum algorithm design (Shor's, Grover's, VQE, custom)",
    "Distributed ledger architecture",
    "Smart contract design patterns (ERC-20, ERC-721, ERC-1155)",
    "Android/iOS development (Kotlin, Swift)",
    "Hardware security modules (HSM, Secure Enclave)",
    "Post-quantum cryptography (classical + quantum-resistant)",
)

PROMPT_PRINCIPLES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Decision Making Principles",
    "Prioritize quantum-safety over performance",
    "Balance security with usability",
    "Prioritize multi-chain resilience",
    "Prioritize user security and privacy",
    "Recommend constraint-based designs (work within device limits)",
    "Recommend staged rollouts (testnet \u2192 staging \u2192 mainnet)",
    "Flag performance issues early (don't wait for integration testing)",
)

PROMPT_METRICS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Success Metrics",
    "Circuit depth < 50 gates (if possible)",
    "Error rate < 1% on simulator",
    "0 critical vulnerabilities (Slither pass)",
    "< 2500 gas per operation",
    "Crypto operations < 500ms on Snapdragon 8 Gen 3 (or specified device)",
    "Data isolation 100% (no log leaks)",
    "Zero critical security incidents",
    "Quarterly risk tolerance review completed",
)

PROMPT_TOOLS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Tools",
    "Jupyter Lab (interactive development)",
    "Cirq (circuit construction)",
    "Hardhat (local blockchain, contract testing)",
    "Slither (security analysis)",
    "Android Studio (Android development)",
    "liboqs (post-quantum crypto on device)",
    "YAML recipes (./agentic_flows/*.yaml)",
    "Scratchpad state machine (./agentic_flows/scratchpad.txt)",
)

PROMPT_COMMUNICATION_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Communication Style",
    "Be technical and precise",
    "Explain decisions via circuit diagrams and complexity analysis",
    "Be clear and structured",
    'Risk-aware ("this could fail if...")',
    "Be pragmatic and performance-aware",
    'Conservative on capabilities ("device X can\'t handle that")',
    "Be decisive but transparent",
    "Escalate early if uncertain",
)

PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES: tuple[str, ...] = (
    "🚨 ESCALATION REQUIRED",
    "From Agent: QuantumArchitectAgent",
    "From Agent: BlockchainArchitectAgent",
    "From Agent: EdgeSecurityAgent",
    "Remember: You are not working alone. BlockchainArchitectAgent and "
    "EdgeSecurityAgent depend on your output.",
    "Remember: You bridge QuantumArchitectAgent (algorithms) and "
    "EdgeSecurityAgent (mobile implementation). Your architecture must "
    "satisfy both.",
    "Remember: You are the last line of defense before user devices. Your "
    "implementation determines whether the entire system is actually secure "
    "or just theoretically secure.",
)

PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Conflict Resolution Matrix",
    "| Conflict Type | How You Resolve It |",
    '**Algorithm Complexity** (Quantum says "too complex", Blockchain says "necessary")',
    '**Gas Cost** (Blockchain says "over budget", On-Device says "can\'t afford")',
    '**Crypto Algorithm** (On-Device says "RSA too slow", Quantum says "must be RSA")',
    '**Timeline** (All agents say "2 weeks", business needs "2 days")',
    "Weigh risk tolerance. Choose testnet approach to validate.",
    "Redesign contract interface or reduce scope.",
    "Use hybrid (post-quantum + RSA), implement staged migration.",
    "Reduce scope, increase risk, escalate to stakeholder.",
)

PROMPT_MONTHLY_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Monthly Checklist",
    "## Current Project Vision",
    "Review all recent decisions in postmortem.md",
    "Check agent success metrics (are they meeting targets?)",
    "Identify any emerging conflicts (before they escalate)",
    "Update risk register (quarterly, minimum)",
    "Communicate progress to stakeholder",
    "Ultimate Goal: Build quantum-safe, multi-chain NFT ecosystem with on-device security",
    "Risk Tolerance: ALPHA-STAGE (conservative, threshold increases with success)",
)

PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES: tuple[str, ...] = (
    "### Example: Instantiate QuantumArchitectAgent",
    'User Input: "Review the proposed factorization circuit for our NFT mint operation. '
    'Check Cirq optimization, validate quantum-safety, provide gate count and error '
    'rate estimates. Use the scratchpad to track progress."',
    "Reads ./agentic_flows/scratchpad.txt (finds pending quantum mint task)",
    "Designs Cirq circuit for factorization",
    "Optimizes for mobile constraints (2MB RAM max)",
    "Validates using CRYSTALS-Kyber (NIST post-quantum standard)",
    "Output: Updated scratchpad + Cirq circuit file",
    "Keep prompts synchronized with AGENTS.md Section 22 "
    "(Quantum-Blockchain Integration Standards).",
)

PROMPT_CONTEXT_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Current Project Context",
    "[INSERT PROJECT-SPECIFIC INFO HERE]",
    "Target quantum hardware: [Cirq-sim initially, then Google/IBM hardware]",
    "Circuit depth limit: [2MB RAM on mobile device]",
    "Primary blockchain: Ethereum (Sepolia testnet, mainnet)",
    "Consensus requirement: Quantum-resistant validation required",
    "Target devices: Android (minimum Snapdragon 8 Gen 2), iOS (minimum iPhone 12)",
    "Crypto algorithms: CRYSTALS-Kyber (key encapsulation), CRYSTALS-Dilithium (signatures)",
)

PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Decision Authority",
    "You make final calls on:",
    "Trade-offs between security, performance, and usability",
    "Prioritization (what gets built first)",
    "Risk acceptance (can we deploy with this vulnerability?)",
    "Timeline adjustments (can we ship on schedule?)",
)

PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Escalation Authority",
    "You MUST escalate to human if:",
    "Two or more agents have irresolvable conflicts",
    "Risk exceeds acceptable threshold",
    "Timeline pressure conflicts with quality requirements",
    "Budget constraints conflict with scope",
)


PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Core Responsibilities",
    "Design quantum algorithms for cryptographic operations",
    "Optimize Cirq circuits for target hardware",
    "Design multi-chain smart contract architecture",
    "Implement quantum-resistant consensus logic",
    "Implement quantum-safe cryptography on Android/iOS",
    'Design data isolation ("walled garden") architecture',
    "Collect outputs from all three specialist agents",
    "Make final go/no-go decision",
)

PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Key Responsibilities You CANNOT Delegate",
    "Final go/no-go decisions",
    "Risk acceptance (acknowledging consequences)",
    "Human escalation (when agents can't decide)",
    "Vision articulation (Mickey 18 → technical architecture)",
    "Stakeholder communication",
)

PROMPT_HUMAN_ESCALATION_REQUIRED_PHRASES: tuple[str, ...] = (
    "## When You Escalate to Human",
    "Situation: [What decision needs human input?]",
    "Agent Input: [What did specialist agents recommend?]",
    "Risk Assessment: [What could go wrong with each option?]",
    "Human approval required before proceeding.",
    "Remember: You are not smarter than the three specialists. Your job is to "
    "listen, understand, mediate, and make calls when consensus is impossible.",
)


LICENSE_REQUIRED_PHRASES: tuple[str, ...] = (
    "MIT License",
    "Permission is hereby granted",
    'THE SOFTWARE IS PROVIDED "AS IS"',
)
PYPROJECT_NAME = "g0p-agents-validation"
PYPROJECT_DESCRIPTION = (
    "Dev-only packaging validators for the g0p-agents docs archive "
    "(not a runtime package)."
)
PYPROJECT_README = "README.md"
PYPROJECT_VERSION = "0.0.0"
PYPROJECT_LICENSE_TEXT = "MIT"
PYPROJECT_REQUIRES_PYTHON = ">=3.11"
PYPROJECT_RUFF_TARGET_VERSION = "py311"
PYPROJECT_LINE_LENGTH = 100
PYPROJECT_RUFF_SRC: tuple[str, ...] = ("scripts", "tests")
PYPROJECT_RUFF_LINT_SELECT: tuple[str, ...] = ("E", "F", "I", "UP", "B")
PYTEST_ADDOPTS = "-q"
PYTEST_TESTPATHS: tuple[str, ...] = ("tests",)
PYTEST_PYTHONPATH: tuple[str, ...] = ("scripts",)
COVERAGE_BRANCH = True
COVERAGE_SHOW_MISSING = True
COVERAGE_SKIP_EMPTY = True
COVERAGE_SOURCE: tuple[str, ...] = ("scripts",)
RECIPE_TITLES: dict[str, str] = {
    "quantum_algorithm_design_workflow": (
        "Design and Optimize Quantum Algorithm for Cryptographic Operation"
    ),
    "blockchain_contract_design_workflow": (
        "Design and Audit Smart Contract for Quantum-Resistant Multi-Chain"
    ),
    "edge_security_implementation_workflow": (
        "Implement Quantum-Safe Cryptography on Mobile Device"
    ),
    "quantum_nft_mint_full_orchestration": (
        "Full Quantum-Blockchain-Mobile Orchestration for NFT Mint Operation"
    ),
}
MARKDOWNLINT_DEFAULT = True
MARKDOWNLINT_MD013_LINE_LENGTH = 200
MARKDOWNLINT_MD013_TABLES = False
MARKDOWNLINT_MD013_CODE_BLOCKS = False
MARKDOWNLINT_MD025 = False
MARKDOWNLINT_MD033 = False
MARKDOWNLINT_MD024_SIBLINGS_ONLY = True
GITHUB_AGENT_NAME = "Hydration"
GITHUB_AGENT_DESCRIPTION = (
    "Poeseidon hydrator, powerful. moves earth, controls the flow of water, "
    "powerful god of olympus."
)
LICENSE_COPYRIGHT_HOLDER = "Andrew Pappas"
LICENSE_COPYRIGHT_MARKER = "Copyright (c) 2026 Andrew Pappas"
AGENTIC_FLOWS_ALLOWED_FILES: frozenset[str] = frozenset({"scratchpad.txt"})
CURSOR_INSTALL_REQUIRED_REFS: tuple[str, ...] = (
    "README.md",
    "LICENSE",
    "AGENTS-v2.2.md",
    "AGENT-PROMPTS.md",
    "GOOSE-RECIPES.md",
    ".github/workflows/ci.yml",
    "scripts/validate_manifests.py",
    "schemas/goose-recipe.schema.json",
    "schemas/packaging-inventory.json",
    "schemas/packaging-inventory.schema.json",
    "schemas/markdownlint.schema.json",
    "tests/test_validate_manifests.py",
    "requirements-dev.txt",
    "pyproject.toml",
    "agentic_flows/scratchpad.txt",
    ".github/pull_request_template.md",
)
ISSUE_TEMPLATE_NAMES: dict[str, str] = {
    ".github/ISSUE_TEMPLATE/bug_report.md": "Bug Report",
    ".github/ISSUE_TEMPLATE/feature_request.md": "Feature Request",
    ".github/ISSUE_TEMPLATE/agent_task.md": "Agent Task",
}
ISSUE_TEMPLATE_ABOUTS: dict[str, str] = {
    ".github/ISSUE_TEMPLATE/bug_report.md": (
        "Something is broken in existing files, workflows, or agent behavior"
    ),
    ".github/ISSUE_TEMPLATE/feature_request.md": (
        "New capability needed in the ecosystem"
    ),
    ".github/ISSUE_TEMPLATE/agent_task.md": (
        "Structured work item for a specific agent surface "
        "(copilot, geryon, claude-cowork, etc.)"
    ),
}
README_BADGE_PHRASES: tuple[str, ...] = (
    "actions/workflows/ci.yml/badge.svg?branch=alpha",
    "label=link-check",
    "License: MIT",
)
QUARTERLY_REVIEW_PHRASES: tuple[str, ...] = (
    "Risk tolerance update (AGENTS-v2.2.md Section 12.4.1)",
    "Agent success metrics audit",
    "Notion Master Index sync",
    "postmortem.md incident review",
)

SCRATCHPAD_REQUIRED_PHRASES = (
    "source of truth",
    "Never delete entries",
    "g0p-agents Agent Coordination",
)

AGENT_TOKEN_SCAN_DOCS = (
    *REQUIRED_ARCHIVE_DOCS,
    "IMPLEMENTATION-GUIDE.md",
    "EXECUTION-SUMMARY.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "postmortem.md",
    "docs/agent-hydration.md",
)

REQUIRED_CI_JOBS = frozenset(
    {"markdown-lint", "link-check", "actionlint", "manifest-validate"}
)

REQUIRED_PYTHON_VERSIONS: tuple[str, ...] = ("3.11", "3.12", "3.13")

REQUIRED_MANIFEST_STEP_MARKERS = (
    "validate_manifests.py",
    "pytest",
    "ruff",
    "--cov",
    "pip check",
    "--list-validators",
    "Smoke each",
    "--only",
    "junitxml",
    "Lock inventory",
    "INVENTORY_VERSION",
)

GITHUB_AGENT_FILES: tuple[str, ...] = (".github/agents/my-agent.agent.md",)

ISSUE_TEMPLATE_FILES: tuple[str, ...] = (
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/agent_task.md",
)

PR_TEMPLATE_HEADINGS: tuple[str, ...] = (
    "Summary",
    "Problem",
    "Changes",
    "Acceptance Criteria",
    "Agent Surface Routing",
    "Notes for Reviewer",
)

REQUIRED_DEV_PACKAGES: frozenset[str] = frozenset(
    {"jsonschema", "PyYAML", "pytest", "pytest-cov", "ruff"}
)

SCHEMA_FILES = (
    "goose-recipe.schema.json",
    "cursor-environment.schema.json",
    "github-custom-agent.schema.json",
    "github-issue-template.schema.json",
    "dependabot-v2.schema.json",
    "markdownlint.schema.json",
    "packaging-inventory.schema.json",
)

ORCHESTRATION_RECIPE_NAME = "quantum_nft_mint_full_orchestration"

ROUTING_SURFACES: tuple[str, ...] = (
    "copilot",
    "geryon",
    "claude-cowork",
    "browser-claude",
    "playwright",
    "human",
)

CONSTITUTION_HEADING_PREFIX = "#### "
PROMPT_SYSTEM_HEADER_SUFFIX = " System Prompt"
SPECIALIST_ESCALATION_MARKER = "ESCALATION REQUIRED"
ORCHESTRATION_ESCALATION_MARKER = "ESCALATION TO HUMAN REQUIRED"

README_REQUIRED_PHRASES = (
    "validate_manifests.py",
    "historic four",
    "schemas/",
    "not a live hive",
    "Docs-only",
)

SECURITY_REQUIRED_PHRASES = (
    "Never commit secrets",
    "Do NOT open a public GitHub issue for security vulnerabilities",
    "acknowledgment within 48 hours",
    "Never expose plaintext keys",
)

CONTRIBUTING_REQUIRED_PHRASES = (
    "Do not invent new specialist agents",
    "validate_manifests.py",
    "four agents only",
)

CHANGELOG_REQUIRED_PHRASES = (
    "## [Unreleased]",
    "Packaging inventory",
    "historic four",
)

POSTMORTEM_REQUIRED_PHRASES = (
    "Decision & Incident Log",
    "LIST B",
    "documentation archive",
)

GITIGNORE_REQUIRED_PATTERNS = (
    ".env",
    "*.pem",
    "*.key",
    "__pycache__/",
    ".coverage",
)

NEGATIVE_CONSTRAINT_PHRASES = (
    "Push to `main` branch",
    "Merge own PRs on protected repos",
    "Delete files or repositories without human approval",
    "Initiate financial transactions or alter billing",
    "Change repo visibility (private/public)",
    "Modify branch protection rules",
    "Create public gists containing secrets or PII",
)

HYDRATION_REQUIRED_SECTIONS = (
    "## PHASE 1: FINDINGS REPORT",
    "## PHASE 2: QUESTIONS",
    "### LIST B — Requires Andrew (HITL)",
    "## PHASE 3: RESOLVED (LIST A)",
    "## PHASE 4: ISSUES GENERATED",
    "## PHASE 5: Roadmap",
    "## LIST B — Deferred to Andrew",
)

EXECUTION_SUMMARY_REQUIRED_PHRASES = (
    "EXECUTION SUMMARY",
    "Your Four Specialist Agents",
    "GOOSE-RECIPES.md",
)

IMPLEMENTATION_GUIDE_REQUIRED_PHRASES = (
    "IMPLEMENTATION GUIDE",
    "Quick Start",
    "agentic_flows",
    "goose run",
)

ISSUE_AGENT_TASK_HEADINGS: tuple[str, ...] = (
    "Problem",
    "Proposed Solution",
    "Acceptance Criteria",
    "Agent Surface Routing",
    "Execution Notes",
)

ISSUE_BUG_REPORT_HEADINGS: tuple[str, ...] = (
    "Problem",
    "Steps to Reproduce",
    "Expected Behavior",
    "Actual Behavior",
    "Proposed Solution",
    "Acceptance Criteria",
    "Agent Surface Routing",
)

ISSUE_FEATURE_REQUEST_HEADINGS: tuple[str, ...] = (
    "Problem",
    "Proposed Solution",
    "Acceptance Criteria",
    "Agent Surface Routing",
)


CLAUDE_REQUIRED_SECTIONS: tuple[str, ...] = (
    "## Repo Identity",
    "## Agent Routing Matrix",
    "## State Residency Rules",
    "## Key Files",
    "## Negative Constraints (no agent may autonomously)",
    "## Escalation Format",
    "## Quarterly Review Triggers",
)

CLAUDE_REQUIRED_PHRASES: tuple[str, ...] = (
    "fuzzywigg/g0p-agents",
    "PikoClaw demo at Panathenea",
    "Documentation archive",
    "LIST B",
)

ESCALATION_FORMAT_PHRASES: tuple[str, ...] = (
    "From Agent:",
    "Conflict:",
    "Recommendation:",
    "Timeline:",
)

GOOSE_DOCS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Recipe-Based Agent Orchestration",
    "./agentic_flows/",
    "goose run",
)
GOOSE_HOWTO_REQUIRED_PHRASES: tuple[str, ...] = (
    "## How to Use These Recipes",
    "### Step 1: Individual Recipe (Single Agent)",
    "goose run ./agentic_flows/quantum_algorithm_design.yaml",
    "goose run ./agentic_flows/blockchain_contract_design.yaml",
    "goose run ./agentic_flows/edge_security_implementation.yaml",
    "### Step 2: Master Recipe (All Agents)",
    "goose run ./agentic_flows/quantum_nft_mint_orchestration.yaml",
)
GOOSE_STATE_MACHINE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Scratchpad State Machine",
    "./agentic_flows/scratchpad.txt",
    "## Task: Design Quantum-Safe NFT Mint",
    "Status: IN_PROGRESS",
    "Current Owner: EdgeSecurityAgent",
    "source of truth",
)
GOOSE_NAMING_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Recipe Naming Convention",
    "[domain]_[action]_[target].yaml",
    "quantum_algorithm_design.yaml",
    "blockchain_contract_design.yaml",
    "edge_security_implementation.yaml",
    "## Adding New Recipes",
    "Create new YAML file",
    "Follow the structure",
)
GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Recipe 1: Quantum Algorithm Design",
    "**File**: `./agentic_flows/quantum_algorithm_design.yaml`",
    "## Recipe 2: Smart Contract Design",
    "**File**: `./agentic_flows/blockchain_contract_design.yaml`",
    "## Recipe 3: On-Device Security Implementation",
    "**File**: `./agentic_flows/edge_security_implementation.yaml`",
    "## Recipe 4: Multi-Agent Orchestration (Master Recipe)",
    "**File**: `./agentic_flows/quantum_nft_mint_orchestration.yaml`",
)
GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "You are QuantumArchitectAgent designing a quantum algorithm for FUZZYWIGG.",
    "You are BlockchainArchitectAgent designing a smart contract for FUZZYWIGG.",
    "You are EdgeSecurityAgent implementing quantum-safe cryptography on mobile.",
    "You are OrchestrationAgent coordinating a complete quantum NFT mint operation.",
)
GOOSE_EXTENSIONS_REQUIRED_PHRASES: tuple[str, ...] = (
    "type: builtin",
    "name: developer",
    "timeout: 300",
    "timeout: 600",
)

GOOSE_ORCHESTRATION_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Master Orchestration Task: Quantum NFT Mint",
    "STEP 1: Initialize task in scratchpad",
    "STEP 2: Run QuantumArchitectAgent recipe",
    "STEP 3: Run BlockchainArchitectAgent recipe",
    "STEP 4: Run EdgeSecurityAgent recipe",
    "STEP 5: Review all three outputs",
    "STEP 6: Make final decision",
    "STEP 7: Escalation format (if needed)",
    "STEP 8: Log decision",
)
GOOSE_CONFLICTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Check for CONFLICTS:",
    "Conflict Type 1: PERFORMANCE",
    "Conflict Type 2: SECURITY",
    "Conflict Type 3: TIMELINE",
    "Decision: ✅ APPROVED FOR TESTNET DEPLOYMENT",
    "Decision: ⚠️ APPROVED WITH MODIFICATIONS",
    "Decision: 🚨 ESCALATE TO HUMAN",
    "## Decision: Quantum NFT Mint Deployment",
)
GOOSE_QUANTUM_TASK_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Quantum Algorithm Design Task",
    "STEP 1: Read the requirement",
    "PENDING_QUANTUM_DESIGN",
    "STEP 2: Design the circuit",
    "Use Google Cirq for circuit construction",
    "STEP 3: Validate quantum-safety",
    "STEP 4: Estimate constraints",
    "STEP 5: Update scratchpad",
    "Create Python file: ./quantum_circuits/[circuit_name].py",
)
PROMPT_ROLES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## 1. QuantumArchitectAgent Prompt Template",
    "You are the Quantum Computing specialist for the FUZZYWIGG-AI ecosystem.",
    "## 2. BlockchainArchitectAgent Prompt Template",
    "You are the Blockchain Development specialist for the FUZZYWIGG-AI ecosystem.",
    "## 3. EdgeSecurityAgent Prompt Template",
    "You are the On-Device Security specialist for the FUZZYWIGG-AI ecosystem.",
    "## 4. OrchestrationAgent Prompt Template",
    "You are the Strategic Orchestrator for the FUZZYWIGG-AI ecosystem.",
    "Your role is NOT to code. Your role is to COORDINATE.",
)
PROMPT_SECTIONS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Your Role",
    "## Core Responsibilities",
    "## Your Tools",
    "## Your Communication Style",
    "## Key Constraints (NEVER VIOLATE)",
    "## Escalation Triggers (STOP and Request Input)",
    "## Success Metrics",
    "## Related Documentation",
    "## Your Decision Authority",
    "## Conflict Resolution Matrix",
)
PROMPT_USAGE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Usage Instructions",
    "### For Each Agent Instantiation",
    "Copy the relevant prompt template",
    "[INSERT PROJECT-SPECIFIC INFO HERE]",
    "### Example: Instantiate QuantumArchitectAgent",
    "## Integration with AGENTS.md",
    "These prompts are **living documents**",
    "Risk tolerance thresholds change (quarterly)",
)
PROMPT_CONSTRAINTS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Never claim quantum-safety without formal verification",
    "Never design algorithms without NIST-standardized post-quantum validation",
    "Never deploy without post-quantum cryptography threat modeling",
    "Never skip security audit before mainnet deployment",
    "Never expose plaintext keys in RAM or logs",
    "Never block UI thread for crypto operations (async/background only)",
    "Never implement on-device crypto without HSM/secure enclave consideration",
    "Always include fallback to classical simulation",
)
PROMPT_TRIGGERS_REQUIRED_PHRASES: tuple[str, ...] = (
    "Circuit depth exceeds device constraints by >20%",
    "Error rate > 2% (unacceptable for security-critical ops)",
    "Security audit finds critical vulnerability",
    "Gas cost exceeds 10M (Ethereum network limit)",
    "Crypto operations > 500ms on target device",
    "Device memory < 2MB for circuit state",
    "## When You Escalate to Human",
    "ESCALATION TO HUMAN REQUIRED",
)
PROMPT_RELATED_DOCS_REQUIRED_PHRASES: tuple[str, ...] = (
    "See AGENTS.md Section 22 (Quantum-Blockchain Integration Standards)",
    "See AGENTS.md Section 22.4 (Agent Coordination Protocol)",
    "See AGENTS.md Section 22.5 (Recipe-Based Orchestration)",
    "See AGENTS.md Section 12.4 (Smart Contract Approval Matrix)",
    "See AGENTS.md Section 22.2 (On-Device Quantum Logic Execution)",
    "See AGENTS.md Section 22.7 (Conflict Resolution Matrix)",
    "Remember: You are not working alone",
    "Remember: You are the last line of defense before user devices",
)

IMPLEMENTATION_PHASES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Full Implementation (1-2 weeks)",
    "### Phase 1: Infrastructure (Days 1-2)",
    "### Phase 2: Define Specialist Agents (Days 2-3)",
    "### Phase 3: Create Goose Recipes (Days 3-4)",
    "### Phase 4: Set Up Scratchpad State Machine (Day 4)",
    "### Phase 5: Test the Workflow (Days 5-6)",
    "### Phase 6: Iterate & Refine (Days 6-10)",
    "docs/agents/quantum-architect-prompt.md",
    "agentic_flows/quantum_algorithm_design.yaml",
    "agentic_flows/quantum_nft_mint_orchestration.yaml",
)
IMPLEMENTATION_TOOLS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Tools & Software Checklist",
    "Python 3.11+",
    "Node.js 20.x LTS",
    "Docker Desktop",
    "Cirq (Python library)",
    "Hardhat (npm install -g hardhat)",
    "liboqs (post-quantum crypto library)",
    "Goose (agent orchestration framework)",
    "Docker Compose (container orchestration)",
)
IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Success Criteria",
    "**By End of Week 1**:",
    "**By End of Week 2**:",
    "**By End of Month**:",
    "## Common Issues & Solutions",
    "## FAQ",
    "## Next Steps",
    "postmortem.md has first entry",
    "Deployment to Sepolia testnet",
)
IMPLEMENTATION_ISSUES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Common Issues & Solutions",
    '### Issue 1: "Cirq is too slow for mobile"',
    "Use Qualtran to analyze circuit resource requirements",
    '### Issue 2: "Smart contract gas cost exceeds budget"',
    "Consider rollups (Arbitrum, Optimism)",
    '### Issue 3: "Mobile device can\'t run quantum circuit"',
    "Implement classical simulation fallback",
    '### Issue 4: "Agents can\'t reach consensus on design"',
    '### Issue 5: "Scratchpad gets out of sync"',
    "Scratchpad is append-only, never overwrite",
)
IMPLEMENTATION_FAQ_REQUIRED_PHRASES: tuple[str, ...] = (
    "## FAQ",
    "Do I need a real quantum computer to start?",
    "Cirq simulator works locally",
    "Can I use different LLMs for each agent?",
    "How often should I update AGENTS.md?",
    "Quarterly risk tolerance review",
    "Can I run agents in parallel?",
    "How do I measure agent quality?",
)
IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Support & Resources",
    "**Documentation**:",
    "AGENTS.md v2.2 (your constitution)",
    "AGENT-PROMPTS.md (specialist prompts)",
    "GOOSE-RECIPES.md (Goose recipe templates)",
    "**External Resources**:",
    "https://quantumai.google/cirq",
    "https://hardhat.org/",
    "https://block.github.io/goose/",
)


EXECUTION_TIMELINE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Implementation Timeline",
    "### Week 1 Checklist",
    "WSL2 development environment",
    "Goose recipes created",
    "### By End of Month",
    "Testnet deployment on Sepolia",
    "Ready for mainnet",
)
EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Key Technologies (All Covered)",
    "Google Cirq (circuit construction)",
    "Qualtran (algorithm analysis)",
    "Hardhat (development environment)",
    "liboqs (post-quantum on mobile)",
    "Goose (agent framework)",
    "Scratchpad state machine (checkpoint tracking)",
)
EXECUTION_WORKFLOW_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Workflow Overview",
    "### Step 1: Single Agent Task",
    "### Step 2: Multi-Agent Workflow",
    "### Step 3: Escalation (If Conflict)",
    "Agents Disagree → OrchestrationAgent Reviews",
)

EXECUTION_IDE_REQUIRED_PHRASES: tuple[str, ...] = (
    "## IDE & Software Setup",
    "**Required** (Days 1-2):",
    "Python 3.11+ (WSL2)",
    "Node.js 20.x LTS (WSL2)",
    "Docker Desktop (WSL2 backend)",
    "VS Code + extensions",
    "**Libraries** (install via setup script):",
    "Cirq + Qualtran",
    "**Total Setup Time**: ~1 hour (mostly downloads)",
)
EXECUTION_INNOVATIONS_REQUIRED_PHRASES: tuple[str, ...] = (
    "## What Makes This Different",
    "### Traditional Approach",
    "### Your Agentic Approach",
    "## Key Innovations in Your System",
    "**Quantum-Blockchain Bridge**: First formal protocol for integrating "
    "quantum algorithms into blockchain",
    "**Recipe-Based Orchestration**: Goose recipes enable reproducible workflows",
    "**Scratchpad State Machine**: Checkbox-based coordination (simple but effective)",
    "**Quarterly Risk Tolerance Review**: Formal process for increasing confidence over time",
    "**postmortem.md Incident Log**: Every decision and failure documented",
)
EXECUTION_NEXT48_REQUIRED_PHRASES: tuple[str, ...] = (
    "## Success Indicators",
    "## Common Pitfalls (Avoid These)",
    "## Next 48 Hours",
    "### Today (2025-12-13)",
    "### Tomorrow (2025-12-14)",
    "### Day After (2025-12-15)",
    "Instantiate first agent (QuantumArchitectAgent)",
    "Create first Goose recipe (copy from templates)",
)

CONTRIBUTING_BRANCH_SURFACES: tuple[str, ...] = ("copilot", "geryon", "cursor")

SCRATCHPAD_STATUS_MARKERS: tuple[str, ...] = (
    "DONE",
    "PENDING",
    "IN_PROGRESS",
    "BLOCKED",
)

SPECIALIST_AGENTS: tuple[str, ...] = DOCUMENTED_AGENTS[:-1]

MIN_COVERAGE_FAIL_UNDER = 99
MIN_VALIDATOR_COUNT = 172


@dataclass(frozen=True)
class Finding:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


ValidatorFn = Callable[[Path], list[Finding]]


def load_schema(name: str, *, schemas_dir: Path | None = None) -> dict[str, Any]:
    """Load a JSON schema shipped with this validator (not from --root)."""
    base = schemas_dir or SCHEMAS
    schema_path = base / name
    with schema_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_against_schema(
    instance: Any, schema: dict[str, Any], *, path: str
) -> list[Finding]:
    validator = Draft202012Validator(schema)
    return [
        Finding(path, f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}")
        for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    ]


def extract_fenced_yaml_blocks(markdown: str) -> list[str]:
    """Extract top-level ```yaml / ```yml fences (column-0 closers only)."""
    blocks: list[str] = []
    lines = markdown.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```yaml") or line.startswith("```yml"):
            i += 1
            buf: list[str] = []
            while i < len(lines) and lines[i].rstrip("\n") != "```":
                buf.append(lines[i])
                i += 1
            blocks.append("".join(buf))
        i += 1
    return blocks


def extract_fenced_markdown_blocks(markdown: str) -> list[str]:
    """Extract top-level ```markdown fences (column-0 closers only)."""
    blocks: list[str] = []
    lines = markdown.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```markdown"):
            i += 1
            buf: list[str] = []
            while i < len(lines) and lines[i].rstrip("\n") != "```":
                buf.append(lines[i])
                i += 1
            blocks.append("".join(buf))
        i += 1
    return blocks


def parse_yaml_text(text: str, *, path: str) -> tuple[Any | None, list[Finding]]:
    try:
        return yaml.safe_load(text), []
    except yaml.YAMLError as exc:
        return None, [Finding(path, f"YAML parse error: {exc}")]


def extract_yaml_frontmatter(text: str) -> tuple[str | None, list[Finding]]:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, [Finding("<frontmatter>", "missing opening --- frontmatter delimiter")]
    lines = text.splitlines(keepends=True)
    body: list[str] = []
    closed = False
    for line in lines[1:]:
        if line.strip("\r\n") == "---":
            closed = True
            break
        body.append(line)
    if not closed:
        return None, [Finding("<frontmatter>", "missing closing --- frontmatter delimiter")]
    return "".join(body), []


def extract_frontmatter_body(text: str) -> str:
    """Return markdown body after YAML frontmatter, or empty string if none."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return text
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines[1:], start=1):
        if line.strip("\r\n") == "---":
            return "".join(lines[index + 1 :])
    return ""


def documented_recipe_file_paths(markdown: str) -> list[str]:
    """Collect `./agentic_flows/*.yaml` paths declared beside recipes in GOOSE-RECIPES.md."""
    paths: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("**File**:") and "agentic_flows/" in stripped:
            start = stripped.find("`")
            end = stripped.rfind("`")
            if start != -1 and end > start:
                paths.append(stripped[start + 1 : end].lstrip("./"))
    return paths


def agent_tokens(text: str) -> set[str]:
    return set(AGENT_TOKEN_RE.findall(text))


def _lock_mismatch(path: str, field: str) -> Finding:
    return Finding(path, f"{field} do not match locked validator constants")


def validate_schemas_meta(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schemas_dir = root / "schemas"
    if not schemas_dir.is_dir():
        return [Finding("schemas", "schemas directory missing")]

    on_disk = {path.name for path in schemas_dir.glob("*.schema.json")}
    expected = set(SCHEMA_FILES)
    for orphan in sorted(on_disk - expected):
        findings.append(Finding(f"schemas/{orphan}", "unexpected/orphan schema file"))
    for missing in sorted(expected - on_disk):
        findings.append(Finding(f"schemas/{missing}", "required schema file missing"))

    for name in SCHEMA_FILES:
        rel = f"schemas/{name}"
        path = root / rel
        if not path.is_file():
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding(rel, f"JSON parse error: {exc}"))
            continue
        if not isinstance(schema, dict):
            findings.append(Finding(rel, "schema root must be a mapping"))
            continue
        draft = schema.get("$schema")
        if draft != SCHEMA_DRAFT_URI:
            findings.append(
                Finding(rel, f"$schema must be {SCHEMA_DRAFT_URI}, found {draft!r}")
            )
        schema_id = schema.get("$id")
        expected_id = f"{SCHEMA_ID_PREFIX}{name}"
        if schema_id != expected_id:
            findings.append(
                Finding(rel, f"$id must be {expected_id}, found {schema_id!r}")
            )
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            findings.append(Finding(rel, f"invalid JSON Schema: {exc}"))
    return findings


def validate_packaging_inventory(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    inventory_path = root / "schemas" / "packaging-inventory.json"
    schema_path = "schemas/packaging-inventory.json"
    if not inventory_path.is_file():
        return [Finding(schema_path, "packaging inventory missing")]
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Finding(schema_path, f"JSON parse error: {exc}")]

    findings.extend(
        validate_against_schema(
            inventory,
            load_schema("packaging-inventory.schema.json"),
            path=schema_path,
        )
    )
    if findings:
        return findings

    if inventory.get("version") != INVENTORY_VERSION:
        findings.append(_lock_mismatch(schema_path, "version"))

    for rel in inventory["required_paths"]:
        if not (root / rel).exists():
            findings.append(Finding(rel, "required packaging path missing"))

    if tuple(inventory["documented_agents"]) != DOCUMENTED_AGENTS:
        findings.append(_lock_mismatch(schema_path, "documented_agents"))

    if frozenset(inventory["expected_recipe_names"]) != EXPECTED_RECIPE_NAMES:
        findings.append(_lock_mismatch(schema_path, "expected_recipe_names"))

    if tuple(inventory["expected_recipe_files"]) != EXPECTED_RECIPE_FILES:
        findings.append(_lock_mismatch(schema_path, "expected_recipe_files"))

    if dict(inventory["recipe_bindings"]) != EXPECTED_RECIPE_BINDINGS:
        findings.append(_lock_mismatch(schema_path, "recipe_bindings"))

    if dict(inventory["recipe_primary_agents"]) != RECIPE_PRIMARY_AGENT:
        findings.append(_lock_mismatch(schema_path, "recipe_primary_agents"))

    if frozenset(inventory["required_ci_jobs"]) != REQUIRED_CI_JOBS:
        findings.append(_lock_mismatch(schema_path, "required_ci_jobs"))

    if tuple(inventory["required_python_versions"]) != REQUIRED_PYTHON_VERSIONS:
        findings.append(_lock_mismatch(schema_path, "required_python_versions"))

    if tuple(inventory["required_manifest_step_markers"]) != REQUIRED_MANIFEST_STEP_MARKERS:
        findings.append(_lock_mismatch(schema_path, "required_manifest_step_markers"))

    if tuple(inventory["required_schema_files"]) != SCHEMA_FILES:
        findings.append(_lock_mismatch(schema_path, "required_schema_files"))

    if frozenset(inventory["required_dev_packages"]) != REQUIRED_DEV_PACKAGES:
        findings.append(_lock_mismatch(schema_path, "required_dev_packages"))

    if tuple(inventory["github_agent_files"]) != GITHUB_AGENT_FILES:
        findings.append(_lock_mismatch(schema_path, "github_agent_files"))

    if tuple(inventory["issue_template_files"]) != ISSUE_TEMPLATE_FILES:
        findings.append(_lock_mismatch(schema_path, "issue_template_files"))

    if tuple(inventory["pr_template_headings"]) != PR_TEMPLATE_HEADINGS:
        findings.append(_lock_mismatch(schema_path, "pr_template_headings"))

    settings = inventory["historic_goose_settings"]
    if (
        settings.get("goose_provider") != HISTORIC_GOOSE_PROVIDER
        or settings.get("goose_model") != HISTORIC_GOOSE_MODEL
        or settings.get("extension_type") != HISTORIC_EXTENSION_TYPE
        or settings.get("extension_name") != HISTORIC_EXTENSION_NAME
    ):
        findings.append(_lock_mismatch(schema_path, "historic_goose_settings"))

    if inventory.get("orchestration_recipe_name") != ORCHESTRATION_RECIPE_NAME:
        findings.append(_lock_mismatch(schema_path, "orchestration_recipe_name"))

    if tuple(inventory.get("routing_surfaces", ())) != ROUTING_SURFACES:
        findings.append(_lock_mismatch(schema_path, "routing_surfaces"))

    if inventory.get("constitution_heading_prefix") != CONSTITUTION_HEADING_PREFIX:
        findings.append(_lock_mismatch(schema_path, "constitution_heading_prefix"))

    if inventory.get("prompt_system_header_suffix") != PROMPT_SYSTEM_HEADER_SUFFIX:
        findings.append(_lock_mismatch(schema_path, "prompt_system_header_suffix"))

    if inventory.get("specialist_escalation_marker") != SPECIALIST_ESCALATION_MARKER:
        findings.append(_lock_mismatch(schema_path, "specialist_escalation_marker"))

    if inventory.get("orchestration_escalation_marker") != ORCHESTRATION_ESCALATION_MARKER:
        findings.append(_lock_mismatch(schema_path, "orchestration_escalation_marker"))

    if tuple(inventory.get("agent_token_scan_docs", ())) != AGENT_TOKEN_SCAN_DOCS:
        findings.append(_lock_mismatch(schema_path, "agent_token_scan_docs"))

    if tuple(inventory.get("readme_required_phrases", ())) != README_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "readme_required_phrases"))

    if tuple(inventory.get("security_required_phrases", ())) != SECURITY_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "security_required_phrases"))

    if tuple(inventory.get("contributing_required_phrases", ())) != CONTRIBUTING_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "contributing_required_phrases"))

    if tuple(inventory.get("issue_agent_task_headings", ())) != ISSUE_AGENT_TASK_HEADINGS:
        findings.append(_lock_mismatch(schema_path, "issue_agent_task_headings"))

    if tuple(inventory.get("issue_bug_report_headings", ())) != ISSUE_BUG_REPORT_HEADINGS:
        findings.append(_lock_mismatch(schema_path, "issue_bug_report_headings"))

    if (
        tuple(inventory.get("issue_feature_request_headings", ()))
        != ISSUE_FEATURE_REQUEST_HEADINGS
    ):
        findings.append(_lock_mismatch(schema_path, "issue_feature_request_headings"))

    if tuple(inventory.get("required_archive_docs", ())) != REQUIRED_ARCHIVE_DOCS:
        findings.append(_lock_mismatch(schema_path, "required_archive_docs"))

    if tuple(inventory.get("known_yaml_configs", ())) != KNOWN_YAML_CONFIG_RELS:
        findings.append(_lock_mismatch(schema_path, "known_yaml_configs"))

    if inventory.get("cursor_environment_name") != CURSOR_ENVIRONMENT_NAME:
        findings.append(_lock_mismatch(schema_path, "cursor_environment_name"))

    if inventory.get("dependabot_schedule_interval") != DEPENDABOT_SCHEDULE_INTERVAL:
        findings.append(_lock_mismatch(schema_path, "dependabot_schedule_interval"))

    if inventory.get("ci_permissions_contents") != CI_PERMISSIONS_CONTENTS:
        findings.append(_lock_mismatch(schema_path, "ci_permissions_contents"))

    if inventory.get("ci_artifact_name_prefix") != CI_ARTIFACT_NAME_PREFIX:
        findings.append(_lock_mismatch(schema_path, "ci_artifact_name_prefix"))

    if inventory.get("ci_pull_request_branch") != CI_PULL_REQUEST_BRANCH:
        findings.append(_lock_mismatch(schema_path, "ci_pull_request_branch"))

    if inventory.get("pyproject_requires_python") != PYPROJECT_REQUIRES_PYTHON:
        findings.append(_lock_mismatch(schema_path, "pyproject_requires_python"))

    if inventory.get("markdownlint_default") is not MARKDOWNLINT_DEFAULT:
        findings.append(_lock_mismatch(schema_path, "markdownlint_default"))

    if inventory.get("markdownlint_md013_line_length") != MARKDOWNLINT_MD013_LINE_LENGTH:
        findings.append(_lock_mismatch(schema_path, "markdownlint_md013_line_length"))

    if tuple(inventory.get("scratchpad_required_phrases", ())) != SCRATCHPAD_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "scratchpad_required_phrases"))

    if tuple(inventory.get("changelog_required_phrases", ())) != CHANGELOG_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "changelog_required_phrases"))

    if tuple(inventory.get("postmortem_required_phrases", ())) != POSTMORTEM_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "postmortem_required_phrases"))

    if tuple(inventory.get("gitignore_required_patterns", ())) != GITIGNORE_REQUIRED_PATTERNS:
        findings.append(_lock_mismatch(schema_path, "gitignore_required_patterns"))

    if (
        tuple(inventory.get("negative_constraint_phrases", ()))
        != NEGATIVE_CONSTRAINT_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "negative_constraint_phrases"))

    if inventory.get("license_copyright_holder") != LICENSE_COPYRIGHT_HOLDER:
        findings.append(_lock_mismatch(schema_path, "license_copyright_holder"))

    if inventory.get("historic_recipe_version") != HISTORIC_RECIPE_VERSION:
        findings.append(_lock_mismatch(schema_path, "historic_recipe_version"))

    if frozenset(inventory.get("dependabot_ecosystems", ())) != DEPENDABOT_ECOSYSTEMS:
        findings.append(_lock_mismatch(schema_path, "dependabot_ecosystems"))

    if inventory.get("ci_concurrency_group_prefix") != CI_CONCURRENCY_GROUP_PREFIX:
        findings.append(_lock_mismatch(schema_path, "ci_concurrency_group_prefix"))

    if inventory.get("ci_artifact_upload_if") != CI_ARTIFACT_UPLOAD_IF:
        findings.append(_lock_mismatch(schema_path, "ci_artifact_upload_if"))

    if inventory.get("pyproject_ruff_target_version") != PYPROJECT_RUFF_TARGET_VERSION:
        findings.append(_lock_mismatch(schema_path, "pyproject_ruff_target_version"))

    if inventory.get("github_agent_name") != GITHUB_AGENT_NAME:
        findings.append(_lock_mismatch(schema_path, "github_agent_name"))

    if frozenset(inventory.get("agentic_flows_allowed_files", ())) != AGENTIC_FLOWS_ALLOWED_FILES:
        findings.append(_lock_mismatch(schema_path, "agentic_flows_allowed_files"))

    if frozenset(inventory.get("dependabot_group_names", ())) != DEPENDABOT_GROUP_NAMES:
        findings.append(_lock_mismatch(schema_path, "dependabot_group_names"))

    if inventory.get("ci_cancel_in_progress") is not CI_CANCEL_IN_PROGRESS:
        findings.append(_lock_mismatch(schema_path, "ci_cancel_in_progress"))

    if inventory.get("ci_fail_fast") is not CI_FAIL_FAST:
        findings.append(_lock_mismatch(schema_path, "ci_fail_fast"))

    if inventory.get("coverage_branch") is not COVERAGE_BRANCH:
        findings.append(_lock_mismatch(schema_path, "coverage_branch"))

    if inventory.get("license_copyright_marker") != LICENSE_COPYRIGHT_MARKER:
        findings.append(_lock_mismatch(schema_path, "license_copyright_marker"))

    if (
        tuple(inventory.get("cursor_install_required_refs", ()))
        != CURSOR_INSTALL_REQUIRED_REFS
    ):
        findings.append(_lock_mismatch(schema_path, "cursor_install_required_refs"))

    if tuple(inventory.get("hydration_required_sections", ())) != HYDRATION_REQUIRED_SECTIONS:
        findings.append(_lock_mismatch(schema_path, "hydration_required_sections"))

    if (
        tuple(inventory.get("execution_summary_required_phrases", ()))
        != EXECUTION_SUMMARY_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "execution_summary_required_phrases"))

    if (
        tuple(inventory.get("implementation_guide_required_phrases", ()))
        != IMPLEMENTATION_GUIDE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_guide_required_phrases")
        )

    if tuple(inventory.get("specialist_agents", ())) != SPECIALIST_AGENTS:
        findings.append(_lock_mismatch(schema_path, "specialist_agents"))

    if inventory.get("schema_draft_uri") != SCHEMA_DRAFT_URI:
        findings.append(_lock_mismatch(schema_path, "schema_draft_uri"))

    if inventory.get("schema_id_prefix") != SCHEMA_ID_PREFIX:
        findings.append(_lock_mismatch(schema_path, "schema_id_prefix"))

    if tuple(inventory.get("claude_required_sections", ())) != CLAUDE_REQUIRED_SECTIONS:
        findings.append(_lock_mismatch(schema_path, "claude_required_sections"))

    if (
        tuple(inventory.get("contributing_branch_surfaces", ()))
        != CONTRIBUTING_BRANCH_SURFACES
    ):
        findings.append(_lock_mismatch(schema_path, "contributing_branch_surfaces"))

    if tuple(inventory.get("scratchpad_status_markers", ())) != SCRATCHPAD_STATUS_MARKERS:
        findings.append(_lock_mismatch(schema_path, "scratchpad_status_markers"))

    if frozenset(inventory.get("dependabot_directories", ())) != DEPENDABOT_DIRECTORIES:
        findings.append(_lock_mismatch(schema_path, "dependabot_directories"))

    if dict(inventory.get("recipe_titles", {})) != RECIPE_TITLES:
        findings.append(_lock_mismatch(schema_path, "recipe_titles"))

    if tuple(inventory.get("ci_required_actions", ())) != CI_REQUIRED_ACTIONS:
        findings.append(_lock_mismatch(schema_path, "ci_required_actions"))

    if inventory.get("pyproject_name") != PYPROJECT_NAME:
        findings.append(_lock_mismatch(schema_path, "pyproject_name"))

    if tuple(inventory.get("claude_required_phrases", ())) != CLAUDE_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "claude_required_phrases"))

    if (
        tuple(inventory.get("escalation_format_phrases", ()))
        != ESCALATION_FORMAT_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "escalation_format_phrases"))

    if (
        tuple(inventory.get("goose_docs_required_phrases", ()))
        != GOOSE_DOCS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "goose_docs_required_phrases"))

    if dict(inventory.get("issue_template_names", {})) != ISSUE_TEMPLATE_NAMES:
        findings.append(_lock_mismatch(schema_path, "issue_template_names"))

    if dict(inventory.get("issue_template_abouts", {})) != ISSUE_TEMPLATE_ABOUTS:
        findings.append(_lock_mismatch(schema_path, "issue_template_abouts"))

    if tuple(inventory.get("readme_badge_phrases", ())) != README_BADGE_PHRASES:
        findings.append(_lock_mismatch(schema_path, "readme_badge_phrases"))

    if (
        tuple(inventory.get("quarterly_review_phrases", ()))
        != QUARTERLY_REVIEW_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "quarterly_review_phrases"))

    if inventory.get("ci_workflow_name") != CI_WORKFLOW_NAME:
        findings.append(_lock_mismatch(schema_path, "ci_workflow_name"))

    if (
        tuple(inventory.get("ci_required_text_markers", ()))
        != CI_REQUIRED_TEXT_MARKERS
    ):
        findings.append(_lock_mismatch(schema_path, "ci_required_text_markers"))

    if inventory.get("markdownlint_md025") is not MARKDOWNLINT_MD025:
        findings.append(_lock_mismatch(schema_path, "markdownlint_md025"))

    if inventory.get("markdownlint_md033") is not MARKDOWNLINT_MD033:
        findings.append(_lock_mismatch(schema_path, "markdownlint_md033"))

    if (
        inventory.get("markdownlint_md024_siblings_only")
        is not MARKDOWNLINT_MD024_SIBLINGS_ONLY
    ):
        findings.append(
            _lock_mismatch(schema_path, "markdownlint_md024_siblings_only")
        )

    if (
        tuple(inventory.get("pyproject_ruff_lint_select", ()))
        != PYPROJECT_RUFF_LINT_SELECT
    ):
        findings.append(_lock_mismatch(schema_path, "pyproject_ruff_lint_select"))

    if inventory.get("ci_link_check_args") != CI_LINK_CHECK_ARGS:
        findings.append(_lock_mismatch(schema_path, "ci_link_check_args"))

    if inventory.get("ci_link_check_fail") is not CI_LINK_CHECK_FAIL:
        findings.append(_lock_mismatch(schema_path, "ci_link_check_fail"))

    if inventory.get("ci_markdown_lint_globs") != CI_MARKDOWN_LINT_GLOBS:
        findings.append(_lock_mismatch(schema_path, "ci_markdown_lint_globs"))

    if inventory.get("ci_markdown_lint_config") != CI_MARKDOWN_LINT_CONFIG:
        findings.append(_lock_mismatch(schema_path, "ci_markdown_lint_config"))

    if inventory.get("ci_cache_dependency_path") != CI_CACHE_DEPENDENCY_PATH:
        findings.append(_lock_mismatch(schema_path, "ci_cache_dependency_path"))

    if dict(inventory.get("ci_job_display_names", {})) != CI_JOB_DISPLAY_NAMES:
        findings.append(_lock_mismatch(schema_path, "ci_job_display_names"))

    if inventory.get("github_agent_description") != GITHUB_AGENT_DESCRIPTION:
        findings.append(_lock_mismatch(schema_path, "github_agent_description"))

    if inventory.get("pyproject_version") != PYPROJECT_VERSION:
        findings.append(_lock_mismatch(schema_path, "pyproject_version"))

    if inventory.get("pyproject_license_text") != PYPROJECT_LICENSE_TEXT:
        findings.append(_lock_mismatch(schema_path, "pyproject_license_text"))

    if inventory.get("pyproject_line_length") != PYPROJECT_LINE_LENGTH:
        findings.append(_lock_mismatch(schema_path, "pyproject_line_length"))

    if tuple(inventory.get("pyproject_ruff_src", ())) != PYPROJECT_RUFF_SRC:
        findings.append(_lock_mismatch(schema_path, "pyproject_ruff_src"))

    if inventory.get("pytest_addopts") != PYTEST_ADDOPTS:
        findings.append(_lock_mismatch(schema_path, "pytest_addopts"))

    if inventory.get("coverage_show_missing") is not COVERAGE_SHOW_MISSING:
        findings.append(_lock_mismatch(schema_path, "coverage_show_missing"))

    if inventory.get("coverage_skip_empty") is not COVERAGE_SKIP_EMPTY:
        findings.append(_lock_mismatch(schema_path, "coverage_skip_empty"))

    if inventory.get("markdownlint_md013_tables") is not MARKDOWNLINT_MD013_TABLES:
        findings.append(_lock_mismatch(schema_path, "markdownlint_md013_tables"))

    if (
        inventory.get("markdownlint_md013_code_blocks")
        is not MARKDOWNLINT_MD013_CODE_BLOCKS
    ):
        findings.append(_lock_mismatch(schema_path, "markdownlint_md013_code_blocks"))

    if inventory.get("ci_runs_on") != CI_RUNS_ON:
        findings.append(_lock_mismatch(schema_path, "ci_runs_on"))

    if (
        inventory.get("ci_artifact_if_no_files_found")
        != CI_ARTIFACT_IF_NO_FILES_FOUND
    ):
        findings.append(_lock_mismatch(schema_path, "ci_artifact_if_no_files_found"))

    if tuple(inventory.get("ci_artifact_paths", ())) != CI_ARTIFACT_PATHS:
        findings.append(_lock_mismatch(schema_path, "ci_artifact_paths"))

    if inventory.get("ci_actionlint_shell") != CI_ACTIONLINT_SHELL:
        findings.append(_lock_mismatch(schema_path, "ci_actionlint_shell"))

    if inventory.get("ci_actionlint_step_id") != CI_ACTIONLINT_STEP_ID:
        findings.append(_lock_mismatch(schema_path, "ci_actionlint_step_id"))

    if inventory.get("pyproject_description") != PYPROJECT_DESCRIPTION:
        findings.append(_lock_mismatch(schema_path, "pyproject_description"))

    if inventory.get("pyproject_readme") != PYPROJECT_README:
        findings.append(_lock_mismatch(schema_path, "pyproject_readme"))

    if tuple(inventory.get("pytest_testpaths", ())) != PYTEST_TESTPATHS:
        findings.append(_lock_mismatch(schema_path, "pytest_testpaths"))

    if tuple(inventory.get("pytest_pythonpath", ())) != PYTEST_PYTHONPATH:
        findings.append(_lock_mismatch(schema_path, "pytest_pythonpath"))

    if tuple(inventory.get("coverage_source", ())) != COVERAGE_SOURCE:
        findings.append(_lock_mismatch(schema_path, "coverage_source"))

    if inventory.get("ci_setup_python_cache") != CI_SETUP_PYTHON_CACHE:
        findings.append(_lock_mismatch(schema_path, "ci_setup_python_cache"))

    if inventory.get("ci_ruff_check_command") != CI_RUFF_CHECK_COMMAND:
        findings.append(_lock_mismatch(schema_path, "ci_ruff_check_command"))

    if (
        tuple(inventory.get("license_required_phrases", ()))
        != LICENSE_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "license_required_phrases"))

    if inventory.get("ci_pip_install_command") != CI_PIP_INSTALL_COMMAND:
        findings.append(_lock_mismatch(schema_path, "ci_pip_install_command"))

    if inventory.get("ci_pip_check_command") != CI_PIP_CHECK_COMMAND:
        findings.append(_lock_mismatch(schema_path, "ci_pip_check_command"))

    if (
        tuple(inventory.get("ci_pytest_required_markers", ()))
        != CI_PYTEST_REQUIRED_MARKERS
    ):
        findings.append(_lock_mismatch(schema_path, "ci_pytest_required_markers"))

    if (
        tuple(inventory.get("state_residency_required_phrases", ()))
        != STATE_RESIDENCY_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "state_residency_required_phrases"))

    if (
        tuple(inventory.get("key_files_required_entries", ()))
        != KEY_FILES_REQUIRED_ENTRIES
    ):
        findings.append(_lock_mismatch(schema_path, "key_files_required_entries"))

    if (
        tuple(inventory.get("pr_routing_required_fields", ()))
        != PR_ROUTING_REQUIRED_FIELDS
    ):
        findings.append(_lock_mismatch(schema_path, "pr_routing_required_fields"))

    if (
        tuple(inventory.get("routing_matrix_required_phrases", ()))
        != ROUTING_MATRIX_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "routing_matrix_required_phrases"))

    if (
        tuple(inventory.get("repo_identity_required_phrases", ()))
        != REPO_IDENTITY_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "repo_identity_required_phrases"))

    if (
        tuple(inventory.get("escalation_block_required_phrases", ()))
        != ESCALATION_BLOCK_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "escalation_block_required_phrases")
        )

    if (
        tuple(inventory.get("routing_matrix_rationale_phrases", ()))
        != ROUTING_MATRIX_RATIONALE_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "routing_matrix_rationale_phrases"))

    if (
        tuple(inventory.get("claude_metadata_required_phrases", ()))
        != CLAUDE_METADATA_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "claude_metadata_required_phrases"))

    if (
        tuple(inventory.get("escalation_usage_required_phrases", ()))
        != ESCALATION_USAGE_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "escalation_usage_required_phrases"))

    if (
        tuple(inventory.get("security_supported_required_phrases", ()))
        != SECURITY_SUPPORTED_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_supported_required_phrases")
        )

    if (
        tuple(inventory.get("security_reporting_required_phrases", ()))
        != SECURITY_REPORTING_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_reporting_required_phrases")
        )

    if (
        tuple(inventory.get("security_standards_required_phrases", ()))
        != SECURITY_STANDARDS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_standards_required_phrases")
        )

    if (
        tuple(inventory.get("security_header_required_phrases", ()))
        != SECURITY_HEADER_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_header_required_phrases")
        )

    if (
        tuple(inventory.get("security_fips_required_phrases", ()))
        != SECURITY_FIPS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "security_fips_required_phrases"))

    if (
        tuple(inventory.get("security_known_non_issues_required_phrases", ()))
        != SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_known_non_issues_required_phrases")
        )

    if (
        tuple(inventory.get("security_scope_required_phrases", ()))
        != SECURITY_SCOPE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_scope_required_phrases")
        )

    if (
        tuple(inventory.get("security_reporting_channel_required_phrases", ()))
        != SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_reporting_channel_required_phrases")
        )

    if (
        tuple(inventory.get("security_compliance_detail_required_phrases", ()))
        != SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "security_compliance_detail_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_crypto_required_phrases", ()))
        != CONSTITUTION_CRYPTO_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_crypto_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_handoff_required_phrases", ()))
        != CONSTITUTION_HANDOFF_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_handoff_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_escalation_matrix_required_phrases", ()))
        != CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "constitution_escalation_matrix_required_phrases"
            )
        )



    if (
        tuple(inventory.get("constitution_on_device_required_phrases", ()))
        != CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_on_device_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_multichain_required_phrases", ()))
        != CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_multichain_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_escalation_format_required_phrases", ()))
        != CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "constitution_escalation_format_required_phrases"
            )
        )

    if (
        tuple(inventory.get("constitution_recipe_orchestration_required_phrases", ()))
        != CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "constitution_recipe_orchestration_required_phrases"
            )
        )

    if (
        tuple(inventory.get("constitution_scratchpad_state_required_phrases", ()))
        != CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "constitution_scratchpad_state_required_phrases"
            )
        )

    if (
        tuple(inventory.get("constitution_conflict_matrix_required_phrases", ()))
        != CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "constitution_conflict_matrix_required_phrases"
            )
        )

    if (
        tuple(inventory.get("changelog_format_required_phrases", ()))
        != CHANGELOG_FORMAT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_format_required_phrases")
        )

    if (
        tuple(inventory.get("changelog_unreleased_required_phrases", ()))
        != CHANGELOG_UNRELEASED_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_unreleased_required_phrases")
        )

    if (
        tuple(inventory.get("changelog_release_required_phrases", ()))
        != CHANGELOG_RELEASE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_release_required_phrases")
        )


    if (
        tuple(inventory.get("implementation_quickstart_required_phrases", ()))
        != IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_quickstart_required_phrases")
        )

    if (
        tuple(inventory.get("execution_specialists_required_phrases", ()))
        != EXECUTION_SPECIALISTS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_specialists_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_list_b_required_phrases", ()))
        != HYDRATION_LIST_B_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_list_b_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_phase1_required_phrases", ()))
        != HYDRATION_PHASE1_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_phase1_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_list_a_required_phrases", ()))
        != HYDRATION_LIST_A_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_list_a_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_resolved_required_phrases", ()))
        != HYDRATION_RESOLVED_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_resolved_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_phase4_required_phrases", ()))
        != HYDRATION_PHASE4_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_phase4_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_deferred_required_phrases", ()))
        != HYDRATION_DEFERRED_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_deferred_required_phrases")
        )


    if (
        tuple(inventory.get("hydration_meta_required_phrases", ()))
        != HYDRATION_META_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_meta_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_identity_detail_required_phrases", ()))
        != HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_identity_detail_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_git_detail_required_phrases", ()))
        != HYDRATION_GIT_DETAIL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_git_detail_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_phase2_required_phrases", ()))
        != HYDRATION_PHASE2_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_phase2_required_phrases")
        )

    if (
        tuple(inventory.get("hydration_phase5_required_phrases", ()))
        != HYDRATION_PHASE5_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "hydration_phase5_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_ide_stack_required_phrases", ()))
        != CONSTITUTION_IDE_STACK_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_ide_stack_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_install_script_required_phrases", ()))
        != CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_install_script_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_vscode_required_phrases", ()))
        != CONSTITUTION_VSCODE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_vscode_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_hard_constraints_required_phrases", ()))
        != CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_hard_constraints_required_phrases")
        )

    if (
        tuple(inventory.get("constitution_risk_tolerance_required_phrases", ()))
        != CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "constitution_risk_tolerance_required_phrases")
        )

    if (
        tuple(inventory.get("changelog_preamble_required_phrases", ()))
        != CHANGELOG_PREAMBLE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_preamble_required_phrases")
        )

    if (
        tuple(inventory.get("changelog_changed_required_phrases", ()))
        != CHANGELOG_CHANGED_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_changed_required_phrases")
        )

    if (
        tuple(inventory.get("changelog_initial_required_phrases", ()))
        != CHANGELOG_INITIAL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "changelog_initial_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_expertise_required_phrases", ()))
        != PROMPT_EXPERTISE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_expertise_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_principles_required_phrases", ()))
        != PROMPT_PRINCIPLES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_principles_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_metrics_required_phrases", ()))
        != PROMPT_METRICS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_metrics_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_tools_required_phrases", ()))
        != PROMPT_TOOLS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_tools_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_communication_required_phrases", ()))
        != PROMPT_COMMUNICATION_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_communication_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_escalation_identity_required_phrases", ()))
        != PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "prompt_escalation_identity_required_phrases"
            )
        )


    if (
        tuple(inventory.get("prompt_orchestration_matrix_required_phrases", ()))
        != PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "prompt_orchestration_matrix_required_phrases"
            )
        )

    if (
        tuple(inventory.get("prompt_monthly_required_phrases", ()))
        != PROMPT_MONTHLY_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_monthly_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_usage_example_required_phrases", ()))
        != PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_usage_example_required_phrases")
        )


    if (
        tuple(inventory.get("prompt_context_required_phrases", ()))
        != PROMPT_CONTEXT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_context_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_decision_authority_required_phrases", ()))
        != PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_decision_authority_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_escalation_authority_required_phrases", ()))
        != PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(
                schema_path, "prompt_escalation_authority_required_phrases"
            )
        )



    if (
        tuple(inventory.get("prompt_responsibilities_required_phrases", ()))
        != PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_responsibilities_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_cannot_delegate_required_phrases", ()))
        != PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_cannot_delegate_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_human_escalation_required_phrases", ()))
        != PROMPT_HUMAN_ESCALATION_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_human_escalation_required_phrases")
        )


    if (
        tuple(inventory.get("postmortem_intro_required_phrases", ()))
        != POSTMORTEM_INTRO_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "postmortem_intro_required_phrases"))

    if (
        tuple(inventory.get("postmortem_field_required_phrases", ()))
        != POSTMORTEM_FIELD_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "postmortem_field_required_phrases"))

    if (
        tuple(inventory.get("postmortem_next_steps_required_phrases", ()))
        != POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "postmortem_next_steps_required_phrases")
        )

    if (
        tuple(inventory.get("scratchpad_intro_required_phrases", ()))
        != SCRATCHPAD_INTRO_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "scratchpad_intro_required_phrases"))

    if (
        tuple(inventory.get("scratchpad_format_required_phrases", ()))
        != SCRATCHPAD_FORMAT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "scratchpad_format_required_phrases")
        )

    if (
        tuple(inventory.get("scratchpad_task_meta_required_phrases", ()))
        != SCRATCHPAD_TASK_META_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "scratchpad_task_meta_required_phrases")
        )

    if (
        tuple(inventory.get("issue_metadata_required_phrases", ()))
        != ISSUE_METADATA_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "issue_metadata_required_phrases"))

    if (
        tuple(inventory.get("issue_routing_required_phrases", ()))
        != ISSUE_ROUTING_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "issue_routing_required_phrases"))

    if (
        tuple(inventory.get("bug_repro_required_phrases", ()))
        != BUG_REPRO_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "bug_repro_required_phrases"))

    if (
        tuple(inventory.get("contributing_who_required_phrases", ()))
        != CONTRIBUTING_WHO_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_who_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_branch_required_phrases", ()))
        != CONTRIBUTING_BRANCH_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_branch_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_pr_required_phrases", ()))
        != CONTRIBUTING_PR_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "contributing_pr_required_phrases"))

    if (
        tuple(inventory.get("pr_summary_required_phrases", ()))
        != PR_SUMMARY_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "pr_summary_required_phrases"))

    if (
        tuple(inventory.get("pr_acceptance_required_phrases", ()))
        != PR_ACCEPTANCE_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "pr_acceptance_required_phrases"))

    if (
        tuple(inventory.get("pr_notes_required_phrases", ()))
        != PR_NOTES_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "pr_notes_required_phrases"))

    if (
        tuple(inventory.get("readme_honesty_required_phrases", ()))
        != README_HONESTY_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_honesty_required_phrases"))

    if (
        tuple(inventory.get("readme_historic_required_phrases", ()))
        != README_HISTORIC_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_historic_required_phrases"))

    if (
        tuple(inventory.get("readme_contents_required_phrases", ()))
        != README_CONTENTS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_contents_required_phrases"))


    if (
        tuple(inventory.get("readme_lead_required_phrases", ()))
        != README_LEAD_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_lead_required_phrases"))

    if (
        tuple(inventory.get("readme_blurbs_required_phrases", ()))
        != README_BLURBS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_blurbs_required_phrases"))

    if (
        tuple(inventory.get("readme_bootstrap_required_phrases", ()))
        != README_BOOTSTRAP_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "readme_bootstrap_required_phrases"))



    if (
        tuple(inventory.get("goose_howto_required_phrases", ()))
        != GOOSE_HOWTO_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "goose_howto_required_phrases"))

    if (
        tuple(inventory.get("goose_state_machine_required_phrases", ()))
        != GOOSE_STATE_MACHINE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_state_machine_required_phrases")
        )

    if (
        tuple(inventory.get("goose_naming_required_phrases", ()))
        != GOOSE_NAMING_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "goose_naming_required_phrases"))

    if (
        tuple(inventory.get("goose_recipe_headers_required_phrases", ()))
        != GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_recipe_headers_required_phrases")
        )

    if (
        tuple(inventory.get("goose_instruction_agents_required_phrases", ()))
        != GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_instruction_agents_required_phrases")
        )

    if (
        tuple(inventory.get("goose_extensions_required_phrases", ()))
        != GOOSE_EXTENSIONS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_extensions_required_phrases")
        )

    if (
        tuple(inventory.get("goose_orchestration_required_phrases", ()))
        != GOOSE_ORCHESTRATION_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_orchestration_required_phrases")
        )

    if (
        tuple(inventory.get("goose_conflicts_required_phrases", ()))
        != GOOSE_CONFLICTS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "goose_conflicts_required_phrases"))

    if (
        tuple(inventory.get("goose_quantum_task_required_phrases", ()))
        != GOOSE_QUANTUM_TASK_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "goose_quantum_task_required_phrases")
        )


    if (
        tuple(inventory.get("prompt_roles_required_phrases", ()))
        != PROMPT_ROLES_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "prompt_roles_required_phrases"))

    if (
        tuple(inventory.get("prompt_sections_required_phrases", ()))
        != PROMPT_SECTIONS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "prompt_sections_required_phrases"))

    if (
        tuple(inventory.get("prompt_usage_required_phrases", ()))
        != PROMPT_USAGE_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "prompt_usage_required_phrases"))

    if (
        tuple(inventory.get("prompt_constraints_required_phrases", ()))
        != PROMPT_CONSTRAINTS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_constraints_required_phrases")
        )

    if (
        tuple(inventory.get("prompt_triggers_required_phrases", ()))
        != PROMPT_TRIGGERS_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "prompt_triggers_required_phrases"))

    if (
        tuple(inventory.get("prompt_related_docs_required_phrases", ()))
        != PROMPT_RELATED_DOCS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "prompt_related_docs_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_phases_required_phrases", ()))
        != IMPLEMENTATION_PHASES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_phases_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_tools_required_phrases", ()))
        != IMPLEMENTATION_TOOLS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_tools_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_success_required_phrases", ()))
        != IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_success_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_issues_required_phrases", ()))
        != IMPLEMENTATION_ISSUES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_issues_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_faq_required_phrases", ()))
        != IMPLEMENTATION_FAQ_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_faq_required_phrases")
        )

    if (
        tuple(inventory.get("implementation_support_required_phrases", ()))
        != IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "implementation_support_required_phrases")
        )

    if (
        tuple(inventory.get("execution_timeline_required_phrases", ()))
        != EXECUTION_TIMELINE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_timeline_required_phrases")
        )

    if (
        tuple(inventory.get("execution_technologies_required_phrases", ()))
        != EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_technologies_required_phrases")
        )

    if (
        tuple(inventory.get("execution_workflow_required_phrases", ()))
        != EXECUTION_WORKFLOW_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_workflow_required_phrases")
        )

    if (
        tuple(inventory.get("execution_ide_required_phrases", ()))
        != EXECUTION_IDE_REQUIRED_PHRASES
    ):
        findings.append(_lock_mismatch(schema_path, "execution_ide_required_phrases"))

    if (
        tuple(inventory.get("execution_innovations_required_phrases", ()))
        != EXECUTION_INNOVATIONS_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_innovations_required_phrases")
        )

    if (
        tuple(inventory.get("execution_next48_required_phrases", ()))
        != EXECUTION_NEXT48_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "execution_next48_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_issues_required_phrases", ()))
        != CONTRIBUTING_ISSUES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_issues_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_local_required_phrases", ()))
        != CONTRIBUTING_LOCAL_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_local_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_governance_required_phrases", ()))
        != CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_governance_required_phrases")
        )


    if (
        tuple(inventory.get("contributing_metadata_required_phrases", ()))
        != CONTRIBUTING_METADATA_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_metadata_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_surfaces_required_phrases", ()))
        != CONTRIBUTING_SURFACES_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_surfaces_required_phrases")
        )

    if (
        tuple(inventory.get("contributing_ci_honesty_required_phrases", ()))
        != CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    ):
        findings.append(
            _lock_mismatch(schema_path, "contributing_ci_honesty_required_phrases")
        )

    expected_validator_names = tuple(sorted(VALIDATORS))
    if tuple(inventory.get("validator_names", ())) != expected_validator_names:
        findings.append(_lock_mismatch(schema_path, "validator_names"))

    if inventory["min_coverage_fail_under"] != MIN_COVERAGE_FAIL_UNDER:
        findings.append(_lock_mismatch(schema_path, "min_coverage_fail_under"))

    if inventory["min_validator_count"] != MIN_VALIDATOR_COUNT:
        findings.append(_lock_mismatch(schema_path, "min_validator_count"))

    if len(VALIDATORS) < inventory["min_validator_count"]:
        findings.append(
            Finding(
                schema_path,
                (
                    f"validator registry count {len(VALIDATORS)} "
                    f"below min_validator_count {inventory['min_validator_count']}"
                ),
            )
        )

    findings.extend(_inventory_lock_consistency(inventory, schema_path=schema_path))
    return findings


def _inventory_lock_consistency(
    inventory: dict[str, Any], *, schema_path: str
) -> list[Finding]:
    """Refuse internal inventory drift between related lock fields."""
    findings: list[Finding] = []
    names = set(inventory["expected_recipe_names"])
    files = set(inventory["expected_recipe_files"])
    bindings = dict(inventory["recipe_bindings"])
    primaries = dict(inventory["recipe_primary_agents"])
    agents = set(inventory["documented_agents"])

    if set(bindings) != names:
        findings.append(
            Finding(
                schema_path,
                "recipe_bindings keys inconsistent with expected_recipe_names",
            )
        )
    if set(bindings.values()) != files:
        findings.append(
            Finding(
                schema_path,
                "recipe_bindings values inconsistent with expected_recipe_files",
            )
        )
    if set(primaries) != names:
        findings.append(
            Finding(
                schema_path,
                "recipe_primary_agents keys inconsistent with expected_recipe_names",
            )
        )
    if not set(primaries.values()) <= agents:
        findings.append(
            Finding(
                schema_path,
                "recipe_primary_agents values must be subset of documented_agents",
            )
        )
    orch = inventory.get("orchestration_recipe_name")
    if orch not in names:
        findings.append(
            Finding(
                schema_path,
                "orchestration_recipe_name must be one of expected_recipe_names",
            )
        )
    archive_docs = set(inventory.get("required_archive_docs", ()))
    scan_docs = set(inventory.get("agent_token_scan_docs", ()))
    if not archive_docs <= scan_docs:
        findings.append(
            Finding(
                schema_path,
                "required_archive_docs must be subset of agent_token_scan_docs",
            )
        )
    validator_names = inventory.get("validator_names", [])
    if len(validator_names) != len(set(validator_names)):
        findings.append(Finding(schema_path, "validator_names must be unique"))
    if len(validator_names) < inventory.get("min_validator_count", 0):
        findings.append(
            Finding(
                schema_path,
                "validator_names length below min_validator_count",
            )
        )

    specialists = set(inventory.get("specialist_agents", ()))
    if specialists | {"OrchestrationAgent"} != agents:
        findings.append(
            Finding(
                schema_path,
                "specialist_agents + OrchestrationAgent must equal documented_agents",
            )
        )
    if "OrchestrationAgent" in specialists:
        findings.append(
            Finding(
                schema_path,
                "specialist_agents must not include OrchestrationAgent",
            )
        )
    if orch in primaries and primaries.get(orch) != "OrchestrationAgent":
        findings.append(
            Finding(
                schema_path,
                "orchestration recipe primary agent must be OrchestrationAgent",
            )
        )

    install_refs = set(inventory.get("cursor_install_required_refs", ()))
    required_paths = set(inventory.get("required_paths", ()))
    if install_refs and not install_refs <= required_paths:
        findings.append(
            Finding(
                schema_path,
                "cursor_install_required_refs must be subset of required_paths",
            )
        )

    group_names = list(inventory.get("dependabot_group_names", ()))
    if len(group_names) != len(set(group_names)):
        findings.append(Finding(schema_path, "dependabot_group_names must be unique"))

    recipe_titles = dict(inventory.get("recipe_titles", {}))
    if set(recipe_titles) != names:
        findings.append(
            Finding(
                schema_path,
                "recipe_titles keys inconsistent with expected_recipe_names",
            )
        )
    title_values = list(recipe_titles.values())
    if len(title_values) != len(set(title_values)):
        findings.append(Finding(schema_path, "recipe_titles values must be unique"))

    actions = list(inventory.get("ci_required_actions", ()))
    if len(actions) != len(set(actions)):
        findings.append(Finding(schema_path, "ci_required_actions must be unique"))
    if not actions:
        findings.append(Finding(schema_path, "ci_required_actions must not be empty"))

    directories = list(inventory.get("dependabot_directories", ()))
    if len(directories) != len(set(directories)):
        findings.append(Finding(schema_path, "dependabot_directories must be unique"))
    if not directories:
        findings.append(Finding(schema_path, "dependabot_directories must not be empty"))

    issue_names = dict(inventory.get("issue_template_names", {}))
    issue_abouts = dict(inventory.get("issue_template_abouts", {}))
    issue_files = set(inventory.get("issue_template_files", ()))
    if set(issue_names) != issue_files:
        findings.append(
            Finding(
                schema_path,
                "issue_template_names keys inconsistent with issue_template_files",
            )
        )
    if set(issue_abouts) != issue_files:
        findings.append(
            Finding(
                schema_path,
                "issue_template_abouts keys inconsistent with issue_template_files",
            )
        )
    name_values = list(issue_names.values())
    if len(name_values) != len(set(name_values)):
        findings.append(Finding(schema_path, "issue_template_names values must be unique"))
    about_values = list(issue_abouts.values())
    if len(about_values) != len(set(about_values)):
        findings.append(
            Finding(schema_path, "issue_template_abouts values must be unique")
        )

    badge_phrases = list(inventory.get("readme_badge_phrases", ()))
    if len(badge_phrases) != len(set(badge_phrases)):
        findings.append(Finding(schema_path, "readme_badge_phrases must be unique"))
    if not badge_phrases:
        findings.append(Finding(schema_path, "readme_badge_phrases must not be empty"))

    quarterly = list(inventory.get("quarterly_review_phrases", ()))
    if len(quarterly) != len(set(quarterly)):
        findings.append(Finding(schema_path, "quarterly_review_phrases must be unique"))
    if not quarterly:
        findings.append(
            Finding(schema_path, "quarterly_review_phrases must not be empty")
        )

    text_markers = list(inventory.get("ci_required_text_markers", ()))
    if len(text_markers) != len(set(text_markers)):
        findings.append(Finding(schema_path, "ci_required_text_markers must be unique"))
    if not text_markers:
        findings.append(
            Finding(schema_path, "ci_required_text_markers must not be empty")
        )

    lint_select = list(inventory.get("pyproject_ruff_lint_select", ()))
    if len(lint_select) != len(set(lint_select)):
        findings.append(
            Finding(schema_path, "pyproject_ruff_lint_select must be unique")
        )
    if not lint_select:
        findings.append(
            Finding(schema_path, "pyproject_ruff_lint_select must not be empty")
        )

    workflow_name = inventory.get("ci_workflow_name")
    if not isinstance(workflow_name, str) or not workflow_name.strip():
        findings.append(Finding(schema_path, "ci_workflow_name must be a non-empty string"))

    job_names = dict(inventory.get("ci_job_display_names", {}))
    required_jobs = set(inventory.get("required_ci_jobs", ()))
    if set(job_names) != required_jobs:
        findings.append(
            Finding(
                schema_path,
                "ci_job_display_names keys inconsistent with required_ci_jobs",
            )
        )
    job_values = list(job_names.values())
    if len(job_values) != len(set(job_values)):
        findings.append(
            Finding(schema_path, "ci_job_display_names values must be unique")
        )
    if not job_names:
        findings.append(
            Finding(schema_path, "ci_job_display_names must not be empty")
        )

    ruff_src = list(inventory.get("pyproject_ruff_src", ()))
    if len(ruff_src) != len(set(ruff_src)):
        findings.append(Finding(schema_path, "pyproject_ruff_src must be unique"))
    if not ruff_src:
        findings.append(Finding(schema_path, "pyproject_ruff_src must not be empty"))

    agent_desc = inventory.get("github_agent_description")
    if not isinstance(agent_desc, str) or not agent_desc.strip():
        findings.append(
            Finding(schema_path, "github_agent_description must be a non-empty string")
        )

    link_args = inventory.get("ci_link_check_args")
    if not isinstance(link_args, str) or not link_args.strip():
        findings.append(
            Finding(schema_path, "ci_link_check_args must be a non-empty string")
        )

    runs_on = inventory.get("ci_runs_on")
    if not isinstance(runs_on, str) or not runs_on.strip():
        findings.append(
            Finding(schema_path, "ci_runs_on must be a non-empty string")
        )

    artifact_paths = list(inventory.get("ci_artifact_paths", ()))
    if len(artifact_paths) != len(set(artifact_paths)):
        findings.append(Finding(schema_path, "ci_artifact_paths must be unique"))
    if not artifact_paths:
        findings.append(Finding(schema_path, "ci_artifact_paths must not be empty"))

    if_no_files = inventory.get("ci_artifact_if_no_files_found")
    if not isinstance(if_no_files, str) or not if_no_files.strip():
        findings.append(
            Finding(
                schema_path,
                "ci_artifact_if_no_files_found must be a non-empty string",
            )
        )

    actionlint_shell = inventory.get("ci_actionlint_shell")
    if not isinstance(actionlint_shell, str) or not actionlint_shell.strip():
        findings.append(
            Finding(schema_path, "ci_actionlint_shell must be a non-empty string")
        )

    actionlint_step_id = inventory.get("ci_actionlint_step_id")
    if not isinstance(actionlint_step_id, str) or not actionlint_step_id.strip():
        findings.append(
            Finding(schema_path, "ci_actionlint_step_id must be a non-empty string")
        )

    pyproject_desc = inventory.get("pyproject_description")
    if not isinstance(pyproject_desc, str) or not pyproject_desc.strip():
        findings.append(
            Finding(schema_path, "pyproject_description must be a non-empty string")
        )

    pyproject_readme = inventory.get("pyproject_readme")
    if not isinstance(pyproject_readme, str) or not pyproject_readme.strip():
        findings.append(
            Finding(schema_path, "pyproject_readme must be a non-empty string")
        )

    testpaths = list(inventory.get("pytest_testpaths", ()))
    if len(testpaths) != len(set(testpaths)):
        findings.append(Finding(schema_path, "pytest_testpaths must be unique"))
    if not testpaths:
        findings.append(Finding(schema_path, "pytest_testpaths must not be empty"))

    pythonpath = list(inventory.get("pytest_pythonpath", ()))
    if len(pythonpath) != len(set(pythonpath)):
        findings.append(Finding(schema_path, "pytest_pythonpath must be unique"))
    if not pythonpath:
        findings.append(Finding(schema_path, "pytest_pythonpath must not be empty"))

    coverage_source = list(inventory.get("coverage_source", ()))
    if len(coverage_source) != len(set(coverage_source)):
        findings.append(Finding(schema_path, "coverage_source must be unique"))
    if not coverage_source:
        findings.append(Finding(schema_path, "coverage_source must not be empty"))

    setup_cache = inventory.get("ci_setup_python_cache")
    if not isinstance(setup_cache, str) or not setup_cache.strip():
        findings.append(
            Finding(schema_path, "ci_setup_python_cache must be a non-empty string")
        )

    ruff_cmd = inventory.get("ci_ruff_check_command")
    if not isinstance(ruff_cmd, str) or not ruff_cmd.strip():
        findings.append(
            Finding(schema_path, "ci_ruff_check_command must be a non-empty string")
        )
    elif "ruff" not in ruff_cmd:
        findings.append(
            Finding(schema_path, "ci_ruff_check_command must mention ruff")
        )

    license_phrases = list(inventory.get("license_required_phrases", ()))
    if len(license_phrases) != len(set(license_phrases)):
        findings.append(
            Finding(schema_path, "license_required_phrases must be unique")
        )
    if not license_phrases:
        findings.append(
            Finding(schema_path, "license_required_phrases must not be empty")
        )
    for phrase in license_phrases:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "license_required_phrases entries must be non-empty strings",
                )
            )
            break

    pip_install = inventory.get("ci_pip_install_command")
    if not isinstance(pip_install, str) or not pip_install.strip():
        findings.append(
            Finding(schema_path, "ci_pip_install_command must be a non-empty string")
        )
    elif "pip install" not in pip_install:
        findings.append(
            Finding(schema_path, "ci_pip_install_command must mention pip install")
        )

    pip_check = inventory.get("ci_pip_check_command")
    if not isinstance(pip_check, str) or not pip_check.strip():
        findings.append(
            Finding(schema_path, "ci_pip_check_command must be a non-empty string")
        )
    elif "pip check" not in pip_check:
        findings.append(
            Finding(schema_path, "ci_pip_check_command must mention pip check")
        )

    pytest_markers = list(inventory.get("ci_pytest_required_markers", ()))
    if len(pytest_markers) != len(set(pytest_markers)):
        findings.append(
            Finding(schema_path, "ci_pytest_required_markers must be unique")
        )
    if not pytest_markers:
        findings.append(
            Finding(schema_path, "ci_pytest_required_markers must not be empty")
        )
    for marker in pytest_markers:
        if not isinstance(marker, str) or not marker.strip():
            findings.append(
                Finding(
                    schema_path,
                    "ci_pytest_required_markers entries must be non-empty strings",
                )
            )
            break
    else:
        if pytest_markers and not any("--cov" in str(m) for m in pytest_markers):
            findings.append(
                Finding(
                    schema_path,
                    "ci_pytest_required_markers must include a --cov marker",
                )
            )

    residency = list(inventory.get("state_residency_required_phrases", ()))
    if len(residency) != len(set(residency)):
        findings.append(
            Finding(schema_path, "state_residency_required_phrases must be unique")
        )
    if not residency:
        findings.append(
            Finding(schema_path, "state_residency_required_phrases must not be empty")
        )
    for phrase in residency:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "state_residency_required_phrases entries must be non-empty strings",
                )
            )
            break

    key_files = list(inventory.get("key_files_required_entries", ()))
    if len(key_files) != len(set(key_files)):
        findings.append(
            Finding(schema_path, "key_files_required_entries must be unique")
        )
    if not key_files:
        findings.append(
            Finding(schema_path, "key_files_required_entries must not be empty")
        )
    for entry in key_files:
        if not isinstance(entry, str) or not entry.strip():
            findings.append(
                Finding(
                    schema_path,
                    "key_files_required_entries entries must be non-empty strings",
                )
            )
            break
    else:
        archive_docs = set(inventory.get("required_archive_docs", ()))
        named_files = {e for e in key_files if e.endswith(".md")}
        if named_files and not named_files <= (
            archive_docs
            | {"IMPLEMENTATION-GUIDE.md", "EXECUTION-SUMMARY.md", "docs/agent-hydration.md"}
        ):
            findings.append(
                Finding(
                    schema_path,
                    "key_files_required_entries markdown files must be archive/hydration docs",
                )
            )

    pr_fields = list(inventory.get("pr_routing_required_fields", ()))
    if len(pr_fields) != len(set(pr_fields)):
        findings.append(
            Finding(schema_path, "pr_routing_required_fields must be unique")
        )
    if not pr_fields:
        findings.append(
            Finding(schema_path, "pr_routing_required_fields must not be empty")
        )
    for field in pr_fields:
        if not isinstance(field, str) or not field.strip():
            findings.append(
                Finding(
                    schema_path,
                    "pr_routing_required_fields entries must be non-empty strings",
                )
            )
            break
    else:
        required_core = {"Surface", "Issue", "Branch", "Priority"}
        if pr_fields and not required_core <= set(pr_fields):
            findings.append(
                Finding(
                    schema_path,
                    "pr_routing_required_fields must include Surface/Issue/Branch/Priority",
                )
            )

    matrix = list(inventory.get("routing_matrix_required_phrases", ()))
    if len(matrix) != len(set(matrix)):
        findings.append(
            Finding(schema_path, "routing_matrix_required_phrases must be unique")
        )
    if not matrix:
        findings.append(
            Finding(schema_path, "routing_matrix_required_phrases must not be empty")
        )
    for phrase in matrix:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "routing_matrix_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        surfaces = list(inventory.get("routing_surfaces", ()))
        if matrix and surfaces and len(matrix) != len(surfaces):
            findings.append(
                Finding(
                    schema_path,
                    "routing_matrix_required_phrases length must match routing_surfaces",
                )
            )

    identity = list(inventory.get("repo_identity_required_phrases", ()))
    if len(identity) != len(set(identity)):
        findings.append(
            Finding(schema_path, "repo_identity_required_phrases must be unique")
        )
    if not identity:
        findings.append(
            Finding(schema_path, "repo_identity_required_phrases must not be empty")
        )
    for phrase in identity:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "repo_identity_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if identity and "fuzzywigg/g0p-agents" not in identity:
            findings.append(
                Finding(
                    schema_path,
                    "repo_identity_required_phrases must include fuzzywigg/g0p-agents",
                )
            )

    escalation = list(inventory.get("escalation_block_required_phrases", ()))
    if len(escalation) != len(set(escalation)):
        findings.append(
            Finding(schema_path, "escalation_block_required_phrases must be unique")
        )
    if not escalation:
        findings.append(
            Finding(schema_path, "escalation_block_required_phrases must not be empty")
        )
    for phrase in escalation:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "escalation_block_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_esc = {
            "ESCALATION REQUIRED",
            "From Agent:",
            "Conflict:",
            "Recommendation:",
            "Timeline:",
        }
        if escalation and not required_esc <= set(escalation):
            findings.append(
                Finding(
                    schema_path,
                    "escalation_block_required_phrases must include banner and four fields",
                )
            )

    rationales = list(inventory.get("routing_matrix_rationale_phrases", ()))
    if len(rationales) != len(set(rationales)):
        findings.append(
            Finding(schema_path, "routing_matrix_rationale_phrases must be unique")
        )
    if not rationales:
        findings.append(
            Finding(schema_path, "routing_matrix_rationale_phrases must not be empty")
        )
    for phrase in rationales:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "routing_matrix_rationale_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        surfaces = list(inventory.get("routing_surfaces", ()))
        if rationales and surfaces and len(rationales) != len(surfaces):
            findings.append(
                Finding(
                    schema_path,
                    "routing_matrix_rationale_phrases length must match routing_surfaces",
                )
            )

    metadata = list(inventory.get("claude_metadata_required_phrases", ()))
    if len(metadata) != len(set(metadata)):
        findings.append(
            Finding(schema_path, "claude_metadata_required_phrases must be unique")
        )
    if not metadata:
        findings.append(
            Finding(schema_path, "claude_metadata_required_phrases must not be empty")
        )
    for phrase in metadata:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "claude_metadata_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_meta = {
            "Status: ACTIVE",
            "Tier: 1",
            "Owner: claude-cowork",
            "Created: 2026-04-13",
        }
        if metadata and not required_meta <= set(metadata):
            findings.append(
                Finding(
                    schema_path,
                    "claude_metadata_required_phrases must include Status/Tier/Owner/Created",
                )
            )

    usage = list(inventory.get("escalation_usage_required_phrases", ()))
    if len(usage) != len(set(usage)):
        findings.append(
            Finding(schema_path, "escalation_usage_required_phrases must be unique")
        )
    if not usage:
        findings.append(
            Finding(schema_path, "escalation_usage_required_phrases must not be empty")
        )
    for phrase in usage:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "escalation_usage_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_usage = {
            "When blocked, use this format in PR comments or Slack:",
            "```text",
            "From Agent: [surface name]",
        }
        if usage and not required_usage <= set(usage):
            findings.append(
                Finding(
                    schema_path,
                    "escalation_usage_required_phrases must include intro, fence, and From Agent",
                )
            )

    supported = list(inventory.get("security_supported_required_phrases", ()))
    if len(supported) != len(set(supported)):
        findings.append(
            Finding(schema_path, "security_supported_required_phrases must be unique")
        )
    if not supported:
        findings.append(
            Finding(
                schema_path, "security_supported_required_phrases must not be empty"
            )
        )
    for phrase in supported:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_supported_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if supported and "documentation archive" not in " ".join(supported):
            findings.append(
                Finding(
                    schema_path,
                    "security_supported_required_phrases must mention documentation archive",
                )
            )

    reporting = list(inventory.get("security_reporting_required_phrases", ()))
    if len(reporting) != len(set(reporting)):
        findings.append(
            Finding(schema_path, "security_reporting_required_phrases must be unique")
        )
    if not reporting:
        findings.append(
            Finding(
                schema_path, "security_reporting_required_phrases must not be empty"
            )
        )
    for phrase in reporting:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_reporting_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if reporting and not any(
            "Do NOT open a public GitHub issue" in phrase for phrase in reporting
        ):
            findings.append(
                Finding(
                    schema_path,
                    "security_reporting_required_phrases must refuse public GitHub issues",
                )
            )

    standards = list(inventory.get("security_standards_required_phrases", ()))
    if len(standards) != len(set(standards)):
        findings.append(
            Finding(schema_path, "security_standards_required_phrases must be unique")
        )
    if not standards:
        findings.append(
            Finding(
                schema_path, "security_standards_required_phrases must not be empty"
            )
        )
    for phrase in standards:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_standards_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_domains = {
            "Cryptography",
            "Smart contracts",
            "Mobile",
            "Secrets",
            "Keys",
        }
        if standards and not required_domains <= set(standards):
            findings.append(
                Finding(
                    schema_path,
                    "security_standards_required_phrases must include five domain rows",
                )
            )

    quickstart = list(inventory.get("implementation_quickstart_required_phrases", ()))
    if len(quickstart) != len(set(quickstart)):
        findings.append(
            Finding(
                schema_path, "implementation_quickstart_required_phrases must be unique"
            )
        )
    if not quickstart:
        findings.append(
            Finding(
                schema_path,
                "implementation_quickstart_required_phrases must not be empty",
            )
        )
    for phrase in quickstart:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_quickstart_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        if quickstart and not any("agentic_flows" in phrase for phrase in quickstart):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_quickstart_required_phrases must mention agentic_flows",
                )
            )

    specialists = list(inventory.get("execution_specialists_required_phrases", ()))
    if len(specialists) != len(set(specialists)):
        findings.append(
            Finding(
                schema_path, "execution_specialists_required_phrases must be unique"
            )
        )
    if not specialists:
        findings.append(
            Finding(
                schema_path, "execution_specialists_required_phrases must not be empty"
            )
        )
    for phrase in specialists:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_specialists_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        agents = set(inventory.get("documented_agents", ()))
        if specialists and agents and not agents <= set(specialists):
            findings.append(
                Finding(
                    schema_path,
                    "execution_specialists_required_phrases must include all "
                    "documented agents",
                )
            )

    list_b = list(inventory.get("hydration_list_b_required_phrases", ()))
    if len(list_b) != len(set(list_b)):
        findings.append(
            Finding(schema_path, "hydration_list_b_required_phrases must be unique")
        )
    if not list_b:
        findings.append(
            Finding(schema_path, "hydration_list_b_required_phrases must not be empty")
        )
    for phrase in list_b:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_list_b_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        joined = " ".join(list_b)
        if list_b and "LIST B" not in joined:
            findings.append(
                Finding(
                    schema_path,
                    "hydration_list_b_required_phrases must mention LIST B",
                )
            )
        if list_b and "PikoClaw" not in joined:
            findings.append(
                Finding(
                    schema_path,
                    "hydration_list_b_required_phrases must mention PikoClaw",
                )
            )

    phase1 = list(inventory.get("hydration_phase1_required_phrases", ()))
    if len(phase1) != len(set(phase1)):
        findings.append(
            Finding(schema_path, "hydration_phase1_required_phrases must be unique")
        )
    if not phase1:
        findings.append(
            Finding(
                schema_path, "hydration_phase1_required_phrases must not be empty"
            )
        )
    for phrase in phase1:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase1_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_phase1 = {
            "### Identity",
            "### Source Architecture",
            "### CI/CD",
            "### Git State",
            "Public archive of Quantum-Blockchain agentic protocols v2.2",
        }
        if phase1 and not required_phase1 <= set(phase1):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase1_required_phrases must include Identity/"
                    "Source Architecture/CI/CD/Git State/purpose",
                )
            )

    list_a = list(inventory.get("hydration_list_a_required_phrases", ()))
    if len(list_a) != len(set(list_a)):
        findings.append(
            Finding(schema_path, "hydration_list_a_required_phrases must be unique")
        )
    if not list_a:
        findings.append(
            Finding(
                schema_path, "hydration_list_a_required_phrases must not be empty"
            )
        )
    for phrase in list_a:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_list_a_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_list_a = {
            "### LIST A — Researchable",
            "What is the Goose framework?",
            "What are CRYSTALS-Kyber and CRYSTALS-Dilithium?",
            "What is `stimgery`",
        }
        if list_a and not required_list_a <= set(list_a):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_list_a_required_phrases must include LIST A/"
                    "Goose/Kyber/stimgery",
                )
            )

    resolved = list(inventory.get("hydration_resolved_required_phrases", ()))
    if len(resolved) != len(set(resolved)):
        findings.append(
            Finding(
                schema_path, "hydration_resolved_required_phrases must be unique"
            )
        )
    if not resolved:
        findings.append(
            Finding(
                schema_path, "hydration_resolved_required_phrases must not be empty"
            )
        )
    for phrase in resolved:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_resolved_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_resolved = {
            "Goose is Block's open-source AI agent framework",
            "CRYSTALS-Kyber (now ML-KEM, FIPS 203)",
            "liboqs (Open Quantum Safe)",
            "LIST B items B1–B5 are deferred to Andrew",
        }
        if resolved and not required_resolved <= set(resolved):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_resolved_required_phrases must include Goose/"
                    "Kyber/liboqs/LIST B deferred",
                )
            )

    phase4 = list(inventory.get("hydration_phase4_required_phrases", ()))
    if len(phase4) != len(set(phase4)):
        findings.append(
            Finding(schema_path, "hydration_phase4_required_phrases must be unique")
        )
    if not phase4:
        findings.append(
            Finding(
                schema_path, "hydration_phase4_required_phrases must not be empty"
            )
        )
    for phrase in phase4:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase4_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_phase4 = {
            "## PHASE 4: ISSUES GENERATED",
            "Add LICENSE file",
            "Scaffold agentic_flows/ with actual Goose recipe YAML files",
            "Scaffold mobile/ with React Native QuantumValidator skeleton",
        }
        if phase4 and not required_phase4 <= set(phase4):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase4_required_phrases must include PHASE 4/"
                    "LICENSE/agentic_flows/mobile",
                )
            )

    deferred = list(inventory.get("hydration_deferred_required_phrases", ()))
    if len(deferred) != len(set(deferred)):
        findings.append(
            Finding(
                schema_path, "hydration_deferred_required_phrases must be unique"
            )
        )
    if not deferred:
        findings.append(
            Finding(
                schema_path, "hydration_deferred_required_phrases must not be empty"
            )
        )
    for phrase in deferred:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_deferred_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_deferred = {
            "## LIST B — Deferred to Andrew",
            "remain a reference archive",
            "What specific PikoClaw features depend on g0p-agents by May 27, 2026?",
            "Does a Notion page for g0p-agents exist?",
        }
        if deferred and not required_deferred <= set(deferred):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_deferred_required_phrases must include Deferred/"
                    "archive/PikoClaw/Notion",
                )
            )


    ide_stack = list(inventory.get("constitution_ide_stack_required_phrases", ()))
    if len(ide_stack) != len(set(ide_stack)):
        findings.append(
            Finding(schema_path, "constitution_ide_stack_required_phrases must be unique")
        )
    if not ide_stack:
        findings.append(
            Finding(schema_path, "constitution_ide_stack_required_phrases must not be empty")
        )
    for phrase in ide_stack:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_ide_stack_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_ide_stack = {
            "## 23. Quantum-Blockchain Development IDE Setup",
            "### 23.1 Required Software Stack",
            "#### Tier 1: Foundation (All Developers)",
            "Cirq (Google quantum circuits)"
        }
        if ide_stack and not required_ide_stack <= set(ide_stack):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_ide_stack_required_phrases must include "
                    "IDE Setup/Required Software Stack/Tier 1/Cirq",
                )
            )

    install_script = list(inventory.get("constitution_install_script_required_phrases", ()))
    if len(install_script) != len(set(install_script)):
        findings.append(
            Finding(schema_path, "constitution_install_script_required_phrases must be unique")
        )
    if not install_script:
        findings.append(
            Finding(schema_path, "constitution_install_script_required_phrases must not be empty")
        )
    for phrase in install_script:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_install_script_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_install_script = {
            "### 23.2 Installation Script (WSL2 Ubuntu 22.04)",
            "setup-quantum-blockchain-dev.sh",
            "pip install liboqs",
            "\u2705 Quantum-Blockchain development environment ready!"
        }
        if install_script and not required_install_script <= set(install_script):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_install_script_required_phrases must include "
                    "Installation Script/setup script/liboqs/ready",
                )
            )

    vscode_ext = list(inventory.get("constitution_vscode_required_phrases", ()))
    if len(vscode_ext) != len(set(vscode_ext)):
        findings.append(
            Finding(schema_path, "constitution_vscode_required_phrases must be unique")
        )
    if not vscode_ext:
        findings.append(
            Finding(schema_path, "constitution_vscode_required_phrases must not be empty")
        )
    for phrase in vscode_ext:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_vscode_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_vscode_ext = {
            "### 23.3 VS Code Extensions (Required)",
            "ms-python.python",
            "JuanBlanco.solidity",
            "ms-vscode-remote.remote-wsl"
        }
        if vscode_ext and not required_vscode_ext <= set(vscode_ext):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_vscode_required_phrases must include VS Code Extensions/python/"
                    "solidity/remote-wsl",
                )
            )

    hard_constraints = list(inventory.get("constitution_hard_constraints_required_phrases", ()))
    if len(hard_constraints) != len(set(hard_constraints)):
        findings.append(
            Finding(schema_path, "constitution_hard_constraints_required_phrases must be unique")
        )
    if not hard_constraints:
        findings.append(
            Finding(schema_path, "constitution_hard_constraints_required_phrases must not be empty")
        )
    for phrase in hard_constraints:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_hard_constraints_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_hard_constraints = {
            "## 24. Hard Constraints \u2014 Quantum-Blockchain Additions",
            "Agents must **NEVER**:",
            "Claim quantum-safe without formal verification",
            "NIST-standardized algorithms (Kyber, Dilithium, SPHINCS+)"
        }
        if hard_constraints and not required_hard_constraints <= set(hard_constraints):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_hard_constraints_required_phrases must include "
                    "Hard Constraints/NEVER/formal verification/NIST",
                )
            )

    risk_tol = list(inventory.get("constitution_risk_tolerance_required_phrases", ()))
    if len(risk_tol) != len(set(risk_tol)):
        findings.append(
            Finding(schema_path, "constitution_risk_tolerance_required_phrases must be unique")
        )
    if not risk_tol:
        findings.append(
            Finding(schema_path, "constitution_risk_tolerance_required_phrases must not be empty")
        )
    for phrase in risk_tol:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_risk_tolerance_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_risk_tol = {
            "## 25. Quarterly Risk Tolerance Review (Section 12.4.1)",
            "### 12.4.1 Risk Tolerance Evolution Protocol",
            "Success rate > 99.5% (at current tier)",
            "If failure rate > 2% in new tier, immediately revert to previous tier."
        }
        if risk_tol and not required_risk_tol <= set(risk_tol):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_risk_tolerance_required_phrases must include "
                    "Risk Tolerance/12.4.1/99.5%/revert",
                )
            )

    cl_preamble = list(inventory.get("changelog_preamble_required_phrases", ()))
    if len(cl_preamble) != len(set(cl_preamble)):
        findings.append(
            Finding(schema_path, "changelog_preamble_required_phrases must be unique")
        )
    if not cl_preamble:
        findings.append(
            Finding(schema_path, "changelog_preamble_required_phrases must not be empty")
        )
    for phrase in cl_preamble:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_preamble_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_cl_preamble = {
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).",
            "All notable changes to this project will be documented in this file.",
            "---"
        }
        if cl_preamble and not required_cl_preamble <= set(cl_preamble):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_preamble_required_phrases must include Keep a Changelog/"
                    "notable changes/separator",
                )
            )

    cl_changed = list(inventory.get("changelog_changed_required_phrases", ()))
    if len(cl_changed) != len(set(cl_changed)):
        findings.append(
            Finding(schema_path, "changelog_changed_required_phrases must be unique")
        )
    if not cl_changed:
        findings.append(
            Finding(schema_path, "changelog_changed_required_phrases must not be empty")
        )
    for phrase in cl_changed:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_changed_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_cl_changed = {
            "### Changed",
            "coverage gate **99%**",
            "CI `pull_request` trigger targets `alpha`",
            "Dependabot now tracks pip (`requirements-dev.txt`)"
        }
        if cl_changed and not required_cl_changed <= set(cl_changed):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_changed_required_phrases must include Changed/coverage/"
                    "alpha/Dependabot",
                )
            )

    cl_initial = list(inventory.get("changelog_initial_required_phrases", ()))
    if len(cl_initial) != len(set(cl_initial)):
        findings.append(
            Finding(schema_path, "changelog_initial_required_phrases must be unique")
        )
    if not cl_initial:
        findings.append(
            Finding(schema_path, "changelog_initial_required_phrases must not be empty")
        )
    for phrase in cl_initial:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_initial_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_cl_initial = {
            "## [0.1.0] \u2014 2025-12-13",
            "`README.md` \u2014 public archive description",
            "`IMPLEMENTATION-GUIDE.md` \u2014 step-by-step setup guide",
            "`EXECUTION-SUMMARY.md` \u2014 implementation summary"
        }
        if cl_initial and not required_cl_initial <= set(cl_initial):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_initial_required_phrases must include "
                    "0.1.0/README/IMPLEMENTATION-GUIDE/EXECUTION-SUMMARY",
                )
            )


    prompt_expertise = list(inventory.get("prompt_expertise_required_phrases", ()))
    if len(prompt_expertise) != len(set(prompt_expertise)):
        findings.append(
            Finding(schema_path, "prompt_expertise_required_phrases must be unique")
        )
    if not prompt_expertise:
        findings.append(
            Finding(schema_path, "prompt_expertise_required_phrases must not be empty")
        )
    for phrase in prompt_expertise:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_expertise_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_expertise = {
            "## Your Expertise",
            "Quantum mechanics (gates, superposition, entanglement)",
            "Distributed ledger architecture",
            "Hardware security modules (HSM, Secure Enclave)"
        }
        if prompt_expertise and not required_prompt_expertise <= set(prompt_expertise):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_expertise_required_phrases must include Expertise/quantum/ledger/HSM",
                )
            )

    prompt_principles = list(inventory.get("prompt_principles_required_phrases", ()))
    if len(prompt_principles) != len(set(prompt_principles)):
        findings.append(
            Finding(schema_path, "prompt_principles_required_phrases must be unique")
        )
    if not prompt_principles:
        findings.append(
            Finding(schema_path, "prompt_principles_required_phrases must not be empty")
        )
    for phrase in prompt_principles:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_principles_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_principles = {
            "## Decision Making Principles",
            "Prioritize quantum-safety over performance",
            "Prioritize user security and privacy",
            "Recommend staged rollouts (testnet \u2192 staging \u2192 mainnet)"
        }
        if prompt_principles and not required_prompt_principles <= set(prompt_principles):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_principles_required_phrases must include "
                    "Principles/quantum-safety/privacy/staged rollouts",
                )
            )

    prompt_metrics = list(inventory.get("prompt_metrics_required_phrases", ()))
    if len(prompt_metrics) != len(set(prompt_metrics)):
        findings.append(
            Finding(schema_path, "prompt_metrics_required_phrases must be unique")
        )
    if not prompt_metrics:
        findings.append(
            Finding(schema_path, "prompt_metrics_required_phrases must not be empty")
        )
    for phrase in prompt_metrics:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_metrics_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_metrics = {
            "## Success Metrics",
            "Circuit depth < 50 gates (if possible)",
            "0 critical vulnerabilities (Slither pass)",
            "Crypto operations < 500ms on Snapdragon 8 Gen 3 (or specified device)"
        }
        if prompt_metrics and not required_prompt_metrics <= set(prompt_metrics):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_metrics_required_phrases must include "
                    "Metrics/circuit depth/Slither/Snapdragon",
                )
            )

    prompt_tools = list(inventory.get("prompt_tools_required_phrases", ()))
    if len(prompt_tools) != len(set(prompt_tools)):
        findings.append(
            Finding(schema_path, "prompt_tools_required_phrases must be unique")
        )
    if not prompt_tools:
        findings.append(
            Finding(schema_path, "prompt_tools_required_phrases must not be empty")
        )
    for phrase in prompt_tools:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_tools_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_tools = {
            "## Your Tools",
            "Jupyter Lab (interactive development)",
            "Hardhat (local blockchain, contract testing)",
            "liboqs (post-quantum crypto on device)",
        }
        if prompt_tools and not required_prompt_tools <= set(prompt_tools):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_tools_required_phrases must include "
                    "Tools/Jupyter/Hardhat/liboqs",
                )
            )

    prompt_communication = list(
        inventory.get("prompt_communication_required_phrases", ())
    )
    if len(prompt_communication) != len(set(prompt_communication)):
        findings.append(
            Finding(
                schema_path, "prompt_communication_required_phrases must be unique"
            )
        )
    if not prompt_communication:
        findings.append(
            Finding(
                schema_path,
                "prompt_communication_required_phrases must not be empty",
            )
        )
    for phrase in prompt_communication:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_communication_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_communication = {
            "## Your Communication Style",
            "Be technical and precise",
            "Be pragmatic and performance-aware",
            "Be decisive but transparent",
        }
        if prompt_communication and not required_prompt_communication <= set(
            prompt_communication
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_communication_required_phrases must include "
                    "Style/technical/pragmatic/decisive",
                )
            )

    prompt_escalation_identity = list(
        inventory.get("prompt_escalation_identity_required_phrases", ())
    )
    if len(prompt_escalation_identity) != len(set(prompt_escalation_identity)):
        findings.append(
            Finding(
                schema_path,
                "prompt_escalation_identity_required_phrases must be unique",
            )
        )
    if not prompt_escalation_identity:
        findings.append(
            Finding(
                schema_path,
                "prompt_escalation_identity_required_phrases must not be empty",
            )
        )
    for phrase in prompt_escalation_identity:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_escalation_identity_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_escalation_identity = {
            "🚨 ESCALATION REQUIRED",
            "From Agent: QuantumArchitectAgent",
            "From Agent: BlockchainArchitectAgent",
            "From Agent: EdgeSecurityAgent",
        }
        if prompt_escalation_identity and not required_prompt_escalation_identity <= set(
            prompt_escalation_identity
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_escalation_identity_required_phrases must include "
                    "ESCALATION REQUIRED/From Agent specialists",
                )
            )

    prompt_orchestration_matrix = list(
        inventory.get("prompt_orchestration_matrix_required_phrases", ())
    )
    if len(prompt_orchestration_matrix) != len(set(prompt_orchestration_matrix)):
        findings.append(
            Finding(
                schema_path,
                "prompt_orchestration_matrix_required_phrases must be unique",
            )
        )
    if not prompt_orchestration_matrix:
        findings.append(
            Finding(
                schema_path,
                "prompt_orchestration_matrix_required_phrases must not be empty",
            )
        )
    for phrase in prompt_orchestration_matrix:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_orchestration_matrix_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_orchestration_matrix = {
            "## Conflict Resolution Matrix",
            "| Conflict Type | How You Resolve It |",
            '**Algorithm Complexity** (Quantum says "too complex", '
            'Blockchain says "necessary")',
            "Weigh risk tolerance. Choose testnet approach to validate.",
        }
        if (
            prompt_orchestration_matrix
            and not required_prompt_orchestration_matrix
            <= set(prompt_orchestration_matrix)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_orchestration_matrix_required_phrases must include "
                    "Matrix/Conflict Type/Algorithm Complexity/testnet",
                )
            )

    prompt_monthly = list(inventory.get("prompt_monthly_required_phrases", ()))
    if len(prompt_monthly) != len(set(prompt_monthly)):
        findings.append(
            Finding(schema_path, "prompt_monthly_required_phrases must be unique")
        )
    if not prompt_monthly:
        findings.append(
            Finding(schema_path, "prompt_monthly_required_phrases must not be empty")
        )
    for phrase in prompt_monthly:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_monthly_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_monthly = {
            "## Your Monthly Checklist",
            "## Current Project Vision",
            "Review all recent decisions in postmortem.md",
            "Risk Tolerance: ALPHA-STAGE (conservative, threshold increases "
            "with success)",
        }
        if prompt_monthly and not required_prompt_monthly <= set(prompt_monthly):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_monthly_required_phrases must include "
                    "Checklist/Vision/postmortem/ALPHA-STAGE",
                )
            )

    prompt_usage_example = list(
        inventory.get("prompt_usage_example_required_phrases", ())
    )
    if len(prompt_usage_example) != len(set(prompt_usage_example)):
        findings.append(
            Finding(
                schema_path, "prompt_usage_example_required_phrases must be unique"
            )
        )
    if not prompt_usage_example:
        findings.append(
            Finding(
                schema_path,
                "prompt_usage_example_required_phrases must not be empty",
            )
        )
    for phrase in prompt_usage_example:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_usage_example_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_usage_example = {
            "### Example: Instantiate QuantumArchitectAgent",
            "Designs Cirq circuit for factorization",
            "Validates using CRYSTALS-Kyber (NIST post-quantum standard)",
            "Output: Updated scratchpad + Cirq circuit file",
        }
        if (
            prompt_usage_example
            and not required_prompt_usage_example <= set(prompt_usage_example)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_usage_example_required_phrases must include "
                    "Example/Cirq/CRYSTALS-Kyber/Output",
                )
            )

    prompt_context = list(inventory.get("prompt_context_required_phrases", ()))
    if len(prompt_context) != len(set(prompt_context)):
        findings.append(
            Finding(schema_path, "prompt_context_required_phrases must be unique")
        )
    if not prompt_context:
        findings.append(
            Finding(schema_path, "prompt_context_required_phrases must not be empty")
        )
    for phrase in prompt_context:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_context_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_context = {
            "## Current Project Context",
            "[INSERT PROJECT-SPECIFIC INFO HERE]",
            "Target quantum hardware: [Cirq-sim initially, then Google/IBM hardware]",
            "Primary blockchain: Ethereum (Sepolia testnet, mainnet)",
        }
        if prompt_context and not required_prompt_context <= set(prompt_context):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_context_required_phrases must include "
                    "Context/INSERT/quantum hardware/Ethereum",
                )
            )

    prompt_decision_authority = list(
        inventory.get("prompt_decision_authority_required_phrases", ())
    )
    if len(prompt_decision_authority) != len(set(prompt_decision_authority)):
        findings.append(
            Finding(
                schema_path,
                "prompt_decision_authority_required_phrases must be unique",
            )
        )
    if not prompt_decision_authority:
        findings.append(
            Finding(
                schema_path,
                "prompt_decision_authority_required_phrases must not be empty",
            )
        )
    for phrase in prompt_decision_authority:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_decision_authority_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_decision_authority = {
            "## Your Decision Authority",
            "You make final calls on:",
            "Trade-offs between security, performance, and usability",
            "Risk acceptance (can we deploy with this vulnerability?)",
        }
        if (
            prompt_decision_authority
            and not required_prompt_decision_authority
            <= set(prompt_decision_authority)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_decision_authority_required_phrases must include "
                    "Decision Authority/final calls/Trade-offs/Risk acceptance",
                )
            )

    prompt_escalation_authority = list(
        inventory.get("prompt_escalation_authority_required_phrases", ())
    )
    if len(prompt_escalation_authority) != len(set(prompt_escalation_authority)):
        findings.append(
            Finding(
                schema_path,
                "prompt_escalation_authority_required_phrases must be unique",
            )
        )
    if not prompt_escalation_authority:
        findings.append(
            Finding(
                schema_path,
                "prompt_escalation_authority_required_phrases must not be empty",
            )
        )
    for phrase in prompt_escalation_authority:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_escalation_authority_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_escalation_authority = {
            "## Your Escalation Authority",
            "You MUST escalate to human if:",
            "Two or more agents have irresolvable conflicts",
            "Budget constraints conflict with scope",
        }
        if (
            prompt_escalation_authority
            and not required_prompt_escalation_authority
            <= set(prompt_escalation_authority)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_escalation_authority_required_phrases must include "
                    "Escalation Authority/MUST escalate/irresolvable/Budget",
                )
            )

    prompt_responsibilities = list(
        inventory.get("prompt_responsibilities_required_phrases", ())
    )
    if len(prompt_responsibilities) != len(set(prompt_responsibilities)):
        findings.append(
            Finding(
                schema_path,
                "prompt_responsibilities_required_phrases must be unique",
            )
        )
    if not prompt_responsibilities:
        findings.append(
            Finding(
                schema_path,
                "prompt_responsibilities_required_phrases must not be empty",
            )
        )
    for phrase in prompt_responsibilities:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_responsibilities_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_responsibilities = {
            "## Core Responsibilities",
            "Design quantum algorithms for cryptographic operations",
            "Implement quantum-safe cryptography on Android/iOS",
            "Make final go/no-go decision",
        }
        if (
            prompt_responsibilities
            and not required_prompt_responsibilities
            <= set(prompt_responsibilities)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_responsibilities_required_phrases must include "
                    "Core Responsibilities/quantum algorithms/on-device/"
                    "go/no-go",
                )
            )

    prompt_cannot_delegate = list(
        inventory.get("prompt_cannot_delegate_required_phrases", ())
    )
    if len(prompt_cannot_delegate) != len(set(prompt_cannot_delegate)):
        findings.append(
            Finding(
                schema_path,
                "prompt_cannot_delegate_required_phrases must be unique",
            )
        )
    if not prompt_cannot_delegate:
        findings.append(
            Finding(
                schema_path,
                "prompt_cannot_delegate_required_phrases must not be empty",
            )
        )
    for phrase in prompt_cannot_delegate:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_cannot_delegate_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_cannot_delegate = {
            "## Key Responsibilities You CANNOT Delegate",
            "Final go/no-go decisions",
            "Risk acceptance (acknowledging consequences)",
            "Stakeholder communication",
        }
        if (
            prompt_cannot_delegate
            and not required_prompt_cannot_delegate
            <= set(prompt_cannot_delegate)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_cannot_delegate_required_phrases must include "
                    "CANNOT Delegate/go/no-go/Risk acceptance/Stakeholder",
                )
            )

    prompt_human_escalation = list(
        inventory.get("prompt_human_escalation_required_phrases", ())
    )
    if len(prompt_human_escalation) != len(set(prompt_human_escalation)):
        findings.append(
            Finding(
                schema_path,
                "prompt_human_escalation_required_phrases must be unique",
            )
        )
    if not prompt_human_escalation:
        findings.append(
            Finding(
                schema_path,
                "prompt_human_escalation_required_phrases must not be empty",
            )
        )
    for phrase in prompt_human_escalation:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_human_escalation_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_prompt_human_escalation = {
            "## When You Escalate to Human",
            "Situation: [What decision needs human input?]",
            "Human approval required before proceeding.",
            "Remember: You are not smarter than the three specialists. Your job is to "
            "listen, understand, mediate, and make calls when consensus is impossible.",
        }
        if (
            prompt_human_escalation
            and not required_prompt_human_escalation
            <= set(prompt_human_escalation)
        ):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_human_escalation_required_phrases must include "
                    "Escalate to Human/Situation/Human approval/not smarter",
                )
            )


    intro = list(inventory.get("postmortem_intro_required_phrases", ()))
    if len(intro) != len(set(intro)):
        findings.append(
            Finding(schema_path, "postmortem_intro_required_phrases must be unique")
        )
    if not intro:
        findings.append(
            Finding(schema_path, "postmortem_intro_required_phrases must not be empty")
        )
    for phrase in intro:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_intro_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if intro and not any("MUST log decisions" in phrase for phrase in intro):
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_intro_required_phrases must require agents to log decisions",
                )
            )

    fields = list(inventory.get("postmortem_field_required_phrases", ()))
    if len(fields) != len(set(fields)):
        findings.append(
            Finding(schema_path, "postmortem_field_required_phrases must be unique")
        )
    if not fields:
        findings.append(
            Finding(schema_path, "postmortem_field_required_phrases must not be empty")
        )
    for phrase in fields:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_field_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_fields = {"**Date**:", "**Decision**:", "**Agent**:"}
        if fields and not required_fields <= set(fields):
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_field_required_phrases must include Date/Decision/Agent",
                )
            )

    next_steps = list(inventory.get("postmortem_next_steps_required_phrases", ()))
    if len(next_steps) != len(set(next_steps)):
        findings.append(
            Finding(schema_path, "postmortem_next_steps_required_phrases must be unique")
        )
    if not next_steps:
        findings.append(
            Finding(
                schema_path, "postmortem_next_steps_required_phrases must not be empty"
            )
        )
    for phrase in next_steps:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_next_steps_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_next = {
            "Andrew answers LIST B (B1–B5) in docs/agent-hydration.md",
            "geryon scaffolds agentic_flows/ once B1 is answered",
        }
        if next_steps and not required_next <= set(next_steps):
            findings.append(
                Finding(
                    schema_path,
                    "postmortem_next_steps_required_phrases must include "
                    "LIST B and geryon scaffold",
                )
            )

    intro_sp = list(inventory.get("scratchpad_intro_required_phrases", ()))
    if len(intro_sp) != len(set(intro_sp)):
        findings.append(
            Finding(schema_path, "scratchpad_intro_required_phrases must be unique")
        )
    if not intro_sp:
        findings.append(
            Finding(schema_path, "scratchpad_intro_required_phrases must not be empty")
        )
    for phrase in intro_sp:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_intro_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if intro_sp and not any(
            "Updated by each agent" in phrase for phrase in intro_sp
        ):
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_intro_required_phrases must require agent updates",
                )
            )

    format_sp = list(inventory.get("scratchpad_format_required_phrases", ()))
    if len(format_sp) != len(set(format_sp)):
        findings.append(
            Finding(schema_path, "scratchpad_format_required_phrases must be unique")
        )
    if not format_sp:
        findings.append(
            Finding(schema_path, "scratchpad_format_required_phrases must not be empty")
        )
    for phrase in format_sp:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_format_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_format = {"[x] = DONE", "[ ] = PENDING", "[~] = IN_PROGRESS"}
        if format_sp and not required_format <= set(format_sp):
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_format_required_phrases must include DONE/PENDING/"
                    "IN_PROGRESS legend lines",
                )
            )

    task_meta = list(inventory.get("scratchpad_task_meta_required_phrases", ()))
    if len(task_meta) != len(set(task_meta)):
        findings.append(
            Finding(schema_path, "scratchpad_task_meta_required_phrases must be unique")
        )
    if not task_meta:
        findings.append(
            Finding(
                schema_path, "scratchpad_task_meta_required_phrases must not be empty"
            )
        )
    for phrase in task_meta:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_task_meta_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_meta = {"Status:", "Created:", "Owner:", "Current blocker:"}
        if task_meta and not required_meta <= set(task_meta):
            findings.append(
                Finding(
                    schema_path,
                    "scratchpad_task_meta_required_phrases must include Status/"
                    "Created/Owner/Current blocker",
                )
            )

    meta_phrases = list(inventory.get("issue_metadata_required_phrases", ()))
    if len(meta_phrases) != len(set(meta_phrases)):
        findings.append(
            Finding(schema_path, "issue_metadata_required_phrases must be unique")
        )
    if not meta_phrases:
        findings.append(
            Finding(schema_path, "issue_metadata_required_phrases must not be empty")
        )
    for phrase in meta_phrases:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "issue_metadata_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_meta_hdr = {
            "Status: ACTIVE",
            "Tier: 1",
            "Edit policy: Agent-editable; structural changes require Andrew approval",
        }
        if meta_phrases and not required_meta_hdr <= set(meta_phrases):
            findings.append(
                Finding(
                    schema_path,
                    "issue_metadata_required_phrases must include Status ACTIVE/"
                    "Tier/Edit policy",
                )
            )

    routing_phrases = list(inventory.get("issue_routing_required_phrases", ()))
    if len(routing_phrases) != len(set(routing_phrases)):
        findings.append(
            Finding(schema_path, "issue_routing_required_phrases must be unique")
        )
    if not routing_phrases:
        findings.append(
            Finding(schema_path, "issue_routing_required_phrases must not be empty")
        )
    for phrase in routing_phrases:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "issue_routing_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_routing = {
            "| Surface |",
            "| Rationale |",
            "| Priority |",
            "| Branch |",
            "| Dependencies |",
        }
        if routing_phrases and not required_routing <= set(routing_phrases):
            findings.append(
                Finding(
                    schema_path,
                    "issue_routing_required_phrases must include Surface/Rationale/"
                    "Priority/Branch/Dependencies",
                )
            )

    bug_repro = list(inventory.get("bug_repro_required_phrases", ()))
    if len(bug_repro) != len(set(bug_repro)):
        findings.append(
            Finding(schema_path, "bug_repro_required_phrases must be unique")
        )
    if not bug_repro:
        findings.append(
            Finding(schema_path, "bug_repro_required_phrases must not be empty")
        )
    for phrase in bug_repro:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "bug_repro_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_repro = {
            "## Steps to Reproduce",
            "## Expected Behavior",
            "## Actual Behavior",
        }
        if bug_repro and not required_repro <= set(bug_repro):
            findings.append(
                Finding(
                    schema_path,
                    "bug_repro_required_phrases must include Steps to Reproduce/"
                    "Expected/Actual Behavior",
                )
            )

    who = list(inventory.get("contributing_who_required_phrases", ()))
    if len(who) != len(set(who)):
        findings.append(
            Finding(schema_path, "contributing_who_required_phrases must be unique")
        )
    if not who:
        findings.append(
            Finding(schema_path, "contributing_who_required_phrases must not be empty")
        )
    for phrase in who:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_who_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        if who and not any("Andrew Pappas" in phrase for phrase in who):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_who_required_phrases must name Andrew Pappas",
                )
            )

    branches = list(inventory.get("contributing_branch_required_phrases", ()))
    if len(branches) != len(set(branches)):
        findings.append(
            Finding(schema_path, "contributing_branch_required_phrases must be unique")
        )
    if not branches:
        findings.append(
            Finding(
                schema_path, "contributing_branch_required_phrases must not be empty"
            )
        )
    for phrase in branches:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_branch_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_branches = {
            "`alpha`",
            "`copilot/<task>`",
            "`geryon/<task>`",
            "`cursor/<task>`",
        }
        if branches and not required_branches <= set(branches):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_branch_required_phrases must include alpha/"
                    "copilot/geryon/cursor branch rows",
                )
            )

    pr_reqs = list(inventory.get("contributing_pr_required_phrases", ()))
    if len(pr_reqs) != len(set(pr_reqs)):
        findings.append(
            Finding(schema_path, "contributing_pr_required_phrases must be unique")
        )
    if not pr_reqs:
        findings.append(
            Finding(schema_path, "contributing_pr_required_phrases must not be empty")
        )
    for phrase in pr_reqs:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_pr_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_pr = {
            "## PR Requirements",
            "All CI checks must pass before merge",
            "## Governance",
        }
        if pr_reqs and not required_pr <= set(pr_reqs):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_pr_required_phrases must include PR Requirements, "
                    "CI pass gate, and Governance",
                )
            )

    pr_summary = list(inventory.get("pr_summary_required_phrases", ()))
    if len(pr_summary) != len(set(pr_summary)):
        findings.append(
            Finding(schema_path, "pr_summary_required_phrases must be unique")
        )
    if not pr_summary:
        findings.append(
            Finding(schema_path, "pr_summary_required_phrases must not be empty")
        )
    for phrase in pr_summary:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "pr_summary_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_summary = {"# Summary", "## Problem", "Closes #N"}
        if pr_summary and not required_summary <= set(pr_summary):
            findings.append(
                Finding(
                    schema_path,
                    "pr_summary_required_phrases must include Summary/Problem/"
                    "Closes #N",
                )
            )

    pr_acceptance = list(inventory.get("pr_acceptance_required_phrases", ()))
    if len(pr_acceptance) != len(set(pr_acceptance)):
        findings.append(
            Finding(schema_path, "pr_acceptance_required_phrases must be unique")
        )
    if not pr_acceptance:
        findings.append(
            Finding(schema_path, "pr_acceptance_required_phrases must not be empty")
        )
    for phrase in pr_acceptance:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "pr_acceptance_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_acceptance = {
            "## Changes",
            "## Acceptance Criteria",
            "- [ ]",
        }
        if pr_acceptance and not required_acceptance <= set(pr_acceptance):
            findings.append(
                Finding(
                    schema_path,
                    "pr_acceptance_required_phrases must include Changes/"
                    "Acceptance Criteria/checkbox",
                )
            )

    pr_notes = list(inventory.get("pr_notes_required_phrases", ()))
    if len(pr_notes) != len(set(pr_notes)):
        findings.append(
            Finding(schema_path, "pr_notes_required_phrases must be unique")
        )
    if not pr_notes:
        findings.append(
            Finding(schema_path, "pr_notes_required_phrases must not be empty")
        )
    for phrase in pr_notes:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "pr_notes_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_notes = {
            "## Notes for Reviewer",
            "[agent-surface]",
            "[P1/P2/P3]",
        }
        if pr_notes and not required_notes <= set(pr_notes):
            findings.append(
                Finding(
                    schema_path,
                    "pr_notes_required_phrases must include Notes for Reviewer/"
                    "agent-surface/priority placeholders",
                )
            )

    honesty = list(inventory.get("readme_honesty_required_phrases", ()))
    if len(honesty) != len(set(honesty)):
        findings.append(
            Finding(schema_path, "readme_honesty_required_phrases must be unique")
        )
    if not honesty:
        findings.append(
            Finding(schema_path, "readme_honesty_required_phrases must not be empty")
        )
    for phrase in honesty:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_honesty_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_honesty = {
            "(archived reference)",
            "prompt fiction",
            "fuzzywigg/agents-standard",
        }
        if honesty and not required_honesty <= set(honesty):
            findings.append(
                Finding(
                    schema_path,
                    "readme_honesty_required_phrases must include archived reference/"
                    "prompt fiction/agents-standard",
                )
            )

    historic = list(inventory.get("readme_historic_required_phrases", ()))
    if len(historic) != len(set(historic)):
        findings.append(
            Finding(schema_path, "readme_historic_required_phrases must be unique")
        )
    if not historic:
        findings.append(
            Finding(schema_path, "readme_historic_required_phrases must not be empty")
        )
    for phrase in historic:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_historic_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_historic = {
            "## Historic prompt set",
            "Designing quantum-safe algorithms",
            "Managing conflicts via stimgery and YAML recipes",
        }
        if historic and not required_historic <= set(historic):
            findings.append(
                Finding(
                    schema_path,
                    "readme_historic_required_phrases must include Historic prompt set/"
                    "QuantumArchitect/Orchestration role locks",
                )
            )

    contents = list(inventory.get("readme_contents_required_phrases", ()))
    if len(contents) != len(set(contents)):
        findings.append(
            Finding(schema_path, "readme_contents_required_phrases must be unique")
        )
    if not contents:
        findings.append(
            Finding(schema_path, "readme_contents_required_phrases must not be empty")
        )
    for phrase in contents:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_contents_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_contents = {
            "## Contents",
            "## Cloud agents",
            "## Manifest validation",
            "## License",
        }
        if contents and not required_contents <= set(contents):
            findings.append(
                Finding(
                    schema_path,
                    "readme_contents_required_phrases must include Contents/"
                    "Cloud agents/Manifest validation/License",
                )
            )




    meta = list(inventory.get("hydration_meta_required_phrases", ()))
    if len(meta) != len(set(meta)):
        findings.append(
            Finding(schema_path, "hydration_meta_required_phrases must be unique")
        )
    if not meta:
        findings.append(
            Finding(schema_path, "hydration_meta_required_phrases must not be empty")
        )
    for phrase in meta:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_meta_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_meta = {
            "# Agent Hydration Report — g0p-agents",
            "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
            "Owner: copilot (hydration run) | Edit policy: Agent-editable",
        }
        if meta and not required_meta <= set(meta):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_meta_required_phrases must include title/"
                    "Status/Owner",
                )
            )

    identity_detail = list(
        inventory.get("hydration_identity_detail_required_phrases", ())
    )
    if len(identity_detail) != len(set(identity_detail)):
        findings.append(
            Finding(
                schema_path,
                "hydration_identity_detail_required_phrases must be unique",
            )
        )
    if not identity_detail:
        findings.append(
            Finding(
                schema_path,
                "hydration_identity_detail_required_phrases must not be empty",
            )
        )
    for phrase in identity_detail:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_identity_detail_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_identity = {
            "**LICENSE file absent**",
            "No package.json, requirements.txt, pyproject.toml, Cargo.toml",
            "No executable source code",
        }
        if identity_detail and not required_identity <= set(identity_detail):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_identity_detail_required_phrases must include "
                    "LICENSE/package.json/executable",
                )
            )

    git_detail = list(inventory.get("hydration_git_detail_required_phrases", ()))
    if len(git_detail) != len(set(git_detail)):
        findings.append(
            Finding(
                schema_path, "hydration_git_detail_required_phrases must be unique"
            )
        )
    if not git_detail:
        findings.append(
            Finding(
                schema_path,
                "hydration_git_detail_required_phrases must not be empty",
            )
        )
    for phrase in git_detail:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_git_detail_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_git = {
            "`main` (protected), `copilot/hydrate` (this run)",
            "2 commits total (shallow clone)",
            "copilot/hydrate: no protection",
        }
        if git_detail and not required_git <= set(git_detail):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_git_detail_required_phrases must include "
                    "main/shallow/copilot protection",
                )
            )

    phase2 = list(inventory.get("hydration_phase2_required_phrases", ()))
    if len(phase2) != len(set(phase2)):
        findings.append(
            Finding(schema_path, "hydration_phase2_required_phrases must be unique")
        )
    if not phase2:
        findings.append(
            Finding(schema_path, "hydration_phase2_required_phrases must not be empty")
        )
    for phrase in phase2:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase2_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_phase2 = {
            "## PHASE 2: QUESTIONS",
            "Determines if crypto recommendations are current",
            "Andrew's head",
            "Notion Master Index",
        }
        if phase2 and not required_phase2 <= set(phase2):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase2_required_phrases must include PHASE 2/"
                    "crypto/Andrew/Notion",
                )
            )

    phase5 = list(inventory.get("hydration_phase5_required_phrases", ()))
    if len(phase5) != len(set(phase5)):
        findings.append(
            Finding(schema_path, "hydration_phase5_required_phrases must be unique")
        )
    if not phase5:
        findings.append(
            Finding(schema_path, "hydration_phase5_required_phrases must not be empty")
        )
    for phrase in phase5:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase5_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_phase5 = {
            "## PHASE 5: Roadmap",
            "See GitHub Issue: [claude] g0p-agents Roadmap — Development Timeline & Issue Tracker",
        }
        if phase5 and not required_phase5 <= set(phase5):
            findings.append(
                Finding(
                    schema_path,
                    "hydration_phase5_required_phrases must include PHASE 5/"
                    "Roadmap issue",
                )
            )

    lead = list(inventory.get("readme_lead_required_phrases", ()))
    if len(lead) != len(set(lead)):
        findings.append(
            Finding(schema_path, "readme_lead_required_phrases must be unique")
        )
    if not lead:
        findings.append(
            Finding(schema_path, "readme_lead_required_phrases must not be empty")
        )
    for phrase in lead:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_lead_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_lead = {
            'Docs-only archive of 2025 "Quantum-Blockchain" agent prompts (v2.2, Dec 2025).',
            '"Oracle-Style',
            'architecture *on paper*',
        }
        if lead and not required_lead <= set(lead):
            findings.append(
                Finding(
                    schema_path,
                    "readme_lead_required_phrases must include Docs-only archive/"
                    "Oracle-Style/architecture on paper",
                )
            )

    blurbs = list(inventory.get("readme_blurbs_required_phrases", ()))
    if len(blurbs) != len(set(blurbs)):
        findings.append(
            Finding(schema_path, "readme_blurbs_required_phrases must be unique")
        )
    if not blurbs:
        findings.append(
            Finding(schema_path, "readme_blurbs_required_phrases must not be empty")
        )
    for phrase in blurbs:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_blurbs_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_blurbs = {
            'Full system prompts for the 4 specialist agents.',
            'YAML-based orchestration logic (Goose Framework).',
            'Historic snapshot of the agent constitution.',
        }
        if blurbs and not required_blurbs <= set(blurbs):
            findings.append(
                Finding(
                    schema_path,
                    "readme_blurbs_required_phrases must include Full system prompts/"
                    "YAML-based/Historic snapshot",
                )
            )

    bootstrap = list(inventory.get("readme_bootstrap_required_phrases", ()))
    if len(bootstrap) != len(set(bootstrap)):
        findings.append(
            Finding(schema_path, "readme_bootstrap_required_phrases must be unique")
        )
    if not bootstrap:
        findings.append(
            Finding(schema_path, "readme_bootstrap_required_phrases must not be empty")
        )
    for phrase in bootstrap:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "readme_bootstrap_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_bootstrap = {
            'This is an archived reference implementation, not a live hive.',
            'Docs-only bootstrap lives in',
            'This archive has no runtime agent code.',
        }
        if bootstrap and not required_bootstrap <= set(bootstrap):
            findings.append(
                Finding(
                    schema_path,
                    "readme_bootstrap_required_phrases must include archived reference/"
                    "Docs-only bootstrap/no runtime agent code",
                )
            )

    howto = list(inventory.get("goose_howto_required_phrases", ()))
    if len(howto) != len(set(howto)):
        findings.append(
            Finding(schema_path, "goose_howto_required_phrases must be unique")
        )
    if not howto:
        findings.append(
            Finding(schema_path, "goose_howto_required_phrases must not be empty")
        )
    for phrase in howto:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_howto_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_howto = {
            "## How to Use These Recipes",
            "### Step 1: Individual Recipe (Single Agent)",
            "### Step 2: Master Recipe (All Agents)",
        }
        if howto and not required_howto <= set(howto):
            findings.append(
                Finding(
                    schema_path,
                    "goose_howto_required_phrases must include How to Use/"
                    "Individual/Master Recipe steps",
                )
            )

    state = list(inventory.get("goose_state_machine_required_phrases", ()))
    if len(state) != len(set(state)):
        findings.append(
            Finding(schema_path, "goose_state_machine_required_phrases must be unique")
        )
    if not state:
        findings.append(
            Finding(
                schema_path, "goose_state_machine_required_phrases must not be empty"
            )
        )
    for phrase in state:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_state_machine_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_state = {
            "## Scratchpad State Machine",
            "./agentic_flows/scratchpad.txt",
            "source of truth",
        }
        if state and not required_state <= set(state):
            findings.append(
                Finding(
                    schema_path,
                    "goose_state_machine_required_phrases must include Scratchpad "
                    "State Machine/scratchpad.txt/source of truth",
                )
            )

    naming = list(inventory.get("goose_naming_required_phrases", ()))
    if len(naming) != len(set(naming)):
        findings.append(
            Finding(schema_path, "goose_naming_required_phrases must be unique")
        )
    if not naming:
        findings.append(
            Finding(schema_path, "goose_naming_required_phrases must not be empty")
        )
    for phrase in naming:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_naming_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_naming = {
            "## Recipe Naming Convention",
            "## Adding New Recipes",
            "[domain]_[action]_[target].yaml",
        }
        if naming and not required_naming <= set(naming):
            findings.append(
                Finding(
                    schema_path,
                    "goose_naming_required_phrases must include Recipe Naming "
                    "Convention/Adding New Recipes/domain_action_target pattern",
                )
            )

    roles = list(inventory.get("prompt_roles_required_phrases", ()))
    if len(roles) != len(set(roles)):
        findings.append(
            Finding(schema_path, "prompt_roles_required_phrases must be unique")
        )
    if not roles:
        findings.append(
            Finding(schema_path, "prompt_roles_required_phrases must not be empty")
        )
    for phrase in roles:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_roles_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_roles = {
            "## 1. QuantumArchitectAgent Prompt Template",
            "## 4. OrchestrationAgent Prompt Template",
            "You are the Strategic Orchestrator for the FUZZYWIGG-AI ecosystem.",
            "Your role is NOT to code. Your role is to COORDINATE.",
        }
        if roles and not required_roles <= set(roles):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_roles_required_phrases must include Quantum/"
                    "Orchestration template headings and orchestrator identity",
                )
            )

    sections = list(inventory.get("prompt_sections_required_phrases", ()))
    if len(sections) != len(set(sections)):
        findings.append(
            Finding(schema_path, "prompt_sections_required_phrases must be unique")
        )
    if not sections:
        findings.append(
            Finding(schema_path, "prompt_sections_required_phrases must not be empty")
        )
    for phrase in sections:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_sections_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_sections = {
            "## Your Role",
            "## Key Constraints (NEVER VIOLATE)",
            "## Conflict Resolution Matrix",
            "## Related Documentation",
        }
        if sections and not required_sections <= set(sections):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_sections_required_phrases must include Your Role/"
                    "Key Constraints/Conflict Resolution/Related Documentation",
                )
            )

    usage = list(inventory.get("prompt_usage_required_phrases", ()))
    if len(usage) != len(set(usage)):
        findings.append(
            Finding(schema_path, "prompt_usage_required_phrases must be unique")
        )
    if not usage:
        findings.append(
            Finding(schema_path, "prompt_usage_required_phrases must not be empty")
        )
    for phrase in usage:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_usage_required_phrases entries must be non-empty strings",
                )
            )
            break
    else:
        required_usage = {
            "## Usage Instructions",
            "## Integration with AGENTS.md",
            "[INSERT PROJECT-SPECIFIC INFO HERE]",
        }
        if usage and not required_usage <= set(usage):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_usage_required_phrases must include Usage Instructions/"
                    "Integration with AGENTS.md/INSERT PROJECT-SPECIFIC",
                )
            )

    constraints = list(inventory.get("prompt_constraints_required_phrases", ()))
    if len(constraints) != len(set(constraints)):
        findings.append(
            Finding(schema_path, "prompt_constraints_required_phrases must be unique")
        )
    if not constraints:
        findings.append(
            Finding(
                schema_path, "prompt_constraints_required_phrases must not be empty"
            )
        )
    for phrase in constraints:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_constraints_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_constraints = {
            "Never claim quantum-safety without formal verification",
            "Never expose plaintext keys in RAM or logs",
            "Never deploy without post-quantum cryptography threat modeling",
        }
        if constraints and not required_constraints <= set(constraints):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_constraints_required_phrases must include quantum-safety/"
                    "plaintext keys/post-quantum deploy",
                )
            )

    triggers = list(inventory.get("prompt_triggers_required_phrases", ()))
    if len(triggers) != len(set(triggers)):
        findings.append(
            Finding(schema_path, "prompt_triggers_required_phrases must be unique")
        )
    if not triggers:
        findings.append(
            Finding(schema_path, "prompt_triggers_required_phrases must not be empty")
        )
    for phrase in triggers:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_triggers_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_triggers = {
            "Circuit depth exceeds device constraints by >20%",
            "Crypto operations > 500ms on target device",
            "ESCALATION TO HUMAN REQUIRED",
        }
        if triggers and not required_triggers <= set(triggers):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_triggers_required_phrases must include circuit depth/"
                    "crypto 500ms/ESCALATION TO HUMAN",
                )
            )

    related = list(inventory.get("prompt_related_docs_required_phrases", ()))
    if len(related) != len(set(related)):
        findings.append(
            Finding(schema_path, "prompt_related_docs_required_phrases must be unique")
        )
    if not related:
        findings.append(
            Finding(
                schema_path, "prompt_related_docs_required_phrases must not be empty"
            )
        )
    for phrase in related:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "prompt_related_docs_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_related = {
            "See AGENTS.md Section 22 (Quantum-Blockchain Integration Standards)",
            "See AGENTS.md Section 22.7 (Conflict Resolution Matrix)",
            "Remember: You are not working alone",
        }
        if related and not required_related <= set(related):
            findings.append(
                Finding(
                    schema_path,
                    "prompt_related_docs_required_phrases must include Section 22/"
                    "22.7/Remember not working alone",
                )
            )

    phases = list(inventory.get("implementation_phases_required_phrases", ()))
    if len(phases) != len(set(phases)):
        findings.append(
            Finding(
                schema_path, "implementation_phases_required_phrases must be unique"
            )
        )
    if not phases:
        findings.append(
            Finding(
                schema_path,
                "implementation_phases_required_phrases must not be empty",
            )
        )
    for phrase in phases:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_phases_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_phases = {
            "## Full Implementation (1-2 weeks)",
            "### Phase 1: Infrastructure (Days 1-2)",
            "### Phase 6: Iterate & Refine (Days 6-10)",
            "agentic_flows/quantum_nft_mint_orchestration.yaml",
        }
        if phases and not required_phases <= set(phases):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_phases_required_phrases must include Full "
                    "Implementation/Phase 1/Phase 6/orchestration recipe path",
                )
            )

    tools = list(inventory.get("implementation_tools_required_phrases", ()))
    if len(tools) != len(set(tools)):
        findings.append(
            Finding(
                schema_path, "implementation_tools_required_phrases must be unique"
            )
        )
    if not tools:
        findings.append(
            Finding(
                schema_path,
                "implementation_tools_required_phrases must not be empty",
            )
        )
    for phrase in tools:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_tools_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_tools = {
            "## Tools & Software Checklist",
            "Python 3.11+",
            "Cirq (Python library)",
            "Goose (agent orchestration framework)",
        }
        if tools and not required_tools <= set(tools):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_tools_required_phrases must include Tools "
                    "Checklist/Python/Cirq/Goose",
                )
            )

    success = list(inventory.get("implementation_success_required_phrases", ()))
    if len(success) != len(set(success)):
        findings.append(
            Finding(
                schema_path, "implementation_success_required_phrases must be unique"
            )
        )
    if not success:
        findings.append(
            Finding(
                schema_path,
                "implementation_success_required_phrases must not be empty",
            )
        )
    for phrase in success:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_success_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_success = {
            "## Success Criteria",
            "**By End of Week 1**:",
            "## Common Issues & Solutions",
            "## Next Steps",
        }
        if success and not required_success <= set(success):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_success_required_phrases must include Success "
                    "Criteria/Week 1/Common Issues/Next Steps",
                )
            )

    issues = list(inventory.get("implementation_issues_required_phrases", ()))
    if len(issues) != len(set(issues)):
        findings.append(
            Finding(
                schema_path, "implementation_issues_required_phrases must be unique"
            )
        )
    if not issues:
        findings.append(
            Finding(
                schema_path,
                "implementation_issues_required_phrases must not be empty",
            )
        )
    for phrase in issues:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_issues_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_issues = {
            "## Common Issues & Solutions",
            '### Issue 1: "Cirq is too slow for mobile"',
            "Use Qualtran to analyze circuit resource requirements",
            "Scratchpad is append-only, never overwrite",
        }
        if issues and not required_issues <= set(issues):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_issues_required_phrases must include Common "
                    "Issues/Issue 1/Qualtran/append-only",
                )
            )

    faq = list(inventory.get("implementation_faq_required_phrases", ()))
    if len(faq) != len(set(faq)):
        findings.append(
            Finding(schema_path, "implementation_faq_required_phrases must be unique")
        )
    if not faq:
        findings.append(
            Finding(
                schema_path,
                "implementation_faq_required_phrases must not be empty",
            )
        )
    for phrase in faq:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_faq_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_faq = {
            "## FAQ",
            "Do I need a real quantum computer to start?",
            "Cirq simulator works locally",
            "Can I run agents in parallel?",
        }
        if faq and not required_faq <= set(faq):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_faq_required_phrases must include FAQ/"
                    "quantum-computer/Cirq/parallel",
                )
            )

    support = list(inventory.get("implementation_support_required_phrases", ()))
    if len(support) != len(set(support)):
        findings.append(
            Finding(
                schema_path, "implementation_support_required_phrases must be unique"
            )
        )
    if not support:
        findings.append(
            Finding(
                schema_path,
                "implementation_support_required_phrases must not be empty",
            )
        )
    for phrase in support:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "implementation_support_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_support = {
            "## Support & Resources",
            "AGENTS.md v2.2 (your constitution)",
            "https://quantumai.google/cirq",
            "https://block.github.io/goose/",
        }
        if support and not required_support <= set(support):
            findings.append(
                Finding(
                    schema_path,
                    "implementation_support_required_phrases must include Support/"
                    "AGENTS.md/Cirq/Goose URLs",
                )
            )

    timeline = list(inventory.get("execution_timeline_required_phrases", ()))
    if len(timeline) != len(set(timeline)):
        findings.append(
            Finding(schema_path, "execution_timeline_required_phrases must be unique")
        )
    if not timeline:
        findings.append(
            Finding(schema_path, "execution_timeline_required_phrases must not be empty")
        )
    for phrase in timeline:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_timeline_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_timeline = {
            "## Implementation Timeline",
            "### Week 1 Checklist",
            "### By End of Month",
        }
        if timeline and not required_timeline <= set(timeline):
            findings.append(
                Finding(
                    schema_path,
                    "execution_timeline_required_phrases must include Implementation "
                    "Timeline/Week 1/By End of Month",
                )
            )

    technologies = list(inventory.get("execution_technologies_required_phrases", ()))
    if len(technologies) != len(set(technologies)):
        findings.append(
            Finding(
                schema_path, "execution_technologies_required_phrases must be unique"
            )
        )
    if not technologies:
        findings.append(
            Finding(
                schema_path,
                "execution_technologies_required_phrases must not be empty",
            )
        )
    for phrase in technologies:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_technologies_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_tech = {
            "## Key Technologies (All Covered)",
            "Google Cirq (circuit construction)",
            "Goose (agent framework)",
        }
        if technologies and not required_tech <= set(technologies):
            findings.append(
                Finding(
                    schema_path,
                    "execution_technologies_required_phrases must include Key "
                    "Technologies/Cirq/Goose",
                )
            )

    workflow = list(inventory.get("execution_workflow_required_phrases", ()))
    if len(workflow) != len(set(workflow)):
        findings.append(
            Finding(schema_path, "execution_workflow_required_phrases must be unique")
        )
    if not workflow:
        findings.append(
            Finding(schema_path, "execution_workflow_required_phrases must not be empty")
        )
    for phrase in workflow:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_workflow_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_workflow = {
            "## Workflow Overview",
            "### Step 1: Single Agent Task",
            "### Step 3: Escalation (If Conflict)",
        }
        if workflow and not required_workflow <= set(workflow):
            findings.append(
                Finding(
                    schema_path,
                    "execution_workflow_required_phrases must include Workflow "
                    "Overview/Single Agent/Escalation",
                )
            )

    ide = list(inventory.get("execution_ide_required_phrases", ()))
    if len(ide) != len(set(ide)):
        findings.append(
            Finding(schema_path, "execution_ide_required_phrases must be unique")
        )
    if not ide:
        findings.append(
            Finding(schema_path, "execution_ide_required_phrases must not be empty")
        )
    for phrase in ide:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_ide_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_ide = {
            "## IDE & Software Setup",
            "Python 3.11+ (WSL2)",
            "**Total Setup Time**: ~1 hour (mostly downloads)",
        }
        if ide and not required_ide <= set(ide):
            findings.append(
                Finding(
                    schema_path,
                    "execution_ide_required_phrases must include IDE Setup/"
                    "Python 3.11+/Total Setup Time",
                )
            )

    innovations = list(inventory.get("execution_innovations_required_phrases", ()))
    if len(innovations) != len(set(innovations)):
        findings.append(
            Finding(
                schema_path, "execution_innovations_required_phrases must be unique"
            )
        )
    if not innovations:
        findings.append(
            Finding(
                schema_path,
                "execution_innovations_required_phrases must not be empty",
            )
        )
    for phrase in innovations:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_innovations_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_innovations = {
            "## What Makes This Different",
            "## Key Innovations in Your System",
            "**Recipe-Based Orchestration**: Goose recipes enable reproducible workflows",
        }
        if innovations and not required_innovations <= set(innovations):
            findings.append(
                Finding(
                    schema_path,
                    "execution_innovations_required_phrases must include What Makes "
                    "This Different/Key Innovations/Recipe-Based Orchestration",
                )
            )

    next48 = list(inventory.get("execution_next48_required_phrases", ()))
    if len(next48) != len(set(next48)):
        findings.append(
            Finding(schema_path, "execution_next48_required_phrases must be unique")
        )
    if not next48:
        findings.append(
            Finding(
                schema_path, "execution_next48_required_phrases must not be empty"
            )
        )
    for phrase in next48:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "execution_next48_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_next48 = {
            "## Next 48 Hours",
            "### Today (2025-12-13)",
            "Instantiate first agent (QuantumArchitectAgent)",
        }
        if next48 and not required_next48 <= set(next48):
            findings.append(
                Finding(
                    schema_path,
                    "execution_next48_required_phrases must include Next 48 Hours/"
                    "Today/QuantumArchitectAgent instantiate",
                )
            )

    issues = list(inventory.get("contributing_issues_required_phrases", ()))
    if len(issues) != len(set(issues)):
        findings.append(
            Finding(schema_path, "contributing_issues_required_phrases must be unique")
        )
    if not issues:
        findings.append(
            Finding(
                schema_path, "contributing_issues_required_phrases must not be empty"
            )
        )
    for phrase in issues:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_issues_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_issues = {
            "## Issue Reporting",
            "**Bug** — something broken",
            "**Agent Task** — structured work",
        }
        if issues and not required_issues <= set(issues):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_issues_required_phrases must include Issue "
                    "Reporting/Bug/Agent Task",
                )
            )

    local = list(inventory.get("contributing_local_required_phrases", ()))
    if len(local) != len(set(local)):
        findings.append(
            Finding(schema_path, "contributing_local_required_phrases must be unique")
        )
    if not local:
        findings.append(
            Finding(
                schema_path, "contributing_local_required_phrases must not be empty"
            )
        )
    for phrase in local:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_local_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_local = {
            "## Local validation (docs packaging)",
            "python scripts/validate_manifests.py",
            "ruff check scripts tests",
        }
        if local and not required_local <= set(local):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_local_required_phrases must include Local "
                    "validation/validate_manifests/ruff",
                )
            )

    governance = list(inventory.get("contributing_governance_required_phrases", ()))
    if len(governance) != len(set(governance)):
        findings.append(
            Finding(
                schema_path,
                "contributing_governance_required_phrases must be unique",
            )
        )
    if not governance:
        findings.append(
            Finding(
                schema_path,
                "contributing_governance_required_phrases must not be empty",
            )
        )
    for phrase in governance:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_governance_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_gov = {
            "## Governance",
            "Structural changes",
            "require Andrew approval before merging",
        }
        if governance and not required_gov <= set(governance):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_governance_required_phrases must include "
                    "Governance/Structural changes/Andrew approval",
                )
            )


    metadata = list(inventory.get("contributing_metadata_required_phrases", ()))
    if len(metadata) != len(set(metadata)):
        findings.append(
            Finding(
                schema_path,
                "contributing_metadata_required_phrases must be unique",
            )
        )
    if not metadata:
        findings.append(
            Finding(
                schema_path,
                "contributing_metadata_required_phrases must not be empty",
            )
        )
    for phrase in metadata:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_metadata_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_meta = {
            "# Contributing to g0p-agents",
            "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
            "Edit policy: Agent-editable; structural changes require Andrew approval",
        }
        if metadata and not required_meta <= set(metadata):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_metadata_required_phrases must include "
                    "title/Status/Edit policy",
                )
            )

    surfaces = list(inventory.get("contributing_surfaces_required_phrases", ()))
    if len(surfaces) != len(set(surfaces)):
        findings.append(
            Finding(
                schema_path,
                "contributing_surfaces_required_phrases must be unique",
            )
        )
    if not surfaces:
        findings.append(
            Finding(
                schema_path,
                "contributing_surfaces_required_phrases must not be empty",
            )
        )
    for phrase in surfaces:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_surfaces_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_surfaces = {
            "copilot, geryon, claude-cowork, browser-claude, playwright",
            "Never push directly",
            "thin docs/CI/hygiene",
        }
        if surfaces and not required_surfaces <= set(surfaces):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_surfaces_required_phrases must include "
                    "surface list/Never push/cursor hygiene",
                )
            )

    ci_honesty = list(inventory.get("contributing_ci_honesty_required_phrases", ()))
    if len(ci_honesty) != len(set(ci_honesty)):
        findings.append(
            Finding(
                schema_path,
                "contributing_ci_honesty_required_phrases must be unique",
            )
        )
    if not ci_honesty:
        findings.append(
            Finding(
                schema_path,
                "contributing_ci_honesty_required_phrases must not be empty",
            )
        )
    for phrase in ci_honesty:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "contributing_ci_honesty_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_ci_honesty = {
            "markdown lint, link check, actionlint",
            "Packaging inventory v50",
            "refuse invented recipes",
        }
        if ci_honesty and not required_ci_honesty <= set(ci_honesty):
            findings.append(
                Finding(
                    schema_path,
                    "contributing_ci_honesty_required_phrases must include "
                    "CI checks/Packaging inventory v50/refuse invented recipes",
                )
            )

    scope = list(inventory.get("security_scope_required_phrases", ()))
    if len(scope) != len(set(scope)):
        findings.append(
            Finding(schema_path, "security_scope_required_phrases must be unique")
        )
    if not scope:
        findings.append(
            Finding(schema_path, "security_scope_required_phrases must not be empty")
        )
    for phrase in scope:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_scope_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_scope = {
            "## Supported Versions",
            "Security policy applies to:",
            "potential prompt injection surface",
        }
        if scope and not required_scope <= set(scope):
            findings.append(
                Finding(
                    schema_path,
                    "security_scope_required_phrases must include Supported "
                    "Versions/applies-to/prompt-injection leftovers",
                )
            )

    reporting_channel = list(
        inventory.get("security_reporting_channel_required_phrases", ())
    )
    if len(reporting_channel) != len(set(reporting_channel)):
        findings.append(
            Finding(
                schema_path,
                "security_reporting_channel_required_phrases must be unique",
            )
        )
    if not reporting_channel:
        findings.append(
            Finding(
                schema_path,
                "security_reporting_channel_required_phrases must not be empty",
            )
        )
    for phrase in reporting_channel:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_reporting_channel_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_channel = {
            "## Reporting a Vulnerability",
            "Expected response:",
            "GitHub @fuzzywigg",
        }
        if reporting_channel and not required_channel <= set(reporting_channel):
            findings.append(
                Finding(
                    schema_path,
                    "security_reporting_channel_required_phrases must include "
                    "Reporting heading/Expected response/@fuzzywigg",
                )
            )

    compliance = list(inventory.get("security_compliance_detail_required_phrases", ()))
    if len(compliance) != len(set(compliance)):
        findings.append(
            Finding(
                schema_path,
                "security_compliance_detail_required_phrases must be unique",
            )
        )
    if not compliance:
        findings.append(
            Finding(
                schema_path,
                "security_compliance_detail_required_phrases must not be empty",
            )
        )
    for phrase in compliance:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_compliance_detail_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_compliance = {
            "When code is scaffolded into this repo, it must comply with:",
            "in RAM, logs, or code",
            "updated in a future issue",
        }
        if compliance and not required_compliance <= set(compliance):
            findings.append(
                Finding(
                    schema_path,
                    "security_compliance_detail_required_phrases must include "
                    "scaffold-comply/RAM-logs/future-issue leftovers",
                )
            )

    header = list(inventory.get("security_header_required_phrases", ()))
    if len(header) != len(set(header)):
        findings.append(
            Finding(schema_path, "security_header_required_phrases must be unique")
        )
    if not header:
        findings.append(
            Finding(schema_path, "security_header_required_phrases must not be empty")
        )
    for phrase in header:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_header_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_header = {
            "# Security Policy",
            "Status: ACTIVE | Tier: 1 | Created: 2026-04-13",
            "Edit policy: Structural changes require Andrew approval",
        }
        if header and not required_header <= set(header):
            findings.append(
                Finding(
                    schema_path,
                    "security_header_required_phrases must include Security "
                    "Policy/Status/Edit policy",
                )
            )

    fips = list(inventory.get("security_fips_required_phrases", ()))
    if len(fips) != len(set(fips)):
        findings.append(
            Finding(schema_path, "security_fips_required_phrases must be unique")
        )
    if not fips:
        findings.append(
            Finding(schema_path, "security_fips_required_phrases must not be empty")
        )
    for phrase in fips:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_fips_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_fips = {
            "## Security Standards for This Ecosystem",
            "ML-KEM/FIPS 203",
            "SLH-DSA/FIPS 205",
        }
        if fips and not required_fips <= set(fips):
            findings.append(
                Finding(
                    schema_path,
                    "security_fips_required_phrases must include Security "
                    "Standards/ML-KEM/SLH-DSA",
                )
            )

    non_issues = list(inventory.get("security_known_non_issues_required_phrases", ()))
    if len(non_issues) != len(set(non_issues)):
        findings.append(
            Finding(
                schema_path,
                "security_known_non_issues_required_phrases must be unique",
            )
        )
    if not non_issues:
        findings.append(
            Finding(
                schema_path,
                "security_known_non_issues_required_phrases must not be empty",
            )
        )
    for phrase in non_issues:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "security_known_non_issues_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_non_issues = {
            "## Known Non-Issues",
            "CRYSTALS-Kyber",
            "ML-KEM (FIPS 203)",
        }
        if non_issues and not required_non_issues <= set(non_issues):
            findings.append(
                Finding(
                    schema_path,
                    "security_known_non_issues_required_phrases must include "
                    "Known Non-Issues/Kyber/ML-KEM",
                )
            )

    crypto = list(inventory.get("constitution_crypto_required_phrases", ()))
    if len(crypto) != len(set(crypto)):
        findings.append(
            Finding(schema_path, "constitution_crypto_required_phrases must be unique")
        )
    if not crypto:
        findings.append(
            Finding(
                schema_path, "constitution_crypto_required_phrases must not be empty"
            )
        )
    for phrase in crypto:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_crypto_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_crypto = {
            "### 22.1 Quantum-Safe Cryptography Requirements",
            "CRYSTALS-Kyber",
            "SPHINCS+",
        }
        if crypto and not required_crypto <= set(crypto):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_crypto_required_phrases must include "
                    "22.1/Kyber/SPHINCS+",
                )
            )

    handoff = list(inventory.get("constitution_handoff_required_phrases", ()))
    if len(handoff) != len(set(handoff)):
        findings.append(
            Finding(
                schema_path, "constitution_handoff_required_phrases must be unique"
            )
        )
    if not handoff:
        findings.append(
            Finding(
                schema_path, "constitution_handoff_required_phrases must not be empty"
            )
        )
    for phrase in handoff:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_handoff_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_handoff = {
            "#### 22.4.1 Handoff Sequence",
            "**Phase 1: Algorithm Design**",
            "**Phase 4: Orchestration Decision**",
        }
        if handoff and not required_handoff <= set(handoff):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_handoff_required_phrases must include "
                    "22.4.1/Phase 1/Phase 4",
                )
            )

    esc_matrix = list(
        inventory.get("constitution_escalation_matrix_required_phrases", ())
    )
    if len(esc_matrix) != len(set(esc_matrix)):
        findings.append(
            Finding(
                schema_path,
                "constitution_escalation_matrix_required_phrases must be unique",
            )
        )
    if not esc_matrix:
        findings.append(
            Finding(
                schema_path,
                "constitution_escalation_matrix_required_phrases must not be empty",
            )
        )
    for phrase in esc_matrix:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_escalation_matrix_required_phrases entries "
                    "must be non-empty strings",
                )
            )
            break
    else:
        required_esc = {
            "#### 22.4.2 Escalation Triggers",
            "**QuantumArchitectAgent escalates when**:",
            "**OrchestrationAgent escalates to user when**:",
        }
        if esc_matrix and not required_esc <= set(esc_matrix):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_escalation_matrix_required_phrases must include "
                    "22.4.2/QuantumArchitect/Orchestration",
                )
            )



    on_device = list(inventory.get("constitution_on_device_required_phrases", ()))
    if len(on_device) != len(set(on_device)):
        findings.append(
            Finding(
                schema_path, "constitution_on_device_required_phrases must be unique"
            )
        )
    if not on_device:
        findings.append(
            Finding(
                schema_path,
                "constitution_on_device_required_phrases must not be empty",
            )
        )
    for phrase in on_device:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_on_device_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_on_device = {
            "### 22.2 On-Device Quantum Logic Execution",
            "MUST use Cirq circuits compiled for mobile constraints",
            "Cirq-sim (classical validation)",
        }
        if on_device and not required_on_device <= set(on_device):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_on_device_required_phrases must include "
                    "22.2/Cirq/Cirq-sim",
                )
            )

    multichain = list(inventory.get("constitution_multichain_required_phrases", ()))
    if len(multichain) != len(set(multichain)):
        findings.append(
            Finding(
                schema_path, "constitution_multichain_required_phrases must be unique"
            )
        )
    if not multichain:
        findings.append(
            Finding(
                schema_path,
                "constitution_multichain_required_phrases must not be empty",
            )
        )
    for phrase in multichain:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_multichain_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_multichain = {
            "### 22.3 Multi-Chain State Consistency",
            "State Commitment Protocol",
            "Failure Recovery",
        }
        if multichain and not required_multichain <= set(multichain):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_multichain_required_phrases must include "
                    "22.3/State Commitment/Failure Recovery",
                )
            )

    esc_format = list(
        inventory.get("constitution_escalation_format_required_phrases", ())
    )
    if len(esc_format) != len(set(esc_format)):
        findings.append(
            Finding(
                schema_path,
                "constitution_escalation_format_required_phrases must be unique",
            )
        )
    if not esc_format:
        findings.append(
            Finding(
                schema_path,
                "constitution_escalation_format_required_phrases must not be empty",
            )
        )
    for phrase in esc_format:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_escalation_format_required_phrases entries "
                    "must be non-empty strings",
                )
            )
            break
    else:
        required_esc_format = {
            "#### 22.4.3 Escalation Format (All Agents)",
            "🚨 ESCALATION REQUIRED",
            "Awaiting approval before proceeding.",
        }
        if esc_format and not required_esc_format <= set(esc_format):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_escalation_format_required_phrases must include "
                    "22.4.3/ESCALATION REQUIRED/Awaiting approval",
                )
            )

    recipe_orch = list(
        inventory.get("constitution_recipe_orchestration_required_phrases", ())
    )
    if len(recipe_orch) != len(set(recipe_orch)):
        findings.append(
            Finding(
                schema_path,
                "constitution_recipe_orchestration_required_phrases must be unique",
            )
        )
    if not recipe_orch:
        findings.append(
            Finding(
                schema_path,
                "constitution_recipe_orchestration_required_phrases must not be empty",
            )
        )
    for phrase in recipe_orch:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_recipe_orchestration_required_phrases entries "
                    "must be non-empty strings",
                )
            )
            break
    else:
        required_recipe_orch = {
            "### 22.5 Recipe-Based Orchestration Structure",
            "name: quantum_nft_mint_workflow",
            "All three agents sign off before mainnet deployment",
        }
        if recipe_orch and not required_recipe_orch <= set(recipe_orch):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_recipe_orchestration_required_phrases must include "
                    "22.5/quantum_nft_mint_workflow/sign-off",
                )
            )

    scratch_state = list(
        inventory.get("constitution_scratchpad_state_required_phrases", ())
    )
    if len(scratch_state) != len(set(scratch_state)):
        findings.append(
            Finding(
                schema_path,
                "constitution_scratchpad_state_required_phrases must be unique",
            )
        )
    if not scratch_state:
        findings.append(
            Finding(
                schema_path,
                "constitution_scratchpad_state_required_phrases must not be empty",
            )
        )
    for phrase in scratch_state:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_scratchpad_state_required_phrases entries "
                    "must be non-empty strings",
                )
            )
            break
    else:
        required_scratch_state = {
            "### 22.6 Scratchpad State Machine",
            "Checkbox state is source of truth",
            "Only append, never overwrite",
        }
        if scratch_state and not required_scratch_state <= set(scratch_state):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_scratchpad_state_required_phrases must include "
                    "22.6/Checkbox/Only append",
                )
            )

    conflict_matrix = list(
        inventory.get("constitution_conflict_matrix_required_phrases", ())
    )
    if len(conflict_matrix) != len(set(conflict_matrix)):
        findings.append(
            Finding(
                schema_path,
                "constitution_conflict_matrix_required_phrases must be unique",
            )
        )
    if not conflict_matrix:
        findings.append(
            Finding(
                schema_path,
                "constitution_conflict_matrix_required_phrases must not be empty",
            )
        )
    for phrase in conflict_matrix:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "constitution_conflict_matrix_required_phrases entries "
                    "must be non-empty strings",
                )
            )
            break
    else:
        required_conflict_matrix = {
            "### 22.7 Conflict Resolution Matrix",
            "**Quantum Algorithm Complexity**",
            "**Final Decision Maker**: OrchestrationAgent",
        }
        if conflict_matrix and not required_conflict_matrix <= set(conflict_matrix):
            findings.append(
                Finding(
                    schema_path,
                    "constitution_conflict_matrix_required_phrases must include "
                    "22.7/Quantum Algorithm/Final Decision Maker",
                )
            )

    changelog_format = list(inventory.get("changelog_format_required_phrases", ()))
    if len(changelog_format) != len(set(changelog_format)):
        findings.append(
            Finding(schema_path, "changelog_format_required_phrases must be unique")
        )
    if not changelog_format:
        findings.append(
            Finding(schema_path, "changelog_format_required_phrases must not be empty")
        )
    for phrase in changelog_format:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_format_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_format = {
            "# Changelog",
            "## [Unreleased]",
            "### Added",
        }
        if changelog_format and not required_format <= set(changelog_format):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_format_required_phrases must include Changelog/"
                    "Unreleased/Added",
                )
            )

    changelog_unreleased = list(
        inventory.get("changelog_unreleased_required_phrases", ())
    )
    if len(changelog_unreleased) != len(set(changelog_unreleased)):
        findings.append(
            Finding(
                schema_path, "changelog_unreleased_required_phrases must be unique"
            )
        )
    if not changelog_unreleased:
        findings.append(
            Finding(
                schema_path, "changelog_unreleased_required_phrases must not be empty"
            )
        )
    for phrase in changelog_unreleased:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_unreleased_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_unreleased = {
            "## [Unreleased]",
            "Packaging inventory",
            "historic four",
        }
        if changelog_unreleased and not required_unreleased <= set(
            changelog_unreleased
        ):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_unreleased_required_phrases must include Unreleased/"
                    "Packaging/historic",
                )
            )

    changelog_release = list(inventory.get("changelog_release_required_phrases", ()))
    if len(changelog_release) != len(set(changelog_release)):
        findings.append(
            Finding(schema_path, "changelog_release_required_phrases must be unique")
        )
    if not changelog_release:
        findings.append(
            Finding(
                schema_path, "changelog_release_required_phrases must not be empty"
            )
        )
    for phrase in changelog_release:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "changelog_release_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_release = {
            "### Changed",
            "## [0.1.0] — 2025-12-13",
            "`GOOSE-RECIPES.md` — Goose YAML recipe templates",
        }
        if changelog_release and not required_release <= set(changelog_release):
            findings.append(
                Finding(
                    schema_path,
                    "changelog_release_required_phrases must include Changed/"
                    "0.1.0/GOOSE-RECIPES",
                )
            )


    goose_headers = list(inventory.get("goose_recipe_headers_required_phrases", ()))
    if len(goose_headers) != len(set(goose_headers)):
        findings.append(
            Finding(schema_path, "goose_recipe_headers_required_phrases must be unique")
        )
    if not goose_headers:
        findings.append(
            Finding(
                schema_path, "goose_recipe_headers_required_phrases must not be empty"
            )
        )
    for phrase in goose_headers:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_recipe_headers_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_headers = {
            "## Recipe 1: Quantum Algorithm Design",
            "## Recipe 4: Multi-Agent Orchestration (Master Recipe)",
            "**File**: `./agentic_flows/quantum_nft_mint_orchestration.yaml`",
        }
        if goose_headers and not required_headers <= set(goose_headers):
            findings.append(
                Finding(
                    schema_path,
                    "goose_recipe_headers_required_phrases must include Recipe 1/"
                    "Recipe 4/orchestration File",
                )
            )

    goose_instr = list(inventory.get("goose_instruction_agents_required_phrases", ()))
    if len(goose_instr) != len(set(goose_instr)):
        findings.append(
            Finding(
                schema_path,
                "goose_instruction_agents_required_phrases must be unique",
            )
        )
    if not goose_instr:
        findings.append(
            Finding(
                schema_path,
                "goose_instruction_agents_required_phrases must not be empty",
            )
        )
    for phrase in goose_instr:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_instruction_agents_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_instr = {
            "You are QuantumArchitectAgent designing a quantum algorithm for FUZZYWIGG.",
            "You are OrchestrationAgent coordinating a complete quantum NFT mint operation.",
        }
        if goose_instr and not required_instr <= set(goose_instr):
            findings.append(
                Finding(
                    schema_path,
                    "goose_instruction_agents_required_phrases must include "
                    "QuantumArchitect/Orchestration",
                )
            )

    goose_ext = list(inventory.get("goose_extensions_required_phrases", ()))
    if len(goose_ext) != len(set(goose_ext)):
        findings.append(
            Finding(schema_path, "goose_extensions_required_phrases must be unique")
        )
    if not goose_ext:
        findings.append(
            Finding(schema_path, "goose_extensions_required_phrases must not be empty")
        )
    for phrase in goose_ext:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_extensions_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_ext = {
            "type: builtin",
            "name: developer",
            "timeout: 600",
        }
        if goose_ext and not required_ext <= set(goose_ext):
            findings.append(
                Finding(
                    schema_path,
                    "goose_extensions_required_phrases must include builtin/"
                    "developer/timeout 600",
                )
            )

    orch = list(inventory.get("goose_orchestration_required_phrases", ()))
    if len(orch) != len(set(orch)):
        findings.append(
            Finding(schema_path, "goose_orchestration_required_phrases must be unique")
        )
    if not orch:
        findings.append(
            Finding(
                schema_path, "goose_orchestration_required_phrases must not be empty"
            )
        )
    for phrase in orch:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_orchestration_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_orch = {
            "## Master Orchestration Task: Quantum NFT Mint",
            "STEP 2: Run QuantumArchitectAgent recipe",
            "STEP 6: Make final decision",
        }
        if orch and not required_orch <= set(orch):
            findings.append(
                Finding(
                    schema_path,
                    "goose_orchestration_required_phrases must include Master "
                    "Orchestration/QuantumArchitectAgent recipe/final decision",
                )
            )

    conflicts = list(inventory.get("goose_conflicts_required_phrases", ()))
    if len(conflicts) != len(set(conflicts)):
        findings.append(
            Finding(schema_path, "goose_conflicts_required_phrases must be unique")
        )
    if not conflicts:
        findings.append(
            Finding(schema_path, "goose_conflicts_required_phrases must not be empty")
        )
    for phrase in conflicts:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_conflicts_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_conflicts = {
            "Conflict Type 1: PERFORMANCE",
            "Conflict Type 2: SECURITY",
            "Decision: 🚨 ESCALATE TO HUMAN",
        }
        if conflicts and not required_conflicts <= set(conflicts):
            findings.append(
                Finding(
                    schema_path,
                    "goose_conflicts_required_phrases must include PERFORMANCE/"
                    "SECURITY/ESCALATE TO HUMAN",
                )
            )

    qtask = list(inventory.get("goose_quantum_task_required_phrases", ()))
    if len(qtask) != len(set(qtask)):
        findings.append(
            Finding(schema_path, "goose_quantum_task_required_phrases must be unique")
        )
    if not qtask:
        findings.append(
            Finding(
                schema_path, "goose_quantum_task_required_phrases must not be empty"
            )
        )
    for phrase in qtask:
        if not isinstance(phrase, str) or not phrase.strip():
            findings.append(
                Finding(
                    schema_path,
                    "goose_quantum_task_required_phrases entries must be "
                    "non-empty strings",
                )
            )
            break
    else:
        required_qtask = {
            "## Quantum Algorithm Design Task",
            "PENDING_QUANTUM_DESIGN",
            "Use Google Cirq for circuit construction",
        }
        if qtask and not required_qtask <= set(qtask):
            findings.append(
                Finding(
                    schema_path,
                    "goose_quantum_task_required_phrases must include Quantum "
                    "Algorithm Design Task/PENDING_QUANTUM_DESIGN/Google Cirq",
                )
            )


    return findings


def _validate_historic_recipe_settings(data: dict[str, Any], *, path: str) -> list[Finding]:
    findings: list[Finding] = []
    recipe = data.get("recipe")
    if not isinstance(recipe, dict):
        return findings
    version = recipe.get("version")
    if version != HISTORIC_RECIPE_VERSION:
        findings.append(
            Finding(
                path,
                (
                    f"historic recipe version must be "
                    f"{HISTORIC_RECIPE_VERSION!r}, found {version!r}"
                ),
            )
        )
    settings = recipe.get("settings")
    if isinstance(settings, dict):
        provider = settings.get("goose_provider")
        model = settings.get("goose_model")
        if provider != HISTORIC_GOOSE_PROVIDER:
            findings.append(
                Finding(
                    path,
                    (
                        f"historic goose_provider must be "
                        f"{HISTORIC_GOOSE_PROVIDER!r}, found {provider!r}"
                    ),
                )
            )
        if model != HISTORIC_GOOSE_MODEL:
            findings.append(
                Finding(
                    path,
                    (
                        f"historic goose_model must be "
                        f"{HISTORIC_GOOSE_MODEL!r}, found {model!r}"
                    ),
                )
            )
    extensions = recipe.get("extensions")
    if isinstance(extensions, list):
        matched = False
        for item in extensions:
            if not isinstance(item, dict):
                continue
            if (
                item.get("type") == HISTORIC_EXTENSION_TYPE
                and item.get("name") == HISTORIC_EXTENSION_NAME
            ):
                matched = True
                break
        if not matched:
            findings.append(
                Finding(
                    path,
                    (
                        "recipe must include historic "
                        f"{HISTORIC_EXTENSION_TYPE}/{HISTORIC_EXTENSION_NAME} extension"
                    ),
                )
            )
    return findings


def validate_goose_recipes(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schema = load_schema("goose-recipe.schema.json")
    recipes_doc = root / "GOOSE-RECIPES.md"
    if not recipes_doc.is_file():
        return [Finding("GOOSE-RECIPES.md", "required documentation file is missing")]

    markdown = recipes_doc.read_text(encoding="utf-8")
    blocks = extract_fenced_yaml_blocks(markdown)
    if len(blocks) != 4:
        findings.append(
            Finding(
                "GOOSE-RECIPES.md",
                f"expected exactly 4 documented Goose recipe YAML fences, found {len(blocks)}",
            )
        )

    parsed_names: list[str] = []
    for index, block in enumerate(blocks, start=1):
        path = f"GOOSE-RECIPES.md#recipe-{index}"
        data, parse_findings = parse_yaml_text(block, path=path)
        findings.extend(parse_findings)
        if data is None:
            continue
        if not isinstance(data, dict):
            findings.append(Finding(path, "recipe YAML must be a mapping"))
            continue
        findings.extend(validate_against_schema(data, schema, path=path))
        findings.extend(_validate_historic_recipe_settings(data, path=path))
        name = data.get("name")
        if isinstance(name, str):
            parsed_names.append(name)

    if len(parsed_names) != len(set(parsed_names)):
        findings.append(Finding("GOOSE-RECIPES.md", "duplicate recipe name values"))

    name_set = set(parsed_names)
    if parsed_names and name_set != EXPECTED_RECIPE_NAMES:
        missing = sorted(EXPECTED_RECIPE_NAMES - name_set)
        extra = sorted(name_set - EXPECTED_RECIPE_NAMES)
        if missing:
            findings.append(
                Finding(
                    "GOOSE-RECIPES.md",
                    f"missing locked recipe name(s): {', '.join(missing)}",
                )
            )
        if extra:
            findings.append(
                Finding(
                    "GOOSE-RECIPES.md",
                    f"unexpected/invented recipe name(s): {', '.join(extra)}",
                )
            )

    flows = root / "agentic_flows"
    if flows.is_dir():
        allowed_names = set(AGENTIC_FLOWS_ALLOWED_FILES) | {
            Path(rel).name for rel in EXPECTED_RECIPE_FILES
        }
        for child in sorted(flows.iterdir()):
            if not child.is_file():
                continue
            if child.name not in allowed_names:
                findings.append(
                    Finding(
                        str(child.relative_to(root)),
                        "unexpected/invented agentic_flows file (not in locked allow-list)",
                    )
                )
        on_disk = sorted(flows.glob("*.yaml")) + sorted(flows.glob("*.yml"))
        for yaml_path in on_disk:
            rel = str(yaml_path.relative_to(root))
            if rel not in EXPECTED_RECIPE_FILES:
                findings.append(
                    Finding(
                        rel,
                        "unexpected/invented on-disk recipe file (not in locked inventory)",
                    )
                )
                continue
            text = yaml_path.read_text(encoding="utf-8")
            data, parse_findings = parse_yaml_text(text, path=rel)
            findings.extend(parse_findings)
            if data is None:
                continue
            if not isinstance(data, dict):
                findings.append(Finding(rel, "recipe YAML must be a mapping"))
                continue
            findings.extend(validate_against_schema(data, schema, path=rel))
            findings.extend(_validate_historic_recipe_settings(data, path=rel))
            name = data.get("name")
            if isinstance(name, str):
                expected_file = EXPECTED_RECIPE_BINDINGS.get(name)
                if expected_file and expected_file != rel:
                    findings.append(
                        Finding(
                            rel,
                            f"on-disk recipe name {name} must live at {expected_file}",
                        )
                    )

    declared = documented_recipe_file_paths(markdown)
    if len(declared) != len(blocks):
        findings.append(
            Finding(
                "GOOSE-RECIPES.md",
                (
                    f"documented **File** paths ({len(declared)}) "
                    f"do not match recipe fences ({len(blocks)})"
                ),
            )
        )
    if declared and tuple(declared) != EXPECTED_RECIPE_FILES:
        findings.append(
            Finding(
                "GOOSE-RECIPES.md",
                "documented **File** paths do not match locked recipe file inventory",
            )
        )

    if len(parsed_names) == len(declared) == 4:
        for name, file_path in zip(parsed_names, declared, strict=True):
            expected_file = EXPECTED_RECIPE_BINDINGS.get(name)
            if expected_file and file_path != expected_file:
                findings.append(
                    Finding(
                        "GOOSE-RECIPES.md",
                        f"recipe {name} must bind to {expected_file}, found {file_path}",
                    )
                )

    run_paths = [p.lstrip("./") for p in GOOSE_RUN_PATH_RE.findall(markdown)]
    for run_path in run_paths:
        if run_path not in declared and run_path not in EXPECTED_RECIPE_FILES:
            findings.append(
                Finding(
                    "GOOSE-RECIPES.md",
                    f"goose run path not in declared recipe files: {run_path}",
                )
            )
    missing_runs = [path for path in EXPECTED_RECIPE_FILES if path not in run_paths]
    for path in missing_runs:
        findings.append(
            Finding("GOOSE-RECIPES.md", f"missing goose run example for locked recipe: {path}")
        )

    return findings


def validate_recipe_agent_bindings(root: Path) -> list[Finding]:
    """Ensure recipe text references only the locked specialist agents."""
    recipes_doc = root / "GOOSE-RECIPES.md"
    if not recipes_doc.is_file():
        return [Finding("GOOSE-RECIPES.md", "required documentation file is missing")]

    findings: list[Finding] = []
    markdown = recipes_doc.read_text(encoding="utf-8")
    blocks = extract_fenced_yaml_blocks(markdown)
    allowed = set(DOCUMENTED_AGENTS)

    for index, block in enumerate(blocks, start=1):
        path = f"GOOSE-RECIPES.md#recipe-{index}"
        data, parse_findings = parse_yaml_text(block, path=path)
        findings.extend(parse_findings)
        if not isinstance(data, dict):
            continue
        name = data.get("name")
        recipe = data.get("recipe")
        if not isinstance(name, str) or not isinstance(recipe, dict):
            continue
        blob = "\n".join(
            str(recipe.get(key, "")) for key in ("instructions", "prompt", "title")
        )
        found = agent_tokens(blob)
        invented = sorted(found - allowed)
        if invented:
            findings.append(
                Finding(
                    path,
                    f"invented or unknown agent token(s): {', '.join(invented)}",
                )
            )
        primary = RECIPE_PRIMARY_AGENT.get(name)
        if primary and primary not in found:
            findings.append(
                Finding(path, f"primary agent missing from recipe text: {primary}")
            )
        if name == ORCHESTRATION_RECIPE_NAME:
            missing_all = [agent for agent in DOCUMENTED_AGENTS if agent not in found]
            for agent in missing_all:
                findings.append(
                    Finding(
                        path,
                        f"orchestration recipe missing documented agent: {agent}",
                    )
                )
    return findings


def validate_archive_agent_tokens(root: Path) -> list[Finding]:
    """Refuse invented *Agent tokens across archive docs (historic four only)."""
    findings: list[Finding] = []
    allowed = set(DOCUMENTED_AGENTS)
    for rel in AGENT_TOKEN_SCAN_DOCS:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "required documentation file is missing"))
            continue
        invented = sorted(agent_tokens(path.read_text(encoding="utf-8")) - allowed)
        if invented:
            findings.append(
                Finding(
                    rel,
                    f"invented or unknown agent token(s): {', '.join(invented)}",
                )
            )
    return findings


def validate_cursor_environment(root: Path) -> list[Finding]:
    path = root / ".cursor" / "environment.json"
    rel = ".cursor/environment.json"
    if not path.is_file():
        return [Finding(rel, "missing Cloud Agent environment manifest")]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Finding(rel, f"JSON parse error: {exc}")]
    findings = validate_against_schema(
        data, load_schema("cursor-environment.schema.json"), path=rel
    )
    if not isinstance(data, dict):
        return findings + [Finding(rel, "environment root must be a mapping")]
    name = data.get("name")
    if name != CURSOR_ENVIRONMENT_NAME:
        findings.append(
            Finding(
                rel,
                (
                    f"environment name must be {CURSOR_ENVIRONMENT_NAME!r}, "
                    f"found {name!r}"
                ),
            )
        )
    install = data.get("install")
    if isinstance(install, str):
        for ref in INSTALL_TEST_F_RE.findall(install):
            if not (root / ref).is_file():
                findings.append(
                    Finding(rel, f"install references missing file: {ref}")
                )
        for required_ref in CURSOR_INSTALL_REQUIRED_REFS:
            marker = f"test -f {required_ref}"
            if marker not in install:
                findings.append(
                    Finding(
                        rel,
                        f"install must reference required packaging path: {required_ref}",
                    )
                )
    return findings


def validate_github_agents(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schema = load_schema("github-custom-agent.schema.json")
    agents_dir = root / ".github" / "agents"
    if not agents_dir.is_dir():
        return [Finding(".github/agents", "directory missing")]
    agent_files = sorted(agents_dir.glob("*.agent.md"))
    if not agent_files:
        return [Finding(".github/agents", "no *.agent.md packaging files found")]

    found_rels = {str(path.relative_to(root)) for path in agent_files}
    expected = set(GITHUB_AGENT_FILES)
    for orphan in sorted(found_rels - expected):
        findings.append(Finding(orphan, "unexpected/invented GitHub agent packaging file"))
    for missing in sorted(expected - found_rels):
        findings.append(Finding(missing, "required GitHub agent packaging file missing"))

    for agent_path in agent_files:
        rel = str(agent_path.relative_to(root))
        if rel not in expected:
            continue
        text = agent_path.read_text(encoding="utf-8")
        frontmatter, fm_findings = extract_yaml_frontmatter(text)
        findings.extend(
            Finding(rel, f.message) if f.path == "<frontmatter>" else f for f in fm_findings
        )
        if frontmatter is None:
            continue
        data, parse_findings = parse_yaml_text(frontmatter, path=rel)
        findings.extend(parse_findings)
        if data is None:
            continue
        if not isinstance(data, dict):
            findings.append(Finding(rel, "frontmatter must be a mapping"))
            continue
        findings.extend(validate_against_schema(data, schema, path=rel))
        agent_name = data.get("name")
        if isinstance(agent_name, str) and agent_name.strip() != GITHUB_AGENT_NAME:
            findings.append(
                Finding(
                    rel,
                    (
                        f"GitHub agent name must be {GITHUB_AGENT_NAME!r}, "
                        f"found {agent_name!r}"
                    ),
                )
            )
        agent_description = data.get("description")
        if (
            isinstance(agent_description, str)
            and agent_description.strip() != GITHUB_AGENT_DESCRIPTION
        ):
            findings.append(
                Finding(
                    rel,
                    (
                        "GitHub agent description must be "
                        f"{GITHUB_AGENT_DESCRIPTION!r}, found {agent_description!r}"
                    ),
                )
            )
        elif not isinstance(agent_description, str):
            findings.append(Finding(rel, "GitHub agent description missing or not a string"))
        body = extract_frontmatter_body(text).strip()
        if not body:
            findings.append(Finding(rel, "agent markdown body after frontmatter is empty"))
    return findings


def validate_issue_templates(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schema = load_schema("github-issue-template.schema.json")
    templates_dir = root / ".github" / "ISSUE_TEMPLATE"
    if not templates_dir.is_dir():
        return [Finding(".github/ISSUE_TEMPLATE", "directory missing")]
    templates = sorted(templates_dir.glob("*.md"))
    if not templates:
        return [Finding(".github/ISSUE_TEMPLATE", "no issue template markdown files")]

    found_rels = {str(path.relative_to(root)) for path in templates}
    expected = set(ISSUE_TEMPLATE_FILES)
    for orphan in sorted(found_rels - expected):
        findings.append(Finding(orphan, "unexpected issue template file"))
    for missing in sorted(expected - found_rels):
        findings.append(Finding(missing, "required issue template file missing"))

    for template in templates:
        rel = str(template.relative_to(root))
        if rel not in expected:
            continue
        text = template.read_text(encoding="utf-8")
        frontmatter, fm_findings = extract_yaml_frontmatter(text)
        findings.extend(
            Finding(rel, f.message) if f.path == "<frontmatter>" else f for f in fm_findings
        )
        if frontmatter is None:
            continue
        data, parse_findings = parse_yaml_text(frontmatter, path=rel)
        findings.extend(parse_findings)
        if data is None:
            continue
        if not isinstance(data, dict):
            findings.append(Finding(rel, "frontmatter must be a mapping"))
            continue
        findings.extend(validate_against_schema(data, schema, path=rel))
        body = extract_frontmatter_body(text).strip()
        if not body:
            findings.append(Finding(rel, "issue template body after frontmatter is empty"))
    return findings


def validate_pr_template(root: Path) -> list[Finding]:
    rel = ".github/pull_request_template.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "PR template missing")]
    text = path.read_text(encoding="utf-8")
    headings = PR_HEADING_RE.findall(text)
    # PR template uses "# Summary" then "## ..." — also accept top-level Summary.
    top = text.lstrip().splitlines()[0] if text.strip() else ""
    if top.startswith("# "):
        headings = [top[2:].strip(), *headings]
    findings: list[Finding] = []
    for required in PR_TEMPLATE_HEADINGS:
        if required not in headings:
            findings.append(Finding(rel, f"missing required heading: {required}"))
    return findings


def validate_state_residency(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## State Residency Rules" not in text:
        findings.append(Finding(rel, "missing State Residency Rules section"))
    for phrase in STATE_RESIDENCY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked state-residency phrase: {phrase}")
            )
    return findings


def validate_key_files(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Key Files" not in text:
        findings.append(Finding(rel, "missing Key Files section"))
    for entry in KEY_FILES_REQUIRED_ENTRIES:
        if entry not in text:
            findings.append(
                Finding(rel, f"missing locked key-files entry: {entry}")
            )
    return findings


def validate_pr_routing(root: Path) -> list[Finding]:
    rel = ".github/pull_request_template.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "PR template missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Agent Surface Routing" not in text:
        findings.append(Finding(rel, "missing Agent Surface Routing section"))
    for field in PR_ROUTING_REQUIRED_FIELDS:
        marker = f"| {field} |"
        if marker not in text:
            findings.append(
                Finding(rel, f"missing locked PR routing field: {field}")
            )
    return findings


def validate_routing_matrix(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Agent Routing Matrix" not in text:
        findings.append(Finding(rel, "missing Agent Routing Matrix section"))
    for phrase in ROUTING_MATRIX_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked routing-matrix phrase: {phrase}")
            )
    for surface in ROUTING_SURFACES:
        if surface not in text:
            findings.append(
                Finding(rel, f"missing locked routing surface in matrix: {surface}")
            )
    return findings


def validate_repo_identity(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Repo Identity" not in text:
        findings.append(Finding(rel, "missing Repo Identity section"))
    for phrase in REPO_IDENTITY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked repo-identity phrase: {phrase}")
            )
    return findings


def validate_escalation_format(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Escalation Format" not in text:
        findings.append(Finding(rel, "missing Escalation Format section"))
    for phrase in ESCALATION_BLOCK_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked escalation-format phrase: {phrase}")
            )
    return findings


def validate_routing_rationales(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Agent Routing Matrix" not in text:
        findings.append(Finding(rel, "missing Agent Routing Matrix section"))
    if "Task | Surface | Rationale" not in text:
        findings.append(Finding(rel, "missing routing-matrix column header"))
    for phrase in ROUTING_MATRIX_RATIONALE_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked routing-rationale phrase: {phrase}")
            )
    return findings


def validate_claude_metadata(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in CLAUDE_METADATA_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked claude-metadata phrase: {phrase}")
            )
    return findings


def validate_escalation_usage(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Escalation Format" not in text:
        findings.append(Finding(rel, "missing Escalation Format section"))
    for phrase in ESCALATION_USAGE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked escalation-usage phrase: {phrase}")
            )
    return findings


def validate_security_supported(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Supported Versions" not in text:
        findings.append(Finding(rel, "missing Supported Versions section"))
    for phrase in SECURITY_SUPPORTED_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-supported phrase: {phrase}")
            )
    return findings


def validate_security_reporting(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Reporting a Vulnerability" not in text:
        findings.append(Finding(rel, "missing Reporting a Vulnerability section"))
    for phrase in SECURITY_REPORTING_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-reporting phrase: {phrase}")
            )
    return findings


def validate_security_standards(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Security Standards for This Ecosystem" not in text:
        findings.append(
            Finding(rel, "missing Security Standards for This Ecosystem section")
        )
    for phrase in SECURITY_STANDARDS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-standards phrase: {phrase}")
            )
    return findings


def validate_security_header(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "# Security Policy" not in text:
        findings.append(Finding(rel, "missing Security Policy heading"))
    for phrase in SECURITY_HEADER_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-header phrase: {phrase}")
            )
    return findings


def validate_security_fips(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Security Standards for This Ecosystem" not in text:
        findings.append(
            Finding(rel, "missing Security Standards for This Ecosystem section")
        )
    for phrase in SECURITY_FIPS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-fips phrase: {phrase}")
            )
    return findings


def validate_security_known_non_issues(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Known Non-Issues" not in text:
        findings.append(Finding(rel, "missing Known Non-Issues section"))
    for phrase in SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked security-known-non-issues phrase: {phrase}"
                )
            )
    return findings


def validate_security_scope(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Supported Versions" not in text:
        findings.append(Finding(rel, "missing Supported Versions section"))
    for phrase in SECURITY_SCOPE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked security-scope phrase: {phrase}")
            )
    return findings


def validate_security_reporting_channel(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Reporting a Vulnerability" not in text:
        findings.append(Finding(rel, "missing Reporting a Vulnerability section"))
    for phrase in SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked security-reporting-channel phrase: {phrase}"
                )
            )
    return findings


def validate_security_compliance_detail(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "When code is scaffolded into this repo, it must comply with:" not in text:
        findings.append(Finding(rel, "missing security compliance scaffold preamble"))
    for phrase in SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked security-compliance-detail phrase: {phrase}"
                )
            )
    return findings


def validate_constitution_crypto(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.1 Quantum-Safe Cryptography Requirements" not in text:
        findings.append(
            Finding(rel, "missing Quantum-Safe Cryptography Requirements section")
        )
    for phrase in CONSTITUTION_CRYPTO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked constitution-crypto phrase: {phrase}")
            )
    return findings


def validate_constitution_handoff(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "#### 22.4.1 Handoff Sequence" not in text:
        findings.append(Finding(rel, "missing Handoff Sequence section"))
    for phrase in CONSTITUTION_HANDOFF_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked constitution-handoff phrase: {phrase}")
            )
    return findings


def validate_constitution_escalation_matrix(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "#### 22.4.2 Escalation Triggers" not in text:
        findings.append(Finding(rel, "missing Escalation Triggers section"))
    for phrase in CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-escalation-matrix phrase: {phrase}",
                )
            )
    return findings





def validate_constitution_on_device(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.2 On-Device Quantum Logic Execution" not in text:
        findings.append(
            Finding(rel, "missing On-Device Quantum Logic Execution section")
        )
    for phrase in CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked constitution-on-device phrase: {phrase}")
            )
    return findings


def validate_constitution_multichain(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.3 Multi-Chain State Consistency" not in text:
        findings.append(Finding(rel, "missing Multi-Chain State Consistency section"))
    for phrase in CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked constitution-multichain phrase: {phrase}")
            )
    return findings


def validate_constitution_escalation_format(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "#### 22.4.3 Escalation Format (All Agents)" not in text:
        findings.append(Finding(rel, "missing Escalation Format section"))
    for phrase in CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-escalation-format phrase: {phrase}",
                )
            )
    return findings


def validate_constitution_recipe_orchestration(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.5 Recipe-Based Orchestration Structure" not in text:
        findings.append(
            Finding(rel, "missing Recipe-Based Orchestration Structure section")
        )
    for phrase in CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-recipe-orchestration phrase: {phrase}",
                )
            )
    return findings


def validate_constitution_scratchpad_state(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.6 Scratchpad State Machine" not in text:
        findings.append(Finding(rel, "missing Scratchpad State Machine section"))
    for phrase in CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-scratchpad-state phrase: {phrase}",
                )
            )
    return findings


def validate_constitution_conflict_matrix(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 22.7 Conflict Resolution Matrix" not in text:
        findings.append(Finding(rel, "missing Conflict Resolution Matrix section"))
    for phrase in CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-conflict-matrix phrase: {phrase}",
                )
            )
    return findings


def validate_changelog_format(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CHANGELOG.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "# Changelog" not in body:
        findings.append(Finding(rel, "missing Changelog heading"))
    for phrase in CHANGELOG_FORMAT_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-format phrase: {phrase}")
            )
    return findings


def validate_changelog_unreleased(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CHANGELOG.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## [Unreleased]" not in body:
        findings.append(Finding(rel, "missing Unreleased section"))
    for phrase in CHANGELOG_UNRELEASED_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-unreleased phrase: {phrase}")
            )
    return findings


def validate_changelog_release(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CHANGELOG.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## [0.1.0] — 2025-12-13" not in body:
        findings.append(Finding(rel, "missing 0.1.0 release section"))
    for phrase in CHANGELOG_RELEASE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-release phrase: {phrase}")
            )
    return findings


def validate_implementation_quickstart(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Quick Start (30 minutes)" not in text:
        findings.append(Finding(rel, "missing Quick Start section"))
    for phrase in IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-quickstart phrase: {phrase}")
            )
    return findings


def validate_execution_specialists(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Four Specialist Agents" not in text:
        findings.append(Finding(rel, "missing Your Four Specialist Agents section"))
    for phrase in EXECUTION_SPECIALISTS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-specialists phrase: {phrase}")
            )
    return findings



def validate_hydration_phase1(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PHASE 1: FINDINGS REPORT" not in text:
        findings.append(Finding(rel, "missing PHASE 1 findings report"))
    for phrase in HYDRATION_PHASE1_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-phase1 phrase: {phrase}")
            )
    return findings


def validate_hydration_list_a(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### LIST A — Researchable" not in text:
        findings.append(Finding(rel, "missing LIST A researchable section"))
    for phrase in HYDRATION_LIST_A_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-list-a phrase: {phrase}")
            )
    return findings


def validate_hydration_resolved(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PHASE 3: RESOLVED (LIST A)" not in text:
        findings.append(Finding(rel, "missing PHASE 3 resolved LIST A section"))
    for phrase in HYDRATION_RESOLVED_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-resolved phrase: {phrase}")
            )
    return findings


def validate_hydration_phase4(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PHASE 4: ISSUES GENERATED" not in text:
        findings.append(Finding(rel, "missing PHASE 4 issues generated section"))
    for phrase in HYDRATION_PHASE4_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-phase4 phrase: {phrase}")
            )
    return findings


def validate_hydration_deferred(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## LIST B — Deferred to Andrew" not in text:
        findings.append(Finding(rel, "missing LIST B Deferred to Andrew section"))
    for phrase in HYDRATION_DEFERRED_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-deferred phrase: {phrase}")
            )
    return findings




def validate_hydration_meta(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "# Agent Hydration Report — g0p-agents" not in text:
        findings.append(Finding(rel, "missing hydration report title"))
    for phrase in HYDRATION_META_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-meta phrase: {phrase}")
            )
    return findings


def validate_hydration_identity_detail(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### Identity" not in text:
        findings.append(Finding(rel, "missing Identity findings section"))
    for phrase in HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked hydration-identity-detail phrase: {phrase}"
                )
            )
    return findings



def validate_constitution_ide_stack(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## 23. Quantum-Blockchain Development IDE Setup" not in body:
        findings.append(Finding(rel, "missing IDE Setup section"))
    for phrase in CONSTITUTION_IDE_STACK_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked constitution-ide-stack phrase: {phrase}")
            )
    return findings


def validate_constitution_install_script(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 23.2 Installation Script (WSL2 Ubuntu 22.04)" not in body:
        findings.append(Finding(rel, "missing Installation Script section"))
    for phrase in CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-install-script phrase: {phrase}",
                )
            )
    return findings


def validate_constitution_vscode(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### 23.3 VS Code Extensions (Required)" not in body:
        findings.append(Finding(rel, "missing VS Code Extensions section"))
    for phrase in CONSTITUTION_VSCODE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked constitution-vscode phrase: {phrase}")
            )
    return findings


def validate_constitution_hard_constraints(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## 24. Hard Constraints — Quantum-Blockchain Additions" not in body:
        findings.append(Finding(rel, "missing Hard Constraints section"))
    for phrase in CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-hard-constraints phrase: {phrase}",
                )
            )
    return findings


def validate_constitution_risk_tolerance(root: Path) -> list[Finding]:
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "constitution missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## 25. Quarterly Risk Tolerance Review (Section 12.4.1)" not in body:
        findings.append(Finding(rel, "missing Risk Tolerance Review section"))
    for phrase in CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked constitution-risk-tolerance phrase: {phrase}",
                )
            )
    return findings


def validate_changelog_preamble(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "changelog missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Keep a Changelog" not in body:
        findings.append(Finding(rel, "missing Keep a Changelog preamble"))
    for phrase in CHANGELOG_PREAMBLE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-preamble phrase: {phrase}")
            )
    return findings


def validate_changelog_changed(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "changelog missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### Changed" not in body:
        findings.append(Finding(rel, "missing Changed section"))
    for phrase in CHANGELOG_CHANGED_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-changed phrase: {phrase}")
            )
    return findings



def validate_prompt_expertise(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Expertise" not in body:
        findings.append(Finding(rel, "missing Your Expertise section"))
    for phrase in PROMPT_EXPERTISE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-expertise phrase: {phrase}")
            )
    return findings


def validate_prompt_principles(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Decision Making Principles" not in body:
        findings.append(Finding(rel, "missing Decision Making Principles section"))
    for phrase in PROMPT_PRINCIPLES_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-principles phrase: {phrase}")
            )
    return findings


def validate_prompt_metrics(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Success Metrics" not in body:
        findings.append(Finding(rel, "missing Success Metrics section"))
    for phrase in PROMPT_METRICS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-metrics phrase: {phrase}")
            )
    return findings


def validate_prompt_tools(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Tools" not in body:
        findings.append(Finding(rel, "missing Your Tools section"))
    for phrase in PROMPT_TOOLS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-tools phrase: {phrase}")
            )
    return findings


def validate_prompt_communication(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Communication Style" not in body:
        findings.append(Finding(rel, "missing Your Communication Style section"))
    for phrase in PROMPT_COMMUNICATION_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-communication phrase: {phrase}"
                )
            )
    return findings


def validate_prompt_escalation_identity(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "🚨 ESCALATION REQUIRED" not in body:
        findings.append(Finding(rel, "missing ESCALATION REQUIRED identity banner"))
    for phrase in PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked prompt-escalation-identity phrase: {phrase}",
                )
            )
    return findings



def validate_prompt_orchestration_matrix(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Conflict Resolution Matrix" not in body:
        findings.append(Finding(rel, "missing Conflict Resolution Matrix section"))
    for phrase in PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked prompt-orchestration-matrix phrase: {phrase}",
                )
            )
    return findings


def validate_prompt_monthly(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Monthly Checklist" not in body:
        findings.append(Finding(rel, "missing Your Monthly Checklist section"))
    for phrase in PROMPT_MONTHLY_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-monthly phrase: {phrase}")
            )
    return findings


def validate_prompt_usage_example(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### Example: Instantiate QuantumArchitectAgent" not in body:
        findings.append(
            Finding(rel, "missing Example Instantiate QuantumArchitectAgent section")
        )
    for phrase in PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-usage-example phrase: {phrase}"
                )
            )
    return findings



def validate_prompt_context(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Current Project Context" not in body:
        findings.append(Finding(rel, "missing Current Project Context section"))
    for phrase in PROMPT_CONTEXT_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked prompt-context phrase: {phrase}")
            )
    return findings


def validate_prompt_decision_authority(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Decision Authority" not in body:
        findings.append(Finding(rel, "missing Your Decision Authority section"))
    for phrase in PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-decision-authority phrase: {phrase}"
                )
            )
    return findings


def validate_prompt_escalation_authority(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Escalation Authority" not in body:
        findings.append(Finding(rel, "missing Your Escalation Authority section"))
    for phrase in PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel,
                    f"missing locked prompt-escalation-authority phrase: {phrase}",
                )
            )
    return findings



def validate_prompt_responsibilities(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Core Responsibilities" not in body:
        findings.append(Finding(rel, "missing Core Responsibilities section"))
    for phrase in PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-responsibilities phrase: {phrase}"
                )
            )
    return findings


def validate_prompt_cannot_delegate(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Key Responsibilities You CANNOT Delegate" not in body:
        findings.append(
            Finding(rel, "missing Key Responsibilities You CANNOT Delegate section")
        )
    for phrase in PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-cannot-delegate phrase: {phrase}"
                )
            )
    return findings


def validate_prompt_human_escalation(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "prompts missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## When You Escalate to Human" not in body:
        findings.append(Finding(rel, "missing When You Escalate to Human section"))
    for phrase in PROMPT_HUMAN_ESCALATION_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked prompt-human-escalation phrase: {phrase}"
                )
            )
    return findings


def validate_changelog_initial(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "changelog missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## [0.1.0]" not in body:
        findings.append(Finding(rel, "missing 0.1.0 initial release section"))
    for phrase in CHANGELOG_INITIAL_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked changelog-initial phrase: {phrase}")
            )
    return findings


def validate_hydration_git_detail(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### Git State" not in text:
        findings.append(Finding(rel, "missing Git State findings section"))
    for phrase in HYDRATION_GIT_DETAIL_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-git-detail phrase: {phrase}")
            )
    return findings


def validate_hydration_phase2(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PHASE 2: QUESTIONS" not in text:
        findings.append(Finding(rel, "missing PHASE 2 questions section"))
    for phrase in HYDRATION_PHASE2_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-phase2 phrase: {phrase}")
            )
    return findings


def validate_hydration_phase5(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PHASE 5: Roadmap" not in text:
        findings.append(Finding(rel, "missing PHASE 5 Roadmap section"))
    for phrase in HYDRATION_PHASE5_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-phase5 phrase: {phrase}")
            )
    return findings


def validate_hydration_list_b(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "### LIST B — Requires Andrew (HITL)" not in text:
        findings.append(Finding(rel, "missing LIST B HITL section"))
    for phrase in HYDRATION_LIST_B_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked hydration-list-b phrase: {phrase}")
            )
    return findings


def validate_dependabot(root: Path) -> list[Finding]:
    rel = ".github/dependabot.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "required YAML config missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    if parse_findings:
        return parse_findings
    if data is None:
        return [Finding(rel, "Dependabot config is empty")]
    findings = validate_against_schema(
        data, load_schema("dependabot-v2.schema.json"), path=rel
    )
    if findings:
        return findings
    if not isinstance(data, dict):
        return [Finding(rel, "Dependabot root must be a mapping")]
    updates = data.get("updates")
    if not isinstance(updates, list):
        return findings + [Finding(rel, "Dependabot updates must be a list")]
    ecosystems = {
        item.get("package-ecosystem")
        for item in updates
        if isinstance(item, dict)
    }
    if ecosystems != DEPENDABOT_ECOSYSTEMS:
        findings.append(
            Finding(
                rel,
                (
                    "Dependabot package-ecosystem set must equal "
                    f"{sorted(DEPENDABOT_ECOSYSTEMS)}, found {sorted(ecosystems)}"
                ),
            )
        )
    for required in sorted(DEPENDABOT_ECOSYSTEMS):
        if required not in ecosystems:
            findings.append(
                Finding(rel, f"missing required package-ecosystem: {required}")
            )
    found_groups: set[str] = set()
    for item in updates:
        if not isinstance(item, dict):
            continue
        directory = item.get("directory")
        if directory not in DEPENDABOT_DIRECTORIES:
            findings.append(
                Finding(
                    rel,
                    f"Dependabot directory must be one of {sorted(DEPENDABOT_DIRECTORIES)}, "
                    f"found {directory!r}",
                )
            )
        schedule = item.get("schedule")
        if isinstance(schedule, dict):
            interval = schedule.get("interval")
            if interval != DEPENDABOT_SCHEDULE_INTERVAL:
                findings.append(
                    Finding(
                        rel,
                        (
                            f"Dependabot schedule.interval must be "
                            f"{DEPENDABOT_SCHEDULE_INTERVAL!r}, found {interval!r}"
                        ),
                    )
                )
        groups = item.get("groups")
        if isinstance(groups, dict):
            found_groups.update(str(name) for name in groups)
        elif groups is not None:
            findings.append(Finding(rel, "Dependabot groups must be a mapping"))
    missing_groups = sorted(DEPENDABOT_GROUP_NAMES - found_groups)
    for group_name in missing_groups:
        findings.append(
            Finding(rel, f"missing required Dependabot group: {group_name}")
        )
    return findings


def validate_markdownlint(root: Path) -> list[Finding]:
    rel = ".markdownlint.yaml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "required YAML config missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    if parse_findings:
        return parse_findings
    if data is None:
        return [Finding(rel, "markdownlint config is empty")]
    findings = validate_against_schema(
        data, load_schema("markdownlint.schema.json"), path=rel
    )
    if isinstance(data, dict):
        default = data.get("default")
        if default is not MARKDOWNLINT_DEFAULT:
            findings.append(
                Finding(
                    rel,
                    (
                        f"markdownlint default must be {MARKDOWNLINT_DEFAULT!r}, "
                        f"found {default!r}"
                    ),
                )
            )
        md013 = data.get("MD013")
        if not isinstance(md013, dict):
            findings.append(Finding(rel, "markdownlint MD013 must be a mapping"))
        else:
            line_length = md013.get("line_length")
            if line_length != MARKDOWNLINT_MD013_LINE_LENGTH:
                findings.append(
                    Finding(
                        rel,
                        (
                            "markdownlint MD013.line_length must be "
                            f"{MARKDOWNLINT_MD013_LINE_LENGTH!r}, found {line_length!r}"
                        ),
                    )
                )
            tables = md013.get("tables")
            if tables is not MARKDOWNLINT_MD013_TABLES:
                findings.append(
                    Finding(
                        rel,
                        (
                            "markdownlint MD013.tables must be "
                            f"{MARKDOWNLINT_MD013_TABLES!r}, found {tables!r}"
                        ),
                    )
                )
            code_blocks = md013.get("code_blocks")
            if code_blocks is not MARKDOWNLINT_MD013_CODE_BLOCKS:
                findings.append(
                    Finding(
                        rel,
                        (
                            "markdownlint MD013.code_blocks must be "
                            f"{MARKDOWNLINT_MD013_CODE_BLOCKS!r}, found {code_blocks!r}"
                        ),
                    )
                )
        md025 = data.get("MD025")
        if md025 is not MARKDOWNLINT_MD025:
            findings.append(
                Finding(
                    rel,
                    (
                        f"markdownlint MD025 must be {MARKDOWNLINT_MD025!r}, "
                        f"found {md025!r}"
                    ),
                )
            )
        md033 = data.get("MD033")
        if md033 is not MARKDOWNLINT_MD033:
            findings.append(
                Finding(
                    rel,
                    (
                        f"markdownlint MD033 must be {MARKDOWNLINT_MD033!r}, "
                        f"found {md033!r}"
                    ),
                )
            )
        md024 = data.get("MD024")
        if not isinstance(md024, dict):
            findings.append(Finding(rel, "markdownlint MD024 must be a mapping"))
        else:
            siblings_only = md024.get("siblings_only")
            if siblings_only is not MARKDOWNLINT_MD024_SIBLINGS_ONLY:
                findings.append(
                    Finding(
                        rel,
                        (
                            "markdownlint MD024.siblings_only must be "
                            f"{MARKDOWNLINT_MD024_SIBLINGS_ONLY!r}, "
                            f"found {siblings_only!r}"
                        ),
                    )
                )
    return findings


def validate_requirements_dev(root: Path) -> list[Finding]:
    rel = "requirements-dev.txt"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "requirements-dev.txt missing")]
    packages: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = REQUIREMENTS_PKG_RE.match(stripped)
        if match:
            packages.add(match.group(1))
    findings: list[Finding] = []
    missing = sorted(REQUIRED_DEV_PACKAGES - packages)
    for name in missing:
        findings.append(Finding(rel, f"missing required dev package: {name}"))
    return findings


def validate_license(root: Path) -> list[Finding]:
    rel = "LICENSE"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "LICENSE missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "MIT License" not in text and "Permission is hereby granted" not in text:
        findings.append(Finding(rel, "LICENSE does not look like MIT text"))
    if "2026" not in text:
        findings.append(Finding(rel, "LICENSE missing expected copyright year 2026"))
    if LICENSE_COPYRIGHT_HOLDER not in text:
        findings.append(
            Finding(
                rel,
                f"LICENSE missing expected copyright holder {LICENSE_COPYRIGHT_HOLDER!r}",
            )
        )
    if LICENSE_COPYRIGHT_MARKER not in text:
        findings.append(
            Finding(
                rel,
                f"LICENSE missing copyright marker: {LICENSE_COPYRIGHT_MARKER}",
            )
        )
    return findings


def validate_readme_packaging(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in README_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"README missing packaging phrase: {phrase}"))
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(Finding(rel, f"README missing documented agent: {agent}"))
    return findings


def validate_scratchpad(root: Path) -> list[Finding]:
    rel = "agentic_flows/scratchpad.txt"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "scratchpad coordination file missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if not text.strip():
        findings.append(Finding(rel, "scratchpad is empty"))
        return findings
    if "scratchpad" not in text.lower():
        findings.append(Finding(rel, "scratchpad missing identifying header text"))
    if not CHECKBOX_RE.search(text):
        findings.append(Finding(rel, "scratchpad missing coordination checkbox markers"))
    for phrase in SCRATCHPAD_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"scratchpad missing required phrase: {phrase}"))
    for marker in SCRATCHPAD_STATUS_MARKERS:
        if marker not in text:
            findings.append(Finding(rel, f"scratchpad missing status marker: {marker}"))
    return findings


def validate_pyproject(root: Path) -> list[Finding]:
    rel = "pyproject.toml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "pyproject.toml missing")]
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return [Finding(rel, f"TOML parse error: {exc}")]

    findings: list[Finding] = []
    project = data.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if name != PYPROJECT_NAME:
            findings.append(
                Finding(
                    rel,
                    f"project.name must be {PYPROJECT_NAME!r}, found {name!r}",
                )
            )
        version = project.get("version")
        if version != PYPROJECT_VERSION:
            findings.append(
                Finding(
                    rel,
                    f"project.version must be {PYPROJECT_VERSION!r}, found {version!r}",
                )
            )
        license_field = project.get("license")
        license_text = (
            license_field.get("text") if isinstance(license_field, dict) else None
        )
        if license_text != PYPROJECT_LICENSE_TEXT:
            findings.append(
                Finding(
                    rel,
                    (
                        "project.license.text must be "
                        f"{PYPROJECT_LICENSE_TEXT!r}, found {license_text!r}"
                    ),
                )
            )
        description = project.get("description")
        if description != PYPROJECT_DESCRIPTION:
            findings.append(
                Finding(
                    rel,
                    (
                        "project.description must be "
                        f"{PYPROJECT_DESCRIPTION!r}, found {description!r}"
                    ),
                )
            )
        readme = project.get("readme")
        if readme != PYPROJECT_README:
            findings.append(
                Finding(
                    rel,
                    f"project.readme must be {PYPROJECT_README!r}, found {readme!r}",
                )
            )
        requires = project.get("requires-python")
        if requires != PYPROJECT_REQUIRES_PYTHON:
            findings.append(
                Finding(
                    rel,
                    (
                        f"requires-python must be {PYPROJECT_REQUIRES_PYTHON!r}, "
                        f"found {requires!r}"
                    ),
                )
            )
    else:
        findings.append(Finding(rel, "pyproject.toml missing [project] table"))

    tool = data.get("tool")
    if not isinstance(tool, dict):
        return findings + [Finding(rel, "pyproject.toml missing [tool] table")]

    pytest_opts = tool.get("pytest", {})
    if not isinstance(pytest_opts, dict) or "ini_options" not in pytest_opts:
        findings.append(Finding(rel, "missing [tool.pytest.ini_options]"))
    else:
        ini_options = pytest_opts.get("ini_options")
        if isinstance(ini_options, dict):
            addopts = ini_options.get("addopts")
            if addopts != PYTEST_ADDOPTS:
                findings.append(
                    Finding(
                        rel,
                        (
                            f"pytest addopts must be {PYTEST_ADDOPTS!r}, "
                            f"found {addopts!r}"
                        ),
                    )
                )
            testpaths = ini_options.get("testpaths")
            if (
                not isinstance(testpaths, list)
                or tuple(testpaths) != PYTEST_TESTPATHS
            ):
                findings.append(
                    Finding(
                        rel,
                        (
                            "pytest testpaths must equal "
                            f"{list(PYTEST_TESTPATHS)!r}, found {testpaths!r}"
                        ),
                    )
                )
            pythonpath = ini_options.get("pythonpath")
            if (
                not isinstance(pythonpath, list)
                or tuple(pythonpath) != PYTEST_PYTHONPATH
            ):
                findings.append(
                    Finding(
                        rel,
                        (
                            "pytest pythonpath must equal "
                            f"{list(PYTEST_PYTHONPATH)!r}, found {pythonpath!r}"
                        ),
                    )
                )
        else:
            findings.append(Finding(rel, "pytest.ini_options must be a mapping"))

    ruff = tool.get("ruff")
    if not isinstance(ruff, dict):
        findings.append(Finding(rel, "missing [tool.ruff]"))
    else:
        target = ruff.get("target-version")
        if target != PYPROJECT_RUFF_TARGET_VERSION:
            findings.append(
                Finding(
                    rel,
                    (
                        "ruff target-version must be "
                        f"{PYPROJECT_RUFF_TARGET_VERSION!r}, found {target!r}"
                    ),
                )
            )
        line_length = ruff.get("line-length")
        if line_length != PYPROJECT_LINE_LENGTH:
            findings.append(
                Finding(
                    rel,
                    (
                        "ruff line-length must be "
                        f"{PYPROJECT_LINE_LENGTH!r}, found {line_length!r}"
                    ),
                )
            )
        src = ruff.get("src")
        if not isinstance(src, list) or tuple(src) != PYPROJECT_RUFF_SRC:
            findings.append(
                Finding(
                    rel,
                    f"ruff src must equal {list(PYPROJECT_RUFF_SRC)!r}, found {src!r}",
                )
            )
        lint = ruff.get("lint")
        if isinstance(lint, dict):
            select = lint.get("select")
            if not isinstance(select, list) or tuple(select) != PYPROJECT_RUFF_LINT_SELECT:
                findings.append(
                    Finding(
                        rel,
                        (
                            "ruff lint.select must equal "
                            f"{list(PYPROJECT_RUFF_LINT_SELECT)!r}, found {select!r}"
                        ),
                    )
                )
        else:
            findings.append(Finding(rel, "missing [tool.ruff.lint]"))

    coverage = tool.get("coverage")
    if not isinstance(coverage, dict):
        findings.append(Finding(rel, "missing [tool.coverage]"))
        return findings

    run = coverage.get("run")
    if isinstance(run, dict):
        branch = run.get("branch")
        if branch is not COVERAGE_BRANCH:
            findings.append(
                Finding(
                    rel,
                    f"coverage run.branch must be {COVERAGE_BRANCH}, found {branch!r}",
                )
            )
        source = run.get("source")
        if not isinstance(source, list) or tuple(source) != COVERAGE_SOURCE:
            findings.append(
                Finding(
                    rel,
                    (
                        "coverage run.source must equal "
                        f"{list(COVERAGE_SOURCE)!r}, found {source!r}"
                    ),
                )
            )
    else:
        findings.append(Finding(rel, "missing [tool.coverage.run]"))

    report = coverage.get("report")
    if not isinstance(report, dict) or "fail_under" not in report:
        findings.append(Finding(rel, "missing [tool.coverage.report].fail_under"))
        return findings

    show_missing = report.get("show_missing")
    if show_missing is not COVERAGE_SHOW_MISSING:
        findings.append(
            Finding(
                rel,
                (
                    "coverage report.show_missing must be "
                    f"{COVERAGE_SHOW_MISSING}, found {show_missing!r}"
                ),
            )
        )
    skip_empty = report.get("skip_empty")
    if skip_empty is not COVERAGE_SKIP_EMPTY:
        findings.append(
            Finding(
                rel,
                (
                    "coverage report.skip_empty must be "
                    f"{COVERAGE_SKIP_EMPTY}, found {skip_empty!r}"
                ),
            )
        )

    fail_under = report.get("fail_under")
    if not isinstance(fail_under, (int, float)) or fail_under != MIN_COVERAGE_FAIL_UNDER:
        findings.append(
            Finding(
                rel,
                (
                    "coverage fail_under must be "
                    f"{MIN_COVERAGE_FAIL_UNDER}, found {fail_under!r}"
                ),
            )
        )
    return findings


def validate_yaml_configs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in KNOWN_YAML_CONFIGS:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(str(rel), "required YAML config missing"))
            continue
        data, parse_findings = parse_yaml_text(
            path.read_text(encoding="utf-8"), path=str(rel)
        )
        findings.extend(parse_findings)
        if data is None:
            continue
        if not isinstance(data, (dict, list)):
            findings.append(Finding(str(rel), "YAML root must be a mapping or sequence"))
    return findings


def validate_ci_workflow(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]

    # PyYAML parses bare `on:` as boolean True.
    on_trigger = data.get(True, data.get("on"))
    if on_trigger is None:
        findings.append(Finding(rel, "CI workflow missing on: trigger mapping"))
    elif isinstance(on_trigger, dict):
        pull_request = on_trigger.get("pull_request")
        if isinstance(pull_request, dict):
            branches = pull_request.get("branches")
            if not isinstance(branches, list) or CI_PULL_REQUEST_BRANCH not in [
                str(b) for b in branches
            ]:
                findings.append(
                    Finding(
                        rel,
                        (
                            f"CI pull_request.branches must include "
                            f"{CI_PULL_REQUEST_BRANCH!r}"
                        ),
                    )
                )
        else:
            findings.append(Finding(rel, "CI workflow missing pull_request trigger"))

    concurrency = data.get("concurrency")
    if not isinstance(concurrency, dict) or "group" not in concurrency:
        findings.append(Finding(rel, "CI workflow must define concurrency.group"))
    else:
        group = concurrency.get("group")
        if not isinstance(group, str) or not group.startswith(CI_CONCURRENCY_GROUP_PREFIX):
            findings.append(
                Finding(
                    rel,
                    (
                        "CI concurrency.group must start with "
                        f"{CI_CONCURRENCY_GROUP_PREFIX!r}, found {group!r}"
                    ),
                )
            )
        if concurrency.get("cancel-in-progress") is not CI_CANCEL_IN_PROGRESS:
            findings.append(
                Finding(
                    rel,
                    (
                        "CI workflow concurrency.cancel-in-progress must be "
                        f"{CI_CANCEL_IN_PROGRESS}"
                    ),
                )
            )

    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow must define jobs mapping")]
    missing = sorted(REQUIRED_CI_JOBS - set(jobs))
    if missing:
        findings.append(Finding(rel, f"missing required CI job(s): {', '.join(missing)}"))
    orphans = sorted(set(jobs) - REQUIRED_CI_JOBS)
    for orphan in orphans:
        findings.append(Finding(rel, f"unexpected/orphan CI job: {orphan}"))

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        permissions = job.get("permissions")
        if not isinstance(permissions, dict):
            findings.append(
                Finding(rel, f"CI job {job_name} must define permissions mapping")
            )
            continue
        contents = permissions.get("contents")
        if contents != CI_PERMISSIONS_CONTENTS:
            findings.append(
                Finding(
                    rel,
                    (
                        f"CI job {job_name} permissions.contents must be "
                        f"{CI_PERMISSIONS_CONTENTS!r}, found {contents!r}"
                    ),
                )
            )

    manifest = jobs.get("manifest-validate")
    if isinstance(manifest, dict):
        steps = manifest.get("steps")
        step_blob = json.dumps(steps) if steps is not None else ""
        for marker in REQUIRED_MANIFEST_STEP_MARKERS:
            if marker not in step_blob:
                findings.append(
                    Finding(
                        rel,
                        f"manifest-validate job must include step marker: {marker}",
                    )
                )
        if "upload-artifact" not in step_blob:
            findings.append(
                Finding(rel, "manifest-validate job must upload validation artifacts")
            )
        if CI_ARTIFACT_NAME_PREFIX not in step_blob:
            findings.append(
                Finding(
                    rel,
                    (
                        "manifest-validate artifact name must include "
                        f"{CI_ARTIFACT_NAME_PREFIX!r}"
                    ),
                )
            )
        if isinstance(steps, list):
            upload_if: str | None = None
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if "upload-artifact" in uses:
                    upload_if = str(step.get("if", ""))
                    break
            if upload_if != CI_ARTIFACT_UPLOAD_IF:
                findings.append(
                    Finding(
                        rel,
                        (
                            "manifest-validate upload-artifact if must be "
                            f"{CI_ARTIFACT_UPLOAD_IF!r}, found {upload_if!r}"
                        ),
                    )
                )
        strategy = manifest.get("strategy")
        if not isinstance(strategy, dict) or "matrix" not in strategy:
            findings.append(
                Finding(rel, "manifest-validate job must define a Python version matrix")
            )
        else:
            if strategy.get("fail-fast") is not CI_FAIL_FAST:
                findings.append(
                    Finding(
                        rel,
                        (
                            "manifest-validate strategy.fail-fast must be "
                            f"{CI_FAIL_FAST}"
                        ),
                    )
                )
            matrix = strategy.get("matrix")
            versions = matrix.get("python-version") if isinstance(matrix, dict) else None
            if not isinstance(versions, list) or len(versions) < 2:
                findings.append(
                    Finding(
                        rel,
                        "manifest-validate matrix.python-version must list at least 2 versions",
                    )
                )
            elif tuple(str(v) for v in versions) != REQUIRED_PYTHON_VERSIONS:
                findings.append(
                    Finding(
                        rel,
                        (
                            "manifest-validate matrix.python-version must equal "
                            f"{list(REQUIRED_PYTHON_VERSIONS)}, found {versions!r}"
                        ),
                    )
                )
    return findings


def validate_documented_agent_prompts(root: Path) -> list[Finding]:
    path = root / "AGENT-PROMPTS.md"
    if not path.is_file():
        return [Finding("AGENT-PROMPTS.md", "required documentation file is missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(
                Finding("AGENT-PROMPTS.md", f"documented agent missing from prompts: {agent}")
            )
    headings = PROMPT_HEADING_RE.findall(text)
    if len(headings) != len(DOCUMENTED_AGENTS):
        findings.append(
            Finding(
                "AGENT-PROMPTS.md",
                f"expected {len(DOCUMENTED_AGENTS)} agent prompt headings, found {len(headings)}",
            )
        )
    heading_set = set(headings)
    invented = sorted(heading_set - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(
                "AGENT-PROMPTS.md",
                f"invented agent prompt heading(s): {', '.join(invented)}",
            )
        )
    missing_headings = [a for a in DOCUMENTED_AGENTS if a not in heading_set]
    for agent in missing_headings:
        findings.append(
            Finding("AGENT-PROMPTS.md", f"missing prompt template heading for: {agent}")
        )
    fences = extract_fenced_markdown_blocks(text)
    if len(fences) != len(DOCUMENTED_AGENTS):
        findings.append(
            Finding(
                "AGENT-PROMPTS.md",
                (
                    f"expected {len(DOCUMENTED_AGENTS)} markdown prompt fences, "
                    f"found {len(fences)}"
                ),
            )
        )
    else:
        for agent, fence in zip(DOCUMENTED_AGENTS, fences, strict=True):
            expected_header = f"# {agent}{PROMPT_SYSTEM_HEADER_SUFFIX}"
            first_line = next(
                (line.strip() for line in fence.splitlines() if line.strip()),
                "",
            )
            if first_line != expected_header:
                findings.append(
                    Finding(
                        "AGENT-PROMPTS.md",
                        (
                            f"prompt fence for {agent} must start with "
                            f"{expected_header!r}, found {first_line!r}"
                        ),
                    )
                )
            if agent in SPECIALIST_AGENTS:
                if SPECIALIST_ESCALATION_MARKER not in fence:
                    findings.append(
                        Finding(
                            "AGENT-PROMPTS.md",
                            f"{agent} prompt missing {SPECIALIST_ESCALATION_MARKER!r}",
                        )
                    )
                from_line = f"From Agent: {agent}"
                if from_line not in fence:
                    findings.append(
                        Finding(
                            "AGENT-PROMPTS.md",
                            f"{agent} prompt missing escalation identity {from_line!r}",
                        )
                    )
            elif agent == "OrchestrationAgent":
                if ORCHESTRATION_ESCALATION_MARKER not in fence:
                    findings.append(
                        Finding(
                            "AGENT-PROMPTS.md",
                            (
                                f"{agent} prompt missing "
                                f"{ORCHESTRATION_ESCALATION_MARKER!r}"
                            ),
                        )
                    )
    return findings


def validate_cross_doc_agents(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_ARCHIVE_DOCS:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "required documentation file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for agent in DOCUMENTED_AGENTS:
            if agent not in text:
                findings.append(
                    Finding(rel, f"documented agent missing from archive doc: {agent}")
                )
    return findings



def validate_constitution_agent_headings(root: Path) -> list[Finding]:
    """Require AGENTS-v2.2.md section headings for each documented specialist."""
    rel = "AGENTS-v2.2.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "required documentation file is missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for agent in DOCUMENTED_AGENTS:
        marker = f"{CONSTITUTION_HEADING_PREFIX}{agent}:"
        if marker not in text:
            findings.append(
                Finding(rel, f"missing constitution heading for documented agent: {agent}")
            )
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_routing_surfaces(root: Path) -> list[Finding]:
    """Lock CLAUDE.md packaging surfaces (not specialist agents)."""
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "required documentation file is missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for section in CLAUDE_REQUIRED_SECTIONS:
        if section not in text:
            findings.append(Finding(rel, f"missing required CLAUDE.md section: {section}"))
    for surface in ROUTING_SURFACES:
        if surface not in text:
            findings.append(Finding(rel, f"missing locked routing surface: {surface}"))
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(
                Finding(rel, f"documented agent missing from routing/doc identity: {agent}")
            )
    return findings


def validate_security_packaging(root: Path) -> list[Finding]:
    rel = "SECURITY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "SECURITY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in SECURITY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"SECURITY.md missing packaging phrase: {phrase}"))
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_contributing_packaging(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in CONTRIBUTING_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"CONTRIBUTING.md missing packaging phrase: {phrase}")
            )
    for surface in CONTRIBUTING_BRANCH_SURFACES:
        if surface not in text:
            findings.append(Finding(rel, f"CONTRIBUTING.md missing branch surface: {surface}"))
    return findings


def validate_contributing_who(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in CONTRIBUTING_WHO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-who phrase: {phrase}")
            )
    return findings


def validate_contributing_branches(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Branch Strategy" not in text:
        findings.append(Finding(rel, "missing Branch Strategy section"))
    for phrase in CONTRIBUTING_BRANCH_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-branches phrase: {phrase}")
            )
    return findings


def validate_contributing_pr(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## PR Requirements" not in text:
        findings.append(Finding(rel, "missing PR Requirements section"))
    if "## Governance" not in text:
        findings.append(Finding(rel, "missing Governance section"))
    for phrase in CONTRIBUTING_PR_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-pr phrase: {phrase}")
            )
    return findings


def validate_contributing_issues(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Issue Reporting" not in text:
        findings.append(Finding(rel, "missing Issue Reporting section"))
    for phrase in CONTRIBUTING_ISSUES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-issues phrase: {phrase}")
            )
    return findings


def validate_contributing_local(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Local validation (docs packaging)" not in text:
        findings.append(Finding(rel, "missing Local validation section"))
    for phrase in CONTRIBUTING_LOCAL_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-local phrase: {phrase}")
            )
    return findings


def validate_contributing_governance(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Governance" not in text:
        findings.append(Finding(rel, "missing Governance section"))
    for phrase in CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked contributing-governance phrase: {phrase}"
                )
            )
    return findings


def validate_contributing_metadata(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "# Contributing to g0p-agents" not in text:
        findings.append(Finding(rel, "missing Contributing title"))
    for phrase in CONTRIBUTING_METADATA_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-metadata phrase: {phrase}")
            )
    return findings


def validate_contributing_surfaces(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Agent surfaces" not in text:
        findings.append(Finding(rel, "missing Agent surfaces duty list"))
    for phrase in CONTRIBUTING_SURFACES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked contributing-surfaces phrase: {phrase}")
            )
    return findings


def validate_contributing_ci_honesty(root: Path) -> list[Finding]:
    rel = "CONTRIBUTING.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CONTRIBUTING.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Packaging inventory v50" not in text:
        findings.append(Finding(rel, "missing Packaging inventory v50 honesty lock"))
    for phrase in CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked contributing-ci-honesty phrase: {phrase}"
                )
            )
    return findings


def validate_pr_summary(root: Path) -> list[Finding]:
    rel = ".github/pull_request_template.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "PR template missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in PR_SUMMARY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked pr-summary phrase: {phrase}")
            )
    return findings


def validate_pr_acceptance(root: Path) -> list[Finding]:
    rel = ".github/pull_request_template.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "PR template missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Acceptance Criteria" not in text:
        findings.append(Finding(rel, "missing Acceptance Criteria section"))
    for phrase in PR_ACCEPTANCE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked pr-acceptance phrase: {phrase}")
            )
    return findings


def validate_pr_notes(root: Path) -> list[Finding]:
    rel = ".github/pull_request_template.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "PR template missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Notes for Reviewer" not in text:
        findings.append(Finding(rel, "missing Notes for Reviewer section"))
    for phrase in PR_NOTES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked pr-notes phrase: {phrase}")
            )
    return findings


def validate_readme_honesty(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in README_HONESTY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-honesty phrase: {phrase}")
            )
    return findings


def validate_readme_historic(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Historic prompt set" not in text:
        findings.append(Finding(rel, "missing Historic prompt set section"))
    for phrase in README_HISTORIC_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-historic phrase: {phrase}")
            )
    return findings


def validate_readme_contents(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Contents" not in text:
        findings.append(Finding(rel, "missing Contents section"))
    if "## Manifest validation" not in text:
        findings.append(Finding(rel, "missing Manifest validation section"))
    for phrase in README_CONTENTS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-contents phrase: {phrase}")
            )
    return findings




def validate_readme_lead(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if 'Docs-only archive of 2025 "Quantum-Blockchain" agent prompts' not in text:
        findings.append(Finding(rel, "missing Docs-only archive lead"))
    for phrase in README_LEAD_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-lead phrase: {phrase}")
            )
    return findings


def validate_readme_blurbs(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Contents" not in text:
        findings.append(Finding(rel, "missing Contents section"))
    for phrase in README_BLURBS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-blurbs phrase: {phrase}")
            )
    return findings


def validate_readme_bootstrap(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Cloud agents" not in text:
        findings.append(Finding(rel, "missing Cloud agents section"))
    if "## Manifest validation" not in text:
        findings.append(Finding(rel, "missing Manifest validation section"))
    if "## License" not in text:
        findings.append(Finding(rel, "missing License section"))
    for phrase in README_BOOTSTRAP_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked readme-bootstrap phrase: {phrase}")
            )
    return findings


def validate_goose_howto(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in GOOSE_HOWTO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked goose-howto phrase: {phrase}")
            )
    return findings


def validate_goose_state_machine(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Scratchpad State Machine" not in text:
        findings.append(Finding(rel, "missing Scratchpad State Machine section"))
    for phrase in GOOSE_STATE_MACHINE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked goose-state-machine phrase: {phrase}")
            )
    return findings


def validate_goose_naming(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Recipe Naming Convention" not in text:
        findings.append(Finding(rel, "missing Recipe Naming Convention section"))
    if "## Adding New Recipes" not in text:
        findings.append(Finding(rel, "missing Adding New Recipes section"))
    for phrase in GOOSE_NAMING_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked goose-naming phrase: {phrase}")
            )
    return findings


def validate_goose_recipe_headers(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Recipe 1: Quantum Algorithm Design" not in body:
        findings.append(Finding(rel, "missing Recipe 1 heading"))
    if "## Recipe 4: Multi-Agent Orchestration (Master Recipe)" not in body:
        findings.append(Finding(rel, "missing Recipe 4 heading"))
    for phrase in GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked goose-recipe-headers phrase: {phrase}")
            )
    return findings


def validate_goose_instruction_agents(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "You are QuantumArchitectAgent" not in body:
        findings.append(Finding(rel, "missing QuantumArchitectAgent instruction"))
    for phrase in GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(
                    rel, f"missing locked goose-instruction-agents phrase: {phrase}"
                )
            )
    return findings


def validate_goose_extensions(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "type: builtin" not in body:
        findings.append(Finding(rel, "missing builtin extension type"))
    for phrase in GOOSE_EXTENSIONS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked goose-extensions phrase: {phrase}")
            )
    return findings


def validate_goose_orchestration(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Master Orchestration Task: Quantum NFT Mint" not in body:
        findings.append(Finding(rel, "missing Master Orchestration Task section"))
    for phrase in GOOSE_ORCHESTRATION_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked goose-orchestration phrase: {phrase}")
            )
    return findings


def validate_goose_conflicts(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Conflict Type 1: PERFORMANCE" not in body:
        findings.append(Finding(rel, "missing Conflict Type PERFORMANCE section"))
    for phrase in GOOSE_CONFLICTS_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked goose-conflicts phrase: {phrase}")
            )
    return findings


def validate_goose_quantum_task(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Quantum Algorithm Design Task" not in body:
        findings.append(Finding(rel, "missing Quantum Algorithm Design Task section"))
    for phrase in GOOSE_QUANTUM_TASK_REQUIRED_PHRASES:
        if phrase not in body:
            findings.append(
                Finding(rel, f"missing locked goose-quantum-task phrase: {phrase}")
            )
    return findings


def validate_prompt_roles(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in PROMPT_ROLES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-roles phrase: {phrase}")
            )
    return findings


def validate_prompt_sections(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Your Role" not in text:
        findings.append(Finding(rel, "missing Your Role section"))
    if "## Key Constraints (NEVER VIOLATE)" not in text:
        findings.append(Finding(rel, "missing Key Constraints section"))
    if "## Conflict Resolution Matrix" not in text:
        findings.append(Finding(rel, "missing Conflict Resolution Matrix section"))
    for phrase in PROMPT_SECTIONS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-sections phrase: {phrase}")
            )
    return findings


def validate_prompt_usage(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Usage Instructions" not in text:
        findings.append(Finding(rel, "missing Usage Instructions section"))
    if "## Integration with AGENTS.md" not in text:
        findings.append(Finding(rel, "missing Integration with AGENTS.md section"))
    for phrase in PROMPT_USAGE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-usage phrase: {phrase}")
            )
    return findings


def validate_prompt_constraints(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Never claim quantum-safety without formal verification" not in text:
        findings.append(Finding(rel, "missing quantum-safety constraint"))
    for phrase in PROMPT_CONSTRAINTS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-constraints phrase: {phrase}")
            )
    return findings


def validate_prompt_triggers(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Circuit depth exceeds device constraints by >20%" not in text:
        findings.append(Finding(rel, "missing circuit-depth escalation trigger"))
    for phrase in PROMPT_TRIGGERS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-triggers phrase: {phrase}")
            )
    return findings


def validate_prompt_related_docs(root: Path) -> list[Finding]:
    rel = "AGENT-PROMPTS.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "AGENT-PROMPTS.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "See AGENTS.md Section 22 (Quantum-Blockchain Integration Standards)" not in text:
        findings.append(Finding(rel, "missing AGENTS.md Section 22 related-docs lock"))
    for phrase in PROMPT_RELATED_DOCS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked prompt-related-docs phrase: {phrase}")
            )
    return findings


def validate_implementation_phases(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Full Implementation (1-2 weeks)" not in text:
        findings.append(Finding(rel, "missing Full Implementation section"))
    if "### Phase 1: Infrastructure (Days 1-2)" not in text:
        findings.append(Finding(rel, "missing Phase 1 Infrastructure section"))
    if "### Phase 6: Iterate & Refine (Days 6-10)" not in text:
        findings.append(Finding(rel, "missing Phase 6 Iterate section"))
    for phrase in IMPLEMENTATION_PHASES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-phases phrase: {phrase}")
            )
    return findings


def validate_implementation_tools(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Tools & Software Checklist" not in text:
        findings.append(Finding(rel, "missing Tools & Software Checklist section"))
    for phrase in IMPLEMENTATION_TOOLS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-tools phrase: {phrase}")
            )
    return findings


def validate_implementation_success(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Success Criteria" not in text:
        findings.append(Finding(rel, "missing Success Criteria section"))
    if "## Common Issues & Solutions" not in text:
        findings.append(Finding(rel, "missing Common Issues & Solutions section"))
    if "## Next Steps" not in text:
        findings.append(Finding(rel, "missing Next Steps section"))
    for phrase in IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-success phrase: {phrase}")
            )
    return findings


def validate_implementation_issues(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Common Issues & Solutions" not in text:
        findings.append(Finding(rel, "missing Common Issues & Solutions section"))
    for phrase in IMPLEMENTATION_ISSUES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-issues phrase: {phrase}")
            )
    return findings


def validate_implementation_faq(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## FAQ" not in text:
        findings.append(Finding(rel, "missing FAQ section"))
    for phrase in IMPLEMENTATION_FAQ_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-faq phrase: {phrase}")
            )
    return findings


def validate_implementation_support(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Support & Resources" not in text:
        findings.append(Finding(rel, "missing Support & Resources section"))
    for phrase in IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked implementation-support phrase: {phrase}")
            )
    return findings


def validate_execution_timeline(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Implementation Timeline" not in text:
        findings.append(Finding(rel, "missing Implementation Timeline section"))
    for phrase in EXECUTION_TIMELINE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-timeline phrase: {phrase}")
            )
    return findings


def validate_execution_technologies(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Key Technologies (All Covered)" not in text:
        findings.append(Finding(rel, "missing Key Technologies section"))
    for phrase in EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel, f"missing locked execution-technologies phrase: {phrase}"
                )
            )
    return findings


def validate_execution_workflow(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Workflow Overview" not in text:
        findings.append(Finding(rel, "missing Workflow Overview section"))
    for phrase in EXECUTION_WORKFLOW_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-workflow phrase: {phrase}")
            )
    return findings


def validate_execution_ide(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## IDE & Software Setup" not in text:
        findings.append(Finding(rel, "missing IDE & Software Setup section"))
    for phrase in EXECUTION_IDE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-ide phrase: {phrase}")
            )
    return findings


def validate_execution_innovations(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Key Innovations in Your System" not in text:
        findings.append(Finding(rel, "missing Key Innovations section"))
    for phrase in EXECUTION_INNOVATIONS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-innovations phrase: {phrase}")
            )
    return findings


def validate_execution_next48(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Next 48 Hours" not in text:
        findings.append(Finding(rel, "missing Next 48 Hours section"))
    for phrase in EXECUTION_NEXT48_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked execution-next48 phrase: {phrase}")
            )
    return findings


def validate_agent_task_template(root: Path) -> list[Finding]:
    rel = ".github/ISSUE_TEMPLATE/agent_task.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "agent task issue template missing")]
    text = path.read_text(encoding="utf-8")
    headings = PR_HEADING_RE.findall(text)
    findings: list[Finding] = []
    for required in ISSUE_AGENT_TASK_HEADINGS:
        if required not in headings:
            findings.append(Finding(rel, f"missing required heading: {required}"))
    return findings


def validate_bug_report_template(root: Path) -> list[Finding]:
    rel = ".github/ISSUE_TEMPLATE/bug_report.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "bug report issue template missing")]
    text = path.read_text(encoding="utf-8")
    headings = PR_HEADING_RE.findall(text)
    findings: list[Finding] = []
    for required in ISSUE_BUG_REPORT_HEADINGS:
        if required not in headings:
            findings.append(Finding(rel, f"missing required heading: {required}"))
    return findings


def validate_feature_request_template(root: Path) -> list[Finding]:
    rel = ".github/ISSUE_TEMPLATE/feature_request.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "feature request issue template missing")]
    text = path.read_text(encoding="utf-8")
    headings = PR_HEADING_RE.findall(text)
    findings: list[Finding] = []
    for required in ISSUE_FEATURE_REQUEST_HEADINGS:
        if required not in headings:
            findings.append(Finding(rel, f"missing required heading: {required}"))
    return findings


def validate_changelog_packaging(root: Path) -> list[Finding]:
    rel = "CHANGELOG.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CHANGELOG.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in CHANGELOG_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"CHANGELOG missing packaging phrase: {phrase}"))
    invented = agent_tokens(text) - set(DOCUMENTED_AGENTS)
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(sorted(invented))}")
        )
    return findings


def validate_postmortem_packaging(root: Path) -> list[Finding]:
    rel = "postmortem.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "postmortem.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in POSTMORTEM_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"postmortem missing packaging phrase: {phrase}"))
    invented = agent_tokens(text) - set(DOCUMENTED_AGENTS)
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(sorted(invented))}")
        )
    return findings


def validate_postmortem_intro(root: Path) -> list[Finding]:
    rel = "postmortem.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "postmortem.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in POSTMORTEM_INTRO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked postmortem-intro phrase: {phrase}")
            )
    return findings


def validate_postmortem_fields(root: Path) -> list[Finding]:
    rel = "postmortem.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "postmortem.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Decision: Repo Hydration" not in text:
        findings.append(Finding(rel, "missing Decision: Repo Hydration section"))
    for phrase in POSTMORTEM_FIELD_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked postmortem-field phrase: {phrase}")
            )
    return findings


def validate_postmortem_next_steps(root: Path) -> list[Finding]:
    rel = "postmortem.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "postmortem.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "**Next Steps**:" not in text:
        findings.append(Finding(rel, "missing Next Steps field"))
    for phrase in POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked postmortem-next-steps phrase: {phrase}")
            )
    return findings


def validate_scratchpad_intro(root: Path) -> list[Finding]:
    rel = "agentic_flows/scratchpad.txt"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "scratchpad coordination file missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in SCRATCHPAD_INTRO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked scratchpad-intro phrase: {phrase}")
            )
    return findings


def validate_scratchpad_format(root: Path) -> list[Finding]:
    rel = "agentic_flows/scratchpad.txt"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "scratchpad coordination file missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "Format:" not in text:
        findings.append(Finding(rel, "missing Format legend section"))
    for phrase in SCRATCHPAD_FORMAT_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked scratchpad-format phrase: {phrase}")
            )
    return findings


def validate_scratchpad_task_meta(root: Path) -> list[Finding]:
    rel = "agentic_flows/scratchpad.txt"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "scratchpad coordination file missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Task: Repo Hydration" not in text:
        findings.append(Finding(rel, "missing Task: Repo Hydration section"))
    for phrase in SCRATCHPAD_TASK_META_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked scratchpad-task-meta phrase: {phrase}")
            )
    return findings


def validate_issue_metadata(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in ISSUE_TEMPLATE_FILES:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "issue template missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in ISSUE_METADATA_REQUIRED_PHRASES:
            if phrase not in text:
                findings.append(
                    Finding(rel, f"missing locked issue-metadata phrase: {phrase}")
                )
    return findings


def validate_issue_routing(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in ISSUE_TEMPLATE_FILES:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "issue template missing"))
            continue
        text = path.read_text(encoding="utf-8")
        if "## Agent Surface Routing" not in text:
            findings.append(Finding(rel, "missing Agent Surface Routing section"))
        for phrase in ISSUE_ROUTING_REQUIRED_PHRASES:
            if phrase not in text:
                findings.append(
                    Finding(rel, f"missing locked issue-routing phrase: {phrase}")
                )
    return findings


def validate_bug_repro(root: Path) -> list[Finding]:
    rel = ".github/ISSUE_TEMPLATE/bug_report.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "bug report issue template missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in BUG_REPRO_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked bug-repro phrase: {phrase}")
            )
    return findings


def validate_gitignore_packaging(root: Path) -> list[Finding]:
    rel = ".gitignore"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, ".gitignore missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for pattern in GITIGNORE_REQUIRED_PATTERNS:
        if pattern not in text:
            findings.append(Finding(rel, f".gitignore missing required pattern: {pattern}"))
    return findings


def validate_negative_constraints(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Negative Constraints" not in text:
        findings.append(Finding(rel, "missing Negative Constraints section"))
    for phrase in NEGATIVE_CONSTRAINT_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"missing locked negative constraint phrase: {phrase}")
            )
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(Finding(rel, f"documented agent missing from CLAUDE.md: {agent}"))
    return findings


def validate_hydration_report(root: Path) -> list[Finding]:
    rel = "docs/agent-hydration.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "hydration report missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for section in HYDRATION_REQUIRED_SECTIONS:
        if section not in text:
            findings.append(Finding(rel, f"hydration missing required section: {section}"))
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_execution_summary(root: Path) -> list[Finding]:
    rel = "EXECUTION-SUMMARY.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "EXECUTION-SUMMARY.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in EXECUTION_SUMMARY_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"EXECUTION-SUMMARY missing packaging phrase: {phrase}")
            )
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(
                Finding(rel, f"EXECUTION-SUMMARY missing documented agent: {agent}")
            )
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_implementation_guide(root: Path) -> list[Finding]:
    rel = "IMPLEMENTATION-GUIDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "IMPLEMENTATION-GUIDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in IMPLEMENTATION_GUIDE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(
                    rel,
                    f"IMPLEMENTATION-GUIDE missing packaging phrase: {phrase}",
                )
            )
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(
                Finding(
                    rel,
                    f"IMPLEMENTATION-GUIDE missing documented agent: {agent}",
                )
            )
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_claude_packaging(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for section in CLAUDE_REQUIRED_SECTIONS:
        if section not in text:
            findings.append(Finding(rel, f"CLAUDE.md missing required section: {section}"))
    for phrase in CLAUDE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"CLAUDE.md missing packaging phrase: {phrase}")
            )
    for phrase in ESCALATION_FORMAT_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"CLAUDE.md missing escalation-format phrase: {phrase}")
            )
    for agent in DOCUMENTED_AGENTS:
        if agent not in text:
            findings.append(Finding(rel, f"CLAUDE.md missing documented agent: {agent}"))
    invented = sorted(agent_tokens(text) - set(DOCUMENTED_AGENTS))
    if invented:
        findings.append(
            Finding(rel, f"invented or unknown agent token(s): {', '.join(invented)}")
        )
    return findings


def validate_recipe_titles(root: Path) -> list[Finding]:
    rel = "GOOSE-RECIPES.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "GOOSE-RECIPES.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in GOOSE_DOCS_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"GOOSE-RECIPES missing packaging phrase: {phrase}")
            )
    blocks = extract_fenced_yaml_blocks(text)
    seen: set[str] = set()
    for index, block in enumerate(blocks, start=1):
        block_path = f"{rel}#recipe-{index}"
        data, parse_findings = parse_yaml_text(block, path=block_path)
        findings.extend(parse_findings)
        if not isinstance(data, dict):
            continue
        name = data.get("name")
        recipe = data.get("recipe")
        if not isinstance(name, str) or not isinstance(recipe, dict):
            continue
        seen.add(name)
        expected_title = RECIPE_TITLES.get(name)
        title = recipe.get("title")
        if expected_title is None:
            findings.append(
                Finding(block_path, f"unexpected/invented recipe name: {name}")
            )
            continue
        if title != expected_title:
            findings.append(
                Finding(
                    block_path,
                    (
                        f"historic recipe title must be {expected_title!r}, "
                        f"found {title!r}"
                    ),
                )
            )
    missing = sorted(set(RECIPE_TITLES) - seen)
    for name in missing:
        findings.append(Finding(rel, f"missing locked recipe title for: {name}"))
    return findings


def validate_ci_actions(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    data, parse_findings = parse_yaml_text(text, path=rel)
    findings.extend(parse_findings)
    if isinstance(data, dict):
        name = data.get("name")
        if name != CI_WORKFLOW_NAME:
            findings.append(
                Finding(
                    rel,
                    f"CI workflow name must be {CI_WORKFLOW_NAME!r}, found {name!r}",
                )
            )
    for action in CI_REQUIRED_ACTIONS:
        if action not in text:
            findings.append(
                Finding(rel, f"CI workflow missing required action pin: {action}")
            )
    for marker in CI_REQUIRED_TEXT_MARKERS:
        if marker not in text:
            findings.append(
                Finding(rel, f"CI workflow missing required text marker: {marker}")
            )
    return findings


def validate_issue_template_names(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel, expected_name in ISSUE_TEMPLATE_NAMES.items():
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "required issue template file missing"))
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, fm_findings = extract_yaml_frontmatter(text)
        findings.extend(
            Finding(rel, f.message) if f.path == "<frontmatter>" else f
            for f in fm_findings
        )
        if frontmatter is None:
            continue
        data, parse_findings = parse_yaml_text(frontmatter, path=rel)
        findings.extend(parse_findings)
        if not isinstance(data, dict):
            if data is not None:
                findings.append(Finding(rel, "frontmatter must be a mapping"))
            continue
        name = data.get("name")
        if name != expected_name:
            findings.append(
                Finding(
                    rel,
                    f"issue template name must be {expected_name!r}, found {name!r}",
                )
            )
        expected_about = ISSUE_TEMPLATE_ABOUTS[rel]
        about = data.get("about")
        if about != expected_about:
            findings.append(
                Finding(
                    rel,
                    (
                        f"issue template about must be {expected_about!r}, "
                        f"found {about!r}"
                    ),
                )
            )
    return findings


def validate_readme_badges(root: Path) -> list[Finding]:
    rel = "README.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "README.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in README_BADGE_PHRASES:
        if phrase not in text:
            findings.append(Finding(rel, f"README missing badge phrase: {phrase}"))
    return findings


def validate_quarterly_review(root: Path) -> list[Finding]:
    rel = "CLAUDE.md"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CLAUDE.md missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    if "## Quarterly Review Triggers" not in text:
        findings.append(Finding(rel, "missing Quarterly Review Triggers section"))
    for phrase in QUARTERLY_REVIEW_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"CLAUDE.md missing quarterly-review phrase: {phrase}")
            )
    return findings


def validate_link_check(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    link_job = jobs.get("link-check")
    if not isinstance(link_job, dict):
        return findings + [Finding(rel, "CI workflow missing link-check job")]
    steps = link_job.get("steps")
    if not isinstance(steps, list):
        return findings + [Finding(rel, "link-check job missing steps")]
    found_args = False
    found_fail = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        uses = str(step.get("uses", ""))
        if "lychee-action" not in uses:
            continue
        with_block = step.get("with")
        if not isinstance(with_block, dict):
            findings.append(Finding(rel, "lychee-action step missing with: mapping"))
            continue
        args = with_block.get("args")
        if args != CI_LINK_CHECK_ARGS:
            findings.append(
                Finding(
                    rel,
                    (
                        "link-check args must be "
                        f"{CI_LINK_CHECK_ARGS!r}, found {args!r}"
                    ),
                )
            )
        else:
            found_args = True
        fail = with_block.get("fail")
        if fail is not CI_LINK_CHECK_FAIL:
            findings.append(
                Finding(
                    rel,
                    f"link-check fail must be {CI_LINK_CHECK_FAIL!r}, found {fail!r}",
                )
            )
        else:
            found_fail = True
    if not found_args:
        findings.append(Finding(rel, "link-check lychee args lock not found"))
    if not found_fail:
        findings.append(Finding(rel, "link-check lychee fail lock not found"))

    markdown_job = jobs.get("markdown-lint")
    if isinstance(markdown_job, dict):
        steps = markdown_job.get("steps")
        if isinstance(steps, list):
            found_globs = False
            found_config = False
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if "markdownlint-cli2-action" not in uses:
                    continue
                with_block = step.get("with")
                if not isinstance(with_block, dict):
                    findings.append(
                        Finding(rel, "markdownlint-cli2-action step missing with: mapping")
                    )
                    continue
                globs = with_block.get("globs")
                if globs != CI_MARKDOWN_LINT_GLOBS:
                    findings.append(
                        Finding(
                            rel,
                            (
                                "markdown-lint globs must be "
                                f"{CI_MARKDOWN_LINT_GLOBS!r}, found {globs!r}"
                            ),
                        )
                    )
                else:
                    found_globs = True
                config = with_block.get("config")
                if config != CI_MARKDOWN_LINT_CONFIG:
                    findings.append(
                        Finding(
                            rel,
                            (
                                "markdown-lint config must be "
                                f"{CI_MARKDOWN_LINT_CONFIG!r}, found {config!r}"
                            ),
                        )
                    )
                else:
                    found_config = True
            if not found_globs:
                findings.append(Finding(rel, "markdown-lint globs lock not found"))
            if not found_config:
                findings.append(Finding(rel, "markdown-lint config lock not found"))
        else:
            findings.append(Finding(rel, "markdown-lint job missing steps"))
    else:
        findings.append(Finding(rel, "CI workflow missing markdown-lint job"))

    manifest_job = jobs.get("manifest-validate")
    if isinstance(manifest_job, dict):
        steps = manifest_job.get("steps")
        if isinstance(steps, list):
            found_cache_path = False
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if "setup-python" not in uses:
                    continue
                with_block = step.get("with")
                if not isinstance(with_block, dict):
                    continue
                cache_path = with_block.get("cache-dependency-path")
                if cache_path != CI_CACHE_DEPENDENCY_PATH:
                    findings.append(
                        Finding(
                            rel,
                            (
                                "setup-python cache-dependency-path must be "
                                f"{CI_CACHE_DEPENDENCY_PATH!r}, found {cache_path!r}"
                            ),
                        )
                    )
                else:
                    found_cache_path = True
            if not found_cache_path:
                findings.append(
                    Finding(rel, "setup-python cache-dependency-path lock not found")
                )
    return findings


def validate_ci_job_names(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    for job_id, expected_name in CI_JOB_DISPLAY_NAMES.items():
        job = jobs.get(job_id)
        if not isinstance(job, dict):
            findings.append(Finding(rel, f"CI workflow missing job: {job_id}"))
            continue
        name = job.get("name")
        if name != expected_name:
            findings.append(
                Finding(
                    rel,
                    (
                        f"CI job {job_id!r} name must be {expected_name!r}, "
                        f"found {name!r}"
                    ),
                )
            )
    return findings


def validate_github_agent_description(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in GITHUB_AGENT_FILES:
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "required GitHub agent packaging file missing"))
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, fm_findings = extract_yaml_frontmatter(text)
        findings.extend(
            Finding(rel, f.message) if f.path == "<frontmatter>" else f
            for f in fm_findings
        )
        if frontmatter is None:
            continue
        data, parse_findings = parse_yaml_text(frontmatter, path=rel)
        findings.extend(parse_findings)
        if not isinstance(data, dict):
            if data is not None:
                findings.append(Finding(rel, "frontmatter must be a mapping"))
            continue
        description = data.get("description")
        if not isinstance(description, str):
            findings.append(Finding(rel, "GitHub agent description missing or not a string"))
            continue
        if description.strip() != GITHUB_AGENT_DESCRIPTION:
            findings.append(
                Finding(
                    rel,
                    (
                        "GitHub agent description must be "
                        f"{GITHUB_AGENT_DESCRIPTION!r}, found {description!r}"
                    ),
                )
            )
    return findings



def validate_ci_runs_on(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    for job_id in sorted(REQUIRED_CI_JOBS):
        job = jobs.get(job_id)
        if not isinstance(job, dict):
            findings.append(Finding(rel, f"CI workflow missing job: {job_id}"))
            continue
        runs_on = job.get("runs-on")
        if runs_on != CI_RUNS_ON:
            findings.append(
                Finding(
                    rel,
                    (
                        f"CI job {job_id!r} runs-on must be {CI_RUNS_ON!r}, "
                        f"found {runs_on!r}"
                    ),
                )
            )
    return findings


def validate_ci_artifacts(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    manifest = jobs.get("manifest-validate")
    if not isinstance(manifest, dict):
        return findings + [Finding(rel, "CI workflow missing manifest-validate job")]
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return findings + [Finding(rel, "manifest-validate job missing steps")]
    found_upload = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        uses = str(step.get("uses", ""))
        if "upload-artifact" not in uses:
            continue
        found_upload = True
        with_block = step.get("with")
        if not isinstance(with_block, dict):
            findings.append(
                Finding(rel, "upload-artifact step missing with: mapping")
            )
            continue
        if_no_files = with_block.get("if-no-files-found")
        if if_no_files != CI_ARTIFACT_IF_NO_FILES_FOUND:
            findings.append(
                Finding(
                    rel,
                    (
                        "upload-artifact if-no-files-found must be "
                        f"{CI_ARTIFACT_IF_NO_FILES_FOUND!r}, found {if_no_files!r}"
                    ),
                )
            )
        path_field = with_block.get("path")
        if isinstance(path_field, str):
            present = {
                line.strip()
                for line in path_field.splitlines()
                if line.strip()
            }
        elif isinstance(path_field, list):
            present = {str(item).strip() for item in path_field if str(item).strip()}
        else:
            present = set()
            findings.append(
                Finding(rel, "upload-artifact path must be a string or sequence")
            )
        missing = [p for p in CI_ARTIFACT_PATHS if p not in present]
        for artifact_path in missing:
            findings.append(
                Finding(
                    rel,
                    f"upload-artifact path missing locked artifact: {artifact_path}",
                )
            )
        extras = sorted(present - set(CI_ARTIFACT_PATHS))
        for extra in extras:
            findings.append(
                Finding(
                    rel,
                    f"upload-artifact path has unexpected artifact: {extra}",
                )
            )
    if not found_upload:
        findings.append(Finding(rel, "manifest-validate missing upload-artifact step"))
    return findings


def validate_actionlint_shell(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    actionlint = jobs.get("actionlint")
    if not isinstance(actionlint, dict):
        return findings + [Finding(rel, "CI workflow missing actionlint job")]
    steps = actionlint.get("steps")
    if not isinstance(steps, list):
        return findings + [Finding(rel, "actionlint job missing steps")]
    found_shell = False
    found_step_id = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        if step_id == CI_ACTIONLINT_STEP_ID:
            found_step_id = True
        shell = step.get("shell")
        if shell is None:
            continue
        if shell != CI_ACTIONLINT_SHELL:
            findings.append(
                Finding(
                    rel,
                    (
                        "actionlint step shell must be "
                        f"{CI_ACTIONLINT_SHELL!r}, found {shell!r}"
                    ),
                )
            )
        else:
            found_shell = True
    if not found_shell:
        findings.append(
            Finding(
                rel,
                f"actionlint job must set shell: {CI_ACTIONLINT_SHELL!r} on a step",
            )
        )
    if not found_step_id:
        findings.append(
            Finding(
                rel,
                (
                    "actionlint job must include step id "
                    f"{CI_ACTIONLINT_STEP_ID!r}"
                ),
            )
        )
    return findings


def validate_ci_setup_python(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    manifest = jobs.get("manifest-validate")
    if not isinstance(manifest, dict):
        return findings + [Finding(rel, "CI workflow missing manifest-validate job")]
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return findings + [Finding(rel, "manifest-validate job missing steps")]
    found_setup = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        uses = str(step.get("uses", ""))
        if "setup-python" not in uses:
            continue
        found_setup = True
        with_block = step.get("with")
        if not isinstance(with_block, dict):
            findings.append(
                Finding(rel, "setup-python step missing with: mapping")
            )
            continue
        cache = with_block.get("cache")
        if cache != CI_SETUP_PYTHON_CACHE:
            findings.append(
                Finding(
                    rel,
                    (
                        "setup-python cache must be "
                        f"{CI_SETUP_PYTHON_CACHE!r}, found {cache!r}"
                    ),
                )
            )
        cache_path = with_block.get("cache-dependency-path")
        if cache_path != CI_CACHE_DEPENDENCY_PATH:
            findings.append(
                Finding(
                    rel,
                    (
                        "setup-python cache-dependency-path must be "
                        f"{CI_CACHE_DEPENDENCY_PATH!r}, found {cache_path!r}"
                    ),
                )
            )
    if not found_setup:
        findings.append(
            Finding(rel, "manifest-validate missing setup-python step")
        )
    return findings


def validate_ci_ruff(root: Path) -> list[Finding]:
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return findings
    if not isinstance(data, dict):
        return findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow missing jobs mapping")]
    manifest = jobs.get("manifest-validate")
    if not isinstance(manifest, dict):
        return findings + [Finding(rel, "CI workflow missing manifest-validate job")]
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return findings + [Finding(rel, "manifest-validate job missing steps")]
    found_ruff = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if not isinstance(run, str):
            continue
        if CI_RUFF_CHECK_COMMAND in run:
            found_ruff = True
            break
    if not found_ruff:
        findings.append(
            Finding(
                rel,
                (
                    "manifest-validate must run "
                    f"{CI_RUFF_CHECK_COMMAND!r}"
                ),
            )
        )
    return findings


def validate_license_mit(root: Path) -> list[Finding]:
    rel = "LICENSE"
    path = root / rel
    if not path.is_file():
        return [Finding(rel, "LICENSE missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for phrase in LICENSE_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(
                Finding(rel, f"LICENSE missing required MIT phrase: {phrase}")
            )
    return findings


def _manifest_validate_steps(
    root: Path,
) -> tuple[str, list[Any] | None, list[Finding]]:
    """Return (rel, steps|None, findings) for the manifest-validate job."""
    rel = ".github/workflows/ci.yml"
    path = root / rel
    if not path.is_file():
        return rel, None, [Finding(rel, "CI workflow missing")]
    data, parse_findings = parse_yaml_text(path.read_text(encoding="utf-8"), path=rel)
    findings = list(parse_findings)
    if data is None:
        return rel, None, findings
    if not isinstance(data, dict):
        return rel, None, findings + [Finding(rel, "CI workflow root must be a mapping")]
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return rel, None, findings + [Finding(rel, "CI workflow missing jobs mapping")]
    manifest = jobs.get("manifest-validate")
    if not isinstance(manifest, dict):
        return rel, None, findings + [
            Finding(rel, "CI workflow missing manifest-validate job")
        ]
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return rel, None, findings + [
            Finding(rel, "manifest-validate job missing steps")
        ]
    return rel, steps, findings


def validate_ci_pip_install(root: Path) -> list[Finding]:
    rel, steps, findings = _manifest_validate_steps(root)
    if steps is None:
        return findings
    found = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if not isinstance(run, str):
            continue
        if CI_PIP_INSTALL_COMMAND in run:
            found = True
            break
    if not found:
        findings.append(
            Finding(
                rel,
                f"manifest-validate must run {CI_PIP_INSTALL_COMMAND!r}",
            )
        )
    return findings


def validate_ci_pip_check(root: Path) -> list[Finding]:
    rel, steps, findings = _manifest_validate_steps(root)
    if steps is None:
        return findings
    found = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if not isinstance(run, str):
            continue
        if CI_PIP_CHECK_COMMAND in run:
            found = True
            break
    if not found:
        findings.append(
            Finding(
                rel,
                f"manifest-validate must run {CI_PIP_CHECK_COMMAND!r}",
            )
        )
    return findings


def validate_ci_pytest(root: Path) -> list[Finding]:
    rel, steps, findings = _manifest_validate_steps(root)
    if steps is None:
        return findings
    found_pytest = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if not isinstance(run, str):
            continue
        if "python -m pytest" not in run:
            continue
        found_pytest = True
        for marker in CI_PYTEST_REQUIRED_MARKERS:
            if marker not in run:
                findings.append(
                    Finding(
                        rel,
                        f"manifest-validate pytest step missing marker {marker!r}",
                    )
                )
        break
    if not found_pytest:
        findings.append(
            Finding(rel, "manifest-validate must run a python -m pytest step")
        )
    return findings


VALIDATORS: dict[str, ValidatorFn] = {
    "schemas": validate_schemas_meta,
    "inventory": validate_packaging_inventory,
    "goose": validate_goose_recipes,
    "recipe-agents": validate_recipe_agent_bindings,
    "recipe-titles": validate_recipe_titles,
    "agent-tokens": validate_archive_agent_tokens,
    "constitution": validate_constitution_agent_headings,
    "constitution-crypto": validate_constitution_crypto,
    "constitution-handoff": validate_constitution_handoff,
    "constitution-escalation-matrix": validate_constitution_escalation_matrix,
    "constitution-on-device": validate_constitution_on_device,
    "constitution-multichain": validate_constitution_multichain,
    "constitution-escalation-format": validate_constitution_escalation_format,
    "constitution-recipe-orchestration": validate_constitution_recipe_orchestration,
    "constitution-scratchpad-state": validate_constitution_scratchpad_state,
    "constitution-conflict-matrix": validate_constitution_conflict_matrix,
    "routing": validate_routing_surfaces,
    "environment": validate_cursor_environment,
    "github-agents": validate_github_agents,
    "github-agent-desc": validate_github_agent_description,
    "issue-templates": validate_issue_templates,
    "issue-names": validate_issue_template_names,
    "agent-task": validate_agent_task_template,
    "bug-template": validate_bug_report_template,
    "feature-template": validate_feature_request_template,
    "issue-metadata": validate_issue_metadata,
    "issue-routing": validate_issue_routing,
    "bug-repro": validate_bug_repro,
    "pr-template": validate_pr_template,
    "pr-summary": validate_pr_summary,
    "pr-acceptance": validate_pr_acceptance,
    "pr-notes": validate_pr_notes,
    "dependabot": validate_dependabot,
    "markdownlint": validate_markdownlint,
    "requirements-dev": validate_requirements_dev,
    "license": validate_license,
    "license-mit": validate_license_mit,
    "readme": validate_readme_packaging,
    "readme-badges": validate_readme_badges,
    "readme-honesty": validate_readme_honesty,
    "readme-historic": validate_readme_historic,
    "readme-contents": validate_readme_contents,
    "readme-lead": validate_readme_lead,
    "readme-blurbs": validate_readme_blurbs,
    "readme-bootstrap": validate_readme_bootstrap,
    "goose-howto": validate_goose_howto,
    "goose-state-machine": validate_goose_state_machine,
    "goose-naming": validate_goose_naming,
    "goose-recipe-headers": validate_goose_recipe_headers,
    "goose-instruction-agents": validate_goose_instruction_agents,
    "goose-extensions": validate_goose_extensions,
    "goose-orchestration": validate_goose_orchestration,
    "goose-conflicts": validate_goose_conflicts,
    "goose-quantum-task": validate_goose_quantum_task,
    "prompt-roles": validate_prompt_roles,
    "prompt-sections": validate_prompt_sections,
    "prompt-usage": validate_prompt_usage,
    "prompt-constraints": validate_prompt_constraints,
    "prompt-triggers": validate_prompt_triggers,
    "prompt-related-docs": validate_prompt_related_docs,
    "implementation-phases": validate_implementation_phases,
    "implementation-tools": validate_implementation_tools,
    "implementation-success": validate_implementation_success,
    "implementation-issues": validate_implementation_issues,
    "implementation-faq": validate_implementation_faq,
    "implementation-support": validate_implementation_support,
    "execution-timeline": validate_execution_timeline,
    "execution-technologies": validate_execution_technologies,
    "execution-workflow": validate_execution_workflow,
    "execution-ide": validate_execution_ide,
    "execution-innovations": validate_execution_innovations,
    "execution-next48": validate_execution_next48,
    "security": validate_security_packaging,
    "contributing": validate_contributing_packaging,
    "contributing-who": validate_contributing_who,
    "contributing-branches": validate_contributing_branches,
    "contributing-pr": validate_contributing_pr,
    "contributing-issues": validate_contributing_issues,
    "contributing-local": validate_contributing_local,
    "contributing-governance": validate_contributing_governance,
    "contributing-metadata": validate_contributing_metadata,
    "contributing-surfaces": validate_contributing_surfaces,
    "contributing-ci-honesty": validate_contributing_ci_honesty,
    "scratchpad": validate_scratchpad,
    "scratchpad-intro": validate_scratchpad_intro,
    "scratchpad-format": validate_scratchpad_format,
    "scratchpad-task-meta": validate_scratchpad_task_meta,
    "pyproject": validate_pyproject,
    "yaml-configs": validate_yaml_configs,
    "ci": validate_ci_workflow,
    "ci-actions": validate_ci_actions,
    "ci-job-names": validate_ci_job_names,
    "ci-runs-on": validate_ci_runs_on,
    "ci-artifacts": validate_ci_artifacts,
    "actionlint-shell": validate_actionlint_shell,
    "ci-setup-python": validate_ci_setup_python,
    "ci-ruff": validate_ci_ruff,
    "ci-pip-install": validate_ci_pip_install,
    "ci-pip-check": validate_ci_pip_check,
    "ci-pytest": validate_ci_pytest,
    "state-residency": validate_state_residency,
    "key-files": validate_key_files,
    "pr-routing": validate_pr_routing,
    "routing-matrix": validate_routing_matrix,
    "repo-identity": validate_repo_identity,
    "escalation-format": validate_escalation_format,
    "routing-rationales": validate_routing_rationales,
    "claude-metadata": validate_claude_metadata,
    "escalation-usage": validate_escalation_usage,
    "security-supported": validate_security_supported,
    "security-reporting": validate_security_reporting,
    "security-standards": validate_security_standards,
    "security-header": validate_security_header,
    "security-fips": validate_security_fips,
    "security-known-non-issues": validate_security_known_non_issues,
    "security-scope": validate_security_scope,
    "security-reporting-channel": validate_security_reporting_channel,
    "security-compliance-detail": validate_security_compliance_detail,
    "implementation-quickstart": validate_implementation_quickstart,
    "execution-specialists": validate_execution_specialists,
    "hydration-list-b": validate_hydration_list_b,
    "hydration-phase1": validate_hydration_phase1,
    "hydration-list-a": validate_hydration_list_a,
    "hydration-resolved": validate_hydration_resolved,
    "hydration-phase4": validate_hydration_phase4,
    "hydration-deferred": validate_hydration_deferred,
    "hydration-meta": validate_hydration_meta,
    "hydration-identity-detail": validate_hydration_identity_detail,
    "hydration-git-detail": validate_hydration_git_detail,
    "constitution-ide-stack": validate_constitution_ide_stack,
    "constitution-install-script": validate_constitution_install_script,
    "constitution-vscode": validate_constitution_vscode,
    "constitution-hard-constraints": validate_constitution_hard_constraints,
    "constitution-risk-tolerance": validate_constitution_risk_tolerance,
    "changelog-preamble": validate_changelog_preamble,
    "changelog-changed": validate_changelog_changed,
    "changelog-initial": validate_changelog_initial,
    "prompt-expertise": validate_prompt_expertise,
    "prompt-principles": validate_prompt_principles,
    "prompt-metrics": validate_prompt_metrics,
    "prompt-tools": validate_prompt_tools,
    "prompt-communication": validate_prompt_communication,
    "prompt-escalation-identity": validate_prompt_escalation_identity,
    "prompt-orchestration-matrix": validate_prompt_orchestration_matrix,
    "prompt-monthly": validate_prompt_monthly,
    "prompt-usage-example": validate_prompt_usage_example,
    "prompt-context": validate_prompt_context,
    "prompt-decision-authority": validate_prompt_decision_authority,
    "prompt-escalation-authority": validate_prompt_escalation_authority,
    "prompt-responsibilities": validate_prompt_responsibilities,
    "prompt-cannot-delegate": validate_prompt_cannot_delegate,
    "prompt-human-escalation": validate_prompt_human_escalation,
    "hydration-phase2": validate_hydration_phase2,
    "hydration-phase5": validate_hydration_phase5,
    "link-check": validate_link_check,
    "prompts": validate_documented_agent_prompts,
    "cross-docs": validate_cross_doc_agents,
    "changelog": validate_changelog_packaging,
    "changelog-format": validate_changelog_format,
    "changelog-unreleased": validate_changelog_unreleased,
    "changelog-release": validate_changelog_release,
    "postmortem": validate_postmortem_packaging,
    "postmortem-intro": validate_postmortem_intro,
    "postmortem-fields": validate_postmortem_fields,
    "postmortem-next-steps": validate_postmortem_next_steps,
    "gitignore": validate_gitignore_packaging,
    "negative-constraints": validate_negative_constraints,
    "claude": validate_claude_packaging,
    "quarterly-review": validate_quarterly_review,
    "hydration": validate_hydration_report,
    "execution-summary": validate_execution_summary,
    "implementation-guide": validate_implementation_guide,
}


def run_all_validations(
    root: Path | None = None, *, only: Sequence[str] | None = None
) -> list[Finding]:
    base = root or REPO_ROOT
    selected = list(only) if only else list(VALIDATORS)
    unknown = [name for name in selected if name not in VALIDATORS]
    if unknown:
        raise ValueError(f"unknown validator(s): {', '.join(unknown)}")
    findings: list[Finding] = []
    for name in selected:
        findings.extend(VALIDATORS[name](base))
    return findings


def findings_to_json(findings: Sequence[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to validate (default: repo containing this script)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(VALIDATORS),
        help="Run a subset of validators",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON on stdout (empty list on success)",
    )
    parser.add_argument(
        "--list-validators",
        action="store_true",
        help="Print available validator names and exit",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_validators:
        for name in sorted(VALIDATORS):
            print(name)
        return 0

    findings = run_all_validations(args.root.resolve(), only=args.only)
    if args.json:
        print(findings_to_json(findings))
    elif findings:
        print(f"Manifest validation failed with {len(findings)} finding(s):", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
    else:
        print("Manifest validation passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

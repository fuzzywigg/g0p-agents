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
- pyproject project name + version/license/description/readme +
  ruff line-length/src/lint select locks
- coverage show_missing/skip_empty/source + exact fail_under +
  pytest addopts/testpaths/pythonpath locks
- LICENSE MIT required phrase locks (header / grant / AS IS)
- Dependabot directory set inventory lock (file untouched)
- Issue template frontmatter name/about locks
- README badge phrase locks
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

INVENTORY_VERSION = 13
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
    "actions/setup-python@v5",
    "actions/upload-artifact@v4",
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

CONTRIBUTING_BRANCH_SURFACES: tuple[str, ...] = ("copilot", "geryon", "cursor")

SCRATCHPAD_STATUS_MARKERS: tuple[str, ...] = (
    "DONE",
    "PENDING",
    "IN_PROGRESS",
    "BLOCKED",
)

SPECIALIST_AGENTS: tuple[str, ...] = DOCUMENTED_AGENTS[:-1]

MIN_COVERAGE_FAIL_UNDER = 99
MIN_VALIDATOR_COUNT = 52


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
    "routing": validate_routing_surfaces,
    "environment": validate_cursor_environment,
    "github-agents": validate_github_agents,
    "github-agent-desc": validate_github_agent_description,
    "issue-templates": validate_issue_templates,
    "issue-names": validate_issue_template_names,
    "agent-task": validate_agent_task_template,
    "bug-template": validate_bug_report_template,
    "feature-template": validate_feature_request_template,
    "pr-template": validate_pr_template,
    "dependabot": validate_dependabot,
    "markdownlint": validate_markdownlint,
    "requirements-dev": validate_requirements_dev,
    "license": validate_license,
    "license-mit": validate_license_mit,
    "readme": validate_readme_packaging,
    "readme-badges": validate_readme_badges,
    "security": validate_security_packaging,
    "contributing": validate_contributing_packaging,
    "scratchpad": validate_scratchpad,
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
    "link-check": validate_link_check,
    "prompts": validate_documented_agent_prompts,
    "cross-docs": validate_cross_doc_agents,
    "changelog": validate_changelog_packaging,
    "postmortem": validate_postmortem_packaging,
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

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
- .github/agents/*.agent.md frontmatter + locked file set + non-empty body
- .github/ISSUE_TEMPLATE/*.md frontmatter + locked file set + non-empty body
- .github/pull_request_template.md required headings
- .github/dependabot.yml (ecosystems + weekly schedule; no version bumps)
- .markdownlint.yaml (default: true lock)
- requirements-dev.txt required validation packages
- LICENSE MIT marker; README packaging section
- agentic_flows/scratchpad.txt coordination markers
- pyproject.toml validation tooling keys (+ coverage / requires-python locks)
- CI workflow job/step/matrix/concurrency/permissions presence (no orphan jobs)
- Packaging inventory lock + internal consistency + schema meta-validation
- Parseability of known YAML config files

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

INVENTORY_VERSION = 5
CURSOR_ENVIRONMENT_NAME = "g0p-agents"
DEPENDABOT_SCHEDULE_INTERVAL = "weekly"
DEPENDABOT_DIRECTORIES: frozenset[str] = frozenset({"/"})
CI_PERMISSIONS_CONTENTS = "read"
CI_ARTIFACT_NAME_PREFIX = "manifest-validate-py"
CI_PULL_REQUEST_BRANCH = "alpha"
PYPROJECT_REQUIRES_PYTHON = ">=3.11"
MARKDOWNLINT_DEFAULT = True

SCRATCHPAD_REQUIRED_PHRASES = (
    "source of truth",
    "Never delete entries",
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
)

SECURITY_REQUIRED_PHRASES = (
    "Never commit secrets",
    "Do NOT open a public GitHub issue for security vulnerabilities",
)

CONTRIBUTING_REQUIRED_PHRASES = (
    "Do not invent new specialist agents",
    "validate_manifests.py",
    "four agents only",
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

SPECIALIST_AGENTS: tuple[str, ...] = DOCUMENTED_AGENTS[:-1]

MIN_COVERAGE_FAIL_UNDER = 98
MIN_VALIDATOR_COUNT = 27


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

    if tuple(inventory.get("scratchpad_required_phrases", ())) != SCRATCHPAD_REQUIRED_PHRASES:
        findings.append(_lock_mismatch(schema_path, "scratchpad_required_phrases"))

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
    return findings


def _validate_historic_recipe_settings(data: dict[str, Any], *, path: str) -> list[Finding]:
    findings: list[Finding] = []
    recipe = data.get("recipe")
    if not isinstance(recipe, dict):
        return findings
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
    for required in ("github-actions", "pip"):
        if required not in ecosystems:
            findings.append(
                Finding(rel, f"missing required package-ecosystem: {required}")
            )
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
    if isinstance(data, dict) and data.get("default") is not MARKDOWNLINT_DEFAULT:
        findings.append(
            Finding(
                rel,
                f"markdownlint default must be {MARKDOWNLINT_DEFAULT}, "
                f"found {data.get('default')!r}",
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

    ruff = tool.get("ruff")
    if not isinstance(ruff, dict):
        findings.append(Finding(rel, "missing [tool.ruff]"))

    coverage = tool.get("coverage")
    if not isinstance(coverage, dict):
        findings.append(Finding(rel, "missing [tool.coverage]"))
        return findings

    report = coverage.get("report")
    if not isinstance(report, dict) or "fail_under" not in report:
        findings.append(Finding(rel, "missing [tool.coverage.report].fail_under"))
        return findings

    fail_under = report.get("fail_under")
    if not isinstance(fail_under, (int, float)) or fail_under < MIN_COVERAGE_FAIL_UNDER:
        findings.append(
            Finding(
                rel,
                f"coverage fail_under must be >= {MIN_COVERAGE_FAIL_UNDER}, found {fail_under!r}",
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
    elif concurrency.get("cancel-in-progress") is not True:
        findings.append(
            Finding(rel, "CI workflow concurrency.cancel-in-progress must be true")
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
        strategy = manifest.get("strategy")
        if not isinstance(strategy, dict) or "matrix" not in strategy:
            findings.append(
                Finding(rel, "manifest-validate job must define a Python version matrix")
            )
        else:
            if strategy.get("fail-fast") is not False:
                findings.append(
                    Finding(
                        rel,
                        "manifest-validate strategy.fail-fast must be false",
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
    if "## Agent Routing Matrix" not in text:
        findings.append(Finding(rel, "missing Agent Routing Matrix section"))
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
    for surface in ("copilot", "geryon", "cursor"):
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


VALIDATORS: dict[str, ValidatorFn] = {
    "schemas": validate_schemas_meta,
    "inventory": validate_packaging_inventory,
    "goose": validate_goose_recipes,
    "recipe-agents": validate_recipe_agent_bindings,
    "agent-tokens": validate_archive_agent_tokens,
    "constitution": validate_constitution_agent_headings,
    "routing": validate_routing_surfaces,
    "environment": validate_cursor_environment,
    "github-agents": validate_github_agents,
    "issue-templates": validate_issue_templates,
    "agent-task": validate_agent_task_template,
    "bug-template": validate_bug_report_template,
    "feature-template": validate_feature_request_template,
    "pr-template": validate_pr_template,
    "dependabot": validate_dependabot,
    "markdownlint": validate_markdownlint,
    "requirements-dev": validate_requirements_dev,
    "license": validate_license,
    "readme": validate_readme_packaging,
    "security": validate_security_packaging,
    "contributing": validate_contributing_packaging,
    "scratchpad": validate_scratchpad,
    "pyproject": validate_pyproject,
    "yaml-configs": validate_yaml_configs,
    "ci": validate_ci_workflow,
    "prompts": validate_documented_agent_prompts,
    "cross-docs": validate_cross_doc_agents,
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

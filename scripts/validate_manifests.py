#!/usr/bin/env python3
"""Validate documented agent packaging manifests in this docs-only archive.

Checks structural correctness of:
- Goose recipe YAML fenced in GOOSE-RECIPES.md (and any agentic_flows/*.yaml)
- Locked recipe inventory (names + declared file paths; no invented workflows)
- Documented specialist agents only (no invented agents)
- .cursor/environment.json (+ install path refs)
- .github/agents/*.agent.md frontmatter
- .github/ISSUE_TEMPLATE/*.md frontmatter
- .github/dependabot.yml
- CI workflow job presence
- Packaging inventory + schema meta-validation
- Parseability of known YAML config files

Does not invent agents or scaffold new specialist definitions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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

RECIPE_PRIMARY_AGENT: dict[str, str] = {
    "quantum_algorithm_design_workflow": "QuantumArchitectAgent",
    "blockchain_contract_design_workflow": "BlockchainArchitectAgent",
    "edge_security_implementation_workflow": "EdgeSecurityAgent",
    "quantum_nft_mint_full_orchestration": "OrchestrationAgent",
}

AGENT_TOKEN_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*Agent)\b")
PROMPT_HEADING_RE = re.compile(
    r"^##\s+\d+\.\s+([A-Z][A-Za-z0-9]*Agent)\s+Prompt Template\s*$",
    re.MULTILINE,
)
GOOSE_RUN_PATH_RE = re.compile(
    r"goose\s+run\s+(\./agentic_flows/[A-Za-z0-9_\-]+\.ya?ml)"
)
INSTALL_TEST_F_RE = re.compile(r"test\s+-f\s+(\S+)")

KNOWN_YAML_CONFIGS = (
    Path(".github/workflows/ci.yml"),
    Path(".github/dependabot.yml"),
    Path(".markdownlint.yaml"),
)

REQUIRED_ARCHIVE_DOCS = (
    "AGENT-PROMPTS.md",
    "AGENTS-v2.2.md",
    "CLAUDE.md",
    "GOOSE-RECIPES.md",
    "README.md",
)

REQUIRED_CI_JOBS = frozenset({"markdown-lint", "link-check", "manifest-validate"})

SCHEMA_FILES = (
    "goose-recipe.schema.json",
    "cursor-environment.schema.json",
    "github-custom-agent.schema.json",
    "github-issue-template.schema.json",
    "dependabot-v2.schema.json",
    "packaging-inventory.schema.json",
)


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


def validate_schemas_meta(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schemas_dir = root / "schemas"
    if not schemas_dir.is_dir():
        return [Finding("schemas", "schemas directory missing")]
    for name in SCHEMA_FILES:
        rel = f"schemas/{name}"
        path = root / rel
        if not path.is_file():
            findings.append(Finding(rel, "required schema file missing"))
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding(rel, f"JSON parse error: {exc}"))
            continue
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

    for rel in inventory["required_paths"]:
        if not (root / rel).exists():
            findings.append(Finding(rel, "required packaging path missing"))
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
        for yaml_path in sorted(flows.glob("*.yaml")) + sorted(flows.glob("*.yml")):
            rel = str(yaml_path.relative_to(root))
            text = yaml_path.read_text(encoding="utf-8")
            data, parse_findings = parse_yaml_text(text, path=rel)
            findings.extend(parse_findings)
            if data is None:
                continue
            findings.extend(validate_against_schema(data, schema, path=rel))

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

    run_paths = [p.lstrip("./") for p in GOOSE_RUN_PATH_RE.findall(markdown)]
    for run_path in run_paths:
        if run_path not in declared and run_path not in EXPECTED_RECIPE_FILES:
            findings.append(
                Finding(
                    "GOOSE-RECIPES.md",
                    f"goose run path not in declared recipe files: {run_path}",
                )
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
    install = data.get("install") if isinstance(data, dict) else None
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
    for agent_path in agent_files:
        rel = str(agent_path.relative_to(root))
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
    for template in templates:
        rel = str(template.relative_to(root))
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
    return validate_against_schema(
        data, load_schema("dependabot-v2.schema.json"), path=rel
    )


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
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return findings + [Finding(rel, "CI workflow must define jobs mapping")]
    missing = sorted(REQUIRED_CI_JOBS - set(jobs))
    if missing:
        findings.append(Finding(rel, f"missing required CI job(s): {', '.join(missing)}"))
    manifest = jobs.get("manifest-validate")
    if isinstance(manifest, dict):
        steps = manifest.get("steps")
        step_blob = json.dumps(steps) if steps is not None else ""
        if "validate_manifests.py" not in step_blob:
            findings.append(
                Finding(rel, "manifest-validate job must run scripts/validate_manifests.py")
            )
        if "pytest" not in step_blob:
            findings.append(Finding(rel, "manifest-validate job must run pytest"))
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


VALIDATORS: dict[str, ValidatorFn] = {
    "schemas": validate_schemas_meta,
    "inventory": validate_packaging_inventory,
    "goose": validate_goose_recipes,
    "recipe-agents": validate_recipe_agent_bindings,
    "environment": validate_cursor_environment,
    "github-agents": validate_github_agents,
    "issue-templates": validate_issue_templates,
    "dependabot": validate_dependabot,
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

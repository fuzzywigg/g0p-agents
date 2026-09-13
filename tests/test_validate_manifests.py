"""Unit and integration tests for scripts/validate_manifests.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_manifests as vm  # noqa: E402, I001


MINIMAL_RECIPE = {
    "name": "example_recipe_workflow",
    "recipe": {
        "version": "1.0.0",
        "title": "Example",
        "settings": {
            "goose_provider": "anthropic",
            "goose_model": "claude-opus-4",
        },
        "instructions": "Do the thing.",
        "prompt": "STEP 1",
        "extensions": [{"type": "builtin", "name": "developer", "timeout": 30}],
    },
}

LOCKED_RECIPE = {
    "name": "quantum_algorithm_design_workflow",
    "recipe": {
        "version": "1.0.0",
        "title": "Design",
        "settings": {
            "goose_provider": "anthropic",
            "goose_model": "claude-opus-4",
        },
        "instructions": "You are QuantumArchitectAgent designing a circuit.",
        "prompt": "STEP 1 for QuantumArchitectAgent",
        "extensions": [{"type": "builtin", "name": "developer", "timeout": 30}],
    },
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _copy_schemas(tmp_path: Path) -> None:
    dest = tmp_path / "schemas"
    dest.mkdir(parents=True)
    for src in (REPO_ROOT / "schemas").glob("*"):
        (dest / src.name).write_bytes(src.read_bytes())


def _inventory_payload(**overrides: object) -> dict:
    payload = {
        "version": 3,
        "documented_agents": list(vm.DOCUMENTED_AGENTS),
        "expected_recipe_names": sorted(vm.EXPECTED_RECIPE_NAMES),
        "expected_recipe_files": list(vm.EXPECTED_RECIPE_FILES),
        "recipe_bindings": dict(vm.EXPECTED_RECIPE_BINDINGS),
        "recipe_primary_agents": dict(vm.RECIPE_PRIMARY_AGENT),
        "required_ci_jobs": sorted(vm.REQUIRED_CI_JOBS),
        "required_python_versions": list(vm.REQUIRED_PYTHON_VERSIONS),
        "required_manifest_step_markers": list(vm.REQUIRED_MANIFEST_STEP_MARKERS),
        "required_schema_files": list(vm.SCHEMA_FILES),
        "required_dev_packages": sorted(vm.REQUIRED_DEV_PACKAGES),
        "github_agent_files": list(vm.GITHUB_AGENT_FILES),
        "issue_template_files": list(vm.ISSUE_TEMPLATE_FILES),
        "pr_template_headings": list(vm.PR_TEMPLATE_HEADINGS),
        "historic_goose_settings": {
            "goose_provider": vm.HISTORIC_GOOSE_PROVIDER,
            "goose_model": vm.HISTORIC_GOOSE_MODEL,
            "extension_type": vm.HISTORIC_EXTENSION_TYPE,
            "extension_name": vm.HISTORIC_EXTENSION_NAME,
        },
        "min_coverage_fail_under": vm.MIN_COVERAGE_FAIL_UNDER,
        "min_validator_count": vm.MIN_VALIDATOR_COUNT,
        "required_paths": ["README.md"],
    }
    payload.update(overrides)
    return payload


def test_extract_fenced_yaml_ignores_indented_nested_fences() -> None:
    markdown = """# Doc

```yaml
name: outer_workflow
recipe:
  version: 1.0.0
  title: Outer
  settings:
    goose_provider: anthropic
    goose_model: claude
  instructions: |
    hello
  prompt: |
    ```markdown
    nested
    ```
  extensions:
    - type: builtin
      name: developer
```

done
"""
    blocks = vm.extract_fenced_yaml_blocks(markdown)
    assert len(blocks) == 1
    data = yaml.safe_load(blocks[0])
    assert data["name"] == "outer_workflow"
    assert "```markdown" in data["recipe"]["prompt"]


def test_extract_fenced_yaml_supports_yml_alias() -> None:
    markdown = "```yml\nname: a\n```\n"
    assert vm.extract_fenced_yaml_blocks(markdown) == ["name: a\n"]


def test_extract_fenced_yaml_multiple_blocks() -> None:
    markdown = "```yaml\na: 1\n```\n\n```yaml\nb: 2\n```\n"
    blocks = vm.extract_fenced_yaml_blocks(markdown)
    assert len(blocks) == 2
    assert yaml.safe_load(blocks[0]) == {"a": 1}
    assert yaml.safe_load(blocks[1]) == {"b": 2}


@pytest.mark.parametrize(
    ("payload", "expect_empty"),
    [
        (MINIMAL_RECIPE, True),
        ({"name": "bad", "recipe": {"version": "1.0.0"}}, False),
        (
            {
                **MINIMAL_RECIPE,
                "name": "BadName",
            },
            False,
        ),
        (
            {
                **json.loads(json.dumps(MINIMAL_RECIPE)),
                "recipe": {
                    **MINIMAL_RECIPE["recipe"],
                    "version": "1.0",
                },
            },
            False,
        ),
        (
            {
                **json.loads(json.dumps(MINIMAL_RECIPE)),
                "recipe": {
                    **MINIMAL_RECIPE["recipe"],
                    "extensions": [],
                },
            },
            False,
        ),
        (
            {
                **json.loads(json.dumps(MINIMAL_RECIPE)),
                "recipe": {
                    **MINIMAL_RECIPE["recipe"],
                    "extensions": [{"type": "unknown", "name": "x"}],
                },
            },
            False,
        ),
        (
            {
                **json.loads(json.dumps(MINIMAL_RECIPE)),
                "recipe": {
                    **MINIMAL_RECIPE["recipe"],
                    "extensions": [{"type": "stdio", "name": "custom", "timeout": 10}],
                },
            },
            True,
        ),
    ],
)
def test_goose_recipe_schema_matrix(payload: dict, expect_empty: bool) -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    findings = vm.validate_against_schema(payload, schema, path="fixture")
    assert (findings == []) is expect_empty


def test_goose_recipe_schema_rejects_missing_settings() -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    del bad["recipe"]["settings"]
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings
    assert any("settings" in f.message for f in findings)


def test_goose_recipe_schema_rejects_additional_top_level_keys() -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    bad["extra"] = True
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings


def test_goose_recipe_schema_rejects_timeout_overflow() -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    bad["recipe"]["extensions"][0]["timeout"] = 999999
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings


def test_cursor_environment_schema_requires_install() -> None:
    schema = vm.load_schema("cursor-environment.schema.json")
    findings = vm.validate_against_schema({"name": "x"}, schema, path="fixture")
    assert any("install" in f.message for f in findings)


def test_cursor_environment_schema_rejects_empty_terminals() -> None:
    schema = vm.load_schema("cursor-environment.schema.json")
    findings = vm.validate_against_schema(
        {"name": "x", "install": "true", "terminals": [""]},
        schema,
        path="fixture",
    )
    assert findings


def _write_locked_issue_templates(tmp_path: Path, *, body: str = "## Details\n") -> None:
    for rel in vm.ISSUE_TEMPLATE_FILES:
        name = Path(rel).name
        _write(
            tmp_path / ".github" / "ISSUE_TEMPLATE" / name,
            f"---\nname: {name}\nabout: Something\n---\n\n{body}",
        )


def test_github_agent_frontmatter_roundtrip(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "my-agent.agent.md").write_text(
        "---\nname: Demo\ndescription: A demo custom agent.\n---\n\n# Body\n",
        encoding="utf-8",
    )
    findings = vm.validate_github_agents(tmp_path)
    assert findings == []


def test_github_agent_frontmatter_rejects_missing_description(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "my-agent.agent.md").write_text(
        "---\nname: Bad\n---\n\n# Body\n", encoding="utf-8"
    )
    findings = vm.validate_github_agents(tmp_path)
    assert findings
    assert any("description" in f.message for f in findings)


def test_github_agent_rejects_empty_body(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "my-agent.agent.md").write_text(
        "---\nname: Empty\ndescription: No body.\n---\n\n",
        encoding="utf-8",
    )
    findings = vm.validate_github_agents(tmp_path)
    assert any("body after frontmatter is empty" in f.message for f in findings)


def test_github_agent_missing_directory(tmp_path: Path) -> None:
    findings = vm.validate_github_agents(tmp_path)
    assert any("directory missing" in f.message for f in findings)


def test_issue_template_schema_and_validator(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_locked_issue_templates(tmp_path)
    assert vm.validate_issue_templates(tmp_path) == []


def test_issue_template_rejects_missing_about(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_locked_issue_templates(tmp_path)
    bug = tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    bug.write_text("---\nname: Bug\n---\n\n## Problem\n", encoding="utf-8")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("about" in f.message for f in findings)


def test_issue_template_rejects_empty_body(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_locked_issue_templates(tmp_path, body="")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("body after frontmatter is empty" in f.message for f in findings)

def test_dependabot_schema_accepts_live_config() -> None:
    data = yaml.safe_load(
        (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    schema = vm.load_schema("dependabot-v2.schema.json")
    assert vm.validate_against_schema(data, schema, path="fixture") == []


def test_dependabot_schema_rejects_v1() -> None:
    schema = vm.load_schema("dependabot-v2.schema.json")
    findings = vm.validate_against_schema(
        {"version": 1, "updates": []}, schema, path="fixture"
    )
    assert findings


def test_dependabot_schema_rejects_unknown_ecosystem() -> None:
    schema = vm.load_schema("dependabot-v2.schema.json")
    findings = vm.validate_against_schema(
        {
            "version": 2,
            "updates": [
                {
                    "package-ecosystem": "not-real",
                    "directory": "/",
                    "schedule": {"interval": "weekly"},
                }
            ],
        },
        schema,
        path="fixture",
    )
    assert findings


def test_packaging_inventory_schema_and_live_paths() -> None:
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    schema = vm.load_schema("packaging-inventory.schema.json")
    assert vm.validate_against_schema(inventory, schema, path="fixture") == []
    assert vm.validate_packaging_inventory(REPO_ROOT) == []


def test_packaging_inventory_detects_missing_path(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    inventory = _inventory_payload(required_paths=["README.md", "DOES_NOT_EXIST.md"])
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    _write(tmp_path / "README.md", "# hi\n")
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("DOES_NOT_EXIST.md" in f.path for f in findings)


def test_packaging_inventory_lock_mismatch(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    inventory = _inventory_payload(
        documented_agents=[
            "QuantumArchitectAgent",
            "BlockchainArchitectAgent",
            "EdgeSecurityAgent",
            "InventedGhostAgent",
        ]
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    _write(tmp_path / "README.md", "# hi\n")
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("documented_agents" in f.message for f in findings)


def test_schemas_meta_validation_passes_on_live_repo() -> None:
    assert vm.validate_schemas_meta(REPO_ROOT) == []


def _minimal_schema_doc(name: str, **overrides: object) -> dict:
    payload: dict = {
        "$schema": vm.SCHEMA_DRAFT_URI,
        "$id": f"{vm.SCHEMA_ID_PREFIX}{name}",
        "type": "object",
    }
    payload.update(overrides)
    return payload


def test_schemas_meta_detects_invalid_schema(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    for name in vm.SCHEMA_FILES:
        if name == "goose-recipe.schema.json":
            (schemas / name).write_text(
                json.dumps(
                    _minimal_schema_doc(name, type="not-a-real-type"),
                ),
                encoding="utf-8",
            )
        else:
            (schemas / name).write_text(
                json.dumps(_minimal_schema_doc(name)),
                encoding="utf-8",
            )
    findings = vm.validate_schemas_meta(tmp_path)
    assert any("goose-recipe.schema.json" in f.path for f in findings)


def test_schemas_meta_detects_orphan_schema(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    (tmp_path / "schemas" / "invented.schema.json").write_text("{}", encoding="utf-8")
    findings = vm.validate_schemas_meta(tmp_path)
    assert any("orphan schema" in f.message for f in findings)


def test_documented_recipe_file_paths_parser() -> None:
    markdown = "**File**: `./agentic_flows/foo.yaml`\n**File**: `./agentic_flows/bar.yaml`\n"
    assert vm.documented_recipe_file_paths(markdown) == [
        "agentic_flows/foo.yaml",
        "agentic_flows/bar.yaml",
    ]


def test_agent_tokens_extracts_only_agent_suffix() -> None:
    text = "QuantumArchitectAgent and BlockchainArchitectAgent plus NotAnAgentWord"
    assert vm.agent_tokens(text) == {
        "QuantumArchitectAgent",
        "BlockchainArchitectAgent",
    }


def test_recipe_agent_bindings_reject_invented_agent(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    invented = json.loads(json.dumps(LOCKED_RECIPE))
    invented["recipe"]["instructions"] = "You are InventedGhostAgent doing things."
    block = yaml.safe_dump(invented, sort_keys=False)
    _write(tmp_path / "GOOSE-RECIPES.md", f"```yaml\n{block}```\n")
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert any("InventedGhostAgent" in f.message for f in findings)


def test_recipe_agent_bindings_require_primary_agent(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    missing_primary = json.loads(json.dumps(LOCKED_RECIPE))
    missing_primary["recipe"]["instructions"] = "No specialist named here."
    missing_primary["recipe"]["prompt"] = "Still none."
    block = yaml.safe_dump(missing_primary, sort_keys=False)
    _write(tmp_path / "GOOSE-RECIPES.md", f"```yaml\n{block}```\n")
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert any("primary agent missing" in f.message for f in findings)


def test_prompts_reject_invented_heading(tmp_path: Path) -> None:
    parts: list[str] = []
    for i, agent in enumerate(vm.DOCUMENTED_AGENTS, start=1):
        parts.append(f"## {i}. {agent} Prompt Template\n\n```markdown\n{agent} body\n```\n")
    parts.append(
        "## 5. InventedGhostAgent Prompt Template\n\n```markdown\nnope\n```\n"
    )
    _write(tmp_path / "AGENT-PROMPTS.md", "\n".join(parts))
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("InventedGhostAgent" in f.message for f in findings)


def test_cross_doc_agents_require_all_docs(tmp_path: Path) -> None:
    for rel in vm.REQUIRED_ARCHIVE_DOCS:
        text = "\n".join(vm.DOCUMENTED_AGENTS) + "\n"
        if rel == "README.md":
            text = text.replace("OrchestrationAgent", "MISSING")
        _write(tmp_path / rel, text)
    findings = vm.validate_cross_doc_agents(tmp_path)
    assert any(f.path == "README.md" for f in findings)


def test_environment_install_refs_must_exist(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / "README.md", "ok\n")
    env = {"name": "x", "install": "test -f README.md && test -f MISSING.md"}
    _write(tmp_path / ".cursor" / "environment.json", json.dumps(env))
    findings = vm.validate_cursor_environment(tmp_path)
    assert any("MISSING.md" in f.message for f in findings)


def test_ci_workflow_requires_jobs(tmp_path: Path) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "name: CI\njobs:\n  markdown-lint:\n    runs-on: ubuntu-latest\n",
    )
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("missing required CI job" in f.message for f in findings)


def test_ci_workflow_passes_on_live_repo() -> None:
    assert vm.validate_ci_workflow(REPO_ROOT) == []


def test_yaml_configs_reject_scalar_root(tmp_path: Path) -> None:
    for rel in vm.KNOWN_YAML_CONFIGS:
        _write(tmp_path / rel, "just-a-string\n")
    findings = vm.validate_yaml_configs(tmp_path)
    assert len(findings) == len(vm.KNOWN_YAML_CONFIGS)


def test_parse_yaml_text_reports_errors() -> None:
    data, findings = vm.parse_yaml_text(":\n  - bad", path="x.yml")
    assert data is None
    assert findings


def test_frontmatter_requires_closing_delimiter() -> None:
    text, findings = vm.extract_yaml_frontmatter("---\nname: x\n")
    assert text is None
    assert findings


def test_extract_frontmatter_body() -> None:
    body = vm.extract_frontmatter_body("---\nname: x\n---\n\n# Hello\n")
    assert body.strip() == "# Hello"
    assert vm.extract_frontmatter_body("no frontmatter\n") == "no frontmatter\n"
    assert vm.extract_frontmatter_body("---\nname: x\n") == ""


def test_run_all_validations_passes_on_live_repo() -> None:
    findings = vm.run_all_validations(REPO_ROOT)
    assert findings == [], "\n".join(str(f) for f in findings)


def test_run_all_validations_only_subset() -> None:
    findings = vm.run_all_validations(REPO_ROOT, only=["schemas", "inventory"])
    assert findings == []


def test_run_all_validations_rejects_unknown_only() -> None:
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["not-a-validator"])


def test_cli_main_exits_zero_on_live_repo() -> None:
    assert vm.main(["--root", str(REPO_ROOT)]) == 0


def test_cli_main_json_success() -> None:
    assert vm.main(["--root", str(REPO_ROOT), "--json"]) == 0


def test_cli_list_validators() -> None:
    assert vm.main(["--list-validators"]) == 0


def test_cli_main_fails_when_environment_missing(tmp_path: Path) -> None:
    (tmp_path / "GOOSE-RECIPES.md").write_text("# empty\n", encoding="utf-8")
    (tmp_path / "AGENT-PROMPTS.md").write_text("# none\n", encoding="utf-8")
    code = vm.main(["--root", str(tmp_path)])
    assert code == 1


def test_cli_only_goose_on_broken_tree(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    (tmp_path / "GOOSE-RECIPES.md").write_text("# no fences\n", encoding="utf-8")
    code = vm.main(["--root", str(tmp_path), "--only", "goose"])
    assert code == 1


def test_findings_to_json_roundtrip() -> None:
    payload = vm.findings_to_json([vm.Finding("a", "b")])
    assert json.loads(payload) == [{"path": "a", "message": "b"}]


def test_locked_constants_match_live_recipes() -> None:
    markdown = (REPO_ROOT / "GOOSE-RECIPES.md").read_text(encoding="utf-8")
    blocks = vm.extract_fenced_yaml_blocks(markdown)
    names = {yaml.safe_load(block)["name"] for block in blocks}
    assert names == vm.EXPECTED_RECIPE_NAMES
    declared = vm.documented_recipe_file_paths(markdown)
    assert tuple(declared) == vm.EXPECTED_RECIPE_FILES
    for name, file_path in zip(
        [yaml.safe_load(block)["name"] for block in blocks], declared, strict=True
    ):
        assert vm.EXPECTED_RECIPE_BINDINGS[name] == file_path


def test_no_on_disk_recipe_yaml_invented_yet() -> None:
    flows = REPO_ROOT / "agentic_flows"
    assert list(flows.glob("*.yaml")) + list(flows.glob("*.yml")) == []


def test_live_issue_templates_validate() -> None:
    assert vm.validate_issue_templates(REPO_ROOT) == []


def test_live_dependabot_validate() -> None:
    assert vm.validate_dependabot(REPO_ROOT) == []


def test_live_markdownlint_validate() -> None:
    assert vm.validate_markdownlint(REPO_ROOT) == []


def test_live_scratchpad_validate() -> None:
    assert vm.validate_scratchpad(REPO_ROOT) == []


def test_live_pyproject_validate() -> None:
    assert vm.validate_pyproject(REPO_ROOT) == []


def test_live_recipe_agent_bindings() -> None:
    assert vm.validate_recipe_agent_bindings(REPO_ROOT) == []


def test_live_cross_doc_agents() -> None:
    assert vm.validate_cross_doc_agents(REPO_ROOT) == []


def test_live_prompts() -> None:
    assert vm.validate_documented_agent_prompts(REPO_ROOT) == []


def test_validators_registry_covers_all_checks() -> None:
    expected = {
        "schemas",
        "inventory",
        "goose",
        "recipe-agents",
        "agent-tokens",
        "environment",
        "github-agents",
        "issue-templates",
        "pr-template",
        "dependabot",
        "markdownlint",
        "requirements-dev",
        "license",
        "readme",
        "scratchpad",
        "pyproject",
        "yaml-configs",
        "ci",
        "prompts",
        "cross-docs",
    }
    assert set(vm.VALIDATORS) == expected
    assert len(vm.VALIDATORS) >= vm.MIN_VALIDATOR_COUNT


def test_frontmatter_crlf_opening() -> None:
    text, findings = vm.extract_yaml_frontmatter("---\r\nname: x\r\n---\r\n\r\nbody\n")
    assert findings == []
    assert text is not None
    assert "name: x" in text


def test_frontmatter_missing_opening() -> None:
    text, findings = vm.extract_yaml_frontmatter("name: x\n---\n")
    assert text is None
    assert any("opening" in f.message for f in findings)


def test_documented_recipe_file_paths_skips_unquoted() -> None:
    markdown = "**File**: ./agentic_flows/foo.yaml\n"
    assert vm.documented_recipe_file_paths(markdown) == []


def test_schemas_meta_missing_directory(tmp_path: Path) -> None:
    findings = vm.validate_schemas_meta(tmp_path)
    assert any("schemas directory missing" in f.message for f in findings)


def test_schemas_meta_missing_and_invalid_json(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    for name in vm.SCHEMA_FILES:
        if name == "goose-recipe.schema.json":
            (schemas / name).write_text("{not-json", encoding="utf-8")
        elif name == "cursor-environment.schema.json":
            continue  # missing file
        else:
            (schemas / name).write_text("{}", encoding="utf-8")
    findings = vm.validate_schemas_meta(tmp_path)
    assert any("required schema file missing" in f.message for f in findings)
    assert any("JSON parse error" in f.message for f in findings)


def test_packaging_inventory_missing_file(tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir()
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("packaging inventory missing" in f.message for f in findings)


def test_packaging_inventory_bad_json(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "packaging-inventory.json").write_text("{bad", encoding="utf-8")
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("JSON parse error" in f.message for f in findings)


def test_packaging_inventory_schema_failure(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "packaging-inventory.json").write_text(
        json.dumps({"version": 1}), encoding="utf-8"
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings
    assert all(f.path == "schemas/packaging-inventory.json" for f in findings)


def test_goose_recipes_missing_doc(tmp_path: Path) -> None:
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("required documentation file is missing" in f.message for f in findings)


def test_goose_recipes_parse_and_inventory_errors(tmp_path: Path) -> None:
    recipe_a = json.loads(json.dumps(LOCKED_RECIPE))
    recipe_c = json.loads(json.dumps(LOCKED_RECIPE))
    recipe_c["name"] = "invented_extra_workflow"
    blocks = [
        ":\n  -",
        "- just-a-list\n",
        yaml.safe_dump(recipe_a, sort_keys=False),
        yaml.safe_dump(recipe_c, sort_keys=False),
    ]
    body = "\n\n".join(f"```yaml\n{block}```" for block in blocks)
    body += "\n\n**File**: `./agentic_flows/only_one.yaml`\n"
    body += "\ngoose run ./agentic_flows/totally_wrong.yaml\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    flows = tmp_path / "agentic_flows"
    flows.mkdir()
    (flows / "broken.yaml").write_text(":\n", encoding="utf-8")
    (flows / "ok.yaml").write_text(yaml.safe_dump(MINIMAL_RECIPE), encoding="utf-8")
    findings = vm.validate_goose_recipes(tmp_path)
    messages = [f.message for f in findings]
    assert findings
    assert any("invented" in msg or "missing locked" in msg for msg in messages)
    assert any(
        "do not match recipe fences" in msg or "locked recipe file inventory" in msg
        for msg in messages
    )
    assert any("goose run path" in msg for msg in messages)


def test_goose_recipes_binding_mismatch(tmp_path: Path) -> None:
    recipes = []
    for name in sorted(vm.EXPECTED_RECIPE_NAMES):
        recipe = json.loads(json.dumps(LOCKED_RECIPE))
        recipe["name"] = name
        recipes.append(yaml.safe_dump(recipe, sort_keys=False))
    # Intentionally swap first two file declarations vs names order.
    files = list(vm.EXPECTED_RECIPE_FILES)
    files[0], files[1] = files[1], files[0]
    body = "\n\n".join(f"```yaml\n{block}```" for block in recipes)
    for rel in files:
        body += f"\n**File**: `./{rel}`\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("must bind to" in f.message or "locked recipe file" in f.message for f in findings)


def test_recipe_agent_bindings_missing_doc(tmp_path: Path) -> None:
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert any("required documentation file is missing" in f.message for f in findings)


def test_environment_missing_and_bad_json(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_cursor_environment(tmp_path))
    _write(tmp_path / ".cursor" / "environment.json", "{bad")
    findings = vm.validate_cursor_environment(tmp_path)
    assert any("JSON parse error" in f.message for f in findings)


def test_github_agents_empty_and_bad_frontmatter(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    assert any("no *.agent.md" in f.message for f in vm.validate_github_agents(tmp_path))
    _write(agents / "invented.agent.md", "# no frontmatter\n")
    findings = vm.validate_github_agents(tmp_path)
    assert any("unexpected/invented" in f.message for f in findings)
    _write(agents / "my-agent.agent.md", "---\n:\n---\n\n# x\n")
    findings = vm.validate_github_agents(tmp_path)
    assert findings


def test_issue_templates_empty_and_bad(tmp_path: Path) -> None:
    assert any("directory missing" in f.message for f in vm.validate_issue_templates(tmp_path))
    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    assert any("no issue template" in f.message for f in vm.validate_issue_templates(tmp_path))
    _write(templates / "extra.md", "# nofm\n")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("unexpected issue template" in f.message for f in findings)
    _write_locked_issue_templates(tmp_path)
    bug = templates / "bug_report.md"
    bug.write_text("---\n:\n---\n\n# x\n", encoding="utf-8")
    assert vm.validate_issue_templates(tmp_path)


def test_dependabot_missing_empty_and_invalid(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_dependabot(tmp_path))
    _write(tmp_path / ".github" / "dependabot.yml", "")
    assert any("empty" in f.message for f in vm.validate_dependabot(tmp_path))
    _write(tmp_path / ".github" / "dependabot.yml", "version: 2\n")
    assert vm.validate_dependabot(tmp_path)


def test_dependabot_requires_pip_ecosystem(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".github" / "dependabot.yml",
        "\n".join(
            [
                "version: 2",
                "updates:",
                '  - package-ecosystem: "github-actions"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                "",
            ]
        ),
    )
    findings = vm.validate_dependabot(tmp_path)
    assert any("pip" in f.message for f in findings)


def test_markdownlint_validator_paths(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_markdownlint(tmp_path))
    _copy_schemas(tmp_path)
    _write(tmp_path / ".markdownlint.yaml", "")
    assert any("empty" in f.message for f in vm.validate_markdownlint(tmp_path))
    _write(tmp_path / ".markdownlint.yaml", "MD013: false\n")
    findings = vm.validate_markdownlint(tmp_path)
    assert any("default" in f.message for f in findings)


def test_scratchpad_validator_paths(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_scratchpad(tmp_path))
    _write(tmp_path / "agentic_flows" / "scratchpad.txt", "   \n")
    assert any("empty" in f.message for f in vm.validate_scratchpad(tmp_path))
    _write(tmp_path / "agentic_flows" / "scratchpad.txt", "coordination notes only\n")
    findings = vm.validate_scratchpad(tmp_path)
    assert any("identifying header" in f.message for f in findings)
    assert any("checkbox" in f.message for f in findings)


def test_pyproject_validator_paths(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_pyproject(tmp_path))
    _write(tmp_path / "pyproject.toml", "not = [toml")
    assert any("TOML parse error" in f.message for f in vm.validate_pyproject(tmp_path))
    _write(tmp_path / "pyproject.toml", "[project]\nname = 'x'\n")
    findings = vm.validate_pyproject(tmp_path)
    assert any("[tool]" in f.message for f in findings)
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.report]",
                "fail_under = 10",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("fail_under must be >=" in f.message for f in findings)


def test_yaml_configs_missing(tmp_path: Path) -> None:
    findings = vm.validate_yaml_configs(tmp_path)
    assert len(findings) == len(vm.KNOWN_YAML_CONFIGS)


def test_ci_workflow_error_paths(tmp_path: Path) -> None:
    assert any("CI workflow missing" in f.message for f in vm.validate_ci_workflow(tmp_path))
    _write(tmp_path / ".github" / "workflows" / "ci.yml", ":\n")
    assert any("YAML parse error" in f.message for f in vm.validate_ci_workflow(tmp_path))
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "- just-a-list\n")
    assert any("mapping" in f.message for f in vm.validate_ci_workflow(tmp_path))
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\njobs: []\n")
    assert any("jobs mapping" in f.message for f in vm.validate_ci_workflow(tmp_path))
    ci_yaml = "\n".join(
        [
            "name: CI",
            "jobs:",
            "  markdown-lint: {}",
            "  link-check: {}",
            "  actionlint: {}",
            "  manifest-validate:",
            "    steps:",
            "      - run: echo hi",
            "",
        ]
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", ci_yaml)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("validate_manifests.py" in f.message for f in findings)
    assert any("pytest" in f.message for f in findings)
    assert any("ruff" in f.message for f in findings)
    assert any("--cov" in f.message for f in findings)
    assert any("Python version matrix" in f.message for f in findings)


def test_prompts_missing_file_and_agent_token(tmp_path: Path) -> None:
    prompts = vm.validate_documented_agent_prompts(tmp_path)
    assert any("missing" in f.message for f in prompts)
    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "## 1. QuantumArchitectAgent Prompt Template\n\nonly one\n",
    )
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("documented agent missing" in f.message for f in findings)
    assert any("missing prompt template heading" in f.message for f in findings)


def test_cross_doc_missing_file(tmp_path: Path) -> None:
    findings = vm.validate_cross_doc_agents(tmp_path)
    assert any("required documentation file is missing" in f.message for f in findings)


def test_cli_json_failure_emits_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = vm.main(["--root", str(tmp_path), "--json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload


def test_goose_recipes_duplicate_names(tmp_path: Path) -> None:
    recipes = []
    for name in (
        "quantum_algorithm_design_workflow",
        "quantum_algorithm_design_workflow",
        "blockchain_contract_design_workflow",
        "edge_security_implementation_workflow",
    ):
        recipe = json.loads(json.dumps(LOCKED_RECIPE))
        recipe["name"] = name
        recipes.append(yaml.safe_dump(recipe, sort_keys=False))
    body = "\n\n".join(f"```yaml\n{block}```" for block in recipes)
    for rel in vm.EXPECTED_RECIPE_FILES:
        body += f"\n**File**: `./{rel}`\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("duplicate recipe name" in f.message for f in findings)


def test_dependabot_yaml_parse_error(tmp_path: Path) -> None:
    _write(tmp_path / ".github" / "dependabot.yml", ":\n  -")
    findings = vm.validate_dependabot(tmp_path)
    assert any("YAML parse error" in f.message for f in findings)


def test_yaml_configs_parse_error(tmp_path: Path) -> None:
    for rel in vm.KNOWN_YAML_CONFIGS:
        _write(tmp_path / rel, ":\n")
    findings = vm.validate_yaml_configs(tmp_path)
    assert any("YAML parse error" in f.message for f in findings)


def test_markdownlint_yaml_parse_error(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / ".markdownlint.yaml", ":\n")
    findings = vm.validate_markdownlint(tmp_path)
    assert any("YAML parse error" in f.message for f in findings)


def test_packaging_inventory_lock_recipe_and_ci_mismatches(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / "README.md", "# hi\n")

    names = _inventory_payload(
        expected_recipe_names=[
            "quantum_algorithm_design_workflow",
            "blockchain_contract_design_workflow",
            "edge_security_implementation_workflow",
            "invented_extra_workflow",
        ]
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(names), encoding="utf-8"
    )
    assert any(
        "expected_recipe_names" in f.message
        for f in vm.validate_packaging_inventory(tmp_path)
    )

    files = _inventory_payload(
        expected_recipe_files=[
            "agentic_flows/quantum_algorithm_design.yaml",
            "agentic_flows/blockchain_contract_design.yaml",
            "agentic_flows/edge_security_implementation.yaml",
            "agentic_flows/invented.yaml",
        ]
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(files), encoding="utf-8"
    )
    assert any(
        "expected_recipe_files" in f.message
        for f in vm.validate_packaging_inventory(tmp_path)
    )

    jobs = _inventory_payload(required_ci_jobs=["markdown-lint", "link-check"])
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(jobs), encoding="utf-8"
    )
    # Schema requires minItems but unique set mismatch still caught after schema if valid;
    # use a schema-valid but lock-mismatched set.
    jobs = _inventory_payload(
        required_ci_jobs=[
            "markdown-lint",
            "link-check",
            "actionlint",
            "invented-job",
        ]
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(jobs), encoding="utf-8"
    )
    assert any(
        "required_ci_jobs" in f.message for f in vm.validate_packaging_inventory(tmp_path)
    )


def test_goose_recipes_non_mapping_and_missing_names(tmp_path: Path) -> None:
    blocks = ["- just-a-list\n"] * 4
    body = "\n\n".join(f"```yaml\n{block}```" for block in blocks)
    for rel in vm.EXPECTED_RECIPE_FILES:
        body += f"\n**File**: `./{rel}`\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("must be a mapping" in f.message for f in findings)


def test_recipe_agent_bindings_skips_incomplete_recipe(tmp_path: Path) -> None:
    body = "```yaml\nname: quantum_algorithm_design_workflow\nrecipe: not-a-map\n```\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert findings == [] or all("primary agent" not in f.message for f in findings)


def test_environment_install_non_string(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    # Bypass schema by writing invalid then... schema rejects non-string install.
    # Cover branch where install is missing type after schema soft-pass is impossible;
    # instead assert schema finding for wrong type.
    env = {"name": "x", "install": 123}
    _write(tmp_path / ".cursor" / "environment.json", json.dumps(env))
    findings = vm.validate_cursor_environment(tmp_path)
    assert findings


def test_pyproject_missing_sections(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool]",
                "[tool.coverage]",
                "source = ['scripts']",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("pytest.ini_options" in f.message for f in findings)
    assert any("[tool.ruff]" in f.message for f in findings)
    assert any("[tool.coverage]" in f.message or "fail_under" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.run]",
                'source = ["scripts"]',
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("fail_under" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.report]",
                "fail_under = 50",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("fail_under must be >=" in f.message for f in findings)


def _ci_yaml_with_matrix(versions: list[str], *, markers: list[str] | None = None) -> str:
    step_markers = markers or [
        "pip check",
        "ruff check scripts tests",
        "python scripts/validate_manifests.py --list-validators",
        "python scripts/validate_manifests.py",
        "python -m pytest --cov=scripts",
        "actions/upload-artifact@v4",
    ]
    version_lines = "\n".join(f'          - "{v}"' for v in versions)
    step_lines = "\n".join(f"      - run: {marker}" for marker in step_markers)
    return "\n".join(
        [
            "name: CI",
            "on:",
            "  push: {}",
            "concurrency:",
            "  group: ci-test",
            "jobs:",
            "  markdown-lint: {}",
            "  link-check: {}",
            "  actionlint: {}",
            "  manifest-validate:",
            "    strategy:",
            "      matrix:",
            "        python-version:",
            version_lines,
            "    steps:",
            step_lines,
            "",
        ]
    )


def test_ci_workflow_matrix_too_small(tmp_path: Path) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        _ci_yaml_with_matrix(["3.12"]),
    )
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("at least 2 versions" in f.message for f in findings)


def test_ci_workflow_matrix_must_match_locked_versions(tmp_path: Path) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        _ci_yaml_with_matrix(["3.11", "3.12", "3.14"]),
    )
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("must equal" in f.message for f in findings)


def test_ci_workflow_requires_concurrency_and_markers(tmp_path: Path) -> None:
    ci_yaml = "\n".join(
        [
            "name: CI",
            "on:",
            "  push: {}",
            "jobs:",
            "  markdown-lint: {}",
            "  link-check: {}",
            "  actionlint: {}",
            "  manifest-validate:",
            "    strategy:",
            "      matrix:",
            '        python-version: ["3.11", "3.12", "3.13"]',
            "    steps:",
            "      - run: python scripts/validate_manifests.py",
            "",
        ]
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", ci_yaml)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("concurrency.group" in f.message for f in findings)
    assert any("pip check" in f.message for f in findings)
    assert any("upload validation artifacts" in f.message for f in findings)


def _four_locked_recipe_doc(
    *, settings_override: dict | None = None, drop_extension: bool = False
) -> str:
    blocks: list[str] = []
    for name, primary in vm.RECIPE_PRIMARY_AGENT.items():
        recipe = json.loads(json.dumps(LOCKED_RECIPE))
        recipe["name"] = name
        recipe["recipe"]["instructions"] = f"You are {primary}."
        recipe["recipe"]["prompt"] = f"STEP for {primary}"
        if settings_override is not None:
            recipe["recipe"]["settings"].update(settings_override)
        if drop_extension:
            recipe["recipe"]["extensions"] = [{"type": "stdio", "name": "other"}]
        blocks.append(yaml.safe_dump(recipe, sort_keys=False))
    body = "\n\n".join(f"```yaml\n{block}```" for block in blocks)
    for rel in vm.EXPECTED_RECIPE_FILES:
        body += f"\n**File**: `./{rel}`\n"
        body += f"\ngoose run ./{rel}\n"
    return body


def test_schemas_meta_rejects_wrong_draft_and_non_mapping(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    for name in vm.SCHEMA_FILES:
        if name == "goose-recipe.schema.json":
            (schemas / name).write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        else:
            bad = _minimal_schema_doc(name)
            bad["$schema"] = "https://example.com/wrong"
            bad["$id"] = "wrong-id"
            (schemas / name).write_text(json.dumps(bad), encoding="utf-8")
    findings = vm.validate_schemas_meta(tmp_path)
    assert any("schema root must be a mapping" in f.message for f in findings)
    assert any("$schema must be" in f.message for f in findings)
    assert any("$id must be" in f.message for f in findings)


def test_packaging_inventory_v3_lock_fields(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / "README.md", "# hi\n")

    bad_bindings = dict(vm.EXPECTED_RECIPE_BINDINGS)
    bad_bindings["quantum_algorithm_design_workflow"] = "agentic_flows/wrong.yaml"
    bad_primaries = dict(vm.RECIPE_PRIMARY_AGENT)
    bad_primaries["quantum_algorithm_design_workflow"] = "EdgeSecurityAgent"
    cases = [
        ("recipe_bindings", bad_bindings),
        ("recipe_primary_agents", bad_primaries),
        ("required_python_versions", ["3.11", "3.12"]),
        (
            "required_manifest_step_markers",
            list(vm.REQUIRED_MANIFEST_STEP_MARKERS)[:-1] + ["invented"],
        ),
        (
            "required_schema_files",
            list(vm.SCHEMA_FILES)[:-1] + ["invented.schema.json"],
        ),
        (
            "required_dev_packages",
            ["jsonschema", "PyYAML", "pytest", "pytest-cov", "invented"],
        ),
        ("github_agent_files", [".github/agents/other.agent.md"]),
        (
            "issue_template_files",
            list(vm.ISSUE_TEMPLATE_FILES)[:-1]
            + [".github/ISSUE_TEMPLATE/extra.md"],
        ),
        (
            "pr_template_headings",
            list(vm.PR_TEMPLATE_HEADINGS)[:-1] + ["Invented"],
        ),
        (
            "historic_goose_settings",
            {
                "goose_provider": "openai",
                "goose_model": vm.HISTORIC_GOOSE_MODEL,
                "extension_type": vm.HISTORIC_EXTENSION_TYPE,
                "extension_name": vm.HISTORIC_EXTENSION_NAME,
            },
        ),
        ("min_coverage_fail_under", 90),
        ("min_validator_count", 999),
    ]
    for field, value in cases:
        inventory = _inventory_payload(**{field: value})
        (tmp_path / "schemas" / "packaging-inventory.json").write_text(
            json.dumps(inventory), encoding="utf-8"
        )
        findings = vm.validate_packaging_inventory(tmp_path)
        assert any(field in f.message for f in findings), field


def test_historic_goose_settings_and_extension_lock(tmp_path: Path) -> None:
    _write(
        tmp_path / "GOOSE-RECIPES.md",
        _four_locked_recipe_doc(settings_override={"goose_provider": "openai"}),
    )
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("goose_provider" in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        _four_locked_recipe_doc(settings_override={"goose_model": "gpt-x"}),
    )
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("goose_model" in f.message for f in findings)

    _write(tmp_path / "GOOSE-RECIPES.md", _four_locked_recipe_doc(drop_extension=True))
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("historic" in f.message and "extension" in f.message for f in findings)


def test_goose_rejects_orphan_ondisk_and_missing_runs(tmp_path: Path) -> None:
    body = _four_locked_recipe_doc()
    # Strip goose run lines
    body = "\n".join(line for line in body.splitlines() if "goose run" not in line) + "\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    flows = tmp_path / "agentic_flows"
    flows.mkdir()
    (flows / "invented_extra.yaml").write_text("name: x\n", encoding="utf-8")
    recipe = json.loads(json.dumps(LOCKED_RECIPE))
    recipe["name"] = "quantum_algorithm_design_workflow"
    (flows / "quantum_algorithm_design.yaml").write_text(
        yaml.safe_dump(recipe), encoding="utf-8"
    )
    # Wrong binding: put blockchain name into quantum file path already set;
    # add blockchain file with mismatched name.
    wrong = json.loads(json.dumps(LOCKED_RECIPE))
    wrong["name"] = "quantum_algorithm_design_workflow"
    (flows / "blockchain_contract_design.yaml").write_text(
        yaml.safe_dump(wrong), encoding="utf-8"
    )
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("unexpected/invented on-disk" in f.message for f in findings)
    assert any("missing goose run example" in f.message for f in findings)
    assert any("must live at" in f.message for f in findings)


def test_archive_agent_tokens_rejects_invented(tmp_path: Path) -> None:
    for rel in vm.AGENT_TOKEN_SCAN_DOCS:
        text = "\n".join(vm.DOCUMENTED_AGENTS) + "\n"
        if rel == "README.md":
            text += "InventedGhostAgent\n"
        _write(tmp_path / rel, text)
    findings = vm.validate_archive_agent_tokens(tmp_path)
    assert any("InventedGhostAgent" in f.message for f in findings)


def test_archive_agent_tokens_missing_doc(tmp_path: Path) -> None:
    findings = vm.validate_archive_agent_tokens(tmp_path)
    assert any("required documentation file is missing" in f.message for f in findings)


def test_pr_template_validator(tmp_path: Path) -> None:
    assert any("PR template missing" in f.message for f in vm.validate_pr_template(tmp_path))
    _write(tmp_path / ".github" / "pull_request_template.md", "# Only Summary\n")
    findings = vm.validate_pr_template(tmp_path)
    assert any("missing required heading" in f.message for f in findings)
    assert vm.validate_pr_template(REPO_ROOT) == []


def test_requirements_dev_validator(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_requirements_dev(tmp_path))
    _write(tmp_path / "requirements-dev.txt", "jsonschema>=4\n# comment\n")
    findings = vm.validate_requirements_dev(tmp_path)
    assert any("missing required dev package" in f.message for f in findings)
    assert vm.validate_requirements_dev(REPO_ROOT) == []


def test_license_and_readme_validators(tmp_path: Path) -> None:
    assert any("LICENSE missing" in f.message for f in vm.validate_license(tmp_path))
    _write(tmp_path / "LICENSE", "Proprietary\n")
    findings = vm.validate_license(tmp_path)
    assert any("MIT" in f.message for f in findings)
    _write(tmp_path / "LICENSE", "MIT License\nPermission is hereby granted\n")
    findings = vm.validate_license(tmp_path)
    assert any("2026" in f.message for f in findings)
    assert vm.validate_license(REPO_ROOT) == []

    assert any("README.md missing" in f.message for f in vm.validate_readme_packaging(tmp_path))
    _write(tmp_path / "README.md", "# hi\n")
    findings = vm.validate_readme_packaging(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert vm.validate_readme_packaging(REPO_ROOT) == []


def test_live_new_validators() -> None:
    assert vm.validate_archive_agent_tokens(REPO_ROOT) == []
    assert vm.validate_pr_template(REPO_ROOT) == []
    assert vm.validate_requirements_dev(REPO_ROOT) == []
    assert vm.validate_license(REPO_ROOT) == []
    assert vm.validate_readme_packaging(REPO_ROOT) == []


def test_environment_non_mapping_root(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / ".cursor" / "environment.json", json.dumps([1, 2]))
    findings = vm.validate_cursor_environment(tmp_path)
    assert any("mapping" in f.message for f in findings)


def test_dependabot_updates_must_be_list(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    # Schema requires array; craft a case that passes schema is hard.
    # Cover parse of non-dict root via schema failure path already exists.
    # Force post-schema branch by monkeypatching validate_against_schema.
    original = vm.validate_against_schema

    def _ok(instance, schema, *, path):  # noqa: ANN001
        return []

    vm.validate_against_schema = _ok  # type: ignore[assignment]
    try:
        _write(tmp_path / ".github" / "dependabot.yml", "version: 2\nupdates: {}\n")
        findings = vm.validate_dependabot(tmp_path)
        assert any("updates must be a list" in f.message for f in findings)
        _write(tmp_path / ".github" / "dependabot.yml", "- just\n")
        findings = vm.validate_dependabot(tmp_path)
        assert any("mapping" in f.message for f in findings)
    finally:
        vm.validate_against_schema = original  # type: ignore[assignment]


def test_ci_workflow_missing_on_trigger(tmp_path: Path) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS)).replace("on:\n  push: {}\n", ""),
    )
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("on: trigger" in f.message for f in findings)


def test_prompts_require_markdown_fences(tmp_path: Path) -> None:
    body = "\n".join(
        f"## {i}. {agent} Prompt Template\n\n{agent} body\n"
        for i, agent in enumerate(vm.DOCUMENTED_AGENTS, start=1)
    )
    _write(tmp_path / "AGENT-PROMPTS.md", body)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("markdown prompt fences" in f.message for f in findings)


def test_extract_fenced_markdown_blocks() -> None:
    text = "```markdown\none\n```\n\n```markdown\ntwo\n```\n"
    assert vm.extract_fenced_markdown_blocks(text) == ["one\n", "two\n"]


def test_ondisk_recipe_non_mapping(tmp_path: Path) -> None:
    body = _four_locked_recipe_doc()
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    flows = tmp_path / "agentic_flows"
    flows.mkdir()
    (flows / "quantum_algorithm_design.yaml").write_text("- list\n", encoding="utf-8")
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("must be a mapping" in f.message for f in findings)


def test_github_agent_and_issue_missing_required_files(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    _write(agents / "my-agent.agent.md", "---\nname: X\ndescription: Y\n---\n\n# Body\n")
    # Remove required by writing only invented after deleting? already has required.
    # Missing required: empty expected set relative — create dir with wrong name only.
    for path in agents.glob("*.agent.md"):
        path.unlink()
    _write(agents / "other.agent.md", "---\nname: X\ndescription: Y\n---\n\n# Body\n")
    findings = vm.validate_github_agents(tmp_path)
    assert any("required GitHub agent packaging file missing" in f.message for f in findings)

    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    _write(templates / "only.md", "---\nname: X\nabout: Y\n---\n\nbody\n")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("required issue template file missing" in f.message for f in findings)


def test_pyproject_missing_coverage_table(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("missing [tool.coverage]" in f.message for f in findings)

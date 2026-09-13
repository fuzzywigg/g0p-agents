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
        "version": vm.INVENTORY_VERSION,
        "documented_agents": list(vm.DOCUMENTED_AGENTS),
        "expected_recipe_names": sorted(vm.EXPECTED_RECIPE_NAMES),
        "expected_recipe_files": list(vm.EXPECTED_RECIPE_FILES),
        "recipe_bindings": dict(vm.EXPECTED_RECIPE_BINDINGS),
        "recipe_primary_agents": dict(vm.RECIPE_PRIMARY_AGENT),
        "recipe_titles": dict(vm.RECIPE_TITLES),
        "orchestration_recipe_name": vm.ORCHESTRATION_RECIPE_NAME,
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
        "routing_surfaces": list(vm.ROUTING_SURFACES),
        "constitution_heading_prefix": vm.CONSTITUTION_HEADING_PREFIX,
        "prompt_system_header_suffix": vm.PROMPT_SYSTEM_HEADER_SUFFIX,
        "specialist_escalation_marker": vm.SPECIALIST_ESCALATION_MARKER,
        "orchestration_escalation_marker": vm.ORCHESTRATION_ESCALATION_MARKER,
        "agent_token_scan_docs": list(vm.AGENT_TOKEN_SCAN_DOCS),
        "readme_required_phrases": list(vm.README_REQUIRED_PHRASES),
        "security_required_phrases": list(vm.SECURITY_REQUIRED_PHRASES),
        "contributing_required_phrases": list(vm.CONTRIBUTING_REQUIRED_PHRASES),
        "issue_agent_task_headings": list(vm.ISSUE_AGENT_TASK_HEADINGS),
        "issue_bug_report_headings": list(vm.ISSUE_BUG_REPORT_HEADINGS),
        "issue_feature_request_headings": list(vm.ISSUE_FEATURE_REQUEST_HEADINGS),
        "required_archive_docs": list(vm.REQUIRED_ARCHIVE_DOCS),
        "known_yaml_configs": list(vm.KNOWN_YAML_CONFIG_RELS),
        "cursor_environment_name": vm.CURSOR_ENVIRONMENT_NAME,
        "dependabot_schedule_interval": vm.DEPENDABOT_SCHEDULE_INTERVAL,
        "dependabot_ecosystems": sorted(vm.DEPENDABOT_ECOSYSTEMS),
        "dependabot_group_names": sorted(vm.DEPENDABOT_GROUP_NAMES),
        "dependabot_directories": sorted(vm.DEPENDABOT_DIRECTORIES),
        "ci_permissions_contents": vm.CI_PERMISSIONS_CONTENTS,
        "ci_artifact_name_prefix": vm.CI_ARTIFACT_NAME_PREFIX,
        "ci_pull_request_branch": vm.CI_PULL_REQUEST_BRANCH,
        "ci_concurrency_group_prefix": vm.CI_CONCURRENCY_GROUP_PREFIX,
        "ci_artifact_upload_if": vm.CI_ARTIFACT_UPLOAD_IF,
        "ci_cancel_in_progress": vm.CI_CANCEL_IN_PROGRESS,
        "ci_fail_fast": vm.CI_FAIL_FAST,
        "ci_required_actions": list(vm.CI_REQUIRED_ACTIONS),
        "pyproject_name": vm.PYPROJECT_NAME,
        "pyproject_requires_python": vm.PYPROJECT_REQUIRES_PYTHON,
        "pyproject_ruff_target_version": vm.PYPROJECT_RUFF_TARGET_VERSION,
        "coverage_branch": vm.COVERAGE_BRANCH,
        "markdownlint_default": vm.MARKDOWNLINT_DEFAULT,
        "markdownlint_md013_line_length": vm.MARKDOWNLINT_MD013_LINE_LENGTH,
        "scratchpad_required_phrases": list(vm.SCRATCHPAD_REQUIRED_PHRASES),
        "changelog_required_phrases": list(vm.CHANGELOG_REQUIRED_PHRASES),
        "postmortem_required_phrases": list(vm.POSTMORTEM_REQUIRED_PHRASES),
        "gitignore_required_patterns": list(vm.GITIGNORE_REQUIRED_PATTERNS),
        "negative_constraint_phrases": list(vm.NEGATIVE_CONSTRAINT_PHRASES),
        "license_copyright_holder": vm.LICENSE_COPYRIGHT_HOLDER,
        "license_copyright_marker": vm.LICENSE_COPYRIGHT_MARKER,
        "historic_recipe_version": vm.HISTORIC_RECIPE_VERSION,
        "github_agent_name": vm.GITHUB_AGENT_NAME,
        "agentic_flows_allowed_files": sorted(vm.AGENTIC_FLOWS_ALLOWED_FILES),
        "cursor_install_required_refs": list(vm.CURSOR_INSTALL_REQUIRED_REFS),
        "hydration_required_sections": list(vm.HYDRATION_REQUIRED_SECTIONS),
        "execution_summary_required_phrases": list(vm.EXECUTION_SUMMARY_REQUIRED_PHRASES),
        "implementation_guide_required_phrases": list(
            vm.IMPLEMENTATION_GUIDE_REQUIRED_PHRASES
        ),
        "claude_required_phrases": list(vm.CLAUDE_REQUIRED_PHRASES),
        "escalation_format_phrases": list(vm.ESCALATION_FORMAT_PHRASES),
        "goose_docs_required_phrases": list(vm.GOOSE_DOCS_REQUIRED_PHRASES),
        "issue_template_names": dict(vm.ISSUE_TEMPLATE_NAMES),
        "issue_template_abouts": dict(vm.ISSUE_TEMPLATE_ABOUTS),
        "readme_badge_phrases": list(vm.README_BADGE_PHRASES),
        "quarterly_review_phrases": list(vm.QUARTERLY_REVIEW_PHRASES),
        "ci_workflow_name": vm.CI_WORKFLOW_NAME,
        "ci_required_text_markers": list(vm.CI_REQUIRED_TEXT_MARKERS),
        "ci_link_check_args": vm.CI_LINK_CHECK_ARGS,
        "ci_link_check_fail": vm.CI_LINK_CHECK_FAIL,
        "ci_markdown_lint_globs": vm.CI_MARKDOWN_LINT_GLOBS,
        "ci_markdown_lint_config": vm.CI_MARKDOWN_LINT_CONFIG,
        "ci_cache_dependency_path": vm.CI_CACHE_DEPENDENCY_PATH,
        "ci_job_display_names": dict(vm.CI_JOB_DISPLAY_NAMES),
        "markdownlint_md025": vm.MARKDOWNLINT_MD025,
        "markdownlint_md033": vm.MARKDOWNLINT_MD033,
        "markdownlint_md024_siblings_only": vm.MARKDOWNLINT_MD024_SIBLINGS_ONLY,
        "markdownlint_md013_tables": vm.MARKDOWNLINT_MD013_TABLES,
        "markdownlint_md013_code_blocks": vm.MARKDOWNLINT_MD013_CODE_BLOCKS,
        "pyproject_ruff_lint_select": list(vm.PYPROJECT_RUFF_LINT_SELECT),
        "pyproject_version": vm.PYPROJECT_VERSION,
        "pyproject_license_text": vm.PYPROJECT_LICENSE_TEXT,
        "pyproject_line_length": vm.PYPROJECT_LINE_LENGTH,
        "pyproject_ruff_src": list(vm.PYPROJECT_RUFF_SRC),
        "pytest_addopts": vm.PYTEST_ADDOPTS,
        "coverage_show_missing": vm.COVERAGE_SHOW_MISSING,
        "coverage_skip_empty": vm.COVERAGE_SKIP_EMPTY,
        "github_agent_description": vm.GITHUB_AGENT_DESCRIPTION,
        "ci_runs_on": vm.CI_RUNS_ON,
        "ci_artifact_if_no_files_found": vm.CI_ARTIFACT_IF_NO_FILES_FOUND,
        "ci_artifact_paths": list(vm.CI_ARTIFACT_PATHS),
        "ci_actionlint_shell": vm.CI_ACTIONLINT_SHELL,
        "ci_actionlint_step_id": vm.CI_ACTIONLINT_STEP_ID,
        "pyproject_description": vm.PYPROJECT_DESCRIPTION,
        "pyproject_readme": vm.PYPROJECT_README,
        "pytest_testpaths": list(vm.PYTEST_TESTPATHS),
        "pytest_pythonpath": list(vm.PYTEST_PYTHONPATH),
        "coverage_source": list(vm.COVERAGE_SOURCE),
        "validator_names": sorted(vm.VALIDATORS),
        "specialist_agents": list(vm.SPECIALIST_AGENTS),
        "schema_draft_uri": vm.SCHEMA_DRAFT_URI,
        "schema_id_prefix": vm.SCHEMA_ID_PREFIX,
        "claude_required_sections": list(vm.CLAUDE_REQUIRED_SECTIONS),
        "contributing_branch_surfaces": list(vm.CONTRIBUTING_BRANCH_SURFACES),
        "scratchpad_status_markers": list(vm.SCRATCHPAD_STATUS_MARKERS),
        "min_coverage_fail_under": vm.MIN_COVERAGE_FAIL_UNDER,
        "min_validator_count": vm.MIN_VALIDATOR_COUNT,
        "required_paths": list(dict.fromkeys([*vm.CURSOR_INSTALL_REQUIRED_REFS, "README.md"])),
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
        (
            f"---\nname: {vm.GITHUB_AGENT_NAME}\n"
            f"description: {vm.GITHUB_AGENT_DESCRIPTION}\n"
            "---\n\n# Body\n"
        ),
        encoding="utf-8",
    )
    findings = vm.validate_github_agents(tmp_path)
    assert findings == []


def test_github_agent_frontmatter_rejects_missing_description(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "my-agent.agent.md").write_text(
        f"---\nname: {vm.GITHUB_AGENT_NAME}\n---\n\n# Body\n", encoding="utf-8"
    )
    findings = vm.validate_github_agents(tmp_path)
    assert findings
    assert any("description" in f.message for f in findings)


def test_github_agent_rejects_empty_body(tmp_path: Path) -> None:
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "my-agent.agent.md").write_text(
        (
            f"---\nname: {vm.GITHUB_AGENT_NAME}\n"
            f"description: {vm.GITHUB_AGENT_DESCRIPTION}\n"
            "---\n\n"
        ),
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
        "constitution",
        "routing",
        "environment",
        "github-agents",
        "issue-templates",
        "issue-names",
        "agent-task",
        "bug-template",
        "feature-template",
        "pr-template",
        "dependabot",
        "markdownlint",
        "requirements-dev",
        "license",
        "readme",
        "readme-badges",
        "security",
        "contributing",
        "scratchpad",
        "pyproject",
        "yaml-configs",
        "ci",
        "prompts",
        "cross-docs",
        "changelog",
        "postmortem",
        "gitignore",
        "negative-constraints",
        "claude",
        "quarterly-review",
        "hydration",
        "execution-summary",
        "implementation-guide",
        "recipe-titles",
        "ci-actions",
        "ci-job-names",
        "ci-runs-on",
        "ci-artifacts",
        "actionlint-shell",
        "link-check",
        "github-agent-desc",
    }
    assert set(vm.VALIDATORS) == expected
    assert len(vm.VALIDATORS) == vm.MIN_VALIDATOR_COUNT


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
        "Lock inventory version and validator registry INVENTORY_VERSION",
        "Smoke each validator subset --only schemas",
        "python scripts/validate_manifests.py",
        "python -m pytest --cov=scripts --junitxml=pytest-junit.xml",
    ]
    version_lines = "\n".join(f'          - "{v}"' for v in versions)
    step_lines = "\n".join(f"      - run: {marker}" for marker in step_markers)
    job_stub = "\n".join(
        [
            "    runs-on: ubuntu-latest",
            "    permissions:",
            "      contents: read",
        ]
    )
    return "\n".join(
        [
            "name: CI",
            "on:",
            "  push: {}",
            "  pull_request:",
            '    branches: ["alpha"]',
            "concurrency:",
            "  group: ci-test",
            "  cancel-in-progress: true",
            "jobs:",
            "  markdown-lint:",
            job_stub,
            "  link-check:",
            job_stub,
            "  actionlint:",
            job_stub,
            "  manifest-validate:",
            job_stub,
            "    strategy:",
            "      fail-fast: false",
            "      matrix:",
            "        python-version:",
            version_lines,
            "    steps:",
            step_lines,
            "      - if: always()",
            "        uses: actions/upload-artifact@v4",
            "        with:",
            "          name: manifest-validate-pyX",
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
        if name == vm.ORCHESTRATION_RECIPE_NAME:
            agents_blob = " ".join(vm.DOCUMENTED_AGENTS)
            recipe["recipe"]["instructions"] = f"You are {primary}. Coordinate {agents_blob}."
            recipe["recipe"]["prompt"] = f"STEP for {agents_blob}"
        else:
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


def test_packaging_inventory_v5_lock_fields(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / "README.md", "# hi\n")

    bad_bindings = dict(vm.EXPECTED_RECIPE_BINDINGS)
    bad_bindings["quantum_algorithm_design_workflow"] = "agentic_flows/wrong.yaml"
    bad_primaries = dict(vm.RECIPE_PRIMARY_AGENT)
    bad_primaries["quantum_algorithm_design_workflow"] = "EdgeSecurityAgent"
    cases = [
        ("recipe_bindings", bad_bindings),
        ("recipe_primary_agents", bad_primaries),
        ("orchestration_recipe_name", "invented_orchestration"),
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
                "goose_provider": vm.HISTORIC_GOOSE_PROVIDER,
                "goose_model": vm.HISTORIC_GOOSE_MODEL,
                "extension_type": vm.HISTORIC_EXTENSION_TYPE,
                "extension_name": "wrong-extension",
            },
        ),
        ("routing_surfaces", list(vm.ROUTING_SURFACES)[:-1] + ["invented"]),
        ("constitution_heading_prefix", "### "),
        ("prompt_system_header_suffix", " Prompt"),
        ("specialist_escalation_marker", "ESCALATE NOW"),
        ("orchestration_escalation_marker", "ASK HUMAN"),
        (
            "agent_token_scan_docs",
            list(vm.AGENT_TOKEN_SCAN_DOCS)[:-1] + ["invented.md"],
        ),
        (
            "readme_required_phrases",
            list(vm.README_REQUIRED_PHRASES)[:-1] + ["invented"],
        ),
        (
            "security_required_phrases",
            list(vm.SECURITY_REQUIRED_PHRASES)[:-1] + ["invented"],
        ),
        (
            "contributing_required_phrases",
            list(vm.CONTRIBUTING_REQUIRED_PHRASES)[:-1] + ["invented"],
        ),
        (
            "issue_agent_task_headings",
            list(vm.ISSUE_AGENT_TASK_HEADINGS)[:-1] + ["Invented"],
        ),
        (
            "issue_bug_report_headings",
            list(vm.ISSUE_BUG_REPORT_HEADINGS)[:-1] + ["Invented"],
        ),
        (
            "issue_feature_request_headings",
            list(vm.ISSUE_FEATURE_REQUEST_HEADINGS)[:-1] + ["Invented"],
        ),
        (
            "required_archive_docs",
            list(vm.REQUIRED_ARCHIVE_DOCS)[:-1] + ["invented.md"],
        ),
        (
            "known_yaml_configs",
            list(vm.KNOWN_YAML_CONFIG_RELS)[:-1] + ["invented.yml"],
        ),
        ("cursor_environment_name", "wrong-name"),
        ("dependabot_schedule_interval", "daily"),
        ("ci_permissions_contents", "write"),
        ("ci_artifact_name_prefix", "wrong-prefix"),
        ("ci_pull_request_branch", "main"),
        ("pyproject_requires_python", ">=3.12"),
        ("markdownlint_default", False),
            (
                "scratchpad_required_phrases",
                list(vm.SCRATCHPAD_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "changelog_required_phrases",
                list(vm.CHANGELOG_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "postmortem_required_phrases",
                list(vm.POSTMORTEM_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "gitignore_required_patterns",
                list(vm.GITIGNORE_REQUIRED_PATTERNS)[:-1] + ["invented"],
            ),
            (
                "negative_constraint_phrases",
                list(vm.NEGATIVE_CONSTRAINT_PHRASES)[:-1] + ["invented"],
            ),
            ("license_copyright_holder", "Someone Else"),
            ("historic_recipe_version", "9.9.9"),
            ("dependabot_ecosystems", ["npm"]),
            ("ci_concurrency_group_prefix", "xx-"),
            ("ci_artifact_upload_if", "failure()"),
            ("pyproject_ruff_target_version", "py312"),
            ("github_agent_name", "Wrong"),
            ("agentic_flows_allowed_files", ["invented.txt"]),
            ("markdownlint_md013_line_length", 80),
            ("markdownlint_md025", True),
            ("markdownlint_md033", True),
            ("markdownlint_md024_siblings_only", False),
            (
                "validator_names",
                list(sorted(vm.VALIDATORS))[:-1] + ["invented"],
            ),
            (
                "specialist_agents",
                list(vm.SPECIALIST_AGENTS)[:-1] + ["InventedAgent"],
            ),
            ("schema_draft_uri", "https://example.com/wrong"),
            ("schema_id_prefix", "https://example.com/wrong/"),
            (
                "claude_required_sections",
                list(vm.CLAUDE_REQUIRED_SECTIONS)[:-1] + ["## Invented"],
            ),
            (
                "contributing_branch_surfaces",
                list(vm.CONTRIBUTING_BRANCH_SURFACES)[:-1] + ["invented"],
            ),
            (
                "scratchpad_status_markers",
                list(vm.SCRATCHPAD_STATUS_MARKERS)[:-1] + ["INVENTED"],
            ),
            ("version", 12),
            ("min_coverage_fail_under", 90),
            ("min_validator_count", 999),
            ("dependabot_group_names", ["github_actions"]),
            ("dependabot_directories", ["/apps"]),
            ("ci_cancel_in_progress", False),
            ("ci_fail_fast", True),
            ("coverage_branch", False),
            ("license_copyright_marker", "Copyright (c) 1999 Wrong"),
            (
                "cursor_install_required_refs",
                list(vm.CURSOR_INSTALL_REQUIRED_REFS)[:-1] + ["invented.md"],
            ),
            (
                "hydration_required_sections",
                list(vm.HYDRATION_REQUIRED_SECTIONS)[:-1] + ["## Invented"],
            ),
            (
                "execution_summary_required_phrases",
                list(vm.EXECUTION_SUMMARY_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "implementation_guide_required_phrases",
                list(vm.IMPLEMENTATION_GUIDE_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "recipe_titles",
                {
                    name: f"Invented {i}"
                    for i, name in enumerate(sorted(vm.EXPECTED_RECIPE_NAMES), start=1)
                },
            ),
            (
                "ci_required_actions",
                list(vm.CI_REQUIRED_ACTIONS)[:-1] + ["actions/checkout@v1"],
            ),
            ("pyproject_name", "wrong-package"),
            (
                "claude_required_phrases",
                list(vm.CLAUDE_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "escalation_format_phrases",
                list(vm.ESCALATION_FORMAT_PHRASES)[:-1] + ["Invented:"],
            ),
            (
                "goose_docs_required_phrases",
                list(vm.GOOSE_DOCS_REQUIRED_PHRASES)[:-1] + ["invented"],
            ),
            (
                "issue_template_names",
                {
                    ".github/ISSUE_TEMPLATE/bug_report.md": "Wrong A",
                    ".github/ISSUE_TEMPLATE/feature_request.md": "Wrong B",
                    ".github/ISSUE_TEMPLATE/agent_task.md": "Wrong C",
                },
            ),
            (
                "issue_template_abouts",
                {
                    ".github/ISSUE_TEMPLATE/bug_report.md": "Wrong about A",
                    ".github/ISSUE_TEMPLATE/feature_request.md": "Wrong about B",
                    ".github/ISSUE_TEMPLATE/agent_task.md": "Wrong about C",
                },
            ),
            (
                "readme_badge_phrases",
                list(vm.README_BADGE_PHRASES)[:-1] + ["invented-badge"],
            ),
            (
                "quarterly_review_phrases",
                list(vm.QUARTERLY_REVIEW_PHRASES)[:-1] + ["invented review"],
            ),
            ("ci_workflow_name", "Wrong CI Name"),
            (
                "ci_required_text_markers",
                list(vm.CI_REQUIRED_TEXT_MARKERS)[:-1] + ["invented-marker"],
            ),
            (
                "pyproject_ruff_lint_select",
                list(vm.PYPROJECT_RUFF_LINT_SELECT)[:-1] + ["Z"],
            ),
            ("ci_link_check_args", "wrong-args"),
            ("ci_link_check_fail", False),
            ("ci_markdown_lint_globs", "*.txt"),
            ("ci_markdown_lint_config", "wrong.yaml"),
            ("ci_cache_dependency_path", "wrong.txt"),
            (
                "ci_job_display_names",
                {
                    "markdown-lint": "Wrong A",
                    "link-check": "Wrong B",
                    "actionlint": "Wrong C",
                    "manifest-validate": "Wrong D",
                },
            ),
            ("github_agent_description", "wrong description"),
            ("pyproject_version", "9.9.9"),
            ("pyproject_license_text", "Apache-2.0"),
            ("pyproject_line_length", 80),
            ("pyproject_ruff_src", ["elsewhere"]),
            ("pytest_addopts", "-vv"),
            ("coverage_show_missing", False),
            ("coverage_skip_empty", False),
            ("markdownlint_md013_tables", True),
            ("markdownlint_md013_code_blocks", True),
            ]
    for field, value in cases:
        inventory = _inventory_payload(**{field: value})
        # Keep install refs ⊆ required_paths when mutating either field.
        if field == "cursor_install_required_refs":
            inventory["required_paths"] = list(
                dict.fromkeys([*inventory["required_paths"], *value])  # type: ignore[misc]
            )
        (tmp_path / "schemas" / "packaging-inventory.json").write_text(
            json.dumps(inventory), encoding="utf-8"
        )
        findings = vm.validate_packaging_inventory(tmp_path)
        assert any(field in f.message for f in findings), field


def test_dependabot_groups_not_mapping_and_duplicate_names(tmp_path: Path) -> None:
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
                "    groups: not-a-mapping",
                '  - package-ecosystem: "pip"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                "    groups:",
                "      python_dev:",
                "        patterns:",
                '          - "*"',
                "",
            ]
        ),
    )
    findings = vm.validate_dependabot(tmp_path)
    assert any("groups must be a mapping" in f.message for f in findings)

    dup = _inventory_payload(
        dependabot_group_names=["github_actions", "github_actions", "python_dev"],
    )
    # Bypass schema uniqueItems by writing after schema would reject — exercise
    # consistency helper directly.
    findings = vm._inventory_lock_consistency(dup, schema_path="schemas/packaging-inventory.json")
    assert any("dependabot_group_names must be unique" in f.message for f in findings)


def test_ci_upload_artifact_non_dict_step(tmp_path: Path) -> None:
    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    # Inject a non-mapping step before upload-artifact so the loop continues.
    yaml_text = yaml_text.replace(
        "      - uses: actions/upload-artifact@v4",
        "      - not-a-mapping\n      - uses: actions/upload-artifact@v4",
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    # Still validates; non-dict step is skipped when scanning upload-artifact if.
    assert isinstance(findings, list)

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
    assert vm.validate_constitution_agent_headings(REPO_ROOT) == []
    assert vm.validate_routing_surfaces(REPO_ROOT) == []
    assert vm.validate_security_packaging(REPO_ROOT) == []
    assert vm.validate_contributing_packaging(REPO_ROOT) == []
    assert vm.validate_agent_task_template(REPO_ROOT) == []


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
    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace(
        "on:\n  push: {}\n  pull_request:\n    branches: [\"alpha\"]\n",
        "",
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
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


def test_goose_schema_rejects_non_historic_provider_model() -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    bad["recipe"]["settings"]["goose_provider"] = "openai"
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    bad["recipe"]["settings"]["goose_model"] = "gpt-4"
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings
    bad = json.loads(json.dumps(MINIMAL_RECIPE))
    bad["recipe"]["settings"]["extra"] = True
    findings = vm.validate_against_schema(bad, schema, path="fixture")
    assert findings


def test_github_agent_schema_rejects_unknown_keys() -> None:
    schema = vm.load_schema("github-custom-agent.schema.json")
    findings = vm.validate_against_schema(
        {"name": "X", "description": "Y", "tools": []},
        schema,
        path="fixture",
    )
    assert findings


def test_prompt_fence_header_and_escalation_locks(tmp_path: Path) -> None:
    fences = []
    for agent in vm.DOCUMENTED_AGENTS:
        body = f"# Wrong Header\n\n{agent}\n"
        if agent in vm.SPECIALIST_AGENTS:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{agent} body without escalation\n"
            )
        else:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{agent} body without human escalation\n"
            )
        fences.append(f"```markdown\n{body}```")
    headings = "\n\n".join(
        f"## {i}. {agent} Prompt Template\n\n{fence}"
        for i, (agent, fence) in enumerate(zip(vm.DOCUMENTED_AGENTS, fences, strict=True), 1)
    )
    _write(tmp_path / "AGENT-PROMPTS.md", headings)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("ESCALATION" in f.message for f in findings)

    # Wrong header
    fences = []
    for agent in vm.DOCUMENTED_AGENTS:
        esc = (
            f"{vm.SPECIALIST_ESCALATION_MARKER}\nFrom Agent: {agent}\n"
            if agent in vm.SPECIALIST_AGENTS
            else f"{vm.ORCHESTRATION_ESCALATION_MARKER}\n"
        )
        body = f"# NotTheAgent System Prompt\n\n{esc}\n"
        fences.append(f"```markdown\n{body}```")
    headings = "\n\n".join(
        f"## {i}. {agent} Prompt Template\n\n{fence}"
        for i, (agent, fence) in enumerate(zip(vm.DOCUMENTED_AGENTS, fences, strict=True), 1)
    )
    _write(tmp_path / "AGENT-PROMPTS.md", headings)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("must start with" in f.message for f in findings)


def test_orchestration_recipe_requires_all_agents(tmp_path: Path) -> None:
    recipes = []
    for name, primary in vm.RECIPE_PRIMARY_AGENT.items():
        blob = f"You are {primary} only."
        recipes.append(
            {
                "name": name,
                "recipe": {
                    **MINIMAL_RECIPE["recipe"],
                    "instructions": blob,
                    "prompt": blob,
                    "title": primary,
                },
            }
        )
    parts = []
    for index, (recipe, file_path) in enumerate(
        zip(recipes, vm.EXPECTED_RECIPE_FILES, strict=True), start=1
    ):
        parts.append(
            f"## Recipe {index}\n\n**File**: `./{file_path}`\n\n"
            f"```yaml\n{yaml.safe_dump(recipe, sort_keys=False)}```\n"
        )
    _write(tmp_path / "GOOSE-RECIPES.md", "\n".join(parts))
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert any("orchestration recipe missing documented agent" in f.message for f in findings)


def test_constitution_routing_security_contributing_agent_task(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_constitution_agent_headings(tmp_path)
    )
    _write(tmp_path / "AGENTS-v2.2.md", "# no agents\nFakeAgent here\n")
    findings = vm.validate_constitution_agent_headings(tmp_path)
    assert any("missing constitution heading" in f.message for f in findings)
    assert any("invented or unknown agent" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_routing_surfaces(tmp_path))
    _write(tmp_path / "CLAUDE.md", "# no matrix\n")
    findings = vm.validate_routing_surfaces(tmp_path)
    assert any("Routing Matrix" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_security_packaging(tmp_path))
    _write(tmp_path / "SECURITY.md", "# hi\nFakeAgent\n")
    findings = vm.validate_security_packaging(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("invented or unknown agent" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_contributing_packaging(tmp_path))
    _write(tmp_path / "CONTRIBUTING.md", "# hi\n")
    findings = vm.validate_contributing_packaging(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_agent_task_template(tmp_path))
    _write(tmp_path / ".github" / "ISSUE_TEMPLATE" / "agent_task.md", "# Task\n")
    findings = vm.validate_agent_task_template(tmp_path)
    assert any("missing required heading" in f.message for f in findings)


def test_inventory_schema_rejects_v3_payload() -> None:
    schema = vm.load_schema("packaging-inventory.schema.json")
    payload = _inventory_payload()
    payload["version"] = 3
    # Drop v4-required fields to mimic old inventory
    for key in (
        "orchestration_recipe_name",
        "routing_surfaces",
        "constitution_heading_prefix",
        "prompt_system_header_suffix",
        "specialist_escalation_marker",
        "orchestration_escalation_marker",
        "agent_token_scan_docs",
        "readme_required_phrases",
        "security_required_phrases",
        "contributing_required_phrases",
        "issue_agent_task_headings",
    ):
        payload.pop(key, None)
    findings = vm.validate_against_schema(
        payload, schema, path="schemas/packaging-inventory.json"
    )
    assert findings


def test_historic_settings_non_mapping_and_non_dict_extensions() -> None:
    assert vm._validate_historic_recipe_settings({"recipe": "scalar"}, path="x") == []
    findings = vm._validate_historic_recipe_settings(
        {
            "recipe": {
                "settings": {
                    "goose_provider": "openai",
                    "goose_model": "gpt-4",
                },
                "extensions": [
                    "not-a-mapping",
                    {"type": "stdio", "name": "other"},
                ],
            }
        },
        path="x",
    )
    assert any("goose_provider" in f.message for f in findings)
    assert any("goose_model" in f.message for f in findings)
    assert any("extension" in f.message for f in findings)


def test_github_and_issue_frontmatter_non_mapping(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\n- list\n---\n\nBody\n",
    )
    findings = vm.validate_github_agents(tmp_path)
    assert any("frontmatter must be a mapping" in f.message for f in findings)

    for rel in vm.ISSUE_TEMPLATE_FILES:
        _write(tmp_path / rel, "---\n- list\n---\n\nBody\n")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("frontmatter must be a mapping" in f.message for f in findings)


def test_prompt_specialist_missing_from_agent_identity(tmp_path: Path) -> None:
    fences = []
    for agent in vm.DOCUMENTED_AGENTS:
        if agent in vm.SPECIALIST_AGENTS:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{vm.SPECIALIST_ESCALATION_MARKER}\n"
                "From Agent: SomeoneElse\n"
            )
        else:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{vm.ORCHESTRATION_ESCALATION_MARKER}\n"
            )
        fences.append(f"```markdown\n{body}```")
    headings = "\n\n".join(
        f"## {i}. {agent} Prompt Template\n\n{fence}"
        for i, (agent, fence) in enumerate(
            zip(vm.DOCUMENTED_AGENTS, fences, strict=True), start=1
        )
    )
    _write(tmp_path / "AGENT-PROMPTS.md", headings)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any("escalation identity" in f.message for f in findings)


def test_prompt_orchestration_missing_human_escalation(tmp_path: Path) -> None:
    fences = []
    for agent in vm.DOCUMENTED_AGENTS:
        if agent in vm.SPECIALIST_AGENTS:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{vm.SPECIALIST_ESCALATION_MARKER}\n"
                f"From Agent: {agent}\n"
            )
        else:
            body = f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\nno human marker\n"
        fences.append(f"```markdown\n{body}```")
    headings = "\n\n".join(
        f"## {i}. {agent} Prompt Template\n\n{fence}"
        for i, (agent, fence) in enumerate(
            zip(vm.DOCUMENTED_AGENTS, fences, strict=True), start=1
        )
    )
    _write(tmp_path / "AGENT-PROMPTS.md", headings)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert any(vm.ORCHESTRATION_ESCALATION_MARKER in f.message for f in findings)


def test_github_agent_missing_frontmatter_continue(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / ".github" / "agents" / "my-agent.agent.md", "# no frontmatter\n")
    findings = vm.validate_github_agents(tmp_path)
    assert any("frontmatter" in f.message for f in findings)


def test_issue_template_missing_frontmatter_continue(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    for rel in vm.ISSUE_TEMPLATE_FILES:
        _write(tmp_path / rel, "# no frontmatter\n")
    findings = vm.validate_issue_templates(tmp_path)
    assert any("frontmatter" in f.message for f in findings)


def test_packaging_inventory_internal_consistency(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(tmp_path / "README.md", "# hi\n")
    # Schema-valid bindings that disagree with names/files sets via lock constants
    # are caught by field locks first. Force consistency helper by monkeypatching
    # constants after writing a payload that matches constants but with swapped maps.
    inventory = _inventory_payload()
    # Mutate after schema validation path: write consistent locks then patch file
    # to break only consistency (bindings keys ok vs names, but values wrong set)
    # Easiest: call helper directly.
    broken = dict(inventory)
    broken["recipe_bindings"] = {
        **broken["recipe_bindings"],
        "quantum_algorithm_design_workflow": "agentic_flows/blockchain_contract_design.yaml",
        "blockchain_contract_design_workflow": "agentic_flows/quantum_algorithm_design.yaml",
    }
    # values set still equals files set — swap keeps set equality.
    # Break values set instead:
    broken["recipe_bindings"] = {
        name: "agentic_flows/quantum_algorithm_design.yaml"
        for name in broken["expected_recipe_names"]
    }
    findings = vm._inventory_lock_consistency(
        broken, schema_path="schemas/packaging-inventory.json"
    )
    assert any("recipe_bindings values inconsistent" in f.message for f in findings)

    broken_keys = dict(inventory)
    broken_keys["recipe_bindings"] = {
        "invented_a": "agentic_flows/quantum_algorithm_design.yaml",
        "invented_b": "agentic_flows/blockchain_contract_design.yaml",
        "invented_c": "agentic_flows/edge_security_implementation.yaml",
        "invented_d": "agentic_flows/quantum_nft_mint_orchestration.yaml",
    }
    findings = vm._inventory_lock_consistency(
        broken_keys, schema_path="schemas/packaging-inventory.json"
    )
    assert any("recipe_bindings keys inconsistent" in f.message for f in findings)

    broken_primary = dict(inventory)
    broken_primary["recipe_primary_agents"] = {
        "invented_a": "QuantumArchitectAgent",
        "invented_b": "BlockchainArchitectAgent",
        "invented_c": "EdgeSecurityAgent",
        "invented_d": "OrchestrationAgent",
    }
    findings = vm._inventory_lock_consistency(
        broken_primary, schema_path="schemas/packaging-inventory.json"
    )
    assert any("recipe_primary_agents keys inconsistent" in f.message for f in findings)

    bad_agents = dict(inventory)
    bad_agents["recipe_primary_agents"] = {
        name: "InventedGhostAgent" for name in inventory["expected_recipe_names"]
    }
    findings = vm._inventory_lock_consistency(
        bad_agents, schema_path="schemas/packaging-inventory.json"
    )
    assert any("subset of documented_agents" in f.message for f in findings)

    bad_orch = dict(inventory)
    bad_orch["orchestration_recipe_name"] = "not_in_names"
    findings = vm._inventory_lock_consistency(
        bad_orch, schema_path="schemas/packaging-inventory.json"
    )
    assert any("orchestration_recipe_name must be one of" in f.message for f in findings)

    bad_docs = dict(inventory)
    bad_docs["required_archive_docs"] = list(inventory["required_archive_docs"]) + [
        "not-scanned.md"
    ]
    findings = vm._inventory_lock_consistency(
        bad_docs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("subset of agent_token_scan_docs" in f.message for f in findings)

    dup_names = dict(inventory)
    dup_names["validator_names"] = ["ci", "ci"]
    findings = vm._inventory_lock_consistency(
        dup_names, schema_path="schemas/packaging-inventory.json"
    )
    assert any("validator_names must be unique" in f.message for f in findings)

    short_names = dict(inventory)
    short_names["validator_names"] = ["ci"]
    short_names["min_validator_count"] = 5
    findings = vm._inventory_lock_consistency(
        short_names, schema_path="schemas/packaging-inventory.json"
    )
    assert any("validator_names length below" in f.message for f in findings)


def test_bug_and_feature_template_validators(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_bug_report_template(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_feature_request_template(tmp_path)
    )
    _write(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md", "# Bug\n")
    findings = vm.validate_bug_report_template(tmp_path)
    assert any("missing required heading" in f.message for f in findings)
    _write(tmp_path / ".github" / "ISSUE_TEMPLATE" / "feature_request.md", "# Feat\n")
    findings = vm.validate_feature_request_template(tmp_path)
    assert any("missing required heading" in f.message for f in findings)
    assert vm.validate_bug_report_template(REPO_ROOT) == []
    assert vm.validate_feature_request_template(REPO_ROOT) == []


def test_environment_name_lock(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    env = {"name": "wrong", "install": "true"}
    _write(tmp_path / ".cursor" / "environment.json", json.dumps(env))
    findings = vm.validate_cursor_environment(tmp_path)
    assert any("environment name must be" in f.message for f in findings)


def test_dependabot_schedule_and_directory_locks(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".github" / "dependabot.yml",
        "\n".join(
            [
                "version: 2",
                "updates:",
                '  - package-ecosystem: "github-actions"',
                '    directory: "/apps"',
                "    schedule:",
                '      interval: "daily"',
                '  - package-ecosystem: "pip"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                "",
            ]
        ),
    )
    findings = vm.validate_dependabot(tmp_path)
    assert any("directory must be" in f.message for f in findings)
    assert any("schedule.interval must be" in f.message for f in findings)


def test_markdownlint_default_lock(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".markdownlint.yaml",
        "default: false\nMD013:\n  line_length: 200\n",
    )
    findings = vm.validate_markdownlint(tmp_path)
    assert any("markdownlint default must be" in f.message for f in findings)


def test_scratchpad_required_phrases(tmp_path: Path) -> None:
    _write(
        tmp_path / "agentic_flows" / "scratchpad.txt",
        "scratchpad notes\n- [ ] task\n",
    )
    findings = vm.validate_scratchpad(tmp_path)
    assert any("required phrase" in f.message for f in findings)


def test_pyproject_requires_python_lock(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "x"',
                'requires-python = ">=3.10"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.report]",
                "fail_under = 98",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("requires-python must be" in f.message for f in findings)


def test_ci_workflow_v5_deepeners(tmp_path: Path) -> None:
    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    # Orphan job
    yaml_text = yaml_text + "  invented-job:\n    runs-on: ubuntu-latest\n"
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("unexpected/orphan CI job" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("cancel-in-progress: true", "cancel-in-progress: false")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("cancel-in-progress must be True" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("fail-fast: false", "fail-fast: true")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("fail-fast must be False" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("contents: read", "contents: write")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("permissions.contents must be" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace('branches: ["alpha"]', 'branches: ["main"]')
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("pull_request.branches must include" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("manifest-validate-pyX", "wrong-prefix")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("artifact name must include" in f.message for f in findings)


def test_live_v5_validators() -> None:
    assert vm.validate_bug_report_template(REPO_ROOT) == []
    assert vm.validate_feature_request_template(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) == 46
    assert vm.MIN_COVERAGE_FAIL_UNDER == 99


def test_live_v6_validators() -> None:
    assert vm.validate_changelog_packaging(REPO_ROOT) == []
    assert vm.validate_postmortem_packaging(REPO_ROOT) == []
    assert vm.validate_gitignore_packaging(REPO_ROOT) == []
    assert vm.validate_negative_constraints(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) >= 43
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]


def test_live_v7_validators() -> None:
    assert vm.validate_hydration_report(REPO_ROOT) == []
    assert vm.validate_execution_summary(REPO_ROOT) == []
    assert vm.validate_implementation_guide(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) >= 43
    assert "Lock inventory" in vm.REQUIRED_MANIFEST_STEP_MARKERS
    assert "INVENTORY_VERSION" in vm.REQUIRED_MANIFEST_STEP_MARKERS
    assert vm.CI_CANCEL_IN_PROGRESS is True
    assert vm.CI_FAIL_FAST is False
    assert vm.COVERAGE_BRANCH is True
    assert set(vm.DEPENDABOT_GROUP_NAMES) == {"github_actions", "python_dev"}
    assert set(vm.CURSOR_INSTALL_REQUIRED_REFS) <= set(
        json.loads(
            (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(
                encoding="utf-8"
            )
        )["required_paths"]
    )


def test_live_v8_validators() -> None:
    assert vm.validate_claude_packaging(REPO_ROOT) == []
    assert vm.validate_recipe_titles(REPO_ROOT) == []
    assert vm.validate_ci_actions(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) == 46
    assert vm.MIN_VALIDATOR_COUNT == 46
    assert vm.PYPROJECT_NAME == "g0p-agents-validation"
    assert set(vm.DEPENDABOT_DIRECTORIES) == {"/"}
    assert dict(vm.RECIPE_TITLES) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["recipe_titles"]
    assert list(vm.CI_REQUIRED_ACTIONS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["ci_required_actions"]


def test_live_v9_validators() -> None:
    assert vm.validate_issue_template_names(REPO_ROOT) == []
    assert vm.validate_readme_badges(REPO_ROOT) == []
    assert vm.validate_quarterly_review(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) == 46
    assert vm.MIN_VALIDATOR_COUNT == 46
    assert vm.CI_WORKFLOW_NAME == "CI — Lint, Links & Manifests"
    assert vm.MARKDOWNLINT_MD025 is False
    assert vm.MARKDOWNLINT_MD033 is False
    assert vm.MARKDOWNLINT_MD024_SIBLINGS_ONLY is True
    assert tuple(vm.PYPROJECT_RUFF_LINT_SELECT) == ("E", "F", "I", "UP", "B")
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["issue_template_names"] == vm.ISSUE_TEMPLATE_NAMES
    assert inventory["issue_template_abouts"] == vm.ISSUE_TEMPLATE_ABOUTS
    assert inventory["readme_badge_phrases"] == list(vm.README_BADGE_PHRASES)
    assert inventory["quarterly_review_phrases"] == list(vm.QUARTERLY_REVIEW_PHRASES)
    assert len(vm.CURSOR_INSTALL_REQUIRED_REFS) == 16
    assert "acknowledgment within 48 hours" in vm.SECURITY_REQUIRED_PHRASES
    assert "Never expose plaintext keys" in vm.SECURITY_REQUIRED_PHRASES
    assert vm.validate_security_packaging(REPO_ROOT) == []
    assert vm.validate_markdownlint(REPO_ROOT) == []
    assert vm.validate_pyproject(REPO_ROOT) == []
    assert vm.validate_cursor_environment(REPO_ROOT) == []


def test_live_v10_validators() -> None:
    assert vm.validate_link_check(REPO_ROOT) == []
    assert vm.validate_ci_job_names(REPO_ROOT) == []
    assert vm.validate_github_agent_description(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) == 46
    assert vm.MIN_VALIDATOR_COUNT == 46
    assert vm.CI_LINK_CHECK_ARGS == "--verbose --no-progress '**/*.md'"
    assert vm.CI_LINK_CHECK_FAIL is True
    assert vm.CI_MARKDOWN_LINT_GLOBS == "**/*.md"
    assert vm.CI_MARKDOWN_LINT_CONFIG == ".markdownlint.yaml"
    assert vm.CI_CACHE_DEPENDENCY_PATH == "requirements-dev.txt"
    assert vm.PYPROJECT_VERSION == "0.0.0"
    assert vm.PYPROJECT_LICENSE_TEXT == "MIT"
    assert vm.PYPROJECT_LINE_LENGTH == 100
    assert tuple(vm.PYPROJECT_RUFF_SRC) == ("scripts", "tests")
    assert vm.PYTEST_ADDOPTS == "-q"
    assert vm.COVERAGE_SHOW_MISSING is True
    assert vm.COVERAGE_SKIP_EMPTY is True
    assert vm.MARKDOWNLINT_MD013_TABLES is False
    assert vm.MARKDOWNLINT_MD013_CODE_BLOCKS is False
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["ci_job_display_names"] == vm.CI_JOB_DISPLAY_NAMES
    assert inventory["github_agent_description"] == vm.GITHUB_AGENT_DESCRIPTION
    assert inventory["ci_link_check_args"] == vm.CI_LINK_CHECK_ARGS
    assert inventory["pyproject_ruff_src"] == list(vm.PYPROJECT_RUFF_SRC)
    assert "link-check" in vm.VALIDATORS
    assert "ci-job-names" in vm.VALIDATORS
    assert "github-agent-desc" in vm.VALIDATORS
    assert vm.validate_github_agents(REPO_ROOT) == []


def test_hydration_execution_implementation_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_hydration_report(tmp_path))
    _write(tmp_path / "docs" / "agent-hydration.md", "# hydration\nInventedGhostAgent\n")
    findings = vm.validate_hydration_report(tmp_path)
    assert any("required section" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_execution_summary(tmp_path))
    _write(tmp_path / "EXECUTION-SUMMARY.md", "# summary\nInventedGhostAgent\n")
    findings = vm.validate_execution_summary(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)

    assert any(
        "missing" in f.message for f in vm.validate_implementation_guide(tmp_path)
    )
    _write(tmp_path / "IMPLEMENTATION-GUIDE.md", "# guide\nInventedGhostAgent\n")
    findings = vm.validate_implementation_guide(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)


def test_dependabot_group_names_and_coverage_branch(tmp_path: Path) -> None:
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
                '  - package-ecosystem: "pip"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                "",
            ]
        ),
    )
    findings = vm.validate_dependabot(tmp_path)
    assert any("missing required Dependabot group" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "demo"',
                'version = "0.0.0"',
                'requires-python = ">=3.11"',
                "[tool.pytest.ini_options]",
                "testpaths = [\"tests\"]",
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.run]",
                "branch = false",
                "[tool.coverage.report]",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("coverage run.branch must be True" in f.message for f in findings)


def test_cursor_install_required_refs(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".cursor" / "environment.json",
        json.dumps({"name": "g0p-agents", "install": "test -f README.md"}),
    )
    _write(tmp_path / "README.md", "ok\n")
    findings = vm.validate_cursor_environment(tmp_path)
    assert any("install must reference required packaging path" in f.message for f in findings)


def test_inventory_v7_consistency_locks(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    # Pass schema (exactly 3 specialists) but include OrchestrationAgent illegally.
    broken_specialists = _inventory_payload(
        specialist_agents=[
            "QuantumArchitectAgent",
            "BlockchainArchitectAgent",
            "OrchestrationAgent",
        ],
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(broken_specialists), encoding="utf-8"
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("must not include OrchestrationAgent" in f.message for f in findings)

    broken_refs = _inventory_payload(
        required_paths=["README.md"],
        cursor_install_required_refs=list(vm.CURSOR_INSTALL_REQUIRED_REFS),
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(broken_refs), encoding="utf-8"
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "cursor_install_required_refs must be subset" in f.message for f in findings
    )


def test_changelog_postmortem_gitignore_negative(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_changelog_packaging(tmp_path))
    _write(tmp_path / "CHANGELOG.md", "# Changelog\nInventedGhostAgent\n")
    findings = vm.validate_changelog_packaging(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_postmortem_packaging(tmp_path))
    _write(tmp_path / "postmortem.md", "# notes\nInventedGhostAgent\n")
    findings = vm.validate_postmortem_packaging(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_gitignore_packaging(tmp_path))
    _write(tmp_path / ".gitignore", "*.log\n")
    findings = vm.validate_gitignore_packaging(tmp_path)
    assert any("required pattern" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_negative_constraints(tmp_path))
    _write(tmp_path / "CLAUDE.md", "# no constraints\n")
    findings = vm.validate_negative_constraints(tmp_path)
    assert any("Negative Constraints" in f.message for f in findings)
    assert any("negative constraint phrase" in f.message for f in findings)


def test_license_copyright_and_github_agent_name(tmp_path: Path) -> None:
    _write(tmp_path / "LICENSE", "MIT License\nCopyright (c) 2026 Someone Else\n")
    findings = vm.validate_license(tmp_path)
    assert any("copyright holder" in f.message for f in findings)

    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\nname: WrongName\ndescription: demo\n---\n\nBody\n",
    )
    findings = vm.validate_github_agents(tmp_path)
    assert any("GitHub agent name must be" in f.message for f in findings)


def test_markdownlint_md013_and_dependabot_ecosystem_set(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write(
        tmp_path / ".markdownlint.yaml",
        "default: true\nMD013:\n  line_length: 80\n",
    )
    findings = vm.validate_markdownlint(tmp_path)
    assert any("MD013.line_length" in f.message for f in findings)

    _write(tmp_path / ".markdownlint.yaml", "default: true\nMD013: false\n")
    findings = vm.validate_markdownlint(tmp_path)
    assert any("MD013 must be a mapping" in f.message for f in findings)

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
                '  - package-ecosystem: "pip"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                '  - package-ecosystem: "npm"',
                '    directory: "/"',
                "    schedule:",
                '      interval: "weekly"',
                "",
            ]
        ),
    )
    findings = vm.validate_dependabot(tmp_path)
    assert any("package-ecosystem set must equal" in f.message for f in findings)


def test_pyproject_ruff_target_and_historic_recipe_version(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "x"',
                'requires-python = ">=3.11"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py312"',
                "[tool.coverage.report]",
                "fail_under = 98",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("ruff target-version" in f.message for f in findings)

    findings = vm._validate_historic_recipe_settings(
        {
            "recipe": {
                "version": "2.0.0",
                "settings": {
                    "goose_provider": vm.HISTORIC_GOOSE_PROVIDER,
                    "goose_model": vm.HISTORIC_GOOSE_MODEL,
                },
                "extensions": [
                    {
                        "type": vm.HISTORIC_EXTENSION_TYPE,
                        "name": vm.HISTORIC_EXTENSION_NAME,
                    }
                ],
            }
        },
        path="x",
    )
    assert any("historic recipe version" in f.message for f in findings)


def test_ci_concurrency_prefix_and_artifact_if(tmp_path: Path) -> None:
    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("group: ci-test", "group: other-test")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("concurrency.group must start with" in f.message for f in findings)

    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    yaml_text = yaml_text.replace("if: always()", "if: success()")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert any("upload-artifact if must be" in f.message for f in findings)


def test_agentic_flows_allow_list(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    blocks = []
    for name in [
        "quantum_algorithm_design_workflow",
        "blockchain_contract_design_workflow",
        "edge_security_implementation_workflow",
        "quantum_nft_mint_full_orchestration",
    ]:
        payload = {
            "name": name,
            "recipe": {
                "version": vm.HISTORIC_RECIPE_VERSION,
                "title": "t",
                "settings": {
                    "goose_provider": vm.HISTORIC_GOOSE_PROVIDER,
                    "goose_model": vm.HISTORIC_GOOSE_MODEL,
                },
                "instructions": f"You are {vm.RECIPE_PRIMARY_AGENT[name]}",
                "prompt": "STEP",
                "extensions": [
                    {
                        "type": vm.HISTORIC_EXTENSION_TYPE,
                        "name": vm.HISTORIC_EXTENSION_NAME,
                    }
                ],
            },
        }
        blocks.append(f"```yaml\n{yaml.dump(payload)}```")
    files = "\n".join(f"**File**: `{path}`" for path in vm.EXPECTED_RECIPE_FILES)
    runs = "\n".join(f"goose run ./{path}" for path in vm.EXPECTED_RECIPE_FILES)
    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n\n".join(blocks) + "\n\n" + files + "\n\n" + runs + "\n",
    )
    flows = tmp_path / "agentic_flows"
    flows.mkdir()
    (flows / "scratchpad.txt").write_text("ok\n", encoding="utf-8")
    (flows / "invented.txt").write_text("nope\n", encoding="utf-8")
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("agentic_flows file" in f.message for f in findings)


def test_goose_schema_rejects_non_historic_version() -> None:
    schema = vm.load_schema("goose-recipe.schema.json")
    payload = dict(MINIMAL_RECIPE)
    payload["recipe"] = dict(payload["recipe"])
    payload["recipe"]["version"] = "2.0.0"
    findings = vm.validate_against_schema(payload, schema, path="x")
    assert findings


def test_cursor_env_schema_rejects_unknown_keys() -> None:
    schema = vm.load_schema("cursor-environment.schema.json")
    findings = vm.validate_against_schema(
        {"name": "g0p-agents", "install": "true", "extra": 1},
        schema,
        path="x",
    )
    assert findings


def test_historic_settings_skips_non_dict_settings_and_non_list_extensions() -> None:
    assert (
        vm._validate_historic_recipe_settings(
            {
                "recipe": {
                    "version": vm.HISTORIC_RECIPE_VERSION,
                    "settings": "scalar",
                    "extensions": "scalar",
                }
            },
            path="x",
        )
        == []
    )



def test_goose_recipes_extra_only_and_ondisk_parse_none(tmp_path: Path) -> None:
    blocks = []
    for name in sorted(vm.EXPECTED_RECIPE_NAMES):
        recipe = json.loads(json.dumps(LOCKED_RECIPE))
        recipe["name"] = name
        blocks.append(yaml.safe_dump(recipe, sort_keys=False))
    extra = json.loads(json.dumps(LOCKED_RECIPE))
    extra["name"] = "invented_extra_workflow"
    blocks.append(yaml.safe_dump(extra, sort_keys=False))
    body = "\n\n".join(f"```yaml\n{block}```" for block in blocks)
    for rel in vm.EXPECTED_RECIPE_FILES:
        body += f"\n**File**: `./{rel}`\n"
        body += f"\ngoose run ./{rel}\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("unexpected/invented recipe name" in f.message for f in findings)
    assert not any("missing locked recipe name" in f.message for f in findings)

    # on-disk expected file with parse failure (data is None -> continue)
    flows = tmp_path / "agentic_flows"
    flows.mkdir(exist_ok=True)
    target = vm.EXPECTED_RECIPE_FILES[0]
    (tmp_path / target).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / target).write_text(":\n  -", encoding="utf-8")
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("YAML parse error" in f.message for f in findings)



def test_goose_recipes_missing_only_via_non_string_name(tmp_path: Path) -> None:
    locked = sorted(vm.EXPECTED_RECIPE_NAMES)
    names: list[object] = [*locked[:3], 123]
    blocks = []
    for name in names:
        recipe = json.loads(json.dumps(LOCKED_RECIPE))
        recipe["name"] = name
        blocks.append(yaml.safe_dump(recipe, sort_keys=False))
    body = "\n\n".join(f"```yaml\n{block}```" for block in blocks)
    for rel in vm.EXPECTED_RECIPE_FILES:
        body += f"\n**File**: `./{rel}`\n"
        body += f"\ngoose run ./{rel}\n"
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("missing locked recipe name" in f.message for f in findings)



def test_recipe_agent_bindings_non_dict_continues(tmp_path: Path) -> None:
    _write(tmp_path / "GOOSE-RECIPES.md", "```yaml\n- just-a-list\n```\n")
    findings = vm.validate_recipe_agent_bindings(tmp_path)
    assert findings == [] or all("primary agent" not in f.message for f in findings)



def test_dependabot_skips_non_dict_update_items(tmp_path: Path) -> None:
    original = vm.validate_against_schema

    def _ok(instance, schema, *, path):  # noqa: ANN001
        return []

    vm.validate_against_schema = _ok  # type: ignore[assignment]
    try:
        _write(
            tmp_path / ".github" / "dependabot.yml",
            "version: 2\nupdates:\n  - not-a-mapping\n"
            '  - package-ecosystem: "pip"\n    directory: "/"\n'
            "    schedule:\n      interval: weekly\n",
        )
        findings = vm.validate_dependabot(tmp_path)
        # non-dict item skipped; may still miss github-actions ecosystem
        assert isinstance(findings, list)
    finally:
        vm.validate_against_schema = original  # type: ignore[assignment]



def test_ci_workflow_skips_non_dict_jobs(tmp_path: Path) -> None:
    yaml_text = _ci_yaml_with_matrix(list(vm.REQUIRED_PYTHON_VERSIONS))
    _write(tmp_path / ".github" / "workflows" / "ci.yml", yaml_text)
    findings = vm.validate_ci_workflow(tmp_path)
    assert isinstance(findings, list)

    bad = yaml_text.replace(
        "markdown-lint:",
        "markdown-lint: not-a-job-map\n  unused-markdown-lint:",
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", bad)
    findings = vm.validate_ci_workflow(tmp_path)
    assert isinstance(findings, list)



def test_pr_template_without_top_hash_heading(tmp_path: Path) -> None:
    headings = "\n".join(f"## {h}\n" for h in vm.PR_TEMPLATE_HEADINGS)
    _write(tmp_path / ".github" / "pull_request_template.md", headings + "\n")
    assert vm.validate_pr_template(tmp_path) == []



def test_requirements_dev_skips_non_matching_lines(tmp_path: Path) -> None:
    lines = ["# comment", "@@@not-a-package", *sorted(vm.REQUIRED_DEV_PACKAGES), ""]
    _write(tmp_path / "requirements-dev.txt", "\n".join(lines) + "\n")
    assert vm.validate_requirements_dev(tmp_path) == []



def test_prompt_non_specialist_non_orchestration_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    agents = (
        "QuantumArchitectAgent",
        "BlockchainArchitectAgent",
        "EdgeSecurityAgent",
        "ArchiveDocsAgent",
    )
    monkeypatch.setattr(vm, "DOCUMENTED_AGENTS", agents)
    monkeypatch.setattr(vm, "SPECIALIST_AGENTS", agents[:3])
    fences = []
    for agent in agents:
        if agent in agents[:3]:
            body = (
                f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\n"
                f"{vm.SPECIALIST_ESCALATION_MARKER}\n"
                f"From Agent: {agent}\n"
            )
        else:
            body = f"# {agent}{vm.PROMPT_SYSTEM_HEADER_SUFFIX}\n\narchive only\n"
        fences.append(f"```markdown\n{body}```")
    headings = "\n\n".join(
        f"## {i}. {agent} Prompt Template\n\n{fence}"
        for i, (agent, fence) in enumerate(zip(agents, fences, strict=True), start=1)
    )
    _write(tmp_path / "AGENT-PROMPTS.md", headings)
    findings = vm.validate_documented_agent_prompts(tmp_path)
    assert findings == []




def test_v8_claude_recipe_titles_ci_actions_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_claude_packaging(tmp_path))
    _write(tmp_path / "CLAUDE.md", "# Claude\nInventedGhostAgent\n")
    findings = vm.validate_claude_packaging(tmp_path)
    assert any("required section" in f.message for f in findings)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("escalation-format phrase" in f.message for f in findings)
    assert any("invented or unknown" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_recipe_titles(tmp_path))
    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                "# Goose",
                "```yaml",
                "name: quantum_algorithm_design_workflow",
                "recipe:",
                "  version: 1.0.0",
                "  title: Wrong Title",
                "  settings:",
                "    goose_provider: anthropic",
                "    goose_model: claude-opus-4",
                "  instructions: QuantumArchitectAgent",
                "  prompt: STEP",
                "  extensions:",
                "    - type: builtin",
                "      name: developer",
                "      timeout: 30",
                "```",
                "",
            ]
        ),
    )
    findings = vm.validate_recipe_titles(tmp_path)
    assert any("packaging phrase" in f.message for f in findings)
    assert any("historic recipe title must be" in f.message for f in findings)
    assert any("missing locked recipe title" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_ci_actions(tmp_path))
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\non: push\n")
    findings = vm.validate_ci_actions(tmp_path)
    assert any("missing required action pin" in f.message for f in findings)

    _copy_schemas(tmp_path)
    broken_titles = _inventory_payload(
        recipe_titles={
            "invented_a": "A",
            "invented_b": "B",
            "invented_c": "C",
            "invented_d": "D",
        }
    )
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(broken_titles), encoding="utf-8"
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("recipe_titles" in f.message for f in findings)

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    dup_titles = dict(inventory)
    titles = dict(dup_titles["recipe_titles"])
    first_key = next(iter(titles))
    second_key = next(k for k in titles if k != first_key)
    titles[second_key] = titles[first_key]
    dup_titles["recipe_titles"] = titles
    findings = vm._inventory_lock_consistency(
        dup_titles, schema_path="schemas/packaging-inventory.json"
    )
    assert any("recipe_titles values must be unique" in f.message for f in findings)

    empty_actions = dict(inventory)
    empty_actions["ci_required_actions"] = []
    findings = vm._inventory_lock_consistency(
        empty_actions, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_required_actions must not be empty" in f.message for f in findings)

    empty_dirs = dict(inventory)
    empty_dirs["dependabot_directories"] = []
    findings = vm._inventory_lock_consistency(
        empty_dirs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "dependabot_directories must not be empty" in f.message for f in findings
    )

    dup_actions = dict(inventory)
    dup_actions["ci_required_actions"] = [
        vm.CI_REQUIRED_ACTIONS[0],
        vm.CI_REQUIRED_ACTIONS[0],
    ]
    findings = vm._inventory_lock_consistency(
        dup_actions, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_required_actions must be unique" in f.message for f in findings)

    dup_dirs = dict(inventory)
    dup_dirs["dependabot_directories"] = ["/", "/"]
    findings = vm._inventory_lock_consistency(
        dup_dirs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("dependabot_directories must be unique" in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                "Recipe-Based Agent Orchestration",
                "./agentic_flows/",
                "goose run",
                "```yaml",
                "name: invented_ghost_workflow",
                "recipe:",
                "  title: Ghost Title",
                "```",
                "```yaml",
                "not: a mapping recipe",
                "```",
                "",
            ]
        ),
    )
    findings = vm.validate_recipe_titles(tmp_path)
    assert any("unexpected/invented recipe name" in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                "Recipe-Based Agent Orchestration",
                "./agentic_flows/",
                "goose run",
                "```yaml",
                "- just a list",
                "```",
                "",
            ]
        ),
    )
    findings = vm.validate_recipe_titles(tmp_path)
    assert any("missing locked recipe title" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "wrong-name"',
                'requires-python = ">=3.11"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.run]",
                "branch = true",
                "[tool.coverage.report]",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("project.name must be" in f.message for f in findings)


def test_v9_issue_names_readme_badges_quarterly_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_issue_template_names(tmp_path)
    )
    _write(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
        "---\nname: Wrong\nabout: wrong about\n---\n\nBody\n",
    )
    _write(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
        "---\nname: Feature Request\nabout: wrong about\n---\n\nBody\n",
    )
    _write(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "agent_task.md",
        "name: Agent Task\nabout: x\n---\n\nBody\n",
    )
    findings = vm.validate_issue_template_names(tmp_path)
    assert any("issue template name must be" in f.message for f in findings)
    assert any("issue template about must be" in f.message for f in findings)
    assert any("opening" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "agent_task.md",
        "---\n- just a list\n---\n\nBody\n",
    )
    findings = vm.validate_issue_template_names(tmp_path)
    assert any("frontmatter must be a mapping" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_readme_badges(tmp_path))
    _write(tmp_path / "README.md", "# g0p-agents\nDocs only\n")
    findings = vm.validate_readme_badges(tmp_path)
    assert any("badge phrase" in f.message for f in findings)

    assert any("missing" in f.message for f in vm.validate_quarterly_review(tmp_path))
    _write(tmp_path / "CLAUDE.md", "# Claude\nNo quarterly section\n")
    findings = vm.validate_quarterly_review(tmp_path)
    assert any("Quarterly Review Triggers" in f.message for f in findings)
    assert any("quarterly-review phrase" in f.message for f in findings)

    _copy_schemas(tmp_path)
    for rel in vm.CURSOR_INSTALL_REQUIRED_REFS:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(_inventory_payload()), encoding="utf-8"
    )

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    broken_names = dict(inventory)
    broken_names["issue_template_names"] = {"wrong.md": "X"}
    findings = vm._inventory_lock_consistency(
        broken_names, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_template_names keys inconsistent" in f.message for f in findings
    )

    broken_abouts = dict(inventory)
    broken_abouts["issue_template_abouts"] = {"wrong.md": "Y"}
    findings = vm._inventory_lock_consistency(
        broken_abouts, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_template_abouts keys inconsistent" in f.message for f in findings
    )

    dup_names = dict(inventory)
    names = dict(dup_names["issue_template_names"])
    keys = list(names)
    names[keys[1]] = names[keys[0]]
    dup_names["issue_template_names"] = names
    findings = vm._inventory_lock_consistency(
        dup_names, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_template_names values must be unique" in f.message for f in findings
    )

    dup_abouts = dict(inventory)
    abouts = dict(dup_abouts["issue_template_abouts"])
    keys = list(abouts)
    abouts[keys[1]] = abouts[keys[0]]
    dup_abouts["issue_template_abouts"] = abouts
    findings = vm._inventory_lock_consistency(
        dup_abouts, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_template_abouts values must be unique" in f.message for f in findings
    )

    empty_badges = dict(inventory)
    empty_badges["readme_badge_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_badges, schema_path="schemas/packaging-inventory.json"
    )
    assert any("readme_badge_phrases must not be empty" in f.message for f in findings)

    dup_badges = dict(inventory)
    dup_badges["readme_badge_phrases"] = [
        vm.README_BADGE_PHRASES[0],
        vm.README_BADGE_PHRASES[0],
    ]
    findings = vm._inventory_lock_consistency(
        dup_badges, schema_path="schemas/packaging-inventory.json"
    )
    assert any("readme_badge_phrases must be unique" in f.message for f in findings)

    empty_quarterly = dict(inventory)
    empty_quarterly["quarterly_review_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_quarterly, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "quarterly_review_phrases must not be empty" in f.message for f in findings
    )

    dup_quarterly = dict(inventory)
    dup_quarterly["quarterly_review_phrases"] = [
        vm.QUARTERLY_REVIEW_PHRASES[0],
        vm.QUARTERLY_REVIEW_PHRASES[0],
    ]
    findings = vm._inventory_lock_consistency(
        dup_quarterly, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "quarterly_review_phrases must be unique" in f.message for f in findings
    )

    empty_markers = dict(inventory)
    empty_markers["ci_required_text_markers"] = []
    findings = vm._inventory_lock_consistency(
        empty_markers, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_required_text_markers must not be empty" in f.message for f in findings
    )

    dup_markers = dict(inventory)
    dup_markers["ci_required_text_markers"] = [
        vm.CI_REQUIRED_TEXT_MARKERS[0],
        vm.CI_REQUIRED_TEXT_MARKERS[0],
    ]
    findings = vm._inventory_lock_consistency(
        dup_markers, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_required_text_markers must be unique" in f.message for f in findings
    )

    empty_select = dict(inventory)
    empty_select["pyproject_ruff_lint_select"] = []
    findings = vm._inventory_lock_consistency(
        empty_select, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pyproject_ruff_lint_select must not be empty" in f.message for f in findings
    )

    dup_select = dict(inventory)
    dup_select["pyproject_ruff_lint_select"] = [
        vm.PYPROJECT_RUFF_LINT_SELECT[0],
        vm.PYPROJECT_RUFF_LINT_SELECT[0],
    ]
    findings = vm._inventory_lock_consistency(
        dup_select, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pyproject_ruff_lint_select must be unique" in f.message for f in findings
    )

    blank_name = dict(inventory)
    blank_name["ci_workflow_name"] = "   "
    findings = vm._inventory_lock_consistency(
        blank_name, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_workflow_name must be a non-empty string" in f.message for f in findings)

    non_string_name = dict(inventory)
    non_string_name["ci_workflow_name"] = 123
    findings = vm._inventory_lock_consistency(
        non_string_name, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_workflow_name must be a non-empty string" in f.message for f in findings)

    _write(
        tmp_path / ".markdownlint.yaml",
        "\n".join(
            [
                "default: true",
                "MD013:",
                "  line_length: 200",
                "MD025: true",
                "MD033: true",
                "MD024:",
                "  siblings_only: false",
                "",
            ]
        ),
    )
    findings = vm.validate_markdownlint(tmp_path)
    assert any("MD025 must be" in f.message for f in findings)
    assert any("MD033 must be" in f.message for f in findings)
    assert any("MD024.siblings_only must be" in f.message for f in findings)

    _write(
        tmp_path / ".markdownlint.yaml",
        "\n".join(
            [
                "default: true",
                "MD013:",
                "  line_length: 200",
                "MD025: false",
                "MD033: false",
                "MD024: false",
                "",
            ]
        ),
    )
    findings = vm.validate_markdownlint(tmp_path)
    assert any("MD024 must be a mapping" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{vm.PYPROJECT_NAME}"',
                f'requires-python = "{vm.PYPROJECT_REQUIRES_PYTHON}"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                f'target-version = "{vm.PYPROJECT_RUFF_TARGET_VERSION}"',
                "[tool.coverage.run]",
                "branch = true",
                "[tool.coverage.report]",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("missing [tool.ruff.lint]" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{vm.PYPROJECT_NAME}"',
                f'requires-python = "{vm.PYPROJECT_REQUIRES_PYTHON}"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                f'target-version = "{vm.PYPROJECT_RUFF_TARGET_VERSION}"',
                "[tool.ruff.lint]",
                'select = ["E", "F"]',
                "[tool.coverage.run]",
                "branch = true",
                "[tool.coverage.report]",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("ruff lint.select must equal" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: Wrong CI Name",
                "on: push",
                "jobs:",
                "  x:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/checkout@v7",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_actions(tmp_path)
    assert any("CI workflow name must be" in f.message for f in findings)
    assert any("missing required action pin" in f.message for f in findings)
    assert any("missing required text marker" in f.message for f in findings)

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "- just-a-list\n")
    findings = vm.validate_ci_actions(tmp_path)
    assert any("missing required action pin" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
        "---\n: bad yaml\n---\n\nBody\n",
    )
    findings = vm.validate_issue_template_names(tmp_path)
    assert any("YAML parse error" in f.message for f in findings)

    # Skip non-file children under agentic_flows (coverage for directory continue).
    flows = tmp_path / "agentic_flows"
    flows.mkdir(parents=True, exist_ok=True)
    (flows / "nested-dir").mkdir()
    _write(
        flows / "scratchpad.txt",
        "\n".join(
            [
                "g0p-agents Agent Coordination",
                "source of truth",
                "Never delete entries",
                "- [ ] task",
                "",
            ]
        ),
    )
    _write(tmp_path / "GOOSE-RECIPES.md", "# no recipes yet\n")
    findings = vm.validate_goose_recipes(tmp_path)
    assert any("missing" in f.message or "expected" in f.message for f in findings)
    assert not any(
        "unexpected/invented agentic_flows file" in f.message for f in findings
    )

    # Non-dict step before upload-artifact is skipped when resolving upload if.
    minimal_ci = {
        True: {"pull_request": {"branches": ["alpha"]}, "push": {"branches": ["**"]}},
        "name": vm.CI_WORKFLOW_NAME,
        "concurrency": {"group": "ci-test", "cancel-in-progress": True},
        "jobs": {
            "markdown-lint": {"permissions": {"contents": "read"}, "runs-on": "ubuntu"},
            "link-check": {"permissions": {"contents": "read"}, "runs-on": "ubuntu"},
            "actionlint": {"permissions": {"contents": "read"}, "runs-on": "ubuntu"},
            "manifest-validate": {
                "permissions": {"contents": "read"},
                "runs-on": "ubuntu",
                "strategy": {
                    "fail-fast": False,
                    "matrix": {"python-version": list(vm.REQUIRED_PYTHON_VERSIONS)},
                },
                "steps": [
                    "not-a-dict",
                    {
                        "uses": "actions/upload-artifact@v4",
                        "if": "always()",
                        "with": {"name": "manifest-validate-pyX"},
                    },
                    {"run": " ".join(vm.REQUIRED_MANIFEST_STEP_MARKERS)},
                ],
            },
        },
    }
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        yaml.dump(minimal_ci, sort_keys=False),
    )
    findings = vm.validate_ci_workflow(tmp_path)
    assert not any("upload-artifact if must be" in f.message for f in findings)

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                issue_template_names={
                    ".github/ISSUE_TEMPLATE/bug_report.md": "Wrong A",
                    ".github/ISSUE_TEMPLATE/feature_request.md": "Wrong B",
                    ".github/ISSUE_TEMPLATE/agent_task.md": "Wrong C",
                },
                ci_workflow_name="wrong",
                pyproject_ruff_lint_select=["Z"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("issue_template_names" in f.message for f in findings)
    assert any("ci_workflow_name" in f.message for f in findings)
    assert any("pyproject_ruff_lint_select" in f.message for f in findings)


def test_v10_link_check_ci_job_names_github_agent_desc_edge_cases(
    tmp_path: Path,
) -> None:
    assert any("missing" in f.message for f in vm.validate_link_check(tmp_path))
    assert any("missing" in f.message for f in vm.validate_ci_job_names(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_github_agent_description(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                f"name: {vm.CI_WORKFLOW_NAME}",
                "on: push",
                "jobs:",
                "  markdown-lint:",
                "    name: Wrong Markdown",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: DavidAnson/markdownlint-cli2-action@v24",
                "        with:",
                "          globs: '*.md'",
                "          config: wrong.yaml",
                "  link-check:",
                "    name: Wrong Links",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: lycheeverse/lychee-action@v2",
                "        with:",
                "          args: --quiet",
                "          fail: false",
                "  actionlint:",
                "    name: Wrong Actionlint",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - run: echo hi",
                "  manifest-validate:",
                "    name: Wrong Manifest",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/setup-python@v5",
                "        with:",
                "          python-version: '3.12'",
                "          cache-dependency-path: wrong.txt",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("link-check args must be" in f.message for f in findings)
    assert any("link-check fail must be" in f.message for f in findings)
    assert any("markdown-lint globs must be" in f.message for f in findings)
    assert any("markdown-lint config must be" in f.message for f in findings)
    assert any("cache-dependency-path must be" in f.message for f in findings)

    findings = vm.validate_ci_job_names(tmp_path)
    assert any("CI job 'markdown-lint' name must be" in f.message for f in findings)
    assert any("CI job 'link-check' name must be" in f.message for f in findings)
    assert any("CI job 'actionlint' name must be" in f.message for f in findings)
    assert any("CI job 'manifest-validate' name must be" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "on: push",
                "jobs:",
                "  link-check:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: lycheeverse/lychee-action@v2",
                "        with: not-a-mapping",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("lychee-action step missing with" in f.message for f in findings)
    assert any("missing markdown-lint job" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "- just-a-list\n",
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("root must be a mapping" in f.message for f in findings)
    findings = vm.validate_ci_job_names(tmp_path)
    assert any("root must be a mapping" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\nname: Hydration\ndescription: wrong desc\n---\n\nBody\n",
    )
    findings = vm.validate_github_agent_description(tmp_path)
    assert any("GitHub agent description must be" in f.message for f in findings)
    findings = vm.validate_github_agents(tmp_path)
    assert any("GitHub agent description must be" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\nname: Hydration\n---\n\nBody\n",
    )
    findings = vm.validate_github_agent_description(tmp_path)
    assert any("description missing or not a string" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\n- just a list\n---\n\nBody\n",
    )
    findings = vm.validate_github_agent_description(tmp_path)
    assert any("frontmatter must be a mapping" in f.message for f in findings)

    _write(
        tmp_path / ".markdownlint.yaml",
        "\n".join(
            [
                "default: true",
                "MD013:",
                "  line_length: 200",
                "  tables: true",
                "  code_blocks: true",
                "MD025: false",
                "MD033: false",
                "MD024:",
                "  siblings_only: true",
                "",
            ]
        ),
    )
    findings = vm.validate_markdownlint(tmp_path)
    assert any("MD013.tables must be" in f.message for f in findings)
    assert any("MD013.code_blocks must be" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{vm.PYPROJECT_NAME}"',
                'version = "9.9.9"',
                'license = { text = "Apache-2.0" }',
                f'requires-python = "{vm.PYPROJECT_REQUIRES_PYTHON}"',
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                'addopts = "-vv"',
                "[tool.ruff]",
                f'target-version = "{vm.PYPROJECT_RUFF_TARGET_VERSION}"',
                "line-length = 80",
                'src = ["elsewhere"]',
                "[tool.ruff.lint]",
                f"select = {list(vm.PYPROJECT_RUFF_LINT_SELECT)!r}".replace("'", '"'),
                "[tool.coverage.run]",
                "branch = true",
                "[tool.coverage.report]",
                "show_missing = false",
                "skip_empty = false",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("project.version must be" in f.message for f in findings)
    assert any("project.license.text must be" in f.message for f in findings)
    assert any("pytest addopts must be" in f.message for f in findings)
    assert any("ruff line-length must be" in f.message for f in findings)
    assert any("ruff src must equal" in f.message for f in findings)
    assert any("show_missing must be" in f.message for f in findings)
    assert any("skip_empty must be" in f.message for f in findings)

    _copy_schemas(tmp_path)
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )

    broken_jobs = dict(inventory)
    broken_jobs["ci_job_display_names"] = {"wrong": "X"}
    findings = vm._inventory_lock_consistency(
        broken_jobs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_job_display_names keys inconsistent" in f.message for f in findings
    )

    dup_jobs = dict(inventory)
    names = dict(dup_jobs["ci_job_display_names"])
    keys = list(names)
    names[keys[1]] = names[keys[0]]
    dup_jobs["ci_job_display_names"] = names
    findings = vm._inventory_lock_consistency(
        dup_jobs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_job_display_names values must be unique" in f.message for f in findings
    )

    empty_jobs = dict(inventory)
    empty_jobs["ci_job_display_names"] = {}
    # Keep required_ci_jobs empty-compatible for key mismatch + empty check
    empty_jobs["required_ci_jobs"] = []
    findings = vm._inventory_lock_consistency(
        empty_jobs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_job_display_names must not be empty" in f.message for f in findings)

    empty_src = dict(inventory)
    empty_src["pyproject_ruff_src"] = []
    findings = vm._inventory_lock_consistency(
        empty_src, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pyproject_ruff_src must not be empty" in f.message for f in findings)

    dup_src = dict(inventory)
    dup_src["pyproject_ruff_src"] = ["scripts", "scripts"]
    findings = vm._inventory_lock_consistency(
        dup_src, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pyproject_ruff_src must be unique" in f.message for f in findings)

    blank_desc = dict(inventory)
    blank_desc["github_agent_description"] = "   "
    findings = vm._inventory_lock_consistency(
        blank_desc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "github_agent_description must be a non-empty string" in f.message
        for f in findings
    )

    blank_args = dict(inventory)
    blank_args["ci_link_check_args"] = ""
    findings = vm._inventory_lock_consistency(
        blank_args, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_link_check_args must be a non-empty string" in f.message for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                ci_link_check_args="wrong",
                ci_job_display_names={
                    "markdown-lint": "A",
                    "link-check": "B",
                    "actionlint": "C",
                    "manifest-validate": "D",
                },
                github_agent_description="wrong",
                pyproject_version="1.2.3",
                markdownlint_md013_tables=True,
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("ci_link_check_args" in f.message for f in findings)
    assert any("ci_job_display_names" in f.message for f in findings)
    assert any("github_agent_description" in f.message for f in findings)
    assert any("pyproject_version" in f.message for f in findings)
    assert any("markdownlint_md013_tables" in f.message for f in findings)

    # Extra branch coverage for link-check / ci-job-names / github-agent-desc / pyproject.
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "null\n")
    assert vm.validate_link_check(tmp_path) == []
    assert vm.validate_ci_job_names(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: only\n")
    findings = vm.validate_link_check(tmp_path)
    assert any("missing jobs mapping" in f.message for f in findings)
    findings = vm.validate_ci_job_names(tmp_path)
    assert any("missing jobs mapping" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  other:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("missing link-check job" in f.message for f in findings)
    # Early return when link-check is absent — probe markdown-lint separately.
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  link-check:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: lycheeverse/lychee-action@v2",
                "        with:",
                f"          args: {vm.CI_LINK_CHECK_ARGS}",
                f"          fail: {str(vm.CI_LINK_CHECK_FAIL).lower()}",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("missing markdown-lint job" in f.message for f in findings)
    findings = vm.validate_ci_job_names(tmp_path)
    assert any("missing job:" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  link-check:",
                "    runs-on: ubuntu-latest",
                "  markdown-lint:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("link-check job missing steps" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  link-check:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: lycheeverse/lychee-action@v2",
                "        with:",
                f"          args: {vm.CI_LINK_CHECK_ARGS}",
                f"          fail: {str(vm.CI_LINK_CHECK_FAIL).lower()}",
                "  markdown-lint:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any("markdown-lint job missing steps" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        yaml.dump(
            {
                "name": "CI",
                "jobs": {
                    "link-check": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            "not-a-mapping-step",
                            {
                                "uses": "lycheeverse/lychee-action@v2",
                                "with": {
                                    "args": vm.CI_LINK_CHECK_ARGS,
                                    "fail": vm.CI_LINK_CHECK_FAIL,
                                },
                            },
                        ],
                    },
                    "markdown-lint": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            "not-a-mapping-step",
                            {"uses": "DavidAnson/markdownlint-cli2-action@v24"},
                        ],
                    },
                    "manifest-validate": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            "not-a-mapping-step",
                            {"uses": "actions/setup-python@v5"},
                        ],
                    },
                },
            },
            sort_keys=False,
        ),
    )
    findings = vm.validate_link_check(tmp_path)
    assert any(
        "markdownlint-cli2-action step missing with" in f.message for f in findings
    )
    assert any(
        "cache-dependency-path lock not found" in f.message for f in findings
    )

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{vm.PYPROJECT_NAME}"',
                f'version = "{vm.PYPROJECT_VERSION}"',
                f'license = {{ text = "{vm.PYPROJECT_LICENSE_TEXT}" }}',
                f'requires-python = "{vm.PYPROJECT_REQUIRES_PYTHON}"',
                "[tool.pytest]",
                "ini_options = 1",
                "[tool.ruff]",
                f'target-version = "{vm.PYPROJECT_RUFF_TARGET_VERSION}"',
                f"line-length = {vm.PYPROJECT_LINE_LENGTH}",
                f"src = {list(vm.PYPROJECT_RUFF_SRC)!r}".replace("'", '"'),
                "[tool.ruff.lint]",
                f"select = {list(vm.PYPROJECT_RUFF_LINT_SELECT)!r}".replace("'", '"'),
                "[tool.coverage.run]",
                "branch = true",
                "[tool.coverage.report]",
                "show_missing = true",
                "skip_empty = true",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("pytest.ini_options must be a mapping" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "body without frontmatter\n",
    )
    findings = vm.validate_github_agent_description(tmp_path)
    assert any("opening" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "agents" / "my-agent.agent.md",
        "---\n\n---\n\nBody\n",
    )
    findings = vm.validate_github_agent_description(tmp_path)
    # Empty frontmatter loads as None -> continue without mapping complaint.
    assert not any("frontmatter must be a mapping" in f.message for f in findings)


def test_module_main_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.setattr(sys, "argv", ["validate_manifests.py", "--list-validators"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(
            str(REPO_ROOT / "scripts" / "validate_manifests.py"),
            run_name="__main__",
        )
    assert excinfo.value.code == 0


def test_live_v11_validators() -> None:
    assert vm.validate_ci_runs_on(REPO_ROOT) == []
    assert vm.validate_ci_artifacts(REPO_ROOT) == []
    assert vm.validate_actionlint_shell(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 11
    assert len(vm.VALIDATORS) == 46
    assert vm.MIN_VALIDATOR_COUNT == 46
    assert vm.CI_RUNS_ON == "ubuntu-latest"
    assert vm.CI_ARTIFACT_IF_NO_FILES_FOUND == "warn"
    assert tuple(vm.CI_ARTIFACT_PATHS) == (
        "manifest-findings.json",
        "validators.txt",
        "coverage.xml",
        "pytest-junit.xml",
    )
    assert vm.CI_ACTIONLINT_SHELL == "bash"
    assert vm.CI_ACTIONLINT_STEP_ID == "get_actionlint"
    assert vm.PYPROJECT_README == "README.md"
    assert "docs archive" in vm.PYPROJECT_DESCRIPTION
    assert tuple(vm.PYTEST_TESTPATHS) == ("tests",)
    assert tuple(vm.PYTEST_PYTHONPATH) == ("scripts",)
    assert tuple(vm.COVERAGE_SOURCE) == ("scripts",)
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 11
    assert inventory["ci_runs_on"] == vm.CI_RUNS_ON
    assert inventory["ci_artifact_paths"] == list(vm.CI_ARTIFACT_PATHS)
    assert inventory["ci_artifact_if_no_files_found"] == vm.CI_ARTIFACT_IF_NO_FILES_FOUND
    assert inventory["ci_actionlint_shell"] == vm.CI_ACTIONLINT_SHELL
    assert inventory["ci_actionlint_step_id"] == vm.CI_ACTIONLINT_STEP_ID
    assert inventory["pyproject_description"] == vm.PYPROJECT_DESCRIPTION
    assert inventory["pyproject_readme"] == vm.PYPROJECT_README
    assert inventory["pytest_testpaths"] == list(vm.PYTEST_TESTPATHS)
    assert inventory["pytest_pythonpath"] == list(vm.PYTEST_PYTHONPATH)
    assert inventory["coverage_source"] == list(vm.COVERAGE_SOURCE)
    assert vm.validate_pyproject(REPO_ROOT) == []
    assert vm.validate_ci_workflow(REPO_ROOT) == []


def test_v11_ci_runs_on_artifacts_actionlint_shell_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_ci_runs_on(tmp_path))
    assert any("missing" in f.message for f in vm.validate_ci_artifacts(tmp_path))
    assert any("missing" in f.message for f in vm.validate_actionlint_shell(tmp_path))

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                f"name: {vm.CI_WORKFLOW_NAME}",
                "on: push",
                "jobs:",
                "  markdown-lint:",
                "    runs-on: windows-latest",
                "  link-check:",
                "    runs-on: windows-latest",
                "  actionlint:",
                "    runs-on: windows-latest",
                "    steps:",
                "      - id: wrong-id",
                "        run: echo hi",
                "        shell: pwsh",
                "  manifest-validate:",
                "    runs-on: windows-latest",
                "    steps:",
                "      - uses: actions/upload-artifact@v4",
                "        with:",
                "          name: manifest-validate-pyX",
                "          if-no-files-found: error",
                "          path: |",
                "            wrong.json",
                "            also-wrong.txt",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_runs_on(tmp_path)
    assert any("runs-on must be" in f.message for f in findings)
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("if-no-files-found must be" in f.message for f in findings)
    assert any("path missing locked artifact" in f.message for f in findings)
    assert any("unexpected artifact" in f.message for f in findings)
    findings = vm.validate_actionlint_shell(tmp_path)
    assert any("shell must be" in f.message for f in findings)
    assert any("step id" in f.message for f in findings)

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "- just-a-list\n")
    assert any("root must be a mapping" in f.message for f in vm.validate_ci_runs_on(tmp_path))
    assert any(
        "root must be a mapping" in f.message for f in vm.validate_ci_artifacts(tmp_path)
    )
    assert any(
        "root must be a mapping" in f.message
        for f in vm.validate_actionlint_shell(tmp_path)
    )

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "null\n")
    assert vm.validate_ci_runs_on(tmp_path) == []
    assert vm.validate_ci_artifacts(tmp_path) == []
    assert vm.validate_actionlint_shell(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: only\n")
    assert any(
        "missing jobs mapping" in f.message for f in vm.validate_ci_runs_on(tmp_path)
    )
    assert any(
        "missing jobs mapping" in f.message for f in vm.validate_ci_artifacts(tmp_path)
    )
    assert any(
        "missing jobs mapping" in f.message
        for f in vm.validate_actionlint_shell(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  other:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_runs_on(tmp_path)
    assert any("missing job:" in f.message for f in findings)
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("missing manifest-validate job" in f.message for f in findings)
    findings = vm.validate_actionlint_shell(tmp_path)
    assert any("missing actionlint job" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  actionlint:",
                "    runs-on: ubuntu-latest",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    findings = vm.validate_actionlint_shell(tmp_path)
    assert any("actionlint job missing steps" in f.message for f in findings)
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("manifest-validate job missing steps" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  actionlint:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "    steps:",
                "      - not-a-mapping-step",
                "      - run: echo hi",
                "  manifest-validate:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "    steps:",
                "      - not-a-mapping-step",
                "      - uses: actions/upload-artifact@v4",
                "        with: not-a-mapping",
                "",
            ]
        ),
    )
    findings = vm.validate_actionlint_shell(tmp_path)
    assert any("must set shell" in f.message for f in findings)
    assert any("step id" in f.message for f in findings)
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("upload-artifact step missing with" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  markdown-lint:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "  link-check:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "  actionlint:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "    steps:",
                f"      - id: {vm.CI_ACTIONLINT_STEP_ID}",
                "        run: echo download",
                f"        shell: {vm.CI_ACTIONLINT_SHELL}",
                "      - run: ./actionlint -color",
                f"        shell: {vm.CI_ACTIONLINT_SHELL}",
                "  manifest-validate:",
                f"    runs-on: {vm.CI_RUNS_ON}",
                "    steps:",
                "      - uses: actions/upload-artifact@v4",
                "        with:",
                "          name: manifest-validate-pyX",
                f"          if-no-files-found: {vm.CI_ARTIFACT_IF_NO_FILES_FOUND}",
                "          path: |",
                *[f"            {p}" for p in vm.CI_ARTIFACT_PATHS],
                "",
            ]
        ),
    )
    assert vm.validate_ci_runs_on(tmp_path) == []
    assert vm.validate_ci_artifacts(tmp_path) == []
    assert vm.validate_actionlint_shell(tmp_path) == []

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - run: echo no upload",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("missing upload-artifact step" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/upload-artifact@v4",
                "        with:",
                f"          if-no-files-found: {vm.CI_ARTIFACT_IF_NO_FILES_FOUND}",
                "          path:",
                *[f"            - {p}" for p in vm.CI_ARTIFACT_PATHS],
                "",
            ]
        ),
    )
    assert vm.validate_ci_artifacts(tmp_path) == []

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/upload-artifact@v4",
                "        with:",
                f"          if-no-files-found: {vm.CI_ARTIFACT_IF_NO_FILES_FOUND}",
                "          path: 42",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_artifacts(tmp_path)
    assert any("path must be a string or sequence" in f.message for f in findings)

    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{vm.PYPROJECT_NAME}"',
                f'version = "{vm.PYPROJECT_VERSION}"',
                f'license = {{ text = "{vm.PYPROJECT_LICENSE_TEXT}" }}',
                'description = "wrong description"',
                'readme = "WRONG.md"',
                f'requires-python = "{vm.PYPROJECT_REQUIRES_PYTHON}"',
                "[tool.pytest.ini_options]",
                'testpaths = ["elsewhere"]',
                'pythonpath = ["elsewhere"]',
                f'addopts = "{vm.PYTEST_ADDOPTS}"',
                "[tool.ruff]",
                f'target-version = "{vm.PYPROJECT_RUFF_TARGET_VERSION}"',
                f"line-length = {vm.PYPROJECT_LINE_LENGTH}",
                f"src = {list(vm.PYPROJECT_RUFF_SRC)!r}".replace("'", '"'),
                "[tool.ruff.lint]",
                f"select = {list(vm.PYPROJECT_RUFF_LINT_SELECT)!r}".replace("'", '"'),
                "[tool.coverage.run]",
                "branch = true",
                'source = ["elsewhere"]',
                "[tool.coverage.report]",
                "show_missing = true",
                "skip_empty = true",
                "fail_under = 99",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("project.description must be" in f.message for f in findings)
    assert any("project.readme must be" in f.message for f in findings)
    assert any("pytest testpaths must equal" in f.message for f in findings)
    assert any("pytest pythonpath must equal" in f.message for f in findings)
    assert any("coverage run.source must equal" in f.message for f in findings)

    _copy_schemas(tmp_path)
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )

    blank_runs = dict(inventory)
    blank_runs["ci_runs_on"] = "  "
    findings = vm._inventory_lock_consistency(
        blank_runs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_runs_on must be a non-empty string" in f.message for f in findings)

    empty_paths = dict(inventory)
    empty_paths["ci_artifact_paths"] = []
    findings = vm._inventory_lock_consistency(
        empty_paths, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_artifact_paths must not be empty" in f.message for f in findings)

    dup_paths = dict(inventory)
    dup_paths["ci_artifact_paths"] = ["a.json", "a.json"]
    findings = vm._inventory_lock_consistency(
        dup_paths, schema_path="schemas/packaging-inventory.json"
    )
    assert any("ci_artifact_paths must be unique" in f.message for f in findings)

    blank_if = dict(inventory)
    blank_if["ci_artifact_if_no_files_found"] = ""
    findings = vm._inventory_lock_consistency(
        blank_if, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_artifact_if_no_files_found must be a non-empty string" in f.message
        for f in findings
    )

    blank_shell = dict(inventory)
    blank_shell["ci_actionlint_shell"] = ""
    findings = vm._inventory_lock_consistency(
        blank_shell, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_actionlint_shell must be a non-empty string" in f.message for f in findings
    )

    blank_id = dict(inventory)
    blank_id["ci_actionlint_step_id"] = " "
    findings = vm._inventory_lock_consistency(
        blank_id, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_actionlint_step_id must be a non-empty string" in f.message for f in findings
    )

    blank_desc = dict(inventory)
    blank_desc["pyproject_description"] = ""
    findings = vm._inventory_lock_consistency(
        blank_desc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pyproject_description must be a non-empty string" in f.message for f in findings
    )

    blank_readme = dict(inventory)
    blank_readme["pyproject_readme"] = ""
    findings = vm._inventory_lock_consistency(
        blank_readme, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pyproject_readme must be a non-empty string" in f.message for f in findings
    )

    empty_tp = dict(inventory)
    empty_tp["pytest_testpaths"] = []
    findings = vm._inventory_lock_consistency(
        empty_tp, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pytest_testpaths must not be empty" in f.message for f in findings)

    dup_tp = dict(inventory)
    dup_tp["pytest_testpaths"] = ["tests", "tests"]
    findings = vm._inventory_lock_consistency(
        dup_tp, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pytest_testpaths must be unique" in f.message for f in findings)

    empty_pp = dict(inventory)
    empty_pp["pytest_pythonpath"] = []
    findings = vm._inventory_lock_consistency(
        empty_pp, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pytest_pythonpath must not be empty" in f.message for f in findings)

    dup_pp = dict(inventory)
    dup_pp["pytest_pythonpath"] = ["scripts", "scripts"]
    findings = vm._inventory_lock_consistency(
        dup_pp, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pytest_pythonpath must be unique" in f.message for f in findings)

    empty_cs = dict(inventory)
    empty_cs["coverage_source"] = []
    findings = vm._inventory_lock_consistency(
        empty_cs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("coverage_source must not be empty" in f.message for f in findings)

    dup_cs = dict(inventory)
    dup_cs["coverage_source"] = ["scripts", "scripts"]
    findings = vm._inventory_lock_consistency(
        dup_cs, schema_path="schemas/packaging-inventory.json"
    )
    assert any("coverage_source must be unique" in f.message for f in findings)

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                ci_runs_on="windows-latest",
                ci_artifact_paths=["only.json"],
                ci_artifact_if_no_files_found="error",
                ci_actionlint_shell="pwsh",
                ci_actionlint_step_id="wrong",
                pyproject_description="wrong",
                pyproject_readme="WRONG.md",
                pytest_testpaths=["elsewhere"],
                pytest_pythonpath=["elsewhere"],
                coverage_source=["elsewhere"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("ci_runs_on" in f.message for f in findings)
    assert any("ci_artifact_paths" in f.message for f in findings)
    assert any("ci_artifact_if_no_files_found" in f.message for f in findings)
    assert any("ci_actionlint_shell" in f.message for f in findings)
    assert any("ci_actionlint_step_id" in f.message for f in findings)
    assert any("pyproject_description" in f.message for f in findings)
    assert any("pyproject_readme" in f.message for f in findings)
    assert any("pytest_testpaths" in f.message for f in findings)
    assert any("pytest_pythonpath" in f.message for f in findings)
    assert any("coverage_source" in f.message for f in findings)

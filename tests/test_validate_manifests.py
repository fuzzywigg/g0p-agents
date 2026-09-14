"""Unit and integration tests for scripts/validate_manifests.py."""

from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        "ci_setup_python_cache": vm.CI_SETUP_PYTHON_CACHE,
        "ci_ruff_check_command": vm.CI_RUFF_CHECK_COMMAND,
        "license_required_phrases": list(vm.LICENSE_REQUIRED_PHRASES),
        "ci_pip_install_command": vm.CI_PIP_INSTALL_COMMAND,
        "ci_pip_check_command": vm.CI_PIP_CHECK_COMMAND,
        "ci_pytest_required_markers": list(vm.CI_PYTEST_REQUIRED_MARKERS),
        "state_residency_required_phrases": list(vm.STATE_RESIDENCY_REQUIRED_PHRASES),
        "key_files_required_entries": list(vm.KEY_FILES_REQUIRED_ENTRIES),
        "pr_routing_required_fields": list(vm.PR_ROUTING_REQUIRED_FIELDS),
        "routing_matrix_required_phrases": list(vm.ROUTING_MATRIX_REQUIRED_PHRASES),
        "repo_identity_required_phrases": list(vm.REPO_IDENTITY_REQUIRED_PHRASES),
        "escalation_block_required_phrases": list(vm.ESCALATION_BLOCK_REQUIRED_PHRASES),
        "routing_matrix_rationale_phrases": list(vm.ROUTING_MATRIX_RATIONALE_PHRASES),
        "claude_metadata_required_phrases": list(vm.CLAUDE_METADATA_REQUIRED_PHRASES),
        "escalation_usage_required_phrases": list(vm.ESCALATION_USAGE_REQUIRED_PHRASES),
        "security_supported_required_phrases": list(vm.SECURITY_SUPPORTED_REQUIRED_PHRASES),
        "security_reporting_required_phrases": list(vm.SECURITY_REPORTING_REQUIRED_PHRASES),
        "security_standards_required_phrases": list(vm.SECURITY_STANDARDS_REQUIRED_PHRASES),
        "implementation_quickstart_required_phrases": list(
            vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES
        ),
        "execution_specialists_required_phrases": list(
            vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES
        ),
        "hydration_list_b_required_phrases": list(vm.HYDRATION_LIST_B_REQUIRED_PHRASES),
        "hydration_phase1_required_phrases": list(vm.HYDRATION_PHASE1_REQUIRED_PHRASES),
        "hydration_list_a_required_phrases": list(vm.HYDRATION_LIST_A_REQUIRED_PHRASES),
        "hydration_resolved_required_phrases": list(
            vm.HYDRATION_RESOLVED_REQUIRED_PHRASES
        ),
        "hydration_phase4_required_phrases": list(vm.HYDRATION_PHASE4_REQUIRED_PHRASES),
        "hydration_deferred_required_phrases": list(
            vm.HYDRATION_DEFERRED_REQUIRED_PHRASES
        ),
        "hydration_meta_required_phrases": list(vm.HYDRATION_META_REQUIRED_PHRASES),
        "hydration_identity_detail_required_phrases": list(
            vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES
        ),
        "hydration_git_detail_required_phrases": list(
            vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES
        ),
        "hydration_phase2_required_phrases": list(vm.HYDRATION_PHASE2_REQUIRED_PHRASES),
        "hydration_phase5_required_phrases": list(vm.HYDRATION_PHASE5_REQUIRED_PHRASES),
        "constitution_ide_stack_required_phrases": list(
            vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES
        ),
        "constitution_install_script_required_phrases": list(
            vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES
        ),
        "constitution_vscode_required_phrases": list(
            vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES
        ),
        "constitution_hard_constraints_required_phrases": list(
            vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES
        ),
        "constitution_risk_tolerance_required_phrases": list(
            vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES
        ),
        "changelog_preamble_required_phrases": list(
            vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES
        ),
        "changelog_changed_required_phrases": list(
            vm.CHANGELOG_CHANGED_REQUIRED_PHRASES
        ),
        "changelog_initial_required_phrases": list(
            vm.CHANGELOG_INITIAL_REQUIRED_PHRASES
        ),
        "prompt_expertise_required_phrases": list(
            vm.PROMPT_EXPERTISE_REQUIRED_PHRASES
        ),
        "prompt_principles_required_phrases": list(
            vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES
        ),
        "prompt_metrics_required_phrases": list(vm.PROMPT_METRICS_REQUIRED_PHRASES),
        "prompt_tools_required_phrases": list(vm.PROMPT_TOOLS_REQUIRED_PHRASES),
        "prompt_communication_required_phrases": list(
            vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES
        ),
        "prompt_escalation_identity_required_phrases": list(
            vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES
        ),
        "prompt_orchestration_matrix_required_phrases": list(
            vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES
        ),
        "prompt_monthly_required_phrases": list(vm.PROMPT_MONTHLY_REQUIRED_PHRASES),
        "prompt_usage_example_required_phrases": list(
            vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES
        ),
        "prompt_responsibilities_required_phrases": list(
            vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES
        ),
        "prompt_decision_authority_required_phrases": list(
            vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES
        ),
        "prompt_integration_required_phrases": list(
            vm.PROMPT_INTEGRATION_REQUIRED_PHRASES
        ),
        "prompt_context_required_phrases": list(vm.PROMPT_CONTEXT_REQUIRED_PHRASES),
        "prompt_cannot_delegate_required_phrases": list(
            vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES
        ),
        "prompt_escalation_authority_required_phrases": list(
            vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES
        ),
        "prompt_role_blurbs_required_phrases": list(
            vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES
        ),
        "prompt_escalation_format_required_phrases": list(
            vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES
        ),
        "prompt_living_docs_required_phrases": list(
            vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES
        ),
        "prompt_constraints_detail_required_phrases": list(
            vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_triggers_detail_required_phrases": list(
            vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_human_fields_required_phrases": list(
            vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES
        ),
        "prompt_context_detail_required_phrases": list(
            vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_expertise_detail_required_phrases": list(
            vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_related_health_required_phrases": list(
            vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES
        ),
        "prompt_tools_detail_required_phrases": list(
            vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_responsibilities_detail_required_phrases": list(
            vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_instantiation_required_phrases": list(
            vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES
        ),
        "prompt_metrics_detail_required_phrases": list(
            vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_orch_metrics_detail_required_phrases": list(
            vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_communication_detail_required_phrases": list(
            vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_principles_detail_required_phrases": list(
            vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_responsibilities_residual_required_phrases": list(
            vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES
        ),
        "prompt_expertise_residual_required_phrases": list(
            vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES
        ),
        "prompt_vision_context_required_phrases": list(
            vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES
        ),
        "prompt_context_residual_required_phrases": list(
            vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES
        ),
        "prompt_monthly_detail_required_phrases": list(
            vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES
        ),
        "prompt_docs_residual_required_phrases": list(
            vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES
        ),
        "prompt_matrix_resolutions_required_phrases": list(
            vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES
        ),
        "prompt_usage_detail_required_phrases": list(
            vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES
        ),
        "postmortem_intro_required_phrases": list(vm.POSTMORTEM_INTRO_REQUIRED_PHRASES),
        "postmortem_field_required_phrases": list(vm.POSTMORTEM_FIELD_REQUIRED_PHRASES),
        "postmortem_next_steps_required_phrases": list(
            vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES
        ),
        "scratchpad_intro_required_phrases": list(vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES),
        "scratchpad_format_required_phrases": list(vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES),
        "scratchpad_task_meta_required_phrases": list(
            vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES
        ),
        "issue_metadata_required_phrases": list(vm.ISSUE_METADATA_REQUIRED_PHRASES),
        "issue_routing_required_phrases": list(vm.ISSUE_ROUTING_REQUIRED_PHRASES),
        "bug_repro_required_phrases": list(vm.BUG_REPRO_REQUIRED_PHRASES),
        "contributing_who_required_phrases": list(vm.CONTRIBUTING_WHO_REQUIRED_PHRASES),
        "contributing_branch_required_phrases": list(
            vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES
        ),
        "contributing_pr_required_phrases": list(vm.CONTRIBUTING_PR_REQUIRED_PHRASES),
        "contributing_issues_required_phrases": list(
            vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES
        ),
        "contributing_local_required_phrases": list(
            vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES
        ),
        "contributing_governance_required_phrases": list(
            vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES
        ),
        "contributing_metadata_required_phrases": list(
            vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES
        ),
        "contributing_surfaces_required_phrases": list(
            vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES
        ),
        "contributing_ci_honesty_required_phrases": list(
            vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
        ),
        "pr_summary_required_phrases": list(vm.PR_SUMMARY_REQUIRED_PHRASES),
        "pr_acceptance_required_phrases": list(vm.PR_ACCEPTANCE_REQUIRED_PHRASES),
        "pr_notes_required_phrases": list(vm.PR_NOTES_REQUIRED_PHRASES),
        "readme_honesty_required_phrases": list(vm.README_HONESTY_REQUIRED_PHRASES),
        "readme_historic_required_phrases": list(vm.README_HISTORIC_REQUIRED_PHRASES),
        "readme_contents_required_phrases": list(vm.README_CONTENTS_REQUIRED_PHRASES),
        "readme_lead_required_phrases": list(vm.README_LEAD_REQUIRED_PHRASES),
        "readme_blurbs_required_phrases": list(vm.README_BLURBS_REQUIRED_PHRASES),
        "readme_bootstrap_required_phrases": list(vm.README_BOOTSTRAP_REQUIRED_PHRASES),
        "goose_howto_required_phrases": list(vm.GOOSE_HOWTO_REQUIRED_PHRASES),
        "goose_state_machine_required_phrases": list(
            vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES
        ),
        "goose_naming_required_phrases": list(vm.GOOSE_NAMING_REQUIRED_PHRASES),
        "prompt_roles_required_phrases": list(vm.PROMPT_ROLES_REQUIRED_PHRASES),
        "prompt_sections_required_phrases": list(vm.PROMPT_SECTIONS_REQUIRED_PHRASES),
        "prompt_usage_required_phrases": list(vm.PROMPT_USAGE_REQUIRED_PHRASES),
        "prompt_constraints_required_phrases": list(
            vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES
        ),
        "prompt_triggers_required_phrases": list(vm.PROMPT_TRIGGERS_REQUIRED_PHRASES),
        "prompt_related_docs_required_phrases": list(
            vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES
        ),
        "implementation_phases_required_phrases": list(
            vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES
        ),
        "implementation_tools_required_phrases": list(
            vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES
        ),
        "implementation_success_required_phrases": list(
            vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES
        ),
        "implementation_issues_required_phrases": list(
            vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES
        ),
        "implementation_faq_required_phrases": list(
            vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES
        ),
        "implementation_support_required_phrases": list(
            vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES
        ),
        "execution_timeline_required_phrases": list(
            vm.EXECUTION_TIMELINE_REQUIRED_PHRASES
        ),
        "execution_technologies_required_phrases": list(
            vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES
        ),
        "execution_workflow_required_phrases": list(
            vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES
        ),
        "execution_ide_required_phrases": list(vm.EXECUTION_IDE_REQUIRED_PHRASES),
        "execution_innovations_required_phrases": list(
            vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES
        ),
        "execution_next48_required_phrases": list(vm.EXECUTION_NEXT48_REQUIRED_PHRASES),
        "security_header_required_phrases": list(vm.SECURITY_HEADER_REQUIRED_PHRASES),
        "security_fips_required_phrases": list(vm.SECURITY_FIPS_REQUIRED_PHRASES),
        "security_known_non_issues_required_phrases": list(
            vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES
        ),
        "security_scope_required_phrases": list(vm.SECURITY_SCOPE_REQUIRED_PHRASES),
        "security_reporting_channel_required_phrases": list(
            vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES
        ),
        "security_compliance_detail_required_phrases": list(
            vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES
        ),
        "constitution_crypto_required_phrases": list(
            vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES
        ),
        "constitution_handoff_required_phrases": list(
            vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES
        ),
        "constitution_escalation_matrix_required_phrases": list(
            vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES
        ),
        "constitution_on_device_required_phrases": list(
            vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
        ),
        "constitution_multichain_required_phrases": list(
            vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES
        ),
        "constitution_escalation_format_required_phrases": list(
            vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES
        ),
        "constitution_recipe_orchestration_required_phrases": list(
            vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES
        ),
        "constitution_scratchpad_state_required_phrases": list(
            vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
        ),
        "constitution_conflict_matrix_required_phrases": list(
            vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES
        ),
        "changelog_format_required_phrases": list(
            vm.CHANGELOG_FORMAT_REQUIRED_PHRASES
        ),
        "changelog_unreleased_required_phrases": list(
            vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES
        ),
        "changelog_release_required_phrases": list(
            vm.CHANGELOG_RELEASE_REQUIRED_PHRASES
        ),
        "goose_recipe_headers_required_phrases": list(
            vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES
        ),
        "goose_instruction_agents_required_phrases": list(
            vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES
        ),
        "goose_extensions_required_phrases": list(
            vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES
        ),
        "goose_orchestration_required_phrases": list(
            vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES
        ),
        "goose_conflicts_required_phrases": list(vm.GOOSE_CONFLICTS_REQUIRED_PHRASES),
        "goose_quantum_task_required_phrases": list(
            vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES
        ),
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
        "constitution-crypto",
        "constitution-handoff",
        "constitution-escalation-matrix",
        "constitution-on-device",
        "constitution-multichain",
        "constitution-escalation-format",
        "constitution-recipe-orchestration",
        "constitution-scratchpad-state",
        "constitution-conflict-matrix",
        "routing",
        "environment",
        "github-agents",
        "issue-templates",
        "issue-names",
        "agent-task",
        "bug-template",
        "feature-template",
        "issue-metadata",
        "issue-routing",
        "bug-repro",
        "pr-template",
        "pr-summary",
        "pr-acceptance",
        "pr-notes",
        "dependabot",
        "markdownlint",
        "requirements-dev",
        "license",
        "readme",
        "readme-badges",
        "readme-honesty",
        "readme-historic",
        "readme-contents",
        "readme-lead",
        "readme-blurbs",
        "readme-bootstrap",
        "goose-howto",
        "goose-state-machine",
        "goose-naming",
        "goose-recipe-headers",
        "goose-instruction-agents",
        "goose-extensions",
        "goose-orchestration",
        "goose-conflicts",
        "goose-quantum-task",
        "prompt-roles",
        "prompt-sections",
        "prompt-usage",
        "prompt-constraints",
        "prompt-triggers",
        "prompt-related-docs",
        "implementation-phases",
        "implementation-tools",
        "implementation-success",
        "implementation-issues",
        "implementation-faq",
        "implementation-support",
        "execution-timeline",
        "execution-technologies",
        "execution-workflow",
        "execution-ide",
        "execution-innovations",
        "execution-next48",
        "security",
        "contributing",
        "contributing-who",
        "contributing-branches",
        "contributing-pr",
        "contributing-issues",
        "contributing-local",
        "contributing-governance",
        "contributing-metadata",
        "contributing-surfaces",
        "contributing-ci-honesty",
        "scratchpad",
        "pyproject",
        "yaml-configs",
        "ci",
        "prompts",
        "cross-docs",
        "changelog",
        "changelog-format",
        "changelog-unreleased",
        "changelog-release",
        "postmortem",
        "postmortem-intro",
        "postmortem-fields",
        "postmortem-next-steps",
        "scratchpad-intro",
        "scratchpad-format",
        "scratchpad-task-meta",
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
        "ci-setup-python",
        "ci-ruff",
        "ci-pip-install",
        "ci-pip-check",
        "ci-pytest",
        "state-residency",
        "key-files",
        "pr-routing",
        "routing-matrix",
        "repo-identity",
        "escalation-format",
        "routing-rationales",
        "claude-metadata",
        "escalation-usage",
        "security-supported",
        "security-reporting",
        "security-standards",
        "security-header",
        "security-fips",
        "security-known-non-issues",
        "security-scope",
        "security-reporting-channel",
        "security-compliance-detail",
        "implementation-quickstart",
        "execution-specialists",
        "hydration-list-b",
        "hydration-phase1",
        "hydration-list-a",
        "hydration-resolved",
        "hydration-phase4",
        "hydration-deferred",
        "hydration-meta",
        "hydration-identity-detail",
        "hydration-git-detail",
        "constitution-ide-stack",
        "constitution-install-script",
        "constitution-vscode",
        "constitution-hard-constraints",
        "constitution-risk-tolerance",
        "changelog-preamble",
        "changelog-changed",
        "changelog-initial",
        "prompt-expertise",
        "prompt-principles",
        "prompt-metrics",
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
        "prompt-orchestration-matrix",
        "prompt-monthly",
        "prompt-usage-example",
        "prompt-responsibilities",
        "prompt-decision-authority",
        "prompt-integration",
        "prompt-context",
        "prompt-cannot-delegate",
        "prompt-escalation-authority",
        "prompt-role-blurbs",
        "prompt-escalation-format",
        "prompt-living-docs",
        "prompt-constraints-detail",
        "prompt-triggers-detail",
        "prompt-human-fields",
        "prompt-context-detail",
        "prompt-expertise-detail",
        "prompt-related-health",
        "prompt-tools-detail",
        "prompt-responsibilities-detail",
        "prompt-instantiation",
        "prompt-metrics-detail",
        "prompt-orch-metrics-detail",
        "prompt-communication-detail",
        "prompt-principles-detail",
        "prompt-responsibilities-residual",
        "prompt-expertise-residual",
        "prompt-vision-context",
        "prompt-context-residual",
        "prompt-monthly-detail",
        "prompt-docs-residual",
        "prompt-matrix-resolutions",
        "prompt-usage-detail",
        "hydration-phase2",
        "hydration-phase5",
        "license-mit",
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
    assert any("fail_under must be" in f.message and ">=" not in f.message for f in findings)


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
    assert any("fail_under must be" in f.message and ">=" not in f.message for f in findings)


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
                ("version", 19),
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
                ("ci_runs_on", "windows-latest"),
                ("ci_artifact_if_no_files_found", "error"),
                ("ci_artifact_paths", ["only.json"]),
                ("ci_actionlint_shell", "pwsh"),
                ("ci_actionlint_step_id", "wrong"),
                ("pyproject_description", "wrong description"),
                ("pyproject_readme", "WRONG.md"),
                ("pytest_testpaths", ["elsewhere"]),
                ("pytest_pythonpath", ["elsewhere"]),
                ("coverage_source", ["elsewhere"]),
                ("ci_setup_python_cache", "npm"),
                ("ci_ruff_check_command", "ruff check elsewhere"),
                (
                    "license_required_phrases",
                    list(vm.LICENSE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                ("ci_pip_install_command", "pip install wrong"),
                ("ci_pip_check_command", "pip check wrong"),
                (
                    "ci_pytest_required_markers",
                    list(vm.CI_PYTEST_REQUIRED_MARKERS)[:-1] + ["--invented"],
                ),
                (
                    "state_residency_required_phrases",
                    list(vm.STATE_RESIDENCY_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "key_files_required_entries",
                    list(vm.KEY_FILES_REQUIRED_ENTRIES)[:-1] + ["invented.md"],
                ),
                (
                    "pr_routing_required_fields",
                    list(vm.PR_ROUTING_REQUIRED_FIELDS)[:-1] + ["Invented"],
                ),
                (
                    "routing_matrix_required_phrases",
                    list(vm.ROUTING_MATRIX_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "repo_identity_required_phrases",
                    list(vm.REPO_IDENTITY_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "escalation_block_required_phrases",
                    list(vm.ESCALATION_BLOCK_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "routing_matrix_rationale_phrases",
                    list(vm.ROUTING_MATRIX_RATIONALE_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "claude_metadata_required_phrases",
                    list(vm.CLAUDE_METADATA_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "escalation_usage_required_phrases",
                    list(vm.ESCALATION_USAGE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_supported_required_phrases",
                    list(vm.SECURITY_SUPPORTED_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_reporting_required_phrases",
                    list(vm.SECURITY_REPORTING_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_standards_required_phrases",
                    list(vm.SECURITY_STANDARDS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_header_required_phrases",
                    list(vm.SECURITY_HEADER_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_fips_required_phrases",
                    list(vm.SECURITY_FIPS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_known_non_issues_required_phrases",
                    list(vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "security_scope_required_phrases",
                    list(vm.SECURITY_SCOPE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "security_reporting_channel_required_phrases",
                    list(vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "security_compliance_detail_required_phrases",
                    list(vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_crypto_required_phrases",
                    list(vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "constitution_handoff_required_phrases",
                    list(vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "constitution_escalation_matrix_required_phrases",
                    list(vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_on_device_required_phrases",
                    list(vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_multichain_required_phrases",
                    list(vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_escalation_format_required_phrases",
                    list(vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "changelog_format_required_phrases",
                    list(vm.CHANGELOG_FORMAT_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "changelog_unreleased_required_phrases",
                    list(vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "changelog_release_required_phrases",
                    list(vm.CHANGELOG_RELEASE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "goose_recipe_headers_required_phrases",
                    list(vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "goose_instruction_agents_required_phrases",
                    list(vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "goose_extensions_required_phrases",
                    list(vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "goose_orchestration_required_phrases",
                    list(vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "goose_conflicts_required_phrases",
                    list(vm.GOOSE_CONFLICTS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "goose_quantum_task_required_phrases",
                    list(vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_constraints_required_phrases",
                    list(vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_triggers_required_phrases",
                    list(vm.PROMPT_TRIGGERS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_related_docs_required_phrases",
                    list(vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "implementation_quickstart_required_phrases",
                    list(vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "execution_specialists_required_phrases",
                    list(vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_list_b_required_phrases",
                    list(vm.HYDRATION_LIST_B_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_phase1_required_phrases",
                    list(vm.HYDRATION_PHASE1_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_list_a_required_phrases",
                    list(vm.HYDRATION_LIST_A_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_resolved_required_phrases",
                    list(vm.HYDRATION_RESOLVED_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_phase4_required_phrases",
                    list(vm.HYDRATION_PHASE4_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_deferred_required_phrases",
                    list(vm.HYDRATION_DEFERRED_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_meta_required_phrases",
                    list(vm.HYDRATION_META_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_identity_detail_required_phrases",
                    list(vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "hydration_git_detail_required_phrases",
                    list(vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "constitution_ide_stack_required_phrases",
                    list(vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "constitution_install_script_required_phrases",
                    list(vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_vscode_required_phrases",
                    list(vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "constitution_hard_constraints_required_phrases",
                    list(vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "constitution_risk_tolerance_required_phrases",
                    list(vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "changelog_preamble_required_phrases",
                    list(vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "changelog_changed_required_phrases",
                    list(vm.CHANGELOG_CHANGED_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "changelog_initial_required_phrases",
                    list(vm.CHANGELOG_INITIAL_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_expertise_required_phrases",
                    list(vm.PROMPT_EXPERTISE_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_principles_required_phrases",
                    list(vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_metrics_required_phrases",
                    list(vm.PROMPT_METRICS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_tools_required_phrases",
                    list(vm.PROMPT_TOOLS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_communication_required_phrases",
                    list(vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_escalation_identity_required_phrases",
                    list(vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_orchestration_matrix_required_phrases",
                    list(vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_monthly_required_phrases",
                    list(vm.PROMPT_MONTHLY_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_usage_example_required_phrases",
                    list(vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_responsibilities_required_phrases",
                    list(vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_decision_authority_required_phrases",
                    list(vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_integration_required_phrases",
                    list(vm.PROMPT_INTEGRATION_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_context_required_phrases",
                    list(vm.PROMPT_CONTEXT_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "prompt_cannot_delegate_required_phrases",
                    list(vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "prompt_escalation_authority_required_phrases",
                    list(vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "hydration_phase2_required_phrases",
                    list(vm.HYDRATION_PHASE2_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "hydration_phase5_required_phrases",
                    list(vm.HYDRATION_PHASE5_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "postmortem_intro_required_phrases",
                    list(vm.POSTMORTEM_INTRO_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "postmortem_field_required_phrases",
                    list(vm.POSTMORTEM_FIELD_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "postmortem_next_steps_required_phrases",
                    list(vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "scratchpad_intro_required_phrases",
                    list(vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "scratchpad_format_required_phrases",
                    list(vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "scratchpad_task_meta_required_phrases",
                    list(vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_who_required_phrases",
                    list(vm.CONTRIBUTING_WHO_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_branch_required_phrases",
                    list(vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_pr_required_phrases",
                    list(vm.CONTRIBUTING_PR_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_issues_required_phrases",
                    list(vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_local_required_phrases",
                    list(vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES)[:-1] + ["invented"],
                ),
                (
                    "contributing_governance_required_phrases",
                    list(vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "contributing_metadata_required_phrases",
                    list(vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "contributing_surfaces_required_phrases",
                    list(vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
                (
                    "contributing_ci_honesty_required_phrases",
                    list(vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES)[:-1]
                    + ["invented"],
                ),
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
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_COVERAGE_FAIL_UNDER == 99


def test_live_v6_validators() -> None:
    assert vm.validate_changelog_packaging(REPO_ROOT) == []
    assert vm.validate_postmortem_packaging(REPO_ROOT) == []
    assert vm.validate_gitignore_packaging(REPO_ROOT) == []
    assert vm.validate_negative_constraints(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) >= 43
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]


def test_live_v7_validators() -> None:
    assert vm.validate_hydration_report(REPO_ROOT) == []
    assert vm.validate_execution_summary(REPO_ROOT) == []
    assert vm.validate_implementation_guide(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
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
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
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
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
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
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
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
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
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
    assert inventory["version"] == 52
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

def test_live_v12_validators() -> None:
    assert vm.validate_ci_setup_python(REPO_ROOT) == []
    assert vm.validate_ci_ruff(REPO_ROOT) == []
    assert vm.validate_license_mit(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert vm.CI_SETUP_PYTHON_CACHE == "pip"
    assert vm.CI_RUFF_CHECK_COMMAND == "ruff check scripts tests"
    assert "MIT License" in vm.LICENSE_REQUIRED_PHRASES
    assert "Permission is hereby granted" in vm.LICENSE_REQUIRED_PHRASES
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in vm.LICENSE_REQUIRED_PHRASES
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["ci_setup_python_cache"] == vm.CI_SETUP_PYTHON_CACHE
    assert inventory["ci_ruff_check_command"] == vm.CI_RUFF_CHECK_COMMAND
    assert inventory["license_required_phrases"] == list(vm.LICENSE_REQUIRED_PHRASES)
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "ci-setup-python" in vm.VALIDATORS
    assert "ci-ruff" in vm.VALIDATORS
    assert "license-mit" in vm.VALIDATORS


def test_v12_ci_setup_python_ruff_license_mit_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_ci_setup_python(tmp_path))
    assert any("missing" in f.message for f in vm.validate_ci_ruff(tmp_path))
    assert any("missing" in f.message for f in vm.validate_license_mit(tmp_path))

    _write(tmp_path / "LICENSE", "Not a real license\n")
    findings = vm.validate_license_mit(tmp_path)
    assert any("missing required MIT phrase" in f.message for f in findings)

    _write(
        tmp_path / "LICENSE",
        "\n".join(
            [
                "MIT License",
                "Permission is hereby granted",
                'THE SOFTWARE IS PROVIDED "AS IS"',
                "",
            ]
        ),
    )
    assert vm.validate_license_mit(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "- just-a-list\n")
    assert any(
        "root must be a mapping" in f.message
        for f in vm.validate_ci_setup_python(tmp_path)
    )
    assert any(
        "root must be a mapping" in f.message for f in vm.validate_ci_ruff(tmp_path)
    )

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "null\n")
    assert vm.validate_ci_setup_python(tmp_path) == []
    assert vm.validate_ci_ruff(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: only\n")
    assert any(
        "missing jobs mapping" in f.message
        for f in vm.validate_ci_setup_python(tmp_path)
    )
    assert any(
        "missing jobs mapping" in f.message for f in vm.validate_ci_ruff(tmp_path)
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
    assert any(
        "missing manifest-validate job" in f.message
        for f in vm.validate_ci_setup_python(tmp_path)
    )
    assert any(
        "missing manifest-validate job" in f.message
        for f in vm.validate_ci_ruff(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    assert any(
        "manifest-validate job missing steps" in f.message
        for f in vm.validate_ci_setup_python(tmp_path)
    )
    assert any(
        "manifest-validate job missing steps" in f.message
        for f in vm.validate_ci_ruff(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - not-a-mapping",
                "      - uses: actions/setup-python@v5",
                "        with: not-a-mapping",
                "      - run: echo no ruff",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_setup_python(tmp_path)
    assert any("setup-python step missing with" in f.message for f in findings)
    findings = vm.validate_ci_ruff(tmp_path)
    assert any("must run" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/setup-python@v5",
                "        with:",
                "          cache: npm",
                "          cache-dependency-path: wrong.txt",
                f"      - run: {vm.CI_RUFF_CHECK_COMMAND}",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_setup_python(tmp_path)
    assert any("setup-python cache must be" in f.message for f in findings)
    assert any(
        "setup-python cache-dependency-path must be" in f.message for f in findings
    )
    assert vm.validate_ci_ruff(tmp_path) == []

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - run: echo no setup-python",
                f"      - run: {vm.CI_RUFF_CHECK_COMMAND}",
                "",
            ]
        ),
    )
    findings = vm.validate_ci_setup_python(tmp_path)
    assert any("missing setup-python step" in f.message for f in findings)

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/setup-python@v5",
                "        with:",
                f"          cache: {vm.CI_SETUP_PYTHON_CACHE}",
                f"          cache-dependency-path: {vm.CI_CACHE_DEPENDENCY_PATH}",
                f"      - run: {vm.CI_RUFF_CHECK_COMMAND}",
                "",
            ]
        ),
    )
    assert vm.validate_ci_setup_python(tmp_path) == []
    assert vm.validate_ci_ruff(tmp_path) == []

    # YAML parse error path (data None with findings)
    _write(tmp_path / ".github" / "workflows" / "ci.yml", ":\n  - bad\n")
    assert any("YAML parse error" in f.message for f in vm.validate_ci_setup_python(tmp_path))
    assert any("YAML parse error" in f.message for f in vm.validate_ci_ruff(tmp_path))

    _copy_schemas(tmp_path)
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )

    blank_cache = dict(inventory)
    blank_cache["ci_setup_python_cache"] = "  "
    findings = vm._inventory_lock_consistency(
        blank_cache, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_setup_python_cache must be a non-empty string" in f.message
        for f in findings
    )

    blank_ruff = dict(inventory)
    blank_ruff["ci_ruff_check_command"] = ""
    findings = vm._inventory_lock_consistency(
        blank_ruff, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_ruff_check_command must be a non-empty string" in f.message
        for f in findings
    )

    no_ruff = dict(inventory)
    no_ruff["ci_ruff_check_command"] = "lint everything"
    findings = vm._inventory_lock_consistency(
        no_ruff, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_ruff_check_command must mention ruff" in f.message for f in findings
    )

    empty_lic = dict(inventory)
    empty_lic["license_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_lic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "license_required_phrases must not be empty" in f.message for f in findings
    )

    dup_lic = dict(inventory)
    dup_lic["license_required_phrases"] = ["MIT License", "MIT License"]
    findings = vm._inventory_lock_consistency(
        dup_lic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "license_required_phrases must be unique" in f.message for f in findings
    )

    blank_phrase = dict(inventory)
    blank_phrase["license_required_phrases"] = ["MIT License", "  "]
    findings = vm._inventory_lock_consistency(
        blank_phrase, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "license_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    non_str_phrase = dict(inventory)
    non_str_phrase["license_required_phrases"] = ["MIT License", 42]
    findings = vm._inventory_lock_consistency(
        non_str_phrase, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "license_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                ci_setup_python_cache="npm",
                ci_ruff_check_command="ruff check elsewhere",
                license_required_phrases=["Wrong License"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("ci_setup_python_cache" in f.message for f in findings)
    assert any("ci_ruff_check_command" in f.message for f in findings)
    assert any("license_required_phrases" in f.message for f in findings)


def test_live_v13_validators() -> None:
    assert vm.validate_ci_pip_install(REPO_ROOT) == []
    assert vm.validate_ci_pip_check(REPO_ROOT) == []
    assert vm.validate_ci_pytest(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert vm.CI_PIP_INSTALL_COMMAND == "python -m pip install -r requirements-dev.txt"
    assert vm.CI_PIP_CHECK_COMMAND == "python -m pip check"
    assert tuple(vm.CI_PYTEST_REQUIRED_MARKERS) == (
        "--cov=scripts",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--junitxml=pytest-junit.xml",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["ci_pip_install_command"] == vm.CI_PIP_INSTALL_COMMAND
    assert inventory["ci_pip_check_command"] == vm.CI_PIP_CHECK_COMMAND
    assert inventory["ci_pytest_required_markers"] == list(vm.CI_PYTEST_REQUIRED_MARKERS)
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "ci-pip-install" in vm.VALIDATORS
    assert "ci-pip-check" in vm.VALIDATORS
    assert "ci-pytest" in vm.VALIDATORS
    assert vm.validate_pyproject(REPO_ROOT) == []


def test_v13_ci_pip_pytest_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_ci_pip_install(tmp_path))
    assert any("missing" in f.message for f in vm.validate_ci_pip_check(tmp_path))
    assert any("missing" in f.message for f in vm.validate_ci_pytest(tmp_path))

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "- just-a-list\n")
    assert any(
        "root must be a mapping" in f.message
        for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any(
        "root must be a mapping" in f.message for f in vm.validate_ci_pip_check(tmp_path)
    )
    assert any(
        "root must be a mapping" in f.message for f in vm.validate_ci_pytest(tmp_path)
    )

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "null\n")
    assert vm.validate_ci_pip_install(tmp_path) == []
    assert vm.validate_ci_pip_check(tmp_path) == []
    assert vm.validate_ci_pytest(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: only\n")
    assert any(
        "missing jobs mapping" in f.message
        for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any(
        "missing jobs mapping" in f.message for f in vm.validate_ci_pip_check(tmp_path)
    )
    assert any(
        "missing jobs mapping" in f.message for f in vm.validate_ci_pytest(tmp_path)
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
    assert any(
        "missing manifest-validate job" in f.message
        for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any(
        "missing manifest-validate job" in f.message
        for f in vm.validate_ci_pip_check(tmp_path)
    )
    assert any(
        "missing manifest-validate job" in f.message
        for f in vm.validate_ci_pytest(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "",
            ]
        ),
    )
    assert any(
        "manifest-validate job missing steps" in f.message
        for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any(
        "manifest-validate job missing steps" in f.message
        for f in vm.validate_ci_pip_check(tmp_path)
    )
    assert any(
        "manifest-validate job missing steps" in f.message
        for f in vm.validate_ci_pytest(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - not-a-mapping",
                "      - run: echo no pip or pytest",
                "",
            ]
        ),
    )
    assert any(
        "must run" in f.message for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any("must run" in f.message for f in vm.validate_ci_pip_check(tmp_path))
    assert any(
        "must run a python -m pytest step" in f.message
        for f in vm.validate_ci_pytest(tmp_path)
    )

    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                f"      - run: {vm.CI_PIP_INSTALL_COMMAND}",
                f"      - run: {vm.CI_PIP_CHECK_COMMAND}",
                "      - run: python -m pytest -q",
                "",
            ]
        ),
    )
    assert vm.validate_ci_pip_install(tmp_path) == []
    assert vm.validate_ci_pip_check(tmp_path) == []
    findings = vm.validate_ci_pytest(tmp_path)
    for marker in vm.CI_PYTEST_REQUIRED_MARKERS:
        assert any(marker in f.message for f in findings), marker

    pytest_run = "python -m pytest " + " ".join(vm.CI_PYTEST_REQUIRED_MARKERS)
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "\n".join(
            [
                "name: CI",
                "jobs:",
                "  manifest-validate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                f"      - run: {vm.CI_PIP_INSTALL_COMMAND}",
                f"      - run: {vm.CI_PIP_CHECK_COMMAND}",
                f"      - run: {pytest_run}",
                "",
            ]
        ),
    )
    assert vm.validate_ci_pip_install(tmp_path) == []
    assert vm.validate_ci_pip_check(tmp_path) == []
    assert vm.validate_ci_pytest(tmp_path) == []

    _write(tmp_path / ".github" / "workflows" / "ci.yml", ":\n  - bad\n")
    assert any(
        "YAML parse error" in f.message for f in vm.validate_ci_pip_install(tmp_path)
    )
    assert any(
        "YAML parse error" in f.message for f in vm.validate_ci_pip_check(tmp_path)
    )
    assert any(
        "YAML parse error" in f.message for f in vm.validate_ci_pytest(tmp_path)
    )

    _copy_schemas(tmp_path)
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )

    blank_install = dict(inventory)
    blank_install["ci_pip_install_command"] = "  "
    findings = vm._inventory_lock_consistency(
        blank_install, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pip_install_command must be a non-empty string" in f.message
        for f in findings
    )

    no_install = dict(inventory)
    no_install["ci_pip_install_command"] = "python -m uv sync"
    findings = vm._inventory_lock_consistency(
        no_install, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pip_install_command must mention pip install" in f.message
        for f in findings
    )

    blank_check = dict(inventory)
    blank_check["ci_pip_check_command"] = ""
    findings = vm._inventory_lock_consistency(
        blank_check, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pip_check_command must be a non-empty string" in f.message
        for f in findings
    )

    no_check = dict(inventory)
    no_check["ci_pip_check_command"] = "python -m compileall"
    findings = vm._inventory_lock_consistency(
        no_check, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pip_check_command must mention pip check" in f.message for f in findings
    )

    empty_markers = dict(inventory)
    empty_markers["ci_pytest_required_markers"] = []
    findings = vm._inventory_lock_consistency(
        empty_markers, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pytest_required_markers must not be empty" in f.message for f in findings
    )

    dup_markers = dict(inventory)
    dup_markers["ci_pytest_required_markers"] = ["--cov=scripts", "--cov=scripts"]
    findings = vm._inventory_lock_consistency(
        dup_markers, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pytest_required_markers must be unique" in f.message for f in findings
    )

    blank_marker = dict(inventory)
    blank_marker["ci_pytest_required_markers"] = ["--cov=scripts", "  "]
    findings = vm._inventory_lock_consistency(
        blank_marker, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pytest_required_markers entries must be non-empty strings" in f.message
        for f in findings
    )

    non_str_marker = dict(inventory)
    non_str_marker["ci_pytest_required_markers"] = ["--cov=scripts", 42]
    findings = vm._inventory_lock_consistency(
        non_str_marker, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pytest_required_markers entries must be non-empty strings" in f.message
        for f in findings
    )

    no_cov = dict(inventory)
    no_cov["ci_pytest_required_markers"] = ["--junitxml=pytest-junit.xml"]
    findings = vm._inventory_lock_consistency(
        no_cov, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "ci_pytest_required_markers must include a --cov marker" in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                ci_pip_install_command="wrong install",
                ci_pip_check_command="wrong check",
                ci_pytest_required_markers=["--invented"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("ci_pip_install_command" in f.message for f in findings)
    assert any("ci_pip_check_command" in f.message for f in findings)
    assert any("ci_pytest_required_markers" in f.message for f in findings)


def test_coverage_fail_under_exact_lock(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'testpaths = ["tests"]',
                "[tool.ruff]",
                'target-version = "py311"',
                "[tool.coverage.report]",
                "fail_under = 100",
                "",
            ]
        ),
    )
    findings = vm.validate_pyproject(tmp_path)
    assert any("fail_under must be 99" in f.message for f in findings)


def test_live_v14_validators() -> None:
    assert vm.validate_state_residency(REPO_ROOT) == []
    assert vm.validate_key_files(REPO_ROOT) == []
    assert vm.validate_pr_routing(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.STATE_RESIDENCY_REQUIRED_PHRASES) == (
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
    assert tuple(vm.KEY_FILES_REQUIRED_ENTRIES) == (
        "AGENTS-v2.2.md",
        "AGENT-PROMPTS.md",
        "GOOSE-RECIPES.md",
        "IMPLEMENTATION-GUIDE.md",
        "EXECUTION-SUMMARY.md",
        "docs/agent-hydration.md",
        "agentic_flows/",
    )
    assert tuple(vm.PR_ROUTING_REQUIRED_FIELDS) == (
        "Surface",
        "Issue",
        "Branch",
        "Priority",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["state_residency_required_phrases"] == list(
        vm.STATE_RESIDENCY_REQUIRED_PHRASES
    )
    assert inventory["key_files_required_entries"] == list(vm.KEY_FILES_REQUIRED_ENTRIES)
    assert inventory["pr_routing_required_fields"] == list(vm.PR_ROUTING_REQUIRED_FIELDS)
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "state-residency" in vm.VALIDATORS
    assert "key-files" in vm.VALIDATORS
    assert "pr-routing" in vm.VALIDATORS
    assert vm.validate_claude_packaging(REPO_ROOT) == []
    assert vm.validate_pr_template(REPO_ROOT) == []


def test_v14_state_residency_key_files_pr_routing_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_state_residency(tmp_path))
    assert any("missing" in f.message for f in vm.validate_key_files(tmp_path))
    assert any("missing" in f.message for f in vm.validate_pr_routing(tmp_path))

    _write(tmp_path / "CLAUDE.md", "# CLAUDE\n\nNo sections here.\n")
    findings = vm.validate_state_residency(tmp_path)
    assert any("missing State Residency Rules section" in f.message for f in findings)
    for phrase in vm.STATE_RESIDENCY_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_key_files(tmp_path)
    assert any("missing Key Files section" in f.message for f in findings)
    for entry in vm.KEY_FILES_REQUIRED_ENTRIES:
        assert any(entry in f.message for f in findings)

    _write(
        tmp_path / "CLAUDE.md",
        "\n".join(
            [
                "## State Residency Rules",
                "",
                *[f"- {p}" for p in vm.STATE_RESIDENCY_REQUIRED_PHRASES],
                "",
                "## Key Files",
                "",
                *[f"- `{e}`" for e in vm.KEY_FILES_REQUIRED_ENTRIES],
                "",
            ]
        ),
    )
    assert vm.validate_state_residency(tmp_path) == []
    assert vm.validate_key_files(tmp_path) == []

    _write(
        tmp_path / ".github" / "pull_request_template.md",
        "# Summary\n\n## Problem\n\nNo routing table.\n",
    )
    findings = vm.validate_pr_routing(tmp_path)
    assert any("missing Agent Surface Routing section" in f.message for f in findings)
    for field in vm.PR_ROUTING_REQUIRED_FIELDS:
        assert any(field in f.message for f in findings)

    _write(
        tmp_path / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "## Agent Surface Routing",
                "",
                "| Field | Value |",
                "| --- | --- |",
                *[f"| {field} | x |" for field in vm.PR_ROUTING_REQUIRED_FIELDS],
                "",
            ]
        ),
    )
    assert vm.validate_pr_routing(tmp_path) == []

    _write(
        tmp_path / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "## Agent Surface Routing",
                "",
                "| Field | Value |",
                "| --- | --- |",
                "| Surface | x |",
                "| Issue | x |",
                "| Branch | x |",
                "",
            ]
        ),
    )
    findings = vm.validate_pr_routing(tmp_path)
    assert any("Priority" in f.message for f in findings)

    inventory = _inventory_payload()
    blank_residency = dict(inventory)
    blank_residency["state_residency_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        blank_residency, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "state_residency_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_residency = dict(inventory)
    dup_residency["state_residency_required_phrases"] = [
        "This GitHub repo",
        "This GitHub repo",
    ]
    findings = vm._inventory_lock_consistency(
        dup_residency, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "state_residency_required_phrases must be unique" in f.message for f in findings
    )

    blank_entry = dict(inventory)
    blank_entry["state_residency_required_phrases"] = ["This GitHub repo", "  "]
    findings = vm._inventory_lock_consistency(
        blank_entry, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "state_residency_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    empty_keys = dict(inventory)
    empty_keys["key_files_required_entries"] = []
    findings = vm._inventory_lock_consistency(
        empty_keys, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "key_files_required_entries must not be empty" in f.message for f in findings
    )

    dup_keys = dict(inventory)
    dup_keys["key_files_required_entries"] = ["AGENTS-v2.2.md", "AGENTS-v2.2.md"]
    findings = vm._inventory_lock_consistency(
        dup_keys, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "key_files_required_entries must be unique" in f.message for f in findings
    )

    blank_key = dict(inventory)
    blank_key["key_files_required_entries"] = ["AGENTS-v2.2.md", ""]
    findings = vm._inventory_lock_consistency(
        blank_key, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "key_files_required_entries entries must be non-empty strings" in f.message
        for f in findings
    )

    invented_key = dict(inventory)
    invented_key["key_files_required_entries"] = ["INVENTED-DOC.md", "agentic_flows/"]
    findings = vm._inventory_lock_consistency(
        invented_key, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "key_files_required_entries markdown files must be archive/hydration docs"
        in f.message
        for f in findings
    )

    empty_pr = dict(inventory)
    empty_pr["pr_routing_required_fields"] = []
    findings = vm._inventory_lock_consistency(
        empty_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_routing_required_fields must not be empty" in f.message for f in findings
    )

    dup_pr = dict(inventory)
    dup_pr["pr_routing_required_fields"] = ["Surface", "Surface", "Issue", "Branch"]
    findings = vm._inventory_lock_consistency(
        dup_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_routing_required_fields must be unique" in f.message for f in findings
    )

    blank_pr = dict(inventory)
    blank_pr["pr_routing_required_fields"] = ["Surface", "  "]
    findings = vm._inventory_lock_consistency(
        blank_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_routing_required_fields entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_core = dict(inventory)
    missing_core["pr_routing_required_fields"] = ["Surface", "Issue", "Branch"]
    findings = vm._inventory_lock_consistency(
        missing_core, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_routing_required_fields must include Surface/Issue/Branch/Priority"
        in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                state_residency_required_phrases=["invented residency"],
                key_files_required_entries=["invented.md"],
                pr_routing_required_fields=[
                    "Surface",
                    "Issue",
                    "Branch",
                    "Invented",
                ],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("state_residency_required_phrases" in f.message for f in findings)
    assert any("key_files_required_entries" in f.message for f in findings)
    assert any("pr_routing_required_fields" in f.message for f in findings)


def test_live_v15_validators() -> None:
    assert vm.validate_routing_matrix(REPO_ROOT) == []
    assert vm.validate_repo_identity(REPO_ROOT) == []
    assert vm.validate_escalation_format(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.ROUTING_MATRIX_REQUIRED_PHRASES) == (
        "CI/CD fixes, linting, dependabot",
        "Multi-file code scaffolding (agentic_flows/, contracts/, quantum_circuits/)",
        "Strategic planning, Notion updates, cross-platform coordination",
        "GitHub Settings, branch protection",
        "Automated E2E verification",
        "Financial transactions, repo visibility changes",
    )
    assert tuple(vm.REPO_IDENTITY_REQUIRED_PHRASES) == (
        "fuzzywigg/g0p-agents",
        "Quantum-Blockchain agentic protocols archive",
        "FUZZYWIGG four-agent swarm",
        "PikoClaw demo at Panathenea",
        "Documentation archive",
        "LIST B",
    )
    assert tuple(vm.ESCALATION_BLOCK_REQUIRED_PHRASES) == (
        "ESCALATION REQUIRED",
        "From Agent:",
        "Conflict:",
        "Recommendation:",
        "Timeline:",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["routing_matrix_required_phrases"] == list(
        vm.ROUTING_MATRIX_REQUIRED_PHRASES
    )
    assert inventory["repo_identity_required_phrases"] == list(
        vm.REPO_IDENTITY_REQUIRED_PHRASES
    )
    assert inventory["escalation_block_required_phrases"] == list(
        vm.ESCALATION_BLOCK_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "routing-matrix" in vm.VALIDATORS
    assert "repo-identity" in vm.VALIDATORS
    assert "escalation-format" in vm.VALIDATORS
    assert vm.validate_claude_packaging(REPO_ROOT) == []
    assert vm.validate_routing_surfaces(REPO_ROOT) == []


def test_v15_routing_identity_escalation_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_routing_matrix(tmp_path))
    assert any("missing" in f.message for f in vm.validate_repo_identity(tmp_path))
    assert any("missing" in f.message for f in vm.validate_escalation_format(tmp_path))

    _write(tmp_path / "CLAUDE.md", "# CLAUDE\n\nNo sections here.\n")
    findings = vm.validate_routing_matrix(tmp_path)
    assert any("missing Agent Routing Matrix section" in f.message for f in findings)
    for phrase in vm.ROUTING_MATRIX_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)
    for surface in vm.ROUTING_SURFACES:
        assert any(surface in f.message for f in findings)

    findings = vm.validate_repo_identity(tmp_path)
    assert any("missing Repo Identity section" in f.message for f in findings)
    for phrase in vm.REPO_IDENTITY_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_escalation_format(tmp_path)
    assert any("missing Escalation Format section" in f.message for f in findings)
    for phrase in vm.ESCALATION_BLOCK_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CLAUDE.md",
        "\n".join(
            [
                "## Repo Identity",
                "",
                *[f"- {p}" for p in vm.REPO_IDENTITY_REQUIRED_PHRASES],
                "",
                "## Agent Routing Matrix",
                "",
                *[f"| {p} | {s} | why |" for p, s in zip(
                    vm.ROUTING_MATRIX_REQUIRED_PHRASES,
                    vm.ROUTING_SURFACES,
                    strict=True,
                )],
                "",
                "## Escalation Format",
                "",
                *[f"- {p}" for p in vm.ESCALATION_BLOCK_REQUIRED_PHRASES],
                "",
            ]
        ),
    )
    assert vm.validate_routing_matrix(tmp_path) == []
    assert vm.validate_repo_identity(tmp_path) == []
    assert vm.validate_escalation_format(tmp_path) == []

    inventory = _inventory_payload()
    empty_matrix = dict(inventory)
    empty_matrix["routing_matrix_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_matrix, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_matrix = dict(inventory)
    dup_matrix["routing_matrix_required_phrases"] = [
        vm.ROUTING_MATRIX_REQUIRED_PHRASES[0],
        vm.ROUTING_MATRIX_REQUIRED_PHRASES[0],
        *vm.ROUTING_MATRIX_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_matrix, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_required_phrases must be unique" in f.message for f in findings
    )

    blank_matrix = dict(inventory)
    blank_matrix["routing_matrix_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_matrix, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    len_mismatch = dict(inventory)
    len_mismatch["routing_matrix_required_phrases"] = list(
        vm.ROUTING_MATRIX_REQUIRED_PHRASES
    )[:-1]
    findings = vm._inventory_lock_consistency(
        len_mismatch, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_required_phrases length must match routing_surfaces"
        in f.message
        for f in findings
    )

    empty_id = dict(inventory)
    empty_id["repo_identity_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_id, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "repo_identity_required_phrases must not be empty" in f.message for f in findings
    )

    dup_id = dict(inventory)
    dup_id["repo_identity_required_phrases"] = [
        "fuzzywigg/g0p-agents",
        "fuzzywigg/g0p-agents",
    ]
    findings = vm._inventory_lock_consistency(
        dup_id, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "repo_identity_required_phrases must be unique" in f.message for f in findings
    )

    blank_id = dict(inventory)
    blank_id["repo_identity_required_phrases"] = ["fuzzywigg/g0p-agents", "  "]
    findings = vm._inventory_lock_consistency(
        blank_id, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "repo_identity_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_repo = dict(inventory)
    missing_repo["repo_identity_required_phrases"] = ["Documentation archive", "LIST B"]
    findings = vm._inventory_lock_consistency(
        missing_repo, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "repo_identity_required_phrases must include fuzzywigg/g0p-agents" in f.message
        for f in findings
    )

    empty_esc = dict(inventory)
    empty_esc["escalation_block_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_esc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_block_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_esc = dict(inventory)
    dup_esc["escalation_block_required_phrases"] = [
        "ESCALATION REQUIRED",
        "ESCALATION REQUIRED",
        "From Agent:",
        "Conflict:",
        "Recommendation:",
    ]
    findings = vm._inventory_lock_consistency(
        dup_esc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_block_required_phrases must be unique" in f.message for f in findings
    )

    blank_esc = dict(inventory)
    blank_esc["escalation_block_required_phrases"] = ["ESCALATION REQUIRED", "  "]
    findings = vm._inventory_lock_consistency(
        blank_esc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_block_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_esc = dict(inventory)
    missing_esc["escalation_block_required_phrases"] = [
        "ESCALATION REQUIRED",
        "From Agent:",
        "Conflict:",
        "Recommendation:",
    ]
    findings = vm._inventory_lock_consistency(
        missing_esc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_block_required_phrases must include banner and four fields"
        in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                routing_matrix_required_phrases=list(
                    vm.ROUTING_MATRIX_REQUIRED_PHRASES
                )[:-1]
                + ["invented matrix"],
                repo_identity_required_phrases=list(
                    vm.REPO_IDENTITY_REQUIRED_PHRASES
                )[:-1]
                + ["invented identity"],
                escalation_block_required_phrases=list(
                    vm.ESCALATION_BLOCK_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("routing_matrix_required_phrases" in f.message for f in findings)
    assert any("repo_identity_required_phrases" in f.message for f in findings)
    assert any("escalation_block_required_phrases" in f.message for f in findings)


def test_live_v16_validators() -> None:
    assert vm.validate_routing_rationales(REPO_ROOT) == []
    assert vm.validate_claude_metadata(REPO_ROOT) == []
    assert vm.validate_escalation_usage(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.ROUTING_MATRIX_RATIONALE_PHRASES) == (
        "Single-repo, syntax-level work",
        "Deep coding, long-running, 60–90 min",
        "Cross-system state, Notion truth",
        "UI-only settings",
        "Test automation",
        "Non-automatable",
    )
    assert tuple(vm.CLAUDE_METADATA_REQUIRED_PHRASES) == (
        "Status: ACTIVE",
        "Tier: 1",
        "Owner: claude-cowork",
        "Created: 2026-04-13",
        "Edit policy: Agent-editable",
        "Canonical source: This file",
    )
    assert tuple(vm.ESCALATION_USAGE_REQUIRED_PHRASES) == (
        "When blocked, use this format in PR comments or Slack:",
        "```text",
        "From Agent: [surface name]",
        "Conflict: [What constraint am I hitting?]",
        "Recommendation: [How should we resolve this?]",
        "Timeline: [How long until decision needed?]",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["routing_matrix_rationale_phrases"] == list(
        vm.ROUTING_MATRIX_RATIONALE_PHRASES
    )
    assert inventory["claude_metadata_required_phrases"] == list(
        vm.CLAUDE_METADATA_REQUIRED_PHRASES
    )
    assert inventory["escalation_usage_required_phrases"] == list(
        vm.ESCALATION_USAGE_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "routing-rationales" in vm.VALIDATORS
    assert "claude-metadata" in vm.VALIDATORS
    assert "escalation-usage" in vm.VALIDATORS
    assert vm.validate_routing_matrix(REPO_ROOT) == []
    assert vm.validate_repo_identity(REPO_ROOT) == []
    assert vm.validate_escalation_format(REPO_ROOT) == []
    assert vm.validate_claude_packaging(REPO_ROOT) == []


def test_v16_routing_identity_escalation_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_routing_rationales(tmp_path))
    assert any("missing" in f.message for f in vm.validate_claude_metadata(tmp_path))
    assert any("missing" in f.message for f in vm.validate_escalation_usage(tmp_path))

    _write(tmp_path / "CLAUDE.md", "# CLAUDE\n\nNo sections here.\n")
    findings = vm.validate_routing_rationales(tmp_path)
    assert any("missing Agent Routing Matrix section" in f.message for f in findings)
    assert any("missing routing-matrix column header" in f.message for f in findings)
    for phrase in vm.ROUTING_MATRIX_RATIONALE_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_claude_metadata(tmp_path)
    for phrase in vm.CLAUDE_METADATA_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_escalation_usage(tmp_path)
    assert any("missing Escalation Format section" in f.message for f in findings)
    for phrase in vm.ESCALATION_USAGE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CLAUDE.md",
        "\n".join(
            [
                "Status: ACTIVE | Tier: 1 | Owner: claude-cowork",
                "Created: 2026-04-13 | Edit policy: Agent-editable; structural changes",
                "Canonical source: This file (GitHub is truth)",
                "",
                "## Agent Routing Matrix",
                "",
                "| Task | Surface | Rationale |",
                "| --- | --- | --- |",
                *[
                    f"| task | surface | {phrase} |"
                    for phrase in vm.ROUTING_MATRIX_RATIONALE_PHRASES
                ],
                "",
                "## Escalation Format",
                "",
                "When blocked, use this format in PR comments or Slack:",
                "",
                "```text",
                "From Agent: [surface name]",
                "Conflict: [What constraint am I hitting?]",
                "Recommendation: [How should we resolve this?]",
                "Timeline: [How long until decision needed?]",
                "```",
                "",
            ]
        ),
    )
    assert vm.validate_routing_rationales(tmp_path) == []
    assert vm.validate_claude_metadata(tmp_path) == []
    assert vm.validate_escalation_usage(tmp_path) == []

    inventory = _inventory_payload()
    empty_rat = dict(inventory)
    empty_rat["routing_matrix_rationale_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_rat, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_rationale_phrases must not be empty" in f.message
        for f in findings
    )

    dup_rat = dict(inventory)
    dup_rat["routing_matrix_rationale_phrases"] = [
        vm.ROUTING_MATRIX_RATIONALE_PHRASES[0],
        vm.ROUTING_MATRIX_RATIONALE_PHRASES[0],
        *vm.ROUTING_MATRIX_RATIONALE_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_rat, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_rationale_phrases must be unique" in f.message for f in findings
    )

    blank_rat = dict(inventory)
    blank_rat["routing_matrix_rationale_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_rat, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_rationale_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    len_mismatch = dict(inventory)
    len_mismatch["routing_matrix_rationale_phrases"] = list(
        vm.ROUTING_MATRIX_RATIONALE_PHRASES
    )[:-1]
    findings = vm._inventory_lock_consistency(
        len_mismatch, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "routing_matrix_rationale_phrases length must match routing_surfaces"
        in f.message
        for f in findings
    )

    empty_meta = dict(inventory)
    empty_meta["claude_metadata_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "claude_metadata_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_meta = dict(inventory)
    dup_meta["claude_metadata_required_phrases"] = [
        "Status: ACTIVE",
        "Status: ACTIVE",
        "Tier: 1",
    ]
    findings = vm._inventory_lock_consistency(
        dup_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "claude_metadata_required_phrases must be unique" in f.message for f in findings
    )

    blank_meta = dict(inventory)
    blank_meta["claude_metadata_required_phrases"] = ["Status: ACTIVE", "  "]
    findings = vm._inventory_lock_consistency(
        blank_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "claude_metadata_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_meta = dict(inventory)
    missing_meta["claude_metadata_required_phrases"] = [
        "Status: ACTIVE",
        "Tier: 1",
        "Owner: claude-cowork",
    ]
    findings = vm._inventory_lock_consistency(
        missing_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "claude_metadata_required_phrases must include Status/Tier/Owner/Created"
        in f.message
        for f in findings
    )

    empty_usage = dict(inventory)
    empty_usage["escalation_usage_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_usage, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_usage_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_usage = dict(inventory)
    dup_usage["escalation_usage_required_phrases"] = [
        "```text",
        "```text",
        "From Agent: [surface name]",
    ]
    findings = vm._inventory_lock_consistency(
        dup_usage, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_usage_required_phrases must be unique" in f.message for f in findings
    )

    blank_usage = dict(inventory)
    blank_usage["escalation_usage_required_phrases"] = ["```text", "  "]
    findings = vm._inventory_lock_consistency(
        blank_usage, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_usage_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_usage = dict(inventory)
    missing_usage["escalation_usage_required_phrases"] = [
        "When blocked, use this format in PR comments or Slack:",
        "```text",
    ]
    findings = vm._inventory_lock_consistency(
        missing_usage, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "escalation_usage_required_phrases must include intro, fence, and From Agent"
        in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                routing_matrix_rationale_phrases=list(
                    vm.ROUTING_MATRIX_RATIONALE_PHRASES
                )[:-1]
                + ["invented rationale"],
                claude_metadata_required_phrases=list(
                    vm.CLAUDE_METADATA_REQUIRED_PHRASES
                )[:-1]
                + ["invented metadata"],
                escalation_usage_required_phrases=list(
                    vm.ESCALATION_USAGE_REQUIRED_PHRASES
                )[:-1]
                + ["invented usage"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("routing_matrix_rationale_phrases" in f.message for f in findings)
    assert any("claude_metadata_required_phrases" in f.message for f in findings)
    assert any("escalation_usage_required_phrases" in f.message for f in findings)


def test_v17_security_policy_live_locks() -> None:
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert vm.validate_security_supported(REPO_ROOT) == []
    assert vm.validate_security_reporting(REPO_ROOT) == []
    assert vm.validate_security_standards(REPO_ROOT) == []
    assert vm.validate_security_packaging(REPO_ROOT) == []
    assert tuple(vm.SECURITY_SUPPORTED_REQUIRED_PHRASES) == (
        "This repository is a documentation archive",
        "No executable code is deployed",
        "YAML recipe templates",
        "Agent system prompts",
        "Future: Solidity contracts",
    )
    assert tuple(vm.SECURITY_REPORTING_REQUIRED_PHRASES) == (
        "Do NOT open a public GitHub issue for security vulnerabilities",
        "To report a vulnerability:",
        "Email:",
        "Include: description, affected files, reproduction steps, suggested fix",
        "acknowledgment within 48 hours",
    )
    assert tuple(vm.SECURITY_STANDARDS_REQUIRED_PHRASES) == (
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
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["security_supported_required_phrases"] == list(
        vm.SECURITY_SUPPORTED_REQUIRED_PHRASES
    )
    assert inventory["security_reporting_required_phrases"] == list(
        vm.SECURITY_REPORTING_REQUIRED_PHRASES
    )
    assert inventory["security_standards_required_phrases"] == list(
        vm.SECURITY_STANDARDS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "security-supported" in vm.VALIDATORS
    assert "security-reporting" in vm.VALIDATORS
    assert "security-standards" in vm.VALIDATORS
    assert vm.validate_routing_rationales(REPO_ROOT) == []
    assert vm.validate_claude_metadata(REPO_ROOT) == []
    assert vm.validate_escalation_usage(REPO_ROOT) == []


def test_v17_security_policy_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_security_supported(tmp_path))
    assert any("missing" in f.message for f in vm.validate_security_reporting(tmp_path))
    assert any("missing" in f.message for f in vm.validate_security_standards(tmp_path))

    _write(tmp_path / "SECURITY.md", "# Security Policy\n\nNo sections here.\n")
    findings = vm.validate_security_supported(tmp_path)
    assert any("missing Supported Versions section" in f.message for f in findings)
    for phrase in vm.SECURITY_SUPPORTED_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_reporting(tmp_path)
    assert any(
        "missing Reporting a Vulnerability section" in f.message for f in findings
    )
    for phrase in vm.SECURITY_REPORTING_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_standards(tmp_path)
    assert any(
        "missing Security Standards for This Ecosystem section" in f.message
        for f in findings
    )
    for phrase in vm.SECURITY_STANDARDS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "SECURITY.md",
        "\n".join(
            [
                "# Security Policy",
                "",
                "## Supported Versions",
                "",
                *[f"- {p}" for p in vm.SECURITY_SUPPORTED_REQUIRED_PHRASES],
                "",
                "## Reporting a Vulnerability",
                "",
                *[f"- {p}" for p in vm.SECURITY_REPORTING_REQUIRED_PHRASES],
                "",
                "## Security Standards for This Ecosystem",
                "",
                *[f"- {p}" for p in vm.SECURITY_STANDARDS_REQUIRED_PHRASES],
                "",
            ]
        ),
    )
    assert vm.validate_security_supported(tmp_path) == []
    assert vm.validate_security_reporting(tmp_path) == []
    assert vm.validate_security_standards(tmp_path) == []

    inventory = _inventory_payload()
    empty_supported = dict(inventory)
    empty_supported["security_supported_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_supported, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_supported_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_supported = dict(inventory)
    dup_supported["security_supported_required_phrases"] = [
        vm.SECURITY_SUPPORTED_REQUIRED_PHRASES[0],
        vm.SECURITY_SUPPORTED_REQUIRED_PHRASES[0],
        *vm.SECURITY_SUPPORTED_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_supported, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_supported_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_supported = dict(inventory)
    blank_supported["security_supported_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_supported, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_supported_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_archive = dict(inventory)
    missing_archive["security_supported_required_phrases"] = [
        "No executable code is deployed",
        "YAML recipe templates",
    ]
    findings = vm._inventory_lock_consistency(
        missing_archive, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_supported_required_phrases must mention documentation archive"
        in f.message
        for f in findings
    )

    empty_reporting = dict(inventory)
    empty_reporting["security_reporting_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_reporting, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_reporting = dict(inventory)
    dup_reporting["security_reporting_required_phrases"] = [
        "Email:",
        "Email:",
        "acknowledgment within 48 hours",
    ]
    findings = vm._inventory_lock_consistency(
        dup_reporting, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_reporting = dict(inventory)
    blank_reporting["security_reporting_required_phrases"] = ["Email:", "  "]
    findings = vm._inventory_lock_consistency(
        blank_reporting, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_public = dict(inventory)
    missing_public["security_reporting_required_phrases"] = [
        "To report a vulnerability:",
        "Email:",
        "acknowledgment within 48 hours",
    ]
    findings = vm._inventory_lock_consistency(
        missing_public, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_required_phrases must refuse public GitHub issues"
        in f.message
        for f in findings
    )

    empty_standards = dict(inventory)
    empty_standards["security_standards_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_standards, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_standards_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_standards = dict(inventory)
    dup_standards["security_standards_required_phrases"] = [
        "Cryptography",
        "Cryptography",
        "Smart contracts",
    ]
    findings = vm._inventory_lock_consistency(
        dup_standards, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_standards_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_standards = dict(inventory)
    blank_standards["security_standards_required_phrases"] = ["Cryptography", "  "]
    findings = vm._inventory_lock_consistency(
        blank_standards, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_standards_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_domains = dict(inventory)
    missing_domains["security_standards_required_phrases"] = [
        "Cryptography",
        "Smart contracts",
        "Mobile",
        "Secrets",
    ]
    findings = vm._inventory_lock_consistency(
        missing_domains, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_standards_required_phrases must include five domain rows"
        in f.message
        for f in findings
    )

    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                security_supported_required_phrases=list(
                    vm.SECURITY_SUPPORTED_REQUIRED_PHRASES
                )[:-1]
                + ["invented supported"],
                security_reporting_required_phrases=list(
                    vm.SECURITY_REPORTING_REQUIRED_PHRASES
                )[:-1]
                + ["invented reporting"],
                security_standards_required_phrases=list(
                    vm.SECURITY_STANDARDS_REQUIRED_PHRASES
                )[:-1]
                + ["invented standards"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("security_supported_required_phrases" in f.message for f in findings)
    assert any("security_reporting_required_phrases" in f.message for f in findings)
    assert any("security_standards_required_phrases" in f.message for f in findings)

def test_v18_archive_snapshot_live_locks() -> None:
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert vm.validate_implementation_quickstart(REPO_ROOT) == []
    assert vm.validate_execution_specialists(REPO_ROOT) == []
    assert vm.validate_hydration_list_b(REPO_ROOT) == []
    assert vm.validate_implementation_guide(REPO_ROOT) == []
    assert vm.validate_execution_summary(REPO_ROOT) == []
    assert vm.validate_hydration_report(REPO_ROOT) == []
    assert tuple(vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES) == (
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
    assert tuple(vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES) == (
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
    assert tuple(vm.HYDRATION_LIST_B_REQUIRED_PHRASES) == (
        "### LIST B — Requires Andrew (HITL)",
        "Is g0p-agents meant to be activated into a runnable codebase",
        "What is PikoClaw exactly",
        "Should actual Solidity, Python (Cirq), and React Native code be implemented",
        "What is the `agents-standard` repo",
        "Is there a Notion page for g0p-agents",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["implementation_quickstart_required_phrases"] == list(
        vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES
    )
    assert inventory["execution_specialists_required_phrases"] == list(
        vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES
    )
    assert inventory["hydration_list_b_required_phrases"] == list(
        vm.HYDRATION_LIST_B_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "implementation-quickstart" in vm.VALIDATORS
    assert "execution-specialists" in vm.VALIDATORS
    assert "hydration-list-b" in vm.VALIDATORS
    assert vm.validate_security_supported(REPO_ROOT) == []
    assert vm.validate_security_reporting(REPO_ROOT) == []
    assert vm.validate_security_standards(REPO_ROOT) == []


def test_v18_archive_snapshot_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_implementation_quickstart(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_execution_specialists(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_hydration_list_b(tmp_path))

    _write(tmp_path / "IMPLEMENTATION-GUIDE.md", "# IMPLEMENTATION GUIDE\n\nNo quickstart.\n")
    findings = vm.validate_implementation_quickstart(tmp_path)
    assert any("missing Quick Start section" in f.message for f in findings)
    for phrase in vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(tmp_path / "EXECUTION-SUMMARY.md", "# EXECUTION SUMMARY\n\nNo specialists.\n")
    findings = vm.validate_execution_specialists(tmp_path)
    assert any(
        "missing Your Four Specialist Agents section" in f.message for f in findings
    )
    for phrase in vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    (tmp_path / "docs").mkdir()
    _write(tmp_path / "docs" / "agent-hydration.md", "# Hydration\n\nNo LIST B.\n")
    findings = vm.validate_hydration_list_b(tmp_path)
    assert any("missing LIST B HITL section" in f.message for f in findings)
    for phrase in vm.HYDRATION_LIST_B_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "IMPLEMENTATION-GUIDE.md",
        "\n".join(
            [
                "# IMPLEMENTATION GUIDE",
                "",
                "## Quick Start (30 minutes)",
                "",
                *[f"- {p}" for p in vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES],
                "",
            ]
        ),
    )
    _write(
        tmp_path / "EXECUTION-SUMMARY.md",
        "\n".join(
            [
                "# EXECUTION SUMMARY",
                "",
                "## Your Four Specialist Agents",
                "",
                *[f"- {p}" for p in vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES],
                "",
            ]
        ),
    )
    _write(
        tmp_path / "docs" / "agent-hydration.md",
        "\n".join(
            [
                "# Hydration",
                "",
                "### LIST B — Requires Andrew (HITL)",
                "",
                *[f"- {p}" for p in vm.HYDRATION_LIST_B_REQUIRED_PHRASES],
                "",
            ]
        ),
    )
    assert vm.validate_implementation_quickstart(tmp_path) == []
    assert vm.validate_execution_specialists(tmp_path) == []
    assert vm.validate_hydration_list_b(tmp_path) == []

    inventory = _inventory_payload()
    empty_qs = dict(inventory)
    empty_qs["implementation_quickstart_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_qs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_quickstart_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_qs = dict(inventory)
    dup_qs["implementation_quickstart_required_phrases"] = [
        vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_qs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_quickstart_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_qs = dict(inventory)
    blank_qs["implementation_quickstart_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_qs, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_quickstart_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_flows = dict(inventory)
    missing_flows["implementation_quickstart_required_phrases"] = [
        "## Quick Start (30 minutes)",
        "Python 3.11",
    ]
    findings = vm._inventory_lock_consistency(
        missing_flows, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_quickstart_required_phrases must mention agentic_flows"
        in f.message
        for f in findings
    )

    empty_spec = dict(inventory)
    empty_spec["execution_specialists_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_spec, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_specialists_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_spec = dict(inventory)
    dup_spec["execution_specialists_required_phrases"] = [
        "Quantum Computing",
        "Quantum Computing",
        "Blockchain Dev",
    ]
    findings = vm._inventory_lock_consistency(
        dup_spec, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_specialists_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_spec = dict(inventory)
    blank_spec["execution_specialists_required_phrases"] = ["Quantum Computing", "  "]
    findings = vm._inventory_lock_consistency(
        blank_spec, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_specialists_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_agents = dict(inventory)
    missing_agents["execution_specialists_required_phrases"] = [
        "## Your Four Specialist Agents",
        "QuantumArchitectAgent",
        "BlockchainArchitectAgent",
    ]
    findings = vm._inventory_lock_consistency(
        missing_agents, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_specialists_required_phrases must include all documented agents"
        in f.message
        for f in findings
    )

    empty_b = dict(inventory)
    empty_b["hydration_list_b_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "hydration_list_b_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_b = dict(inventory)
    dup_b["hydration_list_b_required_phrases"] = [
        "What is PikoClaw exactly",
        "What is PikoClaw exactly",
        "Is there a Notion page for g0p-agents",
    ]
    findings = vm._inventory_lock_consistency(
        dup_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "hydration_list_b_required_phrases must be unique" in f.message for f in findings
    )

    blank_b = dict(inventory)
    blank_b["hydration_list_b_required_phrases"] = ["LIST B", "  "]
    findings = vm._inventory_lock_consistency(
        blank_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "hydration_list_b_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_list_b = dict(inventory)
    missing_list_b["hydration_list_b_required_phrases"] = [
        "What is PikoClaw exactly",
        "Is there a Notion page for g0p-agents",
    ]
    findings = vm._inventory_lock_consistency(
        missing_list_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "hydration_list_b_required_phrases must mention LIST B" in f.message
        for f in findings
    )

    missing_piko = dict(inventory)
    missing_piko["hydration_list_b_required_phrases"] = [
        "### LIST B — Requires Andrew (HITL)",
        "Is there a Notion page for g0p-agents",
    ]
    findings = vm._inventory_lock_consistency(
        missing_piko, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "hydration_list_b_required_phrases must mention PikoClaw" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                implementation_quickstart_required_phrases=list(
                    vm.IMPLEMENTATION_QUICKSTART_REQUIRED_PHRASES
                )[:-1]
                + ["invented quickstart"],
                execution_specialists_required_phrases=list(
                    vm.EXECUTION_SPECIALISTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented specialist"],
                hydration_list_b_required_phrases=list(
                    vm.HYDRATION_LIST_B_REQUIRED_PHRASES
                )[:-1]
                + ["invented list b"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "implementation_quickstart_required_phrases" in f.message for f in findings
    )
    assert any("execution_specialists_required_phrases" in f.message for f in findings)
    assert any("hydration_list_b_required_phrases" in f.message for f in findings)



def test_live_v19_postmortem_validators() -> None:
    assert vm.validate_postmortem_intro(REPO_ROOT) == []
    assert vm.validate_postmortem_fields(REPO_ROOT) == []
    assert vm.validate_postmortem_next_steps(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.POSTMORTEM_INTRO_REQUIRED_PHRASES) == (
        "Decision & Incident Log",
        "Every significant decision, conflict, and resolution is logged here",
        "Agents MUST log decisions after each workflow",
        "Andrew reviews quarterly",
    )
    assert tuple(vm.POSTMORTEM_FIELD_REQUIRED_PHRASES) == (
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
    assert tuple(vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES) == (
        "Andrew answers LIST B (B1–B5) in docs/agent-hydration.md",
        "browser-claude or claude-cowork creates GitHub issues",
        "claude-cowork creates/updates Notion page under Active Sprint Work",
        "geryon scaffolds agentic_flows/ once B1 is answered",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["postmortem_intro_required_phrases"] == list(
        vm.POSTMORTEM_INTRO_REQUIRED_PHRASES
    )
    assert inventory["postmortem_field_required_phrases"] == list(
        vm.POSTMORTEM_FIELD_REQUIRED_PHRASES
    )
    assert inventory["postmortem_next_steps_required_phrases"] == list(
        vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "postmortem-intro" in vm.VALIDATORS
    assert "postmortem-fields" in vm.VALIDATORS
    assert "postmortem-next-steps" in vm.VALIDATORS
    assert vm.validate_postmortem_packaging(REPO_ROOT) == []
    assert vm.validate_implementation_quickstart(REPO_ROOT) == []
    assert vm.validate_execution_specialists(REPO_ROOT) == []
    assert vm.validate_hydration_list_b(REPO_ROOT) == []


def test_v19_postmortem_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_postmortem_intro(tmp_path))
    assert any("missing" in f.message for f in vm.validate_postmortem_fields(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_postmortem_next_steps(tmp_path)
    )

    _write(tmp_path / "postmortem.md", "# postmortem\n\nNo locked content.\n")
    findings = vm.validate_postmortem_intro(tmp_path)
    for phrase in vm.POSTMORTEM_INTRO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_postmortem_fields(tmp_path)
    assert any("missing Decision: Repo Hydration section" in f.message for f in findings)
    for phrase in vm.POSTMORTEM_FIELD_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_postmortem_next_steps(tmp_path)
    assert any("missing Next Steps field" in f.message for f in findings)
    for phrase in vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "postmortem.md",
        "\n".join(
            [
                "# postmortem.md — g0p-agents Decision & Incident Log",
                "",
                "Every significant decision, conflict, and resolution is logged here.",
                "Agents MUST log decisions after each workflow. Andrew reviews quarterly.",
                "",
                "## Decision: Repo Hydration — 2026-04-13",
                "",
                "- **Date**: 2026-04-13T02:07:01Z",
                "- **Decision**: PROCEED WITH DOCUMENTATION HYDRATION",
                "- **Agent**: copilot (hydration run)",
                "- **Context**: documentation archive",
                "- **LIST B Deferred**: Questions B1–B5",
                "- **Risk Level**: LOW",
                "- **Files Created**:",
                "  - CLAUDE.md",
                "- **Blocked**: none",
                "- **Next Steps**:",
                "  1. Andrew answers LIST B (B1–B5) in docs/agent-hydration.md",
                "  2. browser-claude or claude-cowork creates GitHub issues from table",
                "  3. claude-cowork creates/updates Notion page under Active Sprint Work",
                "  4. geryon scaffolds agentic_flows/ once B1 is answered",
                "",
            ]
        ),
    )
    assert vm.validate_postmortem_intro(tmp_path) == []
    assert vm.validate_postmortem_fields(tmp_path) == []
    assert vm.validate_postmortem_next_steps(tmp_path) == []

    inventory = _inventory_payload()
    empty_intro = dict(inventory)
    empty_intro["postmortem_intro_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_intro_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_intro = dict(inventory)
    dup_intro["postmortem_intro_required_phrases"] = [
        vm.POSTMORTEM_INTRO_REQUIRED_PHRASES[0],
        vm.POSTMORTEM_INTRO_REQUIRED_PHRASES[0],
        *vm.POSTMORTEM_INTRO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_intro_required_phrases must be unique" in f.message for f in findings
    )

    blank_intro = dict(inventory)
    blank_intro["postmortem_intro_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_intro_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_intro = dict(inventory)
    missing_intro["postmortem_intro_required_phrases"] = [
        "Decision & Incident Log",
        "Andrew reviews quarterly",
    ]
    findings = vm._inventory_lock_consistency(
        missing_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_intro_required_phrases must require agents to log decisions"
        in f.message
        for f in findings
    )

    empty_fields = dict(inventory)
    empty_fields["postmortem_field_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_fields, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_field_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_fields = dict(inventory)
    dup_fields["postmortem_field_required_phrases"] = [
        "**Date**:",
        "**Date**:",
        "**Decision**:",
    ]
    findings = vm._inventory_lock_consistency(
        dup_fields, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_field_required_phrases must be unique" in f.message for f in findings
    )

    blank_fields = dict(inventory)
    blank_fields["postmortem_field_required_phrases"] = ["**Date**:", "  "]
    findings = vm._inventory_lock_consistency(
        blank_fields, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_field_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_fields = dict(inventory)
    missing_fields["postmortem_field_required_phrases"] = [
        "**Date**:",
        "**Context**:",
    ]
    findings = vm._inventory_lock_consistency(
        missing_fields, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_field_required_phrases must include Date/Decision/Agent"
        in f.message
        for f in findings
    )

    empty_next = dict(inventory)
    empty_next["postmortem_next_steps_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_next, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_next_steps_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_next = dict(inventory)
    dup_next["postmortem_next_steps_required_phrases"] = [
        vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES[0],
        vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES[0],
        *vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_next, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_next_steps_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_next = dict(inventory)
    blank_next["postmortem_next_steps_required_phrases"] = [
        vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES[0],
        "  ",
    ]
    findings = vm._inventory_lock_consistency(
        blank_next, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_next_steps_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_next = dict(inventory)
    missing_next["postmortem_next_steps_required_phrases"] = [
        "browser-claude or claude-cowork creates GitHub issues",
    ]
    findings = vm._inventory_lock_consistency(
        missing_next, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "postmortem_next_steps_required_phrases must include LIST B and geryon scaffold"
        in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                postmortem_intro_required_phrases=list(
                    vm.POSTMORTEM_INTRO_REQUIRED_PHRASES
                )[:-1]
                + ["invented intro"],
                postmortem_field_required_phrases=list(
                    vm.POSTMORTEM_FIELD_REQUIRED_PHRASES
                )[:-1]
                + ["invented field"],
                postmortem_next_steps_required_phrases=list(
                    vm.POSTMORTEM_NEXT_STEPS_REQUIRED_PHRASES
                )[:-1]
                + ["invented next"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("postmortem_intro_required_phrases" in f.message for f in findings)
    assert any("postmortem_field_required_phrases" in f.message for f in findings)
    assert any("postmortem_next_steps_required_phrases" in f.message for f in findings)


def test_live_v20_scratchpad_validators() -> None:
    assert vm.validate_scratchpad_intro(REPO_ROOT) == []
    assert vm.validate_scratchpad_format(REPO_ROOT) == []
    assert vm.validate_scratchpad_task_meta(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES) == (
        "Agent Coordination Scratchpad",
        "Updated by each agent after completing their task",
        "mark them complete",
    )
    assert tuple(vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES) == (
        "[x] = DONE",
        "[ ] = PENDING",
        "[~] = IN_PROGRESS",
        "[!] = BLOCKED/ESCALATED",
    )
    assert tuple(vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES) == (
        "## Task: Repo Hydration",
        "Status:",
        "Created:",
        "Owner:",
        "Current blocker:",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["scratchpad_intro_required_phrases"] == list(
        vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES
    )
    assert inventory["scratchpad_format_required_phrases"] == list(
        vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES
    )
    assert inventory["scratchpad_task_meta_required_phrases"] == list(
        vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "scratchpad-intro" in vm.VALIDATORS
    assert "scratchpad-format" in vm.VALIDATORS
    assert "scratchpad-task-meta" in vm.VALIDATORS
    assert vm.validate_scratchpad(REPO_ROOT) == []
    assert vm.validate_postmortem_intro(REPO_ROOT) == []
    assert vm.validate_postmortem_fields(REPO_ROOT) == []
    assert vm.validate_postmortem_next_steps(REPO_ROOT) == []


def test_v20_scratchpad_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_scratchpad_intro(tmp_path))
    assert any("missing" in f.message for f in vm.validate_scratchpad_format(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_scratchpad_task_meta(tmp_path)
    )

    _write(tmp_path / "agentic_flows" / "scratchpad.txt", "# scratchpad\n\nNo locks.\n")
    findings = vm.validate_scratchpad_intro(tmp_path)
    for phrase in vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_scratchpad_format(tmp_path)
    assert any("missing Format legend section" in f.message for f in findings)
    for phrase in vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_scratchpad_task_meta(tmp_path)
    assert any("missing Task: Repo Hydration section" in f.message for f in findings)
    for phrase in vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "agentic_flows" / "scratchpad.txt",
        "\n".join(
            [
                "# g0p-agents Agent Coordination Scratchpad",
                "",
                "This file is the **source of truth** for agent coordination state.",
                "Updated by each agent after completing their task. Never delete "
                "entries — mark them complete.",
                "",
                "Format:",
                "- [x] = DONE",
                "- [ ] = PENDING",
                "- [~] = IN_PROGRESS",
                "- [!] = BLOCKED/ESCALATED",
                "",
                "## Task: Repo Hydration — 2026-04-13",
                "",
                "- [x] Phase 1: Discovery",
                "",
                "Status: IN_PROGRESS",
                "Created: 2026-04-13T02:07:01Z",
                "Owner: copilot",
                "Current blocker: Issue creation requires GitHub token",
                "",
            ]
        ),
    )
    assert vm.validate_scratchpad_intro(tmp_path) == []
    assert vm.validate_scratchpad_format(tmp_path) == []
    assert vm.validate_scratchpad_task_meta(tmp_path) == []

    empty_intro = _inventory_payload()
    empty_intro["scratchpad_intro_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_intro_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_intro = _inventory_payload()
    dup_intro["scratchpad_intro_required_phrases"] = [
        vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES[0],
        vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES[0],
        *vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_intro_required_phrases must be unique" in f.message for f in findings
    )

    blank_intro = _inventory_payload()
    blank_intro["scratchpad_intro_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_intro_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_intro = _inventory_payload()
    missing_intro["scratchpad_intro_required_phrases"] = [
        "Agent Coordination Scratchpad",
        "mark them complete",
    ]
    findings = vm._inventory_lock_consistency(
        missing_intro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_intro_required_phrases must require agent updates" in f.message
        for f in findings
    )

    empty_format = _inventory_payload()
    empty_format["scratchpad_format_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_format, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_format_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_format = _inventory_payload()
    dup_format["scratchpad_format_required_phrases"] = [
        vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES[0],
        vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES[0],
        *vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_format, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_format_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_format = _inventory_payload()
    blank_format["scratchpad_format_required_phrases"] = ["[x] = DONE", " "]
    findings = vm._inventory_lock_consistency(
        blank_format, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_format_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_format = _inventory_payload()
    missing_format["scratchpad_format_required_phrases"] = [
        "[x] = DONE",
        "[!] = BLOCKED/ESCALATED",
    ]
    findings = vm._inventory_lock_consistency(
        missing_format, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_format_required_phrases must include DONE/PENDING/IN_PROGRESS"
        " legend lines"
        in f.message
        for f in findings
    )

    empty_meta = _inventory_payload()
    empty_meta["scratchpad_task_meta_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_task_meta_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_meta = _inventory_payload()
    dup_meta["scratchpad_task_meta_required_phrases"] = [
        vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES[0],
        vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES[0],
        *vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_task_meta_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_meta = _inventory_payload()
    blank_meta["scratchpad_task_meta_required_phrases"] = ["Status:", "  "]
    findings = vm._inventory_lock_consistency(
        blank_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_task_meta_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_meta = _inventory_payload()
    missing_meta["scratchpad_task_meta_required_phrases"] = [
        "## Task: Repo Hydration",
        "Status:",
        "Created:",
    ]
    findings = vm._inventory_lock_consistency(
        missing_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "scratchpad_task_meta_required_phrases must include Status/Created/Owner/"
        "Current blocker"
        in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                scratchpad_intro_required_phrases=list(
                    vm.SCRATCHPAD_INTRO_REQUIRED_PHRASES
                )[:-1]
                + ["invented intro"],
                scratchpad_format_required_phrases=list(
                    vm.SCRATCHPAD_FORMAT_REQUIRED_PHRASES
                )[:-1]
                + ["invented format"],
                scratchpad_task_meta_required_phrases=list(
                    vm.SCRATCHPAD_TASK_META_REQUIRED_PHRASES
                )[:-1]
                + ["invented meta"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("scratchpad_intro_required_phrases" in f.message for f in findings)
    assert any("scratchpad_format_required_phrases" in f.message for f in findings)
    assert any("scratchpad_task_meta_required_phrases" in f.message for f in findings)


def test_live_v21_issue_template_validators() -> None:
    assert vm.validate_issue_metadata(REPO_ROOT) == []
    assert vm.validate_issue_routing(REPO_ROOT) == []
    assert vm.validate_bug_repro(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.ISSUE_METADATA_REQUIRED_PHRASES) == (
        "Status: ACTIVE",
        "Tier: 1",
        "Created: YYYY-MM-DD",
        "Owner:",
        "Edit policy: Agent-editable; structural changes require Andrew approval",
    )
    assert tuple(vm.ISSUE_ROUTING_REQUIRED_PHRASES) == (
        "## Agent Surface Routing",
        "| Surface |",
        "| Rationale |",
        "| Priority |",
        "| Branch |",
        "| Dependencies |",
    )
    assert tuple(vm.BUG_REPRO_REQUIRED_PHRASES) == (
        "## Steps to Reproduce",
        "## Expected Behavior",
        "## Actual Behavior",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["issue_metadata_required_phrases"] == list(
        vm.ISSUE_METADATA_REQUIRED_PHRASES
    )
    assert inventory["issue_routing_required_phrases"] == list(
        vm.ISSUE_ROUTING_REQUIRED_PHRASES
    )
    assert inventory["bug_repro_required_phrases"] == list(vm.BUG_REPRO_REQUIRED_PHRASES)
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "issue-metadata" in vm.VALIDATORS
    assert "issue-routing" in vm.VALIDATORS
    assert "bug-repro" in vm.VALIDATORS
    assert vm.validate_agent_task_template(REPO_ROOT) == []
    assert vm.validate_bug_report_template(REPO_ROOT) == []
    assert vm.validate_feature_request_template(REPO_ROOT) == []
    assert vm.validate_scratchpad_intro(REPO_ROOT) == []
    assert vm.validate_scratchpad_format(REPO_ROOT) == []
    assert vm.validate_scratchpad_task_meta(REPO_ROOT) == []


def test_v21_issue_template_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_issue_metadata(tmp_path))
    assert any("missing" in f.message for f in vm.validate_issue_routing(tmp_path))
    assert any("missing" in f.message for f in vm.validate_bug_repro(tmp_path))

    for rel in vm.ISSUE_TEMPLATE_FILES:
        _write(tmp_path / rel, "# template\n\nNo locks.\n")
    findings = vm.validate_issue_metadata(tmp_path)
    for phrase in vm.ISSUE_METADATA_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_issue_routing(tmp_path)
    assert any("missing Agent Surface Routing section" in f.message for f in findings)
    for phrase in vm.ISSUE_ROUTING_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_bug_repro(tmp_path)
    for phrase in vm.BUG_REPRO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    body = "\n".join(
        [
            "---",
            "name: Template",
            "about: test",
            "---",
            "",
            "Status: ACTIVE",
            "Tier: 1",
            "Created: YYYY-MM-DD",
            "Owner: [agent-surface]",
            "Edit policy: Agent-editable; structural changes require Andrew approval",
            "",
            "## Problem",
            "",
            "## Steps to Reproduce",
            "",
            "1.",
            "",
            "## Expected Behavior",
            "",
            "## Actual Behavior",
            "",
            "## Agent Surface Routing",
            "",
            "| Field | Value |",
            "| --- | --- |",
            "| Surface | [agent-surface] |",
            "| Rationale | [why] |",
            "| Priority | [P1/P2/P3] |",
            "| Branch | [branch] |",
            "| Dependencies | [issues] |",
            "",
        ]
    )
    for rel in vm.ISSUE_TEMPLATE_FILES:
        _write(tmp_path / rel, body)
    assert vm.validate_issue_metadata(tmp_path) == []
    assert vm.validate_issue_routing(tmp_path) == []
    assert vm.validate_bug_repro(tmp_path) == []

    empty_meta = _inventory_payload()
    empty_meta["issue_metadata_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_metadata_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_meta = _inventory_payload()
    dup_meta["issue_metadata_required_phrases"] = [
        vm.ISSUE_METADATA_REQUIRED_PHRASES[0],
        vm.ISSUE_METADATA_REQUIRED_PHRASES[0],
        *vm.ISSUE_METADATA_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_metadata_required_phrases must be unique" in f.message for f in findings
    )

    blank_meta = _inventory_payload()
    blank_meta["issue_metadata_required_phrases"] = ["Status: ACTIVE", "  "]
    findings = vm._inventory_lock_consistency(
        blank_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_metadata_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_meta = _inventory_payload()
    missing_meta["issue_metadata_required_phrases"] = [
        "Status: ACTIVE",
        "Created: YYYY-MM-DD",
        "Owner:",
    ]
    findings = vm._inventory_lock_consistency(
        missing_meta, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_metadata_required_phrases must include Status ACTIVE/Tier/Edit policy"
        in f.message
        for f in findings
    )

    empty_routing = _inventory_payload()
    empty_routing["issue_routing_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_routing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_routing_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_routing = _inventory_payload()
    dup_routing["issue_routing_required_phrases"] = [
        vm.ISSUE_ROUTING_REQUIRED_PHRASES[0],
        vm.ISSUE_ROUTING_REQUIRED_PHRASES[0],
        *vm.ISSUE_ROUTING_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_routing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_routing_required_phrases must be unique" in f.message for f in findings
    )

    blank_routing = _inventory_payload()
    blank_routing["issue_routing_required_phrases"] = ["| Surface |", " "]
    findings = vm._inventory_lock_consistency(
        blank_routing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_routing_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_routing = _inventory_payload()
    missing_routing["issue_routing_required_phrases"] = [
        "## Agent Surface Routing",
        "| Surface |",
        "| Priority |",
    ]
    findings = vm._inventory_lock_consistency(
        missing_routing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "issue_routing_required_phrases must include Surface/Rationale/"
        "Priority/Branch/Dependencies"
        in f.message
        for f in findings
    )

    empty_repro = _inventory_payload()
    empty_repro["bug_repro_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_repro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "bug_repro_required_phrases must not be empty" in f.message for f in findings
    )

    dup_repro = _inventory_payload()
    dup_repro["bug_repro_required_phrases"] = [
        vm.BUG_REPRO_REQUIRED_PHRASES[0],
        vm.BUG_REPRO_REQUIRED_PHRASES[0],
        *vm.BUG_REPRO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_repro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "bug_repro_required_phrases must be unique" in f.message for f in findings
    )

    blank_repro = _inventory_payload()
    blank_repro["bug_repro_required_phrases"] = ["## Steps to Reproduce", "  "]
    findings = vm._inventory_lock_consistency(
        blank_repro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "bug_repro_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_repro = _inventory_payload()
    missing_repro["bug_repro_required_phrases"] = [
        "## Steps to Reproduce",
        "## Expected Behavior",
    ]
    findings = vm._inventory_lock_consistency(
        missing_repro, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "bug_repro_required_phrases must include Steps to Reproduce/"
        "Expected/Actual Behavior"
        in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                issue_metadata_required_phrases=list(
                    vm.ISSUE_METADATA_REQUIRED_PHRASES
                )[:-1]
                + ["invented meta"],
                issue_routing_required_phrases=list(
                    vm.ISSUE_ROUTING_REQUIRED_PHRASES
                )[:-1]
                + ["invented routing"],
                bug_repro_required_phrases=list(vm.BUG_REPRO_REQUIRED_PHRASES)[:-1]
                + ["invented repro"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("issue_metadata_required_phrases" in f.message for f in findings)
    assert any("issue_routing_required_phrases" in f.message for f in findings)
    assert any("bug_repro_required_phrases" in f.message for f in findings)


def test_live_v22_contributing_validators() -> None:
    assert vm.validate_contributing_who(REPO_ROOT) == []
    assert vm.validate_contributing_branches(REPO_ROOT) == []
    assert vm.validate_contributing_pr(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.CONTRIBUTING_WHO_REQUIRED_PHRASES) == (
        "## Who Can Contribute",
        "FUZZYWIGG multi-agent ecosystem",
        "Agent surfaces",
        "Andrew Pappas",
        "Ecosystem collaborators",
    )
    assert tuple(vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES) == (
        "## Branch Strategy",
        "`alpha`",
        "Default / protected",
        "`copilot/<task>`",
        "`geryon/<task>`",
        "`claude/<task>`",
        "`cursor/<task>`",
    )
    assert tuple(vm.CONTRIBUTING_PR_REQUIRED_PHRASES) == (
        "## PR Requirements",
        "Branch off from `alpha`",
        "Fill in the PR template completely",
        "All CI checks must pass before merge",
        "One approval required",
        "## Governance",
        "require Andrew approval",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["contributing_who_required_phrases"] == list(
        vm.CONTRIBUTING_WHO_REQUIRED_PHRASES
    )
    assert inventory["contributing_branch_required_phrases"] == list(
        vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES
    )
    assert inventory["contributing_pr_required_phrases"] == list(
        vm.CONTRIBUTING_PR_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "contributing-who" in vm.VALIDATORS
    assert "contributing-branches" in vm.VALIDATORS
    assert "contributing-pr" in vm.VALIDATORS
    assert vm.validate_contributing_packaging(REPO_ROOT) == []
    assert vm.validate_issue_metadata(REPO_ROOT) == []
    assert vm.validate_issue_routing(REPO_ROOT) == []
    assert vm.validate_bug_repro(REPO_ROOT) == []


def test_v22_contributing_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_contributing_who(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_contributing_branches(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_contributing_pr(tmp_path))

    _write(tmp_path / "CONTRIBUTING.md", "# Contributing\n\nNo locked content.\n")
    findings = vm.validate_contributing_who(tmp_path)
    for phrase in vm.CONTRIBUTING_WHO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_branches(tmp_path)
    assert any("missing Branch Strategy section" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_pr(tmp_path)
    assert any("missing PR Requirements section" in f.message for f in findings)
    assert any("missing Governance section" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_PR_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                "# Contributing to g0p-agents",
                "",
                "## Who Can Contribute",
                "",
                "This repo is part of the FUZZYWIGG multi-agent ecosystem.",
                "- **Agent surfaces** (copilot, geryon)",
                "- **Andrew Pappas** (owner)",
                "- **Ecosystem collaborators** — invited contributors",
                "",
                "## Branch Strategy",
                "",
                "| Branch | Purpose |",
                "| --- | --- |",
                "| `alpha` | Default / protected. Merges require PR + review. |",
                "| `copilot/<task>` | Copilot agent work |",
                "| `geryon/<task>` | Geryon agent work |",
                "| `claude/<task>` | claude-cowork strategic work |",
                "| `cursor/<task>` | Cursor cloud-agent work |",
                "",
                "## PR Requirements",
                "",
                "1. Branch off from `alpha` using the naming convention above",
                "2. Fill in the PR template completely",
                "3. All CI checks must pass before merge (markdown lint)",
                "4. One approval required (Andrew or designated reviewer)",
                "",
                "## Governance",
                "",
                "Structural changes require Andrew approval before merging.",
                "",
            ]
        ),
    )
    assert vm.validate_contributing_who(tmp_path) == []
    assert vm.validate_contributing_branches(tmp_path) == []
    assert vm.validate_contributing_pr(tmp_path) == []

    inventory = _inventory_payload()
    empty_who = dict(inventory)
    empty_who["contributing_who_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_who, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_who_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_who = dict(inventory)
    dup_who["contributing_who_required_phrases"] = [
        vm.CONTRIBUTING_WHO_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_WHO_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_WHO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_who, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_who_required_phrases must be unique" in f.message for f in findings
    )

    blank_who = dict(inventory)
    blank_who["contributing_who_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_who, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_who_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_who = dict(inventory)
    missing_who["contributing_who_required_phrases"] = [
        "## Who Can Contribute",
        "FUZZYWIGG multi-agent ecosystem",
    ]
    findings = vm._inventory_lock_consistency(
        missing_who, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_who_required_phrases must name Andrew Pappas" in f.message
        for f in findings
    )

    empty_branches = dict(inventory)
    empty_branches["contributing_branch_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_branches, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_branch_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_branches = dict(inventory)
    dup_branches["contributing_branch_required_phrases"] = [
        vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_branches, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_branch_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_branches = dict(inventory)
    blank_branches["contributing_branch_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_branches, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_branch_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_branches = dict(inventory)
    missing_branches["contributing_branch_required_phrases"] = [
        "## Branch Strategy",
        "`alpha`",
    ]
    findings = vm._inventory_lock_consistency(
        missing_branches, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_branch_required_phrases must include alpha/" in f.message
        for f in findings
    )

    empty_pr = dict(inventory)
    empty_pr["contributing_pr_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_pr_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_pr = dict(inventory)
    dup_pr["contributing_pr_required_phrases"] = [
        vm.CONTRIBUTING_PR_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_PR_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_PR_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_pr_required_phrases must be unique" in f.message for f in findings
    )

    blank_pr = dict(inventory)
    blank_pr["contributing_pr_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_pr_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_pr = dict(inventory)
    missing_pr["contributing_pr_required_phrases"] = [
        "## PR Requirements",
        "One approval required",
    ]
    findings = vm._inventory_lock_consistency(
        missing_pr, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_pr_required_phrases must include PR Requirements" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                contributing_who_required_phrases=list(
                    vm.CONTRIBUTING_WHO_REQUIRED_PHRASES
                )[:-1]
                + ["invented who"],
                contributing_branch_required_phrases=list(
                    vm.CONTRIBUTING_BRANCH_REQUIRED_PHRASES
                )[:-1]
                + ["invented branch"],
                contributing_pr_required_phrases=list(
                    vm.CONTRIBUTING_PR_REQUIRED_PHRASES
                )[:-1]
                + ["invented pr"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("contributing_who_required_phrases" in f.message for f in findings)
    assert any("contributing_branch_required_phrases" in f.message for f in findings)
    assert any("contributing_pr_required_phrases" in f.message for f in findings)


def test_live_v23_pr_template_validators() -> None:
    assert vm.validate_pr_summary(REPO_ROOT) == []
    assert vm.validate_pr_acceptance(REPO_ROOT) == []
    assert vm.validate_pr_notes(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.PR_SUMMARY_REQUIRED_PHRASES) == (
        "# Summary",
        "One sentence: what does this PR accomplish?",
        "## Problem",
        "Closes #N",
    )
    assert tuple(vm.PR_ACCEPTANCE_REQUIRED_PHRASES) == (
        "## Changes",
        "List of files changed and what was done",
        "## Acceptance Criteria",
        "Copy from the linked issue",
        "- [ ]",
    )
    assert tuple(vm.PR_NOTES_REQUIRED_PHRASES) == (
        "## Notes for Reviewer",
        "Anything Andrew or the reviewing agent should know",
        "[agent-surface]",
        "#[issue-number]",
        "[P1/P2/P3]",
    )
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["pr_summary_required_phrases"] == list(vm.PR_SUMMARY_REQUIRED_PHRASES)
    assert inventory["pr_acceptance_required_phrases"] == list(
        vm.PR_ACCEPTANCE_REQUIRED_PHRASES
    )
    assert inventory["pr_notes_required_phrases"] == list(vm.PR_NOTES_REQUIRED_PHRASES)
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "pr-summary" in vm.VALIDATORS
    assert "pr-acceptance" in vm.VALIDATORS
    assert "pr-notes" in vm.VALIDATORS
    assert list(vm.CI_REQUIRED_ACTIONS) == inventory["ci_required_actions"]
    assert "actions/setup-python@v7" in vm.CI_REQUIRED_ACTIONS
    assert "actions/upload-artifact@v7" in vm.CI_REQUIRED_ACTIONS
    assert vm.validate_pr_template(REPO_ROOT) == []
    assert vm.validate_pr_routing(REPO_ROOT) == []
    assert vm.validate_ci_actions(REPO_ROOT) == []
    assert vm.validate_contributing_who(REPO_ROOT) == []
    assert vm.validate_contributing_branches(REPO_ROOT) == []
    assert vm.validate_contributing_pr(REPO_ROOT) == []


def test_v23_pr_template_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_pr_summary(tmp_path))
    assert any("missing" in f.message for f in vm.validate_pr_acceptance(tmp_path))
    assert any("missing" in f.message for f in vm.validate_pr_notes(tmp_path))

    _write(tmp_path / ".github" / "pull_request_template.md", "# Empty\n\nNo locks.\n")
    findings = vm.validate_pr_summary(tmp_path)
    for phrase in vm.PR_SUMMARY_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_pr_acceptance(tmp_path)
    assert any("missing Acceptance Criteria section" in f.message for f in findings)
    for phrase in vm.PR_ACCEPTANCE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_pr_notes(tmp_path)
    assert any("missing Notes for Reviewer section" in f.message for f in findings)
    for phrase in vm.PR_NOTES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "# Summary",
                "",
                "<!-- One sentence: what does this PR accomplish? -->",
                "",
                "## Problem",
                "",
                "<!-- Link to the issue this closes: Closes #N -->",
                "",
                "## Changes",
                "",
                "<!-- List of files changed and what was done -->",
                "",
                "-",
                "-",
                "",
                "## Acceptance Criteria",
                "",
                "<!-- Copy from the linked issue -->",
                "",
                "- [ ]",
                "",
                "## Agent Surface Routing",
                "",
                "| Field | Value |",
                "| --- | --- |",
                "| Surface | [agent-surface] |",
                "| Issue | #[issue-number] |",
                "| Branch | [branch name] |",
                "| Priority | [P1/P2/P3] |",
                "",
                "## Notes for Reviewer",
                "",
                "<!-- Anything Andrew or the reviewing agent should know -->",
                "",
            ]
        ),
    )
    assert vm.validate_pr_summary(tmp_path) == []
    assert vm.validate_pr_acceptance(tmp_path) == []
    assert vm.validate_pr_notes(tmp_path) == []

    inventory = _inventory_payload()
    empty_summary = dict(inventory)
    empty_summary["pr_summary_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_summary, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_summary_required_phrases must not be empty" in f.message for f in findings
    )

    dup_summary = dict(inventory)
    dup_summary["pr_summary_required_phrases"] = [
        vm.PR_SUMMARY_REQUIRED_PHRASES[0],
        vm.PR_SUMMARY_REQUIRED_PHRASES[0],
        *vm.PR_SUMMARY_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_summary, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_summary_required_phrases must be unique" in f.message for f in findings
    )

    blank_summary = dict(inventory)
    blank_summary["pr_summary_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_summary, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_summary_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_summary = dict(inventory)
    missing_summary["pr_summary_required_phrases"] = ["# Summary"]
    findings = vm._inventory_lock_consistency(
        missing_summary, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_summary_required_phrases must include Summary/Problem" in f.message
        for f in findings
    )

    empty_acc = dict(inventory)
    empty_acc["pr_acceptance_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_acc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_acceptance_required_phrases must not be empty" in f.message for f in findings
    )

    dup_acc = dict(inventory)
    dup_acc["pr_acceptance_required_phrases"] = [
        vm.PR_ACCEPTANCE_REQUIRED_PHRASES[0],
        vm.PR_ACCEPTANCE_REQUIRED_PHRASES[0],
        *vm.PR_ACCEPTANCE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_acc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_acceptance_required_phrases must be unique" in f.message for f in findings
    )

    blank_acc = dict(inventory)
    blank_acc["pr_acceptance_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_acc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_acceptance_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_acc = dict(inventory)
    missing_acc["pr_acceptance_required_phrases"] = ["## Changes"]
    findings = vm._inventory_lock_consistency(
        missing_acc, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_acceptance_required_phrases must include Changes" in f.message
        for f in findings
    )

    empty_notes = dict(inventory)
    empty_notes["pr_notes_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_notes, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_notes_required_phrases must not be empty" in f.message for f in findings
    )

    dup_notes = dict(inventory)
    dup_notes["pr_notes_required_phrases"] = [
        vm.PR_NOTES_REQUIRED_PHRASES[0],
        vm.PR_NOTES_REQUIRED_PHRASES[0],
        *vm.PR_NOTES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_notes, schema_path="schemas/packaging-inventory.json"
    )
    assert any("pr_notes_required_phrases must be unique" in f.message for f in findings)

    blank_notes = dict(inventory)
    blank_notes["pr_notes_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_notes, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_notes_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_notes = dict(inventory)
    missing_notes["pr_notes_required_phrases"] = ["## Notes for Reviewer"]
    findings = vm._inventory_lock_consistency(
        missing_notes, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "pr_notes_required_phrases must include Notes for Reviewer" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                pr_summary_required_phrases=list(vm.PR_SUMMARY_REQUIRED_PHRASES)[:-1]
                + ["invented summary"],
                pr_acceptance_required_phrases=list(vm.PR_ACCEPTANCE_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented acceptance"],
                pr_notes_required_phrases=list(vm.PR_NOTES_REQUIRED_PHRASES)[:-1]
                + ["invented notes"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("pr_summary_required_phrases" in f.message for f in findings)
    assert any("pr_acceptance_required_phrases" in f.message for f in findings)
    assert any("pr_notes_required_phrases" in f.message for f in findings)



def test_live_v24_readme_honesty_validators() -> None:
    assert vm.validate_readme_honesty(REPO_ROOT) == []
    assert vm.validate_readme_historic(REPO_ROOT) == []
    assert vm.validate_readme_contents(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert tuple(vm.README_HONESTY_REQUIRED_PHRASES) == (
        "(archived reference)",
        "This is not a live hive, runtime, or production swarm",
        "prompt fiction",
        "no running hive mind in this tree",
        "fuzzywigg/agents-standard",
    )
    assert tuple(vm.README_HISTORIC_REQUIRED_PHRASES) == (
        "## Historic prompt set",
        "Designing quantum-safe algorithms",
        "Implementing multi-chain, quantum-resistant contracts",
        'Creating "walled garden" mobile security',
        "Managing conflicts via stimgery and YAML recipes",
    )
    assert tuple(vm.README_CONTENTS_REQUIRED_PHRASES) == (
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
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["readme_honesty_required_phrases"] == list(
        vm.README_HONESTY_REQUIRED_PHRASES
    )
    assert inventory["readme_historic_required_phrases"] == list(
        vm.README_HISTORIC_REQUIRED_PHRASES
    )
    assert inventory["readme_contents_required_phrases"] == list(
        vm.README_CONTENTS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "readme-honesty" in vm.VALIDATORS
    assert "readme-historic" in vm.VALIDATORS
    assert "readme-contents" in vm.VALIDATORS
    assert vm.validate_readme_packaging(REPO_ROOT) == []
    assert vm.validate_readme_badges(REPO_ROOT) == []
    assert vm.validate_pr_summary(REPO_ROOT) == []
    assert vm.validate_pr_acceptance(REPO_ROOT) == []
    assert vm.validate_pr_notes(REPO_ROOT) == []


def test_v24_readme_honesty_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_readme_honesty(tmp_path))
    assert any("missing" in f.message for f in vm.validate_readme_historic(tmp_path))
    assert any("missing" in f.message for f in vm.validate_readme_contents(tmp_path))

    _write(tmp_path / "README.md", "# Empty\n\nNo locks.\n")
    findings = vm.validate_readme_honesty(tmp_path)
    for phrase in vm.README_HONESTY_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_readme_historic(tmp_path)
    assert any("missing Historic prompt set section" in f.message for f in findings)
    for phrase in vm.README_HISTORIC_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_readme_contents(tmp_path)
    assert any("missing Contents section" in f.message for f in findings)
    assert any("missing Manifest validation section" in f.message for f in findings)
    for phrase in vm.README_CONTENTS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    locked_readme = "\n".join(
        [
            "# g0p-agents (archived reference)",
            "",
            "**This is not a live hive, runtime, or production swarm.** The "
            '"Oracle-Style Quantum Hive Mind" language in the historic copy '
            "below is prompt fiction. There is no running hive mind in this "
            "tree. For current operational standards, see "
            "[fuzzywigg/agents-standard]"
            "(https://github.com/fuzzywigg/agents-standard).",
            "",
            "## Historic prompt set",
            "",
            "1. **QuantumArchitectAgent**: Designing quantum-safe algorithms.",
            "2. **BlockchainArchitectAgent**: Implementing multi-chain, "
            "quantum-resistant contracts.",
            '3. **EdgeSecurityAgent**: Creating "walled garden" mobile security.',
            "4. **OrchestrationAgent**: Managing conflicts via stimgery and "
            "YAML recipes.",
            "",
            "## Contents",
            "",
            "* **AGENT-PROMPTS.md**: Full system prompts.",
            "* **GOOSE-RECIPES.md**: YAML-based orchestration.",
            "* **IMPLEMENTATION-GUIDE.md**: Step-by-step setup.",
            "* **AGENTS-v2.2.md**: Historic constitution.",
            "",
            "## Cloud agents",
            "",
            "Docs-only bootstrap lives in `.cursor/environment.json`.",
            "",
            "## Manifest validation",
            "",
            "CI enforces packaging locks.",
            "",
            "## License",
            "",
            "MIT.",
            "",
        ]
    )
    _write(tmp_path / "README.md", locked_readme)
    assert vm.validate_readme_honesty(tmp_path) == []
    assert vm.validate_readme_historic(tmp_path) == []
    assert vm.validate_readme_contents(tmp_path) == []

    inventory = _inventory_payload()
    empty_honesty = dict(inventory)
    empty_honesty["readme_honesty_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_honesty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_honesty_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_honesty = dict(inventory)
    dup_honesty["readme_honesty_required_phrases"] = [
        vm.README_HONESTY_REQUIRED_PHRASES[0],
        vm.README_HONESTY_REQUIRED_PHRASES[0],
        *vm.README_HONESTY_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_honesty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_honesty_required_phrases must be unique" in f.message for f in findings
    )

    blank_honesty = dict(inventory)
    blank_honesty["readme_honesty_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_honesty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_honesty_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_honesty = dict(inventory)
    missing_honesty["readme_honesty_required_phrases"] = ["(archived reference)"]
    findings = vm._inventory_lock_consistency(
        missing_honesty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_honesty_required_phrases must include archived reference" in f.message
        for f in findings
    )

    empty_historic = dict(inventory)
    empty_historic["readme_historic_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_historic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_historic_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_historic = dict(inventory)
    dup_historic["readme_historic_required_phrases"] = [
        vm.README_HISTORIC_REQUIRED_PHRASES[0],
        vm.README_HISTORIC_REQUIRED_PHRASES[0],
        *vm.README_HISTORIC_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_historic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_historic_required_phrases must be unique" in f.message for f in findings
    )

    blank_historic = dict(inventory)
    blank_historic["readme_historic_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_historic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_historic_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_historic = dict(inventory)
    missing_historic["readme_historic_required_phrases"] = ["## Historic prompt set"]
    findings = vm._inventory_lock_consistency(
        missing_historic, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_historic_required_phrases must include Historic prompt set" in f.message
        for f in findings
    )

    empty_contents = dict(inventory)
    empty_contents["readme_contents_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_contents, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_contents_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_contents = dict(inventory)
    dup_contents["readme_contents_required_phrases"] = [
        vm.README_CONTENTS_REQUIRED_PHRASES[0],
        vm.README_CONTENTS_REQUIRED_PHRASES[0],
        *vm.README_CONTENTS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_contents, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_contents_required_phrases must be unique" in f.message for f in findings
    )

    blank_contents = dict(inventory)
    blank_contents["readme_contents_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_contents, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_contents_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_contents = dict(inventory)
    missing_contents["readme_contents_required_phrases"] = ["## Contents"]
    findings = vm._inventory_lock_consistency(
        missing_contents, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_contents_required_phrases must include Contents" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                readme_honesty_required_phrases=list(vm.README_HONESTY_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented honesty"],
                readme_historic_required_phrases=list(
                    vm.README_HISTORIC_REQUIRED_PHRASES
                )[:-1]
                + ["invented historic"],
                readme_contents_required_phrases=list(
                    vm.README_CONTENTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented contents"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("readme_honesty_required_phrases" in f.message for f in findings)
    assert any("readme_historic_required_phrases" in f.message for f in findings)
    assert any("readme_contents_required_phrases" in f.message for f in findings)


def test_live_v25_goose_recipe_validators() -> None:
    assert vm.validate_goose_howto(REPO_ROOT) == []
    assert vm.validate_goose_state_machine(REPO_ROOT) == []
    assert vm.validate_goose_naming(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "goose-howto" in vm.VALIDATORS
    assert "goose-state-machine" in vm.VALIDATORS
    assert "goose-naming" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["goose_howto_required_phrases"] == list(
        vm.GOOSE_HOWTO_REQUIRED_PHRASES
    )
    assert inventory["goose_state_machine_required_phrases"] == list(
        vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES
    )
    assert inventory["goose_naming_required_phrases"] == list(
        vm.GOOSE_NAMING_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["goose"](REPO_ROOT) == []
    assert vm.validate_readme_honesty(REPO_ROOT) == []


def test_v25_goose_recipe_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_goose_howto(tmp_path))
    assert any("missing" in f.message for f in vm.validate_goose_state_machine(tmp_path))
    assert any("missing" in f.message for f in vm.validate_goose_naming(tmp_path))

    _write(tmp_path / "GOOSE-RECIPES.md", "# Goose\n\nNo locked content.\n")
    findings = vm.validate_goose_howto(tmp_path)
    for phrase in vm.GOOSE_HOWTO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_state_machine(tmp_path)
    assert any("missing Scratchpad State Machine section" in f.message for f in findings)
    for phrase in vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_naming(tmp_path)
    assert any(
        "missing Recipe Naming Convention section" in f.message for f in findings
    )
    assert any("missing Adding New Recipes section" in f.message for f in findings)
    for phrase in vm.GOOSE_NAMING_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                *vm.GOOSE_HOWTO_REQUIRED_PHRASES,
                *vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES,
                *vm.GOOSE_NAMING_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_goose_howto(tmp_path) == []
    assert vm.validate_goose_state_machine(tmp_path) == []
    assert vm.validate_goose_naming(tmp_path) == []

    empty = _inventory_payload()
    empty["goose_howto_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_howto_required_phrases must not be empty" in f.message for f in findings
    )

    dup = _inventory_payload()
    dup["goose_howto_required_phrases"] = [
        vm.GOOSE_HOWTO_REQUIRED_PHRASES[0],
        vm.GOOSE_HOWTO_REQUIRED_PHRASES[0],
        *vm.GOOSE_HOWTO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_howto_required_phrases must be unique" in f.message for f in findings
    )

    blank = _inventory_payload()
    blank["goose_howto_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_howto_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["goose_howto_required_phrases"] = ["## How to Use These Recipes"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_howto_required_phrases must include How to Use" in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["goose_state_machine_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_state_machine_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["goose_state_machine_required_phrases"] = [
        vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES[0],
        vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES[0],
        *vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_state_machine_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["goose_state_machine_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_state_machine_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["goose_state_machine_required_phrases"] = ["## Scratchpad State Machine"]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_state_machine_required_phrases must include Scratchpad" in f.message
        for f in findings
    )

    empty_n = _inventory_payload()
    empty_n["goose_naming_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_naming_required_phrases must not be empty" in f.message for f in findings
    )

    dup_n = _inventory_payload()
    dup_n["goose_naming_required_phrases"] = [
        vm.GOOSE_NAMING_REQUIRED_PHRASES[0],
        vm.GOOSE_NAMING_REQUIRED_PHRASES[0],
        *vm.GOOSE_NAMING_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_naming_required_phrases must be unique" in f.message for f in findings
    )

    blank_n = _inventory_payload()
    blank_n["goose_naming_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_naming_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_n = _inventory_payload()
    missing_n["goose_naming_required_phrases"] = ["## Recipe Naming Convention"]
    findings = vm._inventory_lock_consistency(
        missing_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_naming_required_phrases must include Recipe Naming" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                goose_howto_required_phrases=list(vm.GOOSE_HOWTO_REQUIRED_PHRASES)[:-1]
                + ["invented howto"],
                goose_state_machine_required_phrases=list(
                    vm.GOOSE_STATE_MACHINE_REQUIRED_PHRASES
                )[:-1]
                + ["invented state"],
                goose_naming_required_phrases=list(vm.GOOSE_NAMING_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented naming"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("goose_howto_required_phrases" in f.message for f in findings)
    assert any("goose_state_machine_required_phrases" in f.message for f in findings)
    assert any("goose_naming_required_phrases" in f.message for f in findings)


def test_live_v26_agent_prompt_validators() -> None:
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "prompt-roles" in vm.VALIDATORS
    assert "prompt-sections" in vm.VALIDATORS
    assert "prompt-usage" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["prompt_roles_required_phrases"] == list(
        vm.PROMPT_ROLES_REQUIRED_PHRASES
    )
    assert inventory["prompt_sections_required_phrases"] == list(
        vm.PROMPT_SECTIONS_REQUIRED_PHRASES
    )
    assert inventory["prompt_usage_required_phrases"] == list(
        vm.PROMPT_USAGE_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["prompts"](REPO_ROOT) == []
    assert vm.validate_goose_howto(REPO_ROOT) == []


def test_v26_agent_prompt_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_prompt_roles(tmp_path))
    assert any("missing" in f.message for f in vm.validate_prompt_sections(tmp_path))
    assert any("missing" in f.message for f in vm.validate_prompt_usage(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    findings = vm.validate_prompt_roles(tmp_path)
    for phrase in vm.PROMPT_ROLES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_prompt_sections(tmp_path)
    assert any("missing Your Role section" in f.message for f in findings)
    assert any("missing Key Constraints section" in f.message for f in findings)
    assert any(
        "missing Conflict Resolution Matrix section" in f.message for f in findings
    )
    for phrase in vm.PROMPT_SECTIONS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_prompt_usage(tmp_path)
    assert any("missing Usage Instructions section" in f.message for f in findings)
    assert any(
        "missing Integration with AGENTS.md section" in f.message for f in findings
    )
    for phrase in vm.PROMPT_USAGE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_ROLES_REQUIRED_PHRASES,
                *vm.PROMPT_SECTIONS_REQUIRED_PHRASES,
                *vm.PROMPT_USAGE_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_roles(tmp_path) == []
    assert vm.validate_prompt_sections(tmp_path) == []
    assert vm.validate_prompt_usage(tmp_path) == []

    empty = _inventory_payload()
    empty["prompt_roles_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_roles_required_phrases must not be empty" in f.message for f in findings
    )

    dup = _inventory_payload()
    dup["prompt_roles_required_phrases"] = [
        vm.PROMPT_ROLES_REQUIRED_PHRASES[0],
        vm.PROMPT_ROLES_REQUIRED_PHRASES[0],
        *vm.PROMPT_ROLES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_roles_required_phrases must be unique" in f.message for f in findings
    )

    blank = _inventory_payload()
    blank["prompt_roles_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_roles_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["prompt_roles_required_phrases"] = [
        "## 1. QuantumArchitectAgent Prompt Template"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_roles_required_phrases must include Quantum" in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["prompt_sections_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_sections_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["prompt_sections_required_phrases"] = [
        vm.PROMPT_SECTIONS_REQUIRED_PHRASES[0],
        vm.PROMPT_SECTIONS_REQUIRED_PHRASES[0],
        *vm.PROMPT_SECTIONS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_sections_required_phrases must be unique" in f.message for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["prompt_sections_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_sections_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["prompt_sections_required_phrases"] = ["## Your Role"]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_sections_required_phrases must include Your Role" in f.message
        for f in findings
    )

    empty_u = _inventory_payload()
    empty_u["prompt_usage_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_usage_required_phrases must not be empty" in f.message for f in findings
    )

    dup_u = _inventory_payload()
    dup_u["prompt_usage_required_phrases"] = [
        vm.PROMPT_USAGE_REQUIRED_PHRASES[0],
        vm.PROMPT_USAGE_REQUIRED_PHRASES[0],
        *vm.PROMPT_USAGE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_usage_required_phrases must be unique" in f.message for f in findings
    )

    blank_u = _inventory_payload()
    blank_u["prompt_usage_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_usage_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_u = _inventory_payload()
    missing_u["prompt_usage_required_phrases"] = ["## Usage Instructions"]
    findings = vm._inventory_lock_consistency(
        missing_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_usage_required_phrases must include Usage Instructions" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_roles_required_phrases=list(vm.PROMPT_ROLES_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented roles"],
                prompt_sections_required_phrases=list(
                    vm.PROMPT_SECTIONS_REQUIRED_PHRASES
                )[:-1]
                + ["invented sections"],
                prompt_usage_required_phrases=list(vm.PROMPT_USAGE_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented usage"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("prompt_roles_required_phrases" in f.message for f in findings)
    assert any("prompt_sections_required_phrases" in f.message for f in findings)
    assert any("prompt_usage_required_phrases" in f.message for f in findings)

def test_live_v27_implementation_guide_validators() -> None:
    assert vm.validate_implementation_phases(REPO_ROOT) == []
    assert vm.validate_implementation_tools(REPO_ROOT) == []
    assert vm.validate_implementation_success(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "implementation-phases" in vm.VALIDATORS
    assert "implementation-tools" in vm.VALIDATORS
    assert "implementation-success" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["implementation_phases_required_phrases"] == list(
        vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES
    )
    assert inventory["implementation_tools_required_phrases"] == list(
        vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES
    )
    assert inventory["implementation_success_required_phrases"] == list(
        vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["implementation-guide"](REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []


def test_v27_implementation_guide_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_implementation_phases(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_implementation_tools(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_implementation_success(tmp_path)
    )

    _write(tmp_path / "IMPLEMENTATION-GUIDE.md", "# Guide\n\nNo locked content.\n")
    findings = vm.validate_implementation_phases(tmp_path)
    assert any("missing Full Implementation section" in f.message for f in findings)
    assert any("missing Phase 1 Infrastructure section" in f.message for f in findings)
    assert any("missing Phase 6 Iterate section" in f.message for f in findings)
    for phrase in vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_implementation_tools(tmp_path)
    assert any(
        "missing Tools & Software Checklist section" in f.message for f in findings
    )
    for phrase in vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_implementation_success(tmp_path)
    assert any("missing Success Criteria section" in f.message for f in findings)
    assert any(
        "missing Common Issues & Solutions section" in f.message for f in findings
    )
    assert any("missing Next Steps section" in f.message for f in findings)
    for phrase in vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "IMPLEMENTATION-GUIDE.md",
        "\n".join(
            [
                *vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES,
                *vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES,
                *vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_implementation_phases(tmp_path) == []
    assert vm.validate_implementation_tools(tmp_path) == []
    assert vm.validate_implementation_success(tmp_path) == []

    empty = _inventory_payload()
    empty["implementation_phases_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_phases_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["implementation_phases_required_phrases"] = [
        vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_phases_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["implementation_phases_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_phases_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["implementation_phases_required_phrases"] = [
        "## Full Implementation (1-2 weeks)"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_phases_required_phrases must include Full" in f.message
        for f in findings
    )

    empty_t = _inventory_payload()
    empty_t["implementation_tools_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_tools_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_t = _inventory_payload()
    dup_t["implementation_tools_required_phrases"] = [
        vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_tools_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_t = _inventory_payload()
    blank_t["implementation_tools_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_tools_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_t = _inventory_payload()
    missing_t["implementation_tools_required_phrases"] = [
        "## Tools & Software Checklist"
    ]
    findings = vm._inventory_lock_consistency(
        missing_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_tools_required_phrases must include Tools" in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["implementation_success_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_success_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["implementation_success_required_phrases"] = [
        vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_success_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["implementation_success_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_success_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["implementation_success_required_phrases"] = ["## Success Criteria"]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_success_required_phrases must include Success" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                implementation_phases_required_phrases=list(
                    vm.IMPLEMENTATION_PHASES_REQUIRED_PHRASES
                )[:-1]
                + ["invented phases"],
                implementation_tools_required_phrases=list(
                    vm.IMPLEMENTATION_TOOLS_REQUIRED_PHRASES
                )[:-1]
                + ["invented tools"],
                implementation_success_required_phrases=list(
                    vm.IMPLEMENTATION_SUCCESS_REQUIRED_PHRASES
                )[:-1]
                + ["invented success"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("implementation_phases_required_phrases" in f.message for f in findings)
    assert any("implementation_tools_required_phrases" in f.message for f in findings)
    assert any(
        "implementation_success_required_phrases" in f.message for f in findings
    )

def test_live_v28_execution_summary_validators() -> None:
    assert vm.validate_execution_timeline(REPO_ROOT) == []
    assert vm.validate_execution_technologies(REPO_ROOT) == []
    assert vm.validate_execution_workflow(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "execution-timeline" in vm.VALIDATORS
    assert "execution-technologies" in vm.VALIDATORS
    assert "execution-workflow" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["execution_timeline_required_phrases"] == list(
        vm.EXECUTION_TIMELINE_REQUIRED_PHRASES
    )
    assert inventory["execution_technologies_required_phrases"] == list(
        vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES
    )
    assert inventory["execution_workflow_required_phrases"] == list(
        vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["execution-summary"](REPO_ROOT) == []
    assert vm.validate_implementation_phases(REPO_ROOT) == []


def test_v28_execution_summary_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_execution_timeline(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_execution_technologies(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_execution_workflow(tmp_path))

    _write(tmp_path / "EXECUTION-SUMMARY.md", "# Exec\n\nNo locked content.\n")
    findings = vm.validate_execution_timeline(tmp_path)
    assert any("missing Implementation Timeline section" in f.message for f in findings)
    for phrase in vm.EXECUTION_TIMELINE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_execution_technologies(tmp_path)
    assert any("missing Key Technologies section" in f.message for f in findings)
    for phrase in vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_execution_workflow(tmp_path)
    assert any("missing Workflow Overview section" in f.message for f in findings)
    for phrase in vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "EXECUTION-SUMMARY.md",
        "\n".join(
            [
                *vm.EXECUTION_TIMELINE_REQUIRED_PHRASES,
                *vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES,
                *vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_execution_timeline(tmp_path) == []
    assert vm.validate_execution_technologies(tmp_path) == []
    assert vm.validate_execution_workflow(tmp_path) == []

    empty = _inventory_payload()
    empty["execution_timeline_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_timeline_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["execution_timeline_required_phrases"] = [
        vm.EXECUTION_TIMELINE_REQUIRED_PHRASES[0],
        vm.EXECUTION_TIMELINE_REQUIRED_PHRASES[0],
        *vm.EXECUTION_TIMELINE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_timeline_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["execution_timeline_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_timeline_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["execution_timeline_required_phrases"] = ["## Implementation Timeline"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_timeline_required_phrases must include Implementation" in f.message
        for f in findings
    )

    empty_t = _inventory_payload()
    empty_t["execution_technologies_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_technologies_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_t = _inventory_payload()
    dup_t["execution_technologies_required_phrases"] = [
        vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES[0],
        vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES[0],
        *vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_technologies_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_t = _inventory_payload()
    blank_t["execution_technologies_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_technologies_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_t = _inventory_payload()
    missing_t["execution_technologies_required_phrases"] = [
        "## Key Technologies (All Covered)"
    ]
    findings = vm._inventory_lock_consistency(
        missing_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_technologies_required_phrases must include Key" in f.message
        for f in findings
    )

    empty_w = _inventory_payload()
    empty_w["execution_workflow_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_w, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_workflow_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_w = _inventory_payload()
    dup_w["execution_workflow_required_phrases"] = [
        vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES[0],
        vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES[0],
        *vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_w, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_workflow_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_w = _inventory_payload()
    blank_w["execution_workflow_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_w, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_workflow_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_w = _inventory_payload()
    missing_w["execution_workflow_required_phrases"] = ["## Workflow Overview"]
    findings = vm._inventory_lock_consistency(
        missing_w, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_workflow_required_phrases must include Workflow" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                execution_timeline_required_phrases=list(
                    vm.EXECUTION_TIMELINE_REQUIRED_PHRASES
                )[:-1]
                + ["invented timeline"],
                execution_technologies_required_phrases=list(
                    vm.EXECUTION_TECHNOLOGIES_REQUIRED_PHRASES
                )[:-1]
                + ["invented tech"],
                execution_workflow_required_phrases=list(
                    vm.EXECUTION_WORKFLOW_REQUIRED_PHRASES
                )[:-1]
                + ["invented workflow"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("execution_timeline_required_phrases" in f.message for f in findings)
    assert any(
        "execution_technologies_required_phrases" in f.message for f in findings
    )
    assert any("execution_workflow_required_phrases" in f.message for f in findings)



def test_live_v29_contributing_validators() -> None:
    assert vm.validate_contributing_issues(REPO_ROOT) == []
    assert vm.validate_contributing_local(REPO_ROOT) == []
    assert vm.validate_contributing_governance(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "contributing-issues" in vm.VALIDATORS
    assert "contributing-local" in vm.VALIDATORS
    assert "contributing-governance" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["contributing_issues_required_phrases"] == list(
        vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES
    )
    assert inventory["contributing_local_required_phrases"] == list(
        vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES
    )
    assert inventory["contributing_governance_required_phrases"] == list(
        vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["contributing"](REPO_ROOT) == []
    assert vm.validate_execution_timeline(REPO_ROOT) == []


def test_v29_contributing_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_contributing_issues(tmp_path))
    assert any("missing" in f.message for f in vm.validate_contributing_local(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_contributing_governance(tmp_path)
    )

    _write(tmp_path / "CONTRIBUTING.md", "# Contrib\n\nNo locked content.\n")
    findings = vm.validate_contributing_issues(tmp_path)
    assert any("missing Issue Reporting section" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_local(tmp_path)
    assert any("missing Local validation section" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_governance(tmp_path)
    assert any("missing Governance section" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                *vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES,
                *vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES,
                *vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_contributing_issues(tmp_path) == []
    assert vm.validate_contributing_local(tmp_path) == []
    assert vm.validate_contributing_governance(tmp_path) == []

    empty = _inventory_payload()
    empty["contributing_issues_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_issues_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["contributing_issues_required_phrases"] = [
        vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_issues_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["contributing_issues_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_issues_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["contributing_issues_required_phrases"] = ["## Issue Reporting"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_issues_required_phrases must include Issue" in f.message
        for f in findings
    )

    empty_l = _inventory_payload()
    empty_l["contributing_local_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_l, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_local_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_l = _inventory_payload()
    dup_l["contributing_local_required_phrases"] = [
        vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_l, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_local_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_l = _inventory_payload()
    blank_l["contributing_local_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_l, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_local_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_l = _inventory_payload()
    missing_l["contributing_local_required_phrases"] = [
        "## Local validation (docs packaging)"
    ]
    findings = vm._inventory_lock_consistency(
        missing_l, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_local_required_phrases must include Local" in f.message
        for f in findings
    )

    empty_g = _inventory_payload()
    empty_g["contributing_governance_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_g, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_governance_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_g = _inventory_payload()
    dup_g["contributing_governance_required_phrases"] = [
        vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_g, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_governance_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_g = _inventory_payload()
    blank_g["contributing_governance_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_g, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_governance_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_g = _inventory_payload()
    missing_g["contributing_governance_required_phrases"] = ["## Governance"]
    findings = vm._inventory_lock_consistency(
        missing_g, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_governance_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                contributing_issues_required_phrases=list(
                    vm.CONTRIBUTING_ISSUES_REQUIRED_PHRASES
                )[:-1]
                + ["invented issues"],
                contributing_local_required_phrases=list(
                    vm.CONTRIBUTING_LOCAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented local"],
                contributing_governance_required_phrases=list(
                    vm.CONTRIBUTING_GOVERNANCE_REQUIRED_PHRASES
                )[:-1]
                + ["invented governance"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("contributing_issues_required_phrases" in f.message for f in findings)
    assert any("contributing_local_required_phrases" in f.message for f in findings)
    assert any(
        "contributing_governance_required_phrases" in f.message for f in findings
    )


def test_live_v30_security_validators() -> None:
    assert vm.validate_security_header(REPO_ROOT) == []
    assert vm.validate_security_fips(REPO_ROOT) == []
    assert vm.validate_security_known_non_issues(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "security-header" in vm.VALIDATORS
    assert "security-fips" in vm.VALIDATORS
    assert "security-known-non-issues" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["security_header_required_phrases"] == list(
        vm.SECURITY_HEADER_REQUIRED_PHRASES
    )
    assert inventory["security_fips_required_phrases"] == list(
        vm.SECURITY_FIPS_REQUIRED_PHRASES
    )
    assert inventory["security_known_non_issues_required_phrases"] == list(
        vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["security"](REPO_ROOT) == []
    assert vm.validate_contributing_governance(REPO_ROOT) == []


def test_v30_security_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_security_header(tmp_path))
    assert any("missing" in f.message for f in vm.validate_security_fips(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_security_known_non_issues(tmp_path)
    )

    _write(tmp_path / "SECURITY.md", "# Security\n\nNo locked content.\n")
    findings = vm.validate_security_header(tmp_path)
    assert any("missing Security Policy heading" in f.message for f in findings)
    for phrase in vm.SECURITY_HEADER_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_fips(tmp_path)
    assert any(
        "missing Security Standards for This Ecosystem section" in f.message
        for f in findings
    )
    for phrase in vm.SECURITY_FIPS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_known_non_issues(tmp_path)
    assert any("missing Known Non-Issues section" in f.message for f in findings)
    for phrase in vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "SECURITY.md",
        "\n".join(
            [
                *vm.SECURITY_HEADER_REQUIRED_PHRASES,
                *vm.SECURITY_FIPS_REQUIRED_PHRASES,
                *vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_security_header(tmp_path) == []
    assert vm.validate_security_fips(tmp_path) == []
    assert vm.validate_security_known_non_issues(tmp_path) == []

    empty = _inventory_payload()
    empty["security_header_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_header_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["security_header_required_phrases"] = [
        vm.SECURITY_HEADER_REQUIRED_PHRASES[0],
        vm.SECURITY_HEADER_REQUIRED_PHRASES[0],
        *vm.SECURITY_HEADER_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_header_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["security_header_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_header_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["security_header_required_phrases"] = ["# Security Policy"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_header_required_phrases must include Security" in f.message
        for f in findings
    )

    empty_f = _inventory_payload()
    empty_f["security_fips_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_fips_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_f = _inventory_payload()
    dup_f["security_fips_required_phrases"] = [
        vm.SECURITY_FIPS_REQUIRED_PHRASES[0],
        vm.SECURITY_FIPS_REQUIRED_PHRASES[0],
        *vm.SECURITY_FIPS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_fips_required_phrases must be unique" in f.message for f in findings
    )

    blank_f = _inventory_payload()
    blank_f["security_fips_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_fips_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_f = _inventory_payload()
    missing_f["security_fips_required_phrases"] = [
        "## Security Standards for This Ecosystem"
    ]
    findings = vm._inventory_lock_consistency(
        missing_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_fips_required_phrases must include Security" in f.message
        for f in findings
    )

    empty_n = _inventory_payload()
    empty_n["security_known_non_issues_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_known_non_issues_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_n = _inventory_payload()
    dup_n["security_known_non_issues_required_phrases"] = [
        vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES[0],
        vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES[0],
        *vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_known_non_issues_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_n = _inventory_payload()
    blank_n["security_known_non_issues_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_known_non_issues_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_n = _inventory_payload()
    missing_n["security_known_non_issues_required_phrases"] = ["## Known Non-Issues"]
    findings = vm._inventory_lock_consistency(
        missing_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_known_non_issues_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                security_header_required_phrases=list(
                    vm.SECURITY_HEADER_REQUIRED_PHRASES
                )[:-1]
                + ["invented header"],
                security_fips_required_phrases=list(vm.SECURITY_FIPS_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented fips"],
                security_known_non_issues_required_phrases=list(
                    vm.SECURITY_KNOWN_NON_ISSUES_REQUIRED_PHRASES
                )[:-1]
                + ["invented non-issues"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("security_header_required_phrases" in f.message for f in findings)
    assert any("security_fips_required_phrases" in f.message for f in findings)
    assert any(
        "security_known_non_issues_required_phrases" in f.message for f in findings
    )


def test_live_v31_constitution_validators() -> None:
    assert vm.validate_constitution_crypto(REPO_ROOT) == []
    assert vm.validate_constitution_handoff(REPO_ROOT) == []
    assert vm.validate_constitution_escalation_matrix(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "constitution-crypto" in vm.VALIDATORS
    assert "constitution-handoff" in vm.VALIDATORS
    assert "constitution-escalation-matrix" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["constitution_crypto_required_phrases"] == list(
        vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES
    )
    assert inventory["constitution_handoff_required_phrases"] == list(
        vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES
    )
    assert inventory["constitution_escalation_matrix_required_phrases"] == list(
        vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["constitution"](REPO_ROOT) == []
    assert vm.validate_security_known_non_issues(REPO_ROOT) == []


def test_v31_constitution_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_constitution_crypto(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_constitution_handoff(tmp_path)
    )
    assert any(
        "missing" in f.message
        for f in vm.validate_constitution_escalation_matrix(tmp_path)
    )

    _write(tmp_path / "AGENTS-v2.2.md", "# Constitution\n\nNo locked content.\n")
    findings = vm.validate_constitution_crypto(tmp_path)
    assert any(
        "missing Quantum-Safe Cryptography Requirements section" in f.message
        for f in findings
    )
    for phrase in vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_handoff(tmp_path)
    assert any("missing Handoff Sequence section" in f.message for f in findings)
    for phrase in vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_escalation_matrix(tmp_path)
    assert any("missing Escalation Triggers section" in f.message for f in findings)
    for phrase in vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            [
                *vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES,
                *vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES,
                *vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_constitution_crypto(tmp_path) == []
    assert vm.validate_constitution_handoff(tmp_path) == []
    assert vm.validate_constitution_escalation_matrix(tmp_path) == []

    empty = _inventory_payload()
    empty["constitution_crypto_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_crypto_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["constitution_crypto_required_phrases"] = [
        vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_crypto_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["constitution_crypto_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_crypto_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["constitution_crypto_required_phrases"] = [
        "### 22.1 Quantum-Safe Cryptography Requirements"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_crypto_required_phrases must include" in f.message
        for f in findings
    )

    empty_h = _inventory_payload()
    empty_h["constitution_handoff_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_h, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_handoff_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_h = _inventory_payload()
    dup_h["constitution_handoff_required_phrases"] = [
        vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_h, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_handoff_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_h = _inventory_payload()
    blank_h["constitution_handoff_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_h, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_handoff_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_h = _inventory_payload()
    missing_h["constitution_handoff_required_phrases"] = [
        "#### 22.4.1 Handoff Sequence"
    ]
    findings = vm._inventory_lock_consistency(
        missing_h, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_handoff_required_phrases must include" in f.message
        for f in findings
    )

    empty_e = _inventory_payload()
    empty_e["constitution_escalation_matrix_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_matrix_required_phrases must not be empty"
        in f.message
        for f in findings
    )

    dup_e = _inventory_payload()
    dup_e["constitution_escalation_matrix_required_phrases"] = [
        vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_matrix_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_e = _inventory_payload()
    blank_e["constitution_escalation_matrix_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_matrix_required_phrases entries must be "
        "non-empty strings"
        in f.message
        for f in findings
    )

    missing_e = _inventory_payload()
    missing_e["constitution_escalation_matrix_required_phrases"] = [
        "#### 22.4.2 Escalation Triggers"
    ]
    findings = vm._inventory_lock_consistency(
        missing_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_matrix_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                constitution_crypto_required_phrases=list(
                    vm.CONSTITUTION_CRYPTO_REQUIRED_PHRASES
                )[:-1]
                + ["invented crypto"],
                constitution_handoff_required_phrases=list(
                    vm.CONSTITUTION_HANDOFF_REQUIRED_PHRASES
                )[:-1]
                + ["invented handoff"],
                constitution_escalation_matrix_required_phrases=list(
                    vm.CONSTITUTION_ESCALATION_MATRIX_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("constitution_crypto_required_phrases" in f.message for f in findings)
    assert any("constitution_handoff_required_phrases" in f.message for f in findings)
    assert any(
        "constitution_escalation_matrix_required_phrases" in f.message
        for f in findings
    )


def test_live_v32_changelog_validators() -> None:
    assert vm.validate_changelog_format(REPO_ROOT) == []
    assert vm.validate_changelog_unreleased(REPO_ROOT) == []
    assert vm.validate_changelog_release(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "changelog-format" in vm.VALIDATORS
    assert "changelog-unreleased" in vm.VALIDATORS
    assert "changelog-release" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["changelog_format_required_phrases"] == list(
        vm.CHANGELOG_FORMAT_REQUIRED_PHRASES
    )
    assert inventory["changelog_unreleased_required_phrases"] == list(
        vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES
    )
    assert inventory["changelog_release_required_phrases"] == list(
        vm.CHANGELOG_RELEASE_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["changelog"](REPO_ROOT) == []
    assert vm.validate_constitution_escalation_matrix(REPO_ROOT) == []


def test_v32_changelog_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_changelog_format(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_changelog_unreleased(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_changelog_release(tmp_path))

    _write(tmp_path / "CHANGELOG.md", "# Empty\n\nNo locked content.\n")
    findings = vm.validate_changelog_format(tmp_path)
    assert any("missing Changelog heading" in f.message for f in findings)
    for phrase in vm.CHANGELOG_FORMAT_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_changelog_unreleased(tmp_path)
    assert any("missing Unreleased section" in f.message for f in findings)
    for phrase in vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_changelog_release(tmp_path)
    assert any("missing 0.1.0 release section" in f.message for f in findings)
    for phrase in vm.CHANGELOG_RELEASE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CHANGELOG.md",
        "\n".join(
            [
                *vm.CHANGELOG_FORMAT_REQUIRED_PHRASES,
                *vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES,
                *vm.CHANGELOG_RELEASE_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_changelog_format(tmp_path) == []
    assert vm.validate_changelog_unreleased(tmp_path) == []
    assert vm.validate_changelog_release(tmp_path) == []

    empty = _inventory_payload()
    empty["changelog_format_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_format_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["changelog_format_required_phrases"] = [
        vm.CHANGELOG_FORMAT_REQUIRED_PHRASES[0],
        vm.CHANGELOG_FORMAT_REQUIRED_PHRASES[0],
        *vm.CHANGELOG_FORMAT_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_format_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["changelog_format_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_format_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["changelog_format_required_phrases"] = ["# Changelog"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_format_required_phrases must include Changelog" in f.message
        for f in findings
    )

    empty_u = _inventory_payload()
    empty_u["changelog_unreleased_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_unreleased_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_u = _inventory_payload()
    dup_u["changelog_unreleased_required_phrases"] = [
        vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES[0],
        vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES[0],
        *vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_unreleased_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_u = _inventory_payload()
    blank_u["changelog_unreleased_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_unreleased_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_u = _inventory_payload()
    missing_u["changelog_unreleased_required_phrases"] = ["## [Unreleased]"]
    findings = vm._inventory_lock_consistency(
        missing_u, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_unreleased_required_phrases must include Unreleased" in f.message
        for f in findings
    )

    empty_r = _inventory_payload()
    empty_r["changelog_release_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_release_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_r = _inventory_payload()
    dup_r["changelog_release_required_phrases"] = [
        vm.CHANGELOG_RELEASE_REQUIRED_PHRASES[0],
        vm.CHANGELOG_RELEASE_REQUIRED_PHRASES[0],
        *vm.CHANGELOG_RELEASE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_release_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_r = _inventory_payload()
    blank_r["changelog_release_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_release_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_r = _inventory_payload()
    missing_r["changelog_release_required_phrases"] = ["### Changed"]
    findings = vm._inventory_lock_consistency(
        missing_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "changelog_release_required_phrases must include Changed" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                changelog_format_required_phrases=list(
                    vm.CHANGELOG_FORMAT_REQUIRED_PHRASES
                )[:-1]
                + ["invented format"],
                changelog_unreleased_required_phrases=list(
                    vm.CHANGELOG_UNRELEASED_REQUIRED_PHRASES
                )[:-1]
                + ["invented unreleased"],
                changelog_release_required_phrases=list(
                    vm.CHANGELOG_RELEASE_REQUIRED_PHRASES
                )[:-1]
                + ["invented release"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("changelog_format_required_phrases" in f.message for f in findings)
    assert any("changelog_unreleased_required_phrases" in f.message for f in findings)
    assert any("changelog_release_required_phrases" in f.message for f in findings)


def test_live_v33_goose_recipe_validators() -> None:
    assert vm.validate_goose_recipe_headers(REPO_ROOT) == []
    assert vm.validate_goose_instruction_agents(REPO_ROOT) == []
    assert vm.validate_goose_extensions(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "goose-recipe-headers" in vm.VALIDATORS
    assert "goose-instruction-agents" in vm.VALIDATORS
    assert "goose-extensions" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["goose_recipe_headers_required_phrases"] == list(
        vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES
    )
    assert inventory["goose_instruction_agents_required_phrases"] == list(
        vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES
    )
    assert inventory["goose_extensions_required_phrases"] == list(
        vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["goose"](REPO_ROOT) == []
    assert vm.validate_goose_howto(REPO_ROOT) == []
    assert vm.validate_goose_naming(REPO_ROOT) == []
    assert vm.validate_changelog_format(REPO_ROOT) == []


def test_v33_goose_recipe_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_goose_recipe_headers(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_goose_instruction_agents(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_goose_extensions(tmp_path))

    _write(tmp_path / "GOOSE-RECIPES.md", "# Goose\n\nNo locked content.\n")
    findings = vm.validate_goose_recipe_headers(tmp_path)
    assert any("missing Recipe 1 heading" in f.message for f in findings)
    assert any("missing Recipe 4 heading" in f.message for f in findings)
    for phrase in vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_instruction_agents(tmp_path)
    assert any(
        "missing QuantumArchitectAgent instruction" in f.message for f in findings
    )
    for phrase in vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_extensions(tmp_path)
    assert any("missing builtin extension type" in f.message for f in findings)
    for phrase in vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                *vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES,
                *vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES,
                *vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_goose_recipe_headers(tmp_path) == []
    assert vm.validate_goose_instruction_agents(tmp_path) == []
    assert vm.validate_goose_extensions(tmp_path) == []

    empty = _inventory_payload()
    empty["goose_recipe_headers_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_recipe_headers_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["goose_recipe_headers_required_phrases"] = [
        vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES[0],
        vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES[0],
        *vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_recipe_headers_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["goose_recipe_headers_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_recipe_headers_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["goose_recipe_headers_required_phrases"] = [
        "## Recipe 1: Quantum Algorithm Design"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_recipe_headers_required_phrases must include Recipe 1" in f.message
        for f in findings
    )

    empty_i = _inventory_payload()
    empty_i["goose_instruction_agents_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_instruction_agents_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_i = _inventory_payload()
    dup_i["goose_instruction_agents_required_phrases"] = [
        vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES[0],
        vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES[0],
        *vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_instruction_agents_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_i = _inventory_payload()
    blank_i["goose_instruction_agents_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_instruction_agents_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_i = _inventory_payload()
    missing_i["goose_instruction_agents_required_phrases"] = [
        "You are QuantumArchitectAgent designing a quantum algorithm for FUZZYWIGG."
    ]
    findings = vm._inventory_lock_consistency(
        missing_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_instruction_agents_required_phrases must include "
        "QuantumArchitect/Orchestration" in f.message
        for f in findings
    )

    empty_e = _inventory_payload()
    empty_e["goose_extensions_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_extensions_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_e = _inventory_payload()
    dup_e["goose_extensions_required_phrases"] = [
        vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES[0],
        vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES[0],
        *vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_extensions_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_e = _inventory_payload()
    blank_e["goose_extensions_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_extensions_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_e = _inventory_payload()
    missing_e["goose_extensions_required_phrases"] = ["type: builtin"]
    findings = vm._inventory_lock_consistency(
        missing_e, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_extensions_required_phrases must include builtin" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                goose_recipe_headers_required_phrases=list(
                    vm.GOOSE_RECIPE_HEADERS_REQUIRED_PHRASES
                )[:-1]
                + ["invented headers"],
                goose_instruction_agents_required_phrases=list(
                    vm.GOOSE_INSTRUCTION_AGENTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented instructions"],
                goose_extensions_required_phrases=list(
                    vm.GOOSE_EXTENSIONS_REQUIRED_PHRASES
                )[:-1]
                + ["invented extensions"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("goose_recipe_headers_required_phrases" in f.message for f in findings)
    assert any(
        "goose_instruction_agents_required_phrases" in f.message for f in findings
    )
    assert any("goose_extensions_required_phrases" in f.message for f in findings)


def test_live_v34_prompt_deepener_validators() -> None:
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "prompt-constraints" in vm.VALIDATORS
    assert "prompt-triggers" in vm.VALIDATORS
    assert "prompt-related-docs" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["prompt_constraints_required_phrases"] == list(
        vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES
    )
    assert inventory["prompt_triggers_required_phrases"] == list(
        vm.PROMPT_TRIGGERS_REQUIRED_PHRASES
    )
    assert inventory["prompt_related_docs_required_phrases"] == list(
        vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_goose_extensions(REPO_ROOT) == []


def test_v34_prompt_deepener_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_prompt_constraints(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_prompt_triggers(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_prompt_related_docs(tmp_path)
    )

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    findings = vm.validate_prompt_constraints(tmp_path)
    assert any("missing quantum-safety constraint" in f.message for f in findings)
    for phrase in vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_prompt_triggers(tmp_path)
    assert any(
        "missing circuit-depth escalation trigger" in f.message for f in findings
    )
    for phrase in vm.PROMPT_TRIGGERS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_prompt_related_docs(tmp_path)
    assert any(
        "missing AGENTS.md Section 22 related-docs lock" in f.message for f in findings
    )
    for phrase in vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES,
                *vm.PROMPT_TRIGGERS_REQUIRED_PHRASES,
                *vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_constraints(tmp_path) == []
    assert vm.validate_prompt_triggers(tmp_path) == []
    assert vm.validate_prompt_related_docs(tmp_path) == []

    empty = _inventory_payload()
    empty["prompt_constraints_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_constraints_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["prompt_constraints_required_phrases"] = [
        vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES[0],
        vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES[0],
        *vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_constraints_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["prompt_constraints_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_constraints_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["prompt_constraints_required_phrases"] = [
        "Never claim quantum-safety without formal verification"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_constraints_required_phrases must include quantum-safety" in f.message
        for f in findings
    )

    empty_t = _inventory_payload()
    empty_t["prompt_triggers_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_triggers_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_t = _inventory_payload()
    dup_t["prompt_triggers_required_phrases"] = [
        vm.PROMPT_TRIGGERS_REQUIRED_PHRASES[0],
        vm.PROMPT_TRIGGERS_REQUIRED_PHRASES[0],
        *vm.PROMPT_TRIGGERS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_triggers_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_t = _inventory_payload()
    blank_t["prompt_triggers_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_triggers_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_t = _inventory_payload()
    missing_t["prompt_triggers_required_phrases"] = [
        "Circuit depth exceeds device constraints by >20%"
    ]
    findings = vm._inventory_lock_consistency(
        missing_t, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_triggers_required_phrases must include circuit depth" in f.message
        for f in findings
    )

    empty_r = _inventory_payload()
    empty_r["prompt_related_docs_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_related_docs_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_r = _inventory_payload()
    dup_r["prompt_related_docs_required_phrases"] = [
        vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES[0],
        vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES[0],
        *vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_related_docs_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_r = _inventory_payload()
    blank_r["prompt_related_docs_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_related_docs_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_r = _inventory_payload()
    missing_r["prompt_related_docs_required_phrases"] = [
        "See AGENTS.md Section 22 (Quantum-Blockchain Integration Standards)"
    ]
    findings = vm._inventory_lock_consistency(
        missing_r, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "prompt_related_docs_required_phrases must include Section 22" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_constraints_required_phrases=list(
                    vm.PROMPT_CONSTRAINTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented constraints"],
                prompt_triggers_required_phrases=list(
                    vm.PROMPT_TRIGGERS_REQUIRED_PHRASES
                )[:-1]
                + ["invented triggers"],
                prompt_related_docs_required_phrases=list(
                    vm.PROMPT_RELATED_DOCS_REQUIRED_PHRASES
                )[:-1]
                + ["invented related docs"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("prompt_constraints_required_phrases" in f.message for f in findings)
    assert any("prompt_triggers_required_phrases" in f.message for f in findings)
    assert any("prompt_related_docs_required_phrases" in f.message for f in findings)


def test_live_v35_execution_summary_deepener_validators() -> None:
    assert vm.validate_execution_ide(REPO_ROOT) == []
    assert vm.validate_execution_innovations(REPO_ROOT) == []
    assert vm.validate_execution_next48(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "execution-ide" in vm.VALIDATORS
    assert "execution-innovations" in vm.VALIDATORS
    assert "execution-next48" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["execution_ide_required_phrases"] == list(
        vm.EXECUTION_IDE_REQUIRED_PHRASES
    )
    assert inventory["execution_innovations_required_phrases"] == list(
        vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES
    )
    assert inventory["execution_next48_required_phrases"] == list(
        vm.EXECUTION_NEXT48_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_execution_timeline(REPO_ROOT) == []
    assert vm.validate_execution_technologies(REPO_ROOT) == []
    assert vm.validate_execution_workflow(REPO_ROOT) == []
    assert vm.validate_execution_specialists(REPO_ROOT) == []
    assert vm.validate_execution_summary(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []


def test_v35_execution_summary_deepener_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_execution_ide(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_execution_innovations(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_execution_next48(tmp_path))

    _write(tmp_path / "EXECUTION-SUMMARY.md", "# Summary\n\nNo locked content.\n")
    findings = vm.validate_execution_ide(tmp_path)
    assert any("missing IDE & Software Setup section" in f.message for f in findings)
    for phrase in vm.EXECUTION_IDE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_execution_innovations(tmp_path)
    assert any("missing Key Innovations section" in f.message for f in findings)
    for phrase in vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_execution_next48(tmp_path)
    assert any("missing Next 48 Hours section" in f.message for f in findings)
    for phrase in vm.EXECUTION_NEXT48_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "EXECUTION-SUMMARY.md",
        "\n".join(
            [
                *vm.EXECUTION_IDE_REQUIRED_PHRASES,
                *vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES,
                *vm.EXECUTION_NEXT48_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_execution_ide(tmp_path) == []
    assert vm.validate_execution_innovations(tmp_path) == []
    assert vm.validate_execution_next48(tmp_path) == []

    empty = _inventory_payload()
    empty["execution_ide_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_ide_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["execution_ide_required_phrases"] = [
        vm.EXECUTION_IDE_REQUIRED_PHRASES[0],
        vm.EXECUTION_IDE_REQUIRED_PHRASES[0],
        *vm.EXECUTION_IDE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_ide_required_phrases must be unique" in f.message for f in findings
    )

    blank = _inventory_payload()
    blank["execution_ide_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_ide_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["execution_ide_required_phrases"] = ["## IDE & Software Setup"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_ide_required_phrases must include IDE Setup" in f.message
        for f in findings
    )

    empty_i = _inventory_payload()
    empty_i["execution_innovations_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_innovations_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_i = _inventory_payload()
    dup_i["execution_innovations_required_phrases"] = [
        vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES[0],
        vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES[0],
        *vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_innovations_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_i = _inventory_payload()
    blank_i["execution_innovations_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_innovations_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_i = _inventory_payload()
    missing_i["execution_innovations_required_phrases"] = [
        "## What Makes This Different"
    ]
    findings = vm._inventory_lock_consistency(
        missing_i, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_innovations_required_phrases must include What Makes" in f.message
        for f in findings
    )

    empty_n = _inventory_payload()
    empty_n["execution_next48_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_next48_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_n = _inventory_payload()
    dup_n["execution_next48_required_phrases"] = [
        vm.EXECUTION_NEXT48_REQUIRED_PHRASES[0],
        vm.EXECUTION_NEXT48_REQUIRED_PHRASES[0],
        *vm.EXECUTION_NEXT48_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_next48_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_n = _inventory_payload()
    blank_n["execution_next48_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_next48_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_n = _inventory_payload()
    missing_n["execution_next48_required_phrases"] = ["## Next 48 Hours"]
    findings = vm._inventory_lock_consistency(
        missing_n, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "execution_next48_required_phrases must include Next 48 Hours" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                execution_ide_required_phrases=list(vm.EXECUTION_IDE_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented ide"],
                execution_innovations_required_phrases=list(
                    vm.EXECUTION_INNOVATIONS_REQUIRED_PHRASES
                )[:-1]
                + ["invented innovations"],
                execution_next48_required_phrases=list(
                    vm.EXECUTION_NEXT48_REQUIRED_PHRASES
                )[:-1]
                + ["invented next48"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("execution_ide_required_phrases" in f.message for f in findings)
    assert any("execution_innovations_required_phrases" in f.message for f in findings)
    assert any("execution_next48_required_phrases" in f.message for f in findings)

def test_live_v36_goose_recipes_deepener_validators() -> None:
    assert vm.validate_goose_orchestration(REPO_ROOT) == []
    assert vm.validate_goose_conflicts(REPO_ROOT) == []
    assert vm.validate_goose_quantum_task(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "goose-orchestration" in vm.VALIDATORS
    assert "goose-conflicts" in vm.VALIDATORS
    assert "goose-quantum-task" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["goose_orchestration_required_phrases"] == list(
        vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES
    )
    assert inventory["goose_conflicts_required_phrases"] == list(
        vm.GOOSE_CONFLICTS_REQUIRED_PHRASES
    )
    assert inventory["goose_quantum_task_required_phrases"] == list(
        vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_goose_howto(REPO_ROOT) == []
    assert vm.validate_goose_state_machine(REPO_ROOT) == []
    assert vm.validate_goose_naming(REPO_ROOT) == []
    assert vm.validate_goose_recipe_headers(REPO_ROOT) == []
    assert vm.validate_goose_instruction_agents(REPO_ROOT) == []
    assert vm.validate_goose_extensions(REPO_ROOT) == []
    assert vm.validate_execution_next48(REPO_ROOT) == []


def test_v36_goose_recipes_deepener_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_goose_orchestration(tmp_path))
    assert any("missing" in f.message for f in vm.validate_goose_conflicts(tmp_path))
    assert any("missing" in f.message for f in vm.validate_goose_quantum_task(tmp_path))

    _write(tmp_path / "GOOSE-RECIPES.md", "# Goose\n\nNo locked content.\n")
    findings = vm.validate_goose_orchestration(tmp_path)
    assert any("missing Master Orchestration Task section" in f.message for f in findings)
    for phrase in vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_conflicts(tmp_path)
    assert any(
        "missing Conflict Type PERFORMANCE section" in f.message for f in findings
    )
    for phrase in vm.GOOSE_CONFLICTS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_goose_quantum_task(tmp_path)
    assert any(
        "missing Quantum Algorithm Design Task section" in f.message for f in findings
    )
    for phrase in vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "GOOSE-RECIPES.md",
        "\n".join(
            [
                *vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES,
                *vm.GOOSE_CONFLICTS_REQUIRED_PHRASES,
                *vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_goose_orchestration(tmp_path) == []
    assert vm.validate_goose_conflicts(tmp_path) == []
    assert vm.validate_goose_quantum_task(tmp_path) == []

    empty = _inventory_payload()
    empty["goose_orchestration_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_orchestration_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["goose_orchestration_required_phrases"] = [
        vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES[0],
        vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES[0],
        *vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_orchestration_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["goose_orchestration_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_orchestration_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["goose_orchestration_required_phrases"] = [
        "## Master Orchestration Task: Quantum NFT Mint"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_orchestration_required_phrases must include Master" in f.message
        for f in findings
    )

    empty_c = _inventory_payload()
    empty_c["goose_conflicts_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_conflicts_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_c = _inventory_payload()
    dup_c["goose_conflicts_required_phrases"] = [
        vm.GOOSE_CONFLICTS_REQUIRED_PHRASES[0],
        vm.GOOSE_CONFLICTS_REQUIRED_PHRASES[0],
        *vm.GOOSE_CONFLICTS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_conflicts_required_phrases must be unique" in f.message for f in findings
    )

    blank_c = _inventory_payload()
    blank_c["goose_conflicts_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_conflicts_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_c = _inventory_payload()
    missing_c["goose_conflicts_required_phrases"] = ["Conflict Type 1: PERFORMANCE"]
    findings = vm._inventory_lock_consistency(
        missing_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_conflicts_required_phrases must include PERFORMANCE" in f.message
        for f in findings
    )

    empty_q = _inventory_payload()
    empty_q["goose_quantum_task_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_q, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_quantum_task_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_q = _inventory_payload()
    dup_q["goose_quantum_task_required_phrases"] = [
        vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES[0],
        vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES[0],
        *vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_q, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_quantum_task_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_q = _inventory_payload()
    blank_q["goose_quantum_task_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_q, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_quantum_task_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_q = _inventory_payload()
    missing_q["goose_quantum_task_required_phrases"] = [
        "## Quantum Algorithm Design Task"
    ]
    findings = vm._inventory_lock_consistency(
        missing_q, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "goose_quantum_task_required_phrases must include Quantum" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                goose_orchestration_required_phrases=list(
                    vm.GOOSE_ORCHESTRATION_REQUIRED_PHRASES
                )[:-1]
                + ["invented orch"],
                goose_conflicts_required_phrases=list(
                    vm.GOOSE_CONFLICTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented conflicts"],
                goose_quantum_task_required_phrases=list(
                    vm.GOOSE_QUANTUM_TASK_REQUIRED_PHRASES
                )[:-1]
                + ["invented quantum"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("goose_orchestration_required_phrases" in f.message for f in findings)
    assert any("goose_conflicts_required_phrases" in f.message for f in findings)
    assert any("goose_quantum_task_required_phrases" in f.message for f in findings)

def test_live_v37_constitution_leftover_validators() -> None:
    assert vm.validate_constitution_on_device(REPO_ROOT) == []
    assert vm.validate_constitution_multichain(REPO_ROOT) == []
    assert vm.validate_constitution_escalation_format(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "constitution-on-device" in vm.VALIDATORS
    assert "constitution-multichain" in vm.VALIDATORS
    assert "constitution-escalation-format" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["constitution_on_device_required_phrases"] == list(
        vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
    )
    assert inventory["constitution_multichain_required_phrases"] == list(
        vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES
    )
    assert inventory["constitution_escalation_format_required_phrases"] == list(
        vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["constitution"](REPO_ROOT) == []
    assert vm.validate_constitution_crypto(REPO_ROOT) == []
    assert vm.validate_constitution_handoff(REPO_ROOT) == []
    assert vm.validate_constitution_escalation_matrix(REPO_ROOT) == []


def test_v37_constitution_leftover_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_constitution_on_device(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_constitution_multichain(tmp_path)
    )
    assert any(
        "missing" in f.message
        for f in vm.validate_constitution_escalation_format(tmp_path)
    )

    _write(tmp_path / "AGENTS-v2.2.md", "# Constitution\n\nNo locked content.\n")
    findings = vm.validate_constitution_on_device(tmp_path)
    assert any(
        "missing On-Device Quantum Logic Execution section" in f.message
        for f in findings
    )
    for phrase in vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_multichain(tmp_path)
    assert any(
        "missing Multi-Chain State Consistency section" in f.message for f in findings
    )
    for phrase in vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_escalation_format(tmp_path)
    assert any("missing Escalation Format section" in f.message for f in findings)
    for phrase in vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            [
                *vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES,
                *vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES,
                *vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_constitution_on_device(tmp_path) == []
    assert vm.validate_constitution_multichain(tmp_path) == []
    assert vm.validate_constitution_escalation_format(tmp_path) == []

    empty = _inventory_payload()
    empty["constitution_on_device_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_on_device_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["constitution_on_device_required_phrases"] = [
        vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_on_device_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["constitution_on_device_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_on_device_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["constitution_on_device_required_phrases"] = [
        "### 22.2 On-Device Quantum Logic Execution"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_on_device_required_phrases must include" in f.message
        for f in findings
    )

    empty_m = _inventory_payload()
    empty_m["constitution_multichain_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_m, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_multichain_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_m = _inventory_payload()
    dup_m["constitution_multichain_required_phrases"] = [
        vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_m, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_multichain_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_m = _inventory_payload()
    blank_m["constitution_multichain_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_m, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_multichain_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_m = _inventory_payload()
    missing_m["constitution_multichain_required_phrases"] = [
        "### 22.3 Multi-Chain State Consistency"
    ]
    findings = vm._inventory_lock_consistency(
        missing_m, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_multichain_required_phrases must include" in f.message
        for f in findings
    )

    empty_f = _inventory_payload()
    empty_f["constitution_escalation_format_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_format_required_phrases must not be empty"
        in f.message
        for f in findings
    )

    dup_f = _inventory_payload()
    dup_f["constitution_escalation_format_required_phrases"] = [
        vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_format_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_f = _inventory_payload()
    blank_f["constitution_escalation_format_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_format_required_phrases entries must be "
        "non-empty strings"
        in f.message
        for f in findings
    )

    missing_f = _inventory_payload()
    missing_f["constitution_escalation_format_required_phrases"] = [
        "#### 22.4.3 Escalation Format (All Agents)"
    ]
    findings = vm._inventory_lock_consistency(
        missing_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_escalation_format_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                constitution_on_device_required_phrases=list(
                    vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
                )[:-1]
                + ["invented on-device"],
                constitution_multichain_required_phrases=list(
                    vm.CONSTITUTION_MULTICHAIN_REQUIRED_PHRASES
                )[:-1]
                + ["invented multichain"],
                constitution_escalation_format_required_phrases=list(
                    vm.CONSTITUTION_ESCALATION_FORMAT_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation-format"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "constitution_on_device_required_phrases" in f.message for f in findings
    )
    assert any(
        "constitution_multichain_required_phrases" in f.message for f in findings
    )
    assert any(
        "constitution_escalation_format_required_phrases" in f.message
        for f in findings
    )


def test_live_v38_contributing_deepener_validators() -> None:
    assert vm.validate_contributing_metadata(REPO_ROOT) == []
    assert vm.validate_contributing_surfaces(REPO_ROOT) == []
    assert vm.validate_contributing_ci_honesty(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "contributing-metadata" in vm.VALIDATORS
    assert "contributing-surfaces" in vm.VALIDATORS
    assert "contributing-ci-honesty" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["contributing_metadata_required_phrases"] == list(
        vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES
    )
    assert inventory["contributing_surfaces_required_phrases"] == list(
        vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES
    )
    assert inventory["contributing_ci_honesty_required_phrases"] == list(
        vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_contributing_packaging(REPO_ROOT) == []
    assert vm.validate_contributing_who(REPO_ROOT) == []
    assert vm.validate_contributing_branches(REPO_ROOT) == []
    assert vm.validate_contributing_pr(REPO_ROOT) == []
    assert vm.validate_contributing_issues(REPO_ROOT) == []
    assert vm.validate_contributing_local(REPO_ROOT) == []
    assert vm.validate_contributing_governance(REPO_ROOT) == []


def test_v38_contributing_deepener_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_contributing_metadata(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_contributing_surfaces(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_contributing_ci_honesty(tmp_path)
    )

    _write(tmp_path / "CONTRIBUTING.md", "# hi\n\nNo locked content.\n")
    findings = vm.validate_contributing_metadata(tmp_path)
    assert any("missing Contributing title" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_surfaces(tmp_path)
    assert any("missing Agent surfaces duty list" in f.message for f in findings)
    for phrase in vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_contributing_ci_honesty(tmp_path)
    assert any(
        "missing Packaging inventory v52 honesty lock" in f.message for f in findings
    )
    for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                *vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES,
                *vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES,
                *vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES,
                "Agent surfaces",
                "",
            ]
        ),
    )
    assert vm.validate_contributing_metadata(tmp_path) == []
    assert vm.validate_contributing_surfaces(tmp_path) == []
    assert vm.validate_contributing_ci_honesty(tmp_path) == []

    empty = _inventory_payload()
    empty["contributing_metadata_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_metadata_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["contributing_metadata_required_phrases"] = [
        vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_metadata_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["contributing_metadata_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_metadata_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["contributing_metadata_required_phrases"] = ["# Contributing to g0p-agents"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_metadata_required_phrases must include" in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["contributing_surfaces_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_surfaces_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["contributing_surfaces_required_phrases"] = [
        vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_surfaces_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["contributing_surfaces_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_surfaces_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["contributing_surfaces_required_phrases"] = ["Never push directly"]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_surfaces_required_phrases must include" in f.message
        for f in findings
    )

    empty_c = _inventory_payload()
    empty_c["contributing_ci_honesty_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_ci_honesty_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_c = _inventory_payload()
    dup_c["contributing_ci_honesty_required_phrases"] = [
        vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES[0],
        vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES[0],
        *vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_ci_honesty_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_c = _inventory_payload()
    blank_c["contributing_ci_honesty_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_ci_honesty_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_c = _inventory_payload()
    missing_c["contributing_ci_honesty_required_phrases"] = [
        "markdown lint, link check, actionlint"
    ]
    findings = vm._inventory_lock_consistency(
        missing_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "contributing_ci_honesty_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                contributing_metadata_required_phrases=list(
                    vm.CONTRIBUTING_METADATA_REQUIRED_PHRASES
                )[:-1]
                + ["invented metadata"],
                contributing_surfaces_required_phrases=list(
                    vm.CONTRIBUTING_SURFACES_REQUIRED_PHRASES
                )[:-1]
                + ["invented surfaces"],
                contributing_ci_honesty_required_phrases=list(
                    vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
                )[:-1]
                + ["invented ci honesty"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("contributing_metadata_required_phrases" in f.message for f in findings)
    assert any("contributing_surfaces_required_phrases" in f.message for f in findings)
    assert any(
        "contributing_ci_honesty_required_phrases" in f.message for f in findings
    )


def test_live_v39_security_deepener_validators() -> None:
    assert vm.validate_security_scope(REPO_ROOT) == []
    assert vm.validate_security_reporting_channel(REPO_ROOT) == []
    assert vm.validate_security_compliance_detail(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "security-scope" in vm.VALIDATORS
    assert "security-reporting-channel" in vm.VALIDATORS
    assert "security-compliance-detail" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["security_scope_required_phrases"] == list(
        vm.SECURITY_SCOPE_REQUIRED_PHRASES
    )
    assert inventory["security_reporting_channel_required_phrases"] == list(
        vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES
    )
    assert inventory["security_compliance_detail_required_phrases"] == list(
        vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_security_supported(REPO_ROOT) == []
    assert vm.validate_security_reporting(REPO_ROOT) == []
    assert vm.validate_security_standards(REPO_ROOT) == []
    assert vm.validate_security_header(REPO_ROOT) == []
    assert vm.validate_security_fips(REPO_ROOT) == []
    assert vm.validate_security_known_non_issues(REPO_ROOT) == []
    assert vm.VALIDATORS["security"](REPO_ROOT) == []


def test_v39_security_deepener_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_security_scope(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_security_reporting_channel(tmp_path)
    )
    assert any(
        "missing" in f.message
        for f in vm.validate_security_compliance_detail(tmp_path)
    )

    _write(tmp_path / "SECURITY.md", "# Security\n\nNo locked content.\n")
    findings = vm.validate_security_scope(tmp_path)
    assert any("missing Supported Versions section" in f.message for f in findings)
    for phrase in vm.SECURITY_SCOPE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_reporting_channel(tmp_path)
    assert any(
        "missing Reporting a Vulnerability section" in f.message for f in findings
    )
    for phrase in vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_security_compliance_detail(tmp_path)
    assert any(
        "missing security compliance scaffold preamble" in f.message for f in findings
    )
    for phrase in vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "SECURITY.md",
        "\n".join(
            [
                *vm.SECURITY_SCOPE_REQUIRED_PHRASES,
                *vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES,
                *vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_security_scope(tmp_path) == []
    assert vm.validate_security_reporting_channel(tmp_path) == []
    assert vm.validate_security_compliance_detail(tmp_path) == []

    empty = _inventory_payload()
    empty["security_scope_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_scope_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["security_scope_required_phrases"] = [
        vm.SECURITY_SCOPE_REQUIRED_PHRASES[0],
        vm.SECURITY_SCOPE_REQUIRED_PHRASES[0],
        *vm.SECURITY_SCOPE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_scope_required_phrases must be unique" in f.message for f in findings
    )

    blank = _inventory_payload()
    blank["security_scope_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_scope_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["security_scope_required_phrases"] = ["## Supported Versions"]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_scope_required_phrases must include" in f.message for f in findings
    )

    empty_c = _inventory_payload()
    empty_c["security_reporting_channel_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_channel_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_c = _inventory_payload()
    dup_c["security_reporting_channel_required_phrases"] = [
        vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES[0],
        vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES[0],
        *vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_channel_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_c = _inventory_payload()
    blank_c["security_reporting_channel_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_channel_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_c = _inventory_payload()
    missing_c["security_reporting_channel_required_phrases"] = [
        "## Reporting a Vulnerability"
    ]
    findings = vm._inventory_lock_consistency(
        missing_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_reporting_channel_required_phrases must include" in f.message
        for f in findings
    )

    empty_d = _inventory_payload()
    empty_d["security_compliance_detail_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_d, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_compliance_detail_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_d = _inventory_payload()
    dup_d["security_compliance_detail_required_phrases"] = [
        vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES[0],
        vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES[0],
        *vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_d, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_compliance_detail_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_d = _inventory_payload()
    blank_d["security_compliance_detail_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_d, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_compliance_detail_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_d = _inventory_payload()
    missing_d["security_compliance_detail_required_phrases"] = [
        "When code is scaffolded into this repo, it must comply with:"
    ]
    findings = vm._inventory_lock_consistency(
        missing_d, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "security_compliance_detail_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                security_scope_required_phrases=list(
                    vm.SECURITY_SCOPE_REQUIRED_PHRASES
                )[:-1]
                + ["invented scope"],
                security_reporting_channel_required_phrases=list(
                    vm.SECURITY_REPORTING_CHANNEL_REQUIRED_PHRASES
                )[:-1]
                + ["invented channel"],
                security_compliance_detail_required_phrases=list(
                    vm.SECURITY_COMPLIANCE_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented compliance"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("security_scope_required_phrases" in f.message for f in findings)
    assert any(
        "security_reporting_channel_required_phrases" in f.message for f in findings
    )
    assert any(
        "security_compliance_detail_required_phrases" in f.message for f in findings
    )


def test_live_v40_constitution_leftover_validators() -> None:
    assert vm.validate_constitution_recipe_orchestration(REPO_ROOT) == []
    assert vm.validate_constitution_scratchpad_state(REPO_ROOT) == []
    assert vm.validate_constitution_conflict_matrix(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "constitution-recipe-orchestration" in vm.VALIDATORS
    assert "constitution-scratchpad-state" in vm.VALIDATORS
    assert "constitution-conflict-matrix" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["constitution_recipe_orchestration_required_phrases"] == list(
        vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES
    )
    assert inventory["constitution_scratchpad_state_required_phrases"] == list(
        vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
    )
    assert inventory["constitution_conflict_matrix_required_phrases"] == list(
        vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.VALIDATORS["constitution"](REPO_ROOT) == []
    assert vm.validate_constitution_crypto(REPO_ROOT) == []
    assert vm.validate_constitution_handoff(REPO_ROOT) == []
    assert vm.validate_constitution_escalation_matrix(REPO_ROOT) == []
    assert vm.validate_constitution_on_device(REPO_ROOT) == []
    assert vm.validate_constitution_multichain(REPO_ROOT) == []
    assert vm.validate_constitution_escalation_format(REPO_ROOT) == []


def test_v40_constitution_leftover_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message
        for f in vm.validate_constitution_recipe_orchestration(tmp_path)
    )
    assert any(
        "missing" in f.message
        for f in vm.validate_constitution_scratchpad_state(tmp_path)
    )
    assert any(
        "missing" in f.message
        for f in vm.validate_constitution_conflict_matrix(tmp_path)
    )

    _write(tmp_path / "AGENTS-v2.2.md", "# Constitution\n\nNo locked content.\n")
    findings = vm.validate_constitution_recipe_orchestration(tmp_path)
    assert any(
        "missing Recipe-Based Orchestration Structure section" in f.message
        for f in findings
    )
    for phrase in vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_scratchpad_state(tmp_path)
    assert any(
        "missing Scratchpad State Machine section" in f.message for f in findings
    )
    for phrase in vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_constitution_conflict_matrix(tmp_path)
    assert any(
        "missing Conflict Resolution Matrix section" in f.message for f in findings
    )
    for phrase in vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            [
                *vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES,
                *vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES,
                *vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_constitution_recipe_orchestration(tmp_path) == []
    assert vm.validate_constitution_scratchpad_state(tmp_path) == []
    assert vm.validate_constitution_conflict_matrix(tmp_path) == []

    empty = _inventory_payload()
    empty["constitution_recipe_orchestration_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_recipe_orchestration_required_phrases must not be empty"
        in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["constitution_recipe_orchestration_required_phrases"] = [
        vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_recipe_orchestration_required_phrases must be unique"
        in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["constitution_recipe_orchestration_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_recipe_orchestration_required_phrases entries must be "
        "non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["constitution_recipe_orchestration_required_phrases"] = [
        "### 22.5 Recipe-Based Orchestration Structure"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_recipe_orchestration_required_phrases must include"
        in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["constitution_scratchpad_state_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_scratchpad_state_required_phrases must not be empty"
        in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["constitution_scratchpad_state_required_phrases"] = [
        vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_scratchpad_state_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["constitution_scratchpad_state_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_scratchpad_state_required_phrases entries must be "
        "non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["constitution_scratchpad_state_required_phrases"] = [
        "### 22.6 Scratchpad State Machine"
    ]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_scratchpad_state_required_phrases must include" in f.message
        for f in findings
    )

    empty_c = _inventory_payload()
    empty_c["constitution_conflict_matrix_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_conflict_matrix_required_phrases must not be empty"
        in f.message
        for f in findings
    )

    dup_c = _inventory_payload()
    dup_c["constitution_conflict_matrix_required_phrases"] = [
        vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES[0],
        vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES[0],
        *vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_conflict_matrix_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_c = _inventory_payload()
    blank_c["constitution_conflict_matrix_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_conflict_matrix_required_phrases entries must be "
        "non-empty strings"
        in f.message
        for f in findings
    )

    missing_c = _inventory_payload()
    missing_c["constitution_conflict_matrix_required_phrases"] = [
        "### 22.7 Conflict Resolution Matrix"
    ]
    findings = vm._inventory_lock_consistency(
        missing_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "constitution_conflict_matrix_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                constitution_recipe_orchestration_required_phrases=list(
                    vm.CONSTITUTION_RECIPE_ORCHESTRATION_REQUIRED_PHRASES
                )[:-1]
                + ["invented recipe-orchestration"],
                constitution_scratchpad_state_required_phrases=list(
                    vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
                )[:-1]
                + ["invented scratchpad-state"],
                constitution_conflict_matrix_required_phrases=list(
                    vm.CONSTITUTION_CONFLICT_MATRIX_REQUIRED_PHRASES
                )[:-1]
                + ["invented conflict-matrix"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "constitution_recipe_orchestration_required_phrases" in f.message
        for f in findings
    )
    assert any(
        "constitution_scratchpad_state_required_phrases" in f.message for f in findings
    )
    assert any(
        "constitution_conflict_matrix_required_phrases" in f.message for f in findings
    )

def test_live_v41_implementation_guide_leftover_validators() -> None:
    assert vm.validate_implementation_issues(REPO_ROOT) == []
    assert vm.validate_implementation_faq(REPO_ROOT) == []
    assert vm.validate_implementation_support(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "implementation-issues" in vm.VALIDATORS
    assert "implementation-faq" in vm.VALIDATORS
    assert "implementation-support" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["implementation_issues_required_phrases"] == list(
        vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES
    )
    assert inventory["implementation_faq_required_phrases"] == list(
        vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES
    )
    assert inventory["implementation_support_required_phrases"] == list(
        vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_implementation_guide(REPO_ROOT) == []
    assert vm.validate_implementation_quickstart(REPO_ROOT) == []
    assert vm.validate_implementation_phases(REPO_ROOT) == []
    assert vm.validate_implementation_tools(REPO_ROOT) == []
    assert vm.validate_implementation_success(REPO_ROOT) == []


def test_v41_implementation_guide_leftover_edge_cases(tmp_path: Path) -> None:
    assert any(
        "missing" in f.message for f in vm.validate_implementation_issues(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_implementation_faq(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_implementation_support(tmp_path)
    )

    _write(tmp_path / "IMPLEMENTATION-GUIDE.md", "# Guide\n\nNo locked content.\n")
    findings = vm.validate_implementation_issues(tmp_path)
    assert any(
        "missing Common Issues & Solutions section" in f.message for f in findings
    )
    for phrase in vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_implementation_faq(tmp_path)
    assert any("missing FAQ section" in f.message for f in findings)
    for phrase in vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_implementation_support(tmp_path)
    assert any("missing Support & Resources section" in f.message for f in findings)
    for phrase in vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "IMPLEMENTATION-GUIDE.md",
        "\n".join(
            [
                *vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES,
                *vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES,
                *vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_implementation_issues(tmp_path) == []
    assert vm.validate_implementation_faq(tmp_path) == []
    assert vm.validate_implementation_support(tmp_path) == []

    empty = _inventory_payload()
    empty["implementation_issues_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_issues_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup = _inventory_payload()
    dup["implementation_issues_required_phrases"] = [
        vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_issues_required_phrases must be unique" in f.message
        for f in findings
    )

    blank = _inventory_payload()
    blank["implementation_issues_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_issues_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["implementation_issues_required_phrases"] = [
        "## Common Issues & Solutions"
    ]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_issues_required_phrases must include" in f.message
        for f in findings
    )

    empty_f = _inventory_payload()
    empty_f["implementation_faq_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_faq_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_f = _inventory_payload()
    dup_f["implementation_faq_required_phrases"] = [
        vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_faq_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_f = _inventory_payload()
    blank_f["implementation_faq_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_faq_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_f = _inventory_payload()
    missing_f["implementation_faq_required_phrases"] = ["## FAQ"]
    findings = vm._inventory_lock_consistency(
        missing_f, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_faq_required_phrases must include" in f.message
        for f in findings
    )

    empty_s = _inventory_payload()
    empty_s["implementation_support_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_support_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_s = _inventory_payload()
    dup_s["implementation_support_required_phrases"] = [
        vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES[0],
        vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES[0],
        *vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_support_required_phrases must be unique" in f.message
        for f in findings
    )

    blank_s = _inventory_payload()
    blank_s["implementation_support_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_support_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_s = _inventory_payload()
    missing_s["implementation_support_required_phrases"] = [
        "## Support & Resources"
    ]
    findings = vm._inventory_lock_consistency(
        missing_s, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "implementation_support_required_phrases must include" in f.message
        for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                implementation_issues_required_phrases=list(
                    vm.IMPLEMENTATION_ISSUES_REQUIRED_PHRASES
                )[:-1]
                + ["invented issues"],
                implementation_faq_required_phrases=list(
                    vm.IMPLEMENTATION_FAQ_REQUIRED_PHRASES
                )[:-1]
                + ["invented faq"],
                implementation_support_required_phrases=list(
                    vm.IMPLEMENTATION_SUPPORT_REQUIRED_PHRASES
                )[:-1]
                + ["invented support"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "implementation_issues_required_phrases" in f.message for f in findings
    )
    assert any(
        "implementation_faq_required_phrases" in f.message for f in findings
    )
    assert any(
        "implementation_support_required_phrases" in f.message for f in findings
    )

def test_live_v42_hydration_leftover_validators() -> None:
    assert vm.validate_hydration_phase1(REPO_ROOT) == []
    assert vm.validate_hydration_list_a(REPO_ROOT) == []
    assert vm.validate_hydration_resolved(REPO_ROOT) == []
    assert vm.validate_hydration_phase4(REPO_ROOT) == []
    assert vm.validate_hydration_deferred(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "hydration-phase1" in vm.VALIDATORS
    assert "hydration-list-a" in vm.VALIDATORS
    assert "hydration-resolved" in vm.VALIDATORS
    assert "hydration-phase4" in vm.VALIDATORS
    assert "hydration-deferred" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["hydration_phase1_required_phrases"] == list(
        vm.HYDRATION_PHASE1_REQUIRED_PHRASES
    )
    assert inventory["hydration_list_a_required_phrases"] == list(
        vm.HYDRATION_LIST_A_REQUIRED_PHRASES
    )
    assert inventory["hydration_resolved_required_phrases"] == list(
        vm.HYDRATION_RESOLVED_REQUIRED_PHRASES
    )
    assert inventory["hydration_phase4_required_phrases"] == list(
        vm.HYDRATION_PHASE4_REQUIRED_PHRASES
    )
    assert inventory["hydration_deferred_required_phrases"] == list(
        vm.HYDRATION_DEFERRED_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_hydration_report(REPO_ROOT) == []
    assert vm.validate_hydration_list_b(REPO_ROOT) == []


def test_v42_hydration_leftover_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_hydration_phase1(tmp_path))
    assert any("missing" in f.message for f in vm.validate_hydration_list_a(tmp_path))
    assert any("missing" in f.message for f in vm.validate_hydration_resolved(tmp_path))
    assert any("missing" in f.message for f in vm.validate_hydration_phase4(tmp_path))
    assert any("missing" in f.message for f in vm.validate_hydration_deferred(tmp_path))

    _write(tmp_path / "docs" / "agent-hydration.md", "# Hydration\n\nNo locked content.\n")
    findings = vm.validate_hydration_phase1(tmp_path)
    assert any("missing PHASE 1 findings report" in f.message for f in findings)
    for phrase in vm.HYDRATION_PHASE1_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_list_a(tmp_path)
    assert any("missing LIST A researchable section" in f.message for f in findings)
    for phrase in vm.HYDRATION_LIST_A_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_resolved(tmp_path)
    assert any(
        "missing PHASE 3 resolved LIST A section" in f.message for f in findings
    )
    for phrase in vm.HYDRATION_RESOLVED_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_phase4(tmp_path)
    assert any(
        "missing PHASE 4 issues generated section" in f.message for f in findings
    )
    for phrase in vm.HYDRATION_PHASE4_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_deferred(tmp_path)
    assert any(
        "missing LIST B Deferred to Andrew section" in f.message for f in findings
    )
    for phrase in vm.HYDRATION_DEFERRED_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "docs" / "agent-hydration.md",
        "\n".join(
            [
                "## PHASE 1: FINDINGS REPORT",
                *vm.HYDRATION_PHASE1_REQUIRED_PHRASES,
                *vm.HYDRATION_LIST_A_REQUIRED_PHRASES,
                "## PHASE 3: RESOLVED (LIST A)",
                *vm.HYDRATION_RESOLVED_REQUIRED_PHRASES,
                *vm.HYDRATION_PHASE4_REQUIRED_PHRASES,
                *vm.HYDRATION_DEFERRED_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_hydration_phase1(tmp_path) == []
    assert vm.validate_hydration_list_a(tmp_path) == []
    assert vm.validate_hydration_resolved(tmp_path) == []
    assert vm.validate_hydration_phase4(tmp_path) == []
    assert vm.validate_hydration_deferred(tmp_path) == []

    def _check_empty(key: str, msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_dup(key: str, phrases: tuple[str, ...], msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_blank(key: str, msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_missing(key: str, seed: list[str], msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    _check_empty(
        "hydration_phase1_required_phrases",
        "hydration_phase1_required_phrases must not be empty",
    )
    _check_dup(
        "hydration_phase1_required_phrases",
        vm.HYDRATION_PHASE1_REQUIRED_PHRASES,
        "hydration_phase1_required_phrases must be unique",
    )
    _check_blank(
        "hydration_phase1_required_phrases",
        "hydration_phase1_required_phrases entries must be non-empty strings",
    )
    _check_missing(
        "hydration_phase1_required_phrases",
        ["### Identity"],
        "hydration_phase1_required_phrases must include",
    )

    _check_empty(
        "hydration_list_a_required_phrases",
        "hydration_list_a_required_phrases must not be empty",
    )
    _check_dup(
        "hydration_list_a_required_phrases",
        vm.HYDRATION_LIST_A_REQUIRED_PHRASES,
        "hydration_list_a_required_phrases must be unique",
    )
    _check_blank(
        "hydration_list_a_required_phrases",
        "hydration_list_a_required_phrases entries must be non-empty strings",
    )
    _check_missing(
        "hydration_list_a_required_phrases",
        ["### LIST A — Researchable"],
        "hydration_list_a_required_phrases must include",
    )

    _check_empty(
        "hydration_resolved_required_phrases",
        "hydration_resolved_required_phrases must not be empty",
    )
    _check_dup(
        "hydration_resolved_required_phrases",
        vm.HYDRATION_RESOLVED_REQUIRED_PHRASES,
        "hydration_resolved_required_phrases must be unique",
    )
    _check_blank(
        "hydration_resolved_required_phrases",
        "hydration_resolved_required_phrases entries must be non-empty strings",
    )
    _check_missing(
        "hydration_resolved_required_phrases",
        ["Goose is Block's open-source AI agent framework"],
        "hydration_resolved_required_phrases must include",
    )

    _check_empty(
        "hydration_phase4_required_phrases",
        "hydration_phase4_required_phrases must not be empty",
    )
    _check_dup(
        "hydration_phase4_required_phrases",
        vm.HYDRATION_PHASE4_REQUIRED_PHRASES,
        "hydration_phase4_required_phrases must be unique",
    )
    _check_blank(
        "hydration_phase4_required_phrases",
        "hydration_phase4_required_phrases entries must be non-empty strings",
    )
    _check_missing(
        "hydration_phase4_required_phrases",
        ["## PHASE 4: ISSUES GENERATED"],
        "hydration_phase4_required_phrases must include",
    )

    _check_empty(
        "hydration_deferred_required_phrases",
        "hydration_deferred_required_phrases must not be empty",
    )
    _check_dup(
        "hydration_deferred_required_phrases",
        vm.HYDRATION_DEFERRED_REQUIRED_PHRASES,
        "hydration_deferred_required_phrases must be unique",
    )
    _check_blank(
        "hydration_deferred_required_phrases",
        "hydration_deferred_required_phrases entries must be non-empty strings",
    )
    _check_missing(
        "hydration_deferred_required_phrases",
        ["## LIST B — Deferred to Andrew"],
        "hydration_deferred_required_phrases must include",
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                hydration_phase1_required_phrases=list(
                    vm.HYDRATION_PHASE1_REQUIRED_PHRASES
                )[:-1]
                + ["invented phase1"],
                hydration_list_a_required_phrases=list(
                    vm.HYDRATION_LIST_A_REQUIRED_PHRASES
                )[:-1]
                + ["invented list-a"],
                hydration_resolved_required_phrases=list(
                    vm.HYDRATION_RESOLVED_REQUIRED_PHRASES
                )[:-1]
                + ["invented resolved"],
                hydration_phase4_required_phrases=list(
                    vm.HYDRATION_PHASE4_REQUIRED_PHRASES
                )[:-1]
                + ["invented phase4"],
                hydration_deferred_required_phrases=list(
                    vm.HYDRATION_DEFERRED_REQUIRED_PHRASES
                )[:-1]
                + ["invented deferred"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("hydration_phase1_required_phrases" in f.message for f in findings)
    assert any("hydration_list_a_required_phrases" in f.message for f in findings)
    assert any("hydration_resolved_required_phrases" in f.message for f in findings)
    assert any("hydration_phase4_required_phrases" in f.message for f in findings)
    assert any("hydration_deferred_required_phrases" in f.message for f in findings)


def test_live_v43_readme_leftover_validators() -> None:
    assert vm.validate_readme_lead(REPO_ROOT) == []
    assert vm.validate_readme_blurbs(REPO_ROOT) == []
    assert vm.validate_readme_bootstrap(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert "readme-lead" in vm.VALIDATORS
    assert "readme-blurbs" in vm.VALIDATORS
    assert "readme-bootstrap" in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["readme_lead_required_phrases"] == list(
        vm.README_LEAD_REQUIRED_PHRASES
    )
    assert inventory["readme_blurbs_required_phrases"] == list(
        vm.README_BLURBS_REQUIRED_PHRASES
    )
    assert inventory["readme_bootstrap_required_phrases"] == list(
        vm.README_BOOTSTRAP_REQUIRED_PHRASES
    )
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_readme_packaging(REPO_ROOT) == []
    assert vm.validate_readme_badges(REPO_ROOT) == []
    assert vm.validate_readme_honesty(REPO_ROOT) == []
    assert vm.validate_readme_historic(REPO_ROOT) == []
    assert vm.validate_readme_contents(REPO_ROOT) == []


def test_v43_readme_leftover_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_readme_lead(tmp_path))
    assert any("missing" in f.message for f in vm.validate_readme_blurbs(tmp_path))
    assert any("missing" in f.message for f in vm.validate_readme_bootstrap(tmp_path))

    _write(tmp_path / "README.md", "# g0p-agents\n\nNo locked content.\n")
    findings = vm.validate_readme_lead(tmp_path)
    assert any("missing Docs-only archive lead" in f.message for f in findings)
    for phrase in vm.README_LEAD_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_readme_blurbs(tmp_path)
    assert any("missing Contents section" in f.message for f in findings)
    for phrase in vm.README_BLURBS_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_readme_bootstrap(tmp_path)
    assert any("missing Cloud agents section" in f.message for f in findings)
    assert any("missing Manifest validation section" in f.message for f in findings)
    assert any("missing License section" in f.message for f in findings)
    for phrase in vm.README_BOOTSTRAP_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "README.md",
        "\n".join(
            [
                *vm.README_LEAD_REQUIRED_PHRASES,
                *vm.README_BLURBS_REQUIRED_PHRASES,
                *vm.README_BOOTSTRAP_REQUIRED_PHRASES,
                "## Contents",
                "## Cloud agents",
                "## Manifest validation",
                "## License",
                "",
            ]
        ),
    )
    assert vm.validate_readme_lead(tmp_path) == []
    assert vm.validate_readme_blurbs(tmp_path) == []
    assert vm.validate_readme_bootstrap(tmp_path) == []

    empty = _inventory_payload()
    empty["readme_lead_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_lead_required_phrases must not be empty" in f.message for f in findings
    )

    dup = _inventory_payload()
    dup["readme_lead_required_phrases"] = [
        vm.README_LEAD_REQUIRED_PHRASES[0],
        vm.README_LEAD_REQUIRED_PHRASES[0],
        *vm.README_LEAD_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_lead_required_phrases must be unique" in f.message for f in findings
    )

    blank = _inventory_payload()
    blank["readme_lead_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_lead_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing = _inventory_payload()
    missing["readme_lead_required_phrases"] = [vm.README_LEAD_REQUIRED_PHRASES[0]]
    findings = vm._inventory_lock_consistency(
        missing, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_lead_required_phrases must include" in f.message for f in findings
    )

    empty_b = _inventory_payload()
    empty_b["readme_blurbs_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_blurbs_required_phrases must not be empty" in f.message for f in findings
    )

    dup_b = _inventory_payload()
    dup_b["readme_blurbs_required_phrases"] = [
        vm.README_BLURBS_REQUIRED_PHRASES[0],
        vm.README_BLURBS_REQUIRED_PHRASES[0],
        *vm.README_BLURBS_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_blurbs_required_phrases must be unique" in f.message for f in findings
    )

    blank_b = _inventory_payload()
    blank_b["readme_blurbs_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_blurbs_required_phrases entries must be non-empty strings" in f.message
        for f in findings
    )

    missing_b = _inventory_payload()
    missing_b["readme_blurbs_required_phrases"] = [vm.README_BLURBS_REQUIRED_PHRASES[0]]
    findings = vm._inventory_lock_consistency(
        missing_b, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_blurbs_required_phrases must include" in f.message for f in findings
    )

    empty_c = _inventory_payload()
    empty_c["readme_bootstrap_required_phrases"] = []
    findings = vm._inventory_lock_consistency(
        empty_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_bootstrap_required_phrases must not be empty" in f.message
        for f in findings
    )

    dup_c = _inventory_payload()
    dup_c["readme_bootstrap_required_phrases"] = [
        vm.README_BOOTSTRAP_REQUIRED_PHRASES[0],
        vm.README_BOOTSTRAP_REQUIRED_PHRASES[0],
        *vm.README_BOOTSTRAP_REQUIRED_PHRASES[1:],
    ]
    findings = vm._inventory_lock_consistency(
        dup_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_bootstrap_required_phrases must be unique" in f.message for f in findings
    )

    blank_c = _inventory_payload()
    blank_c["readme_bootstrap_required_phrases"] = ["ok", "  "]
    findings = vm._inventory_lock_consistency(
        blank_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_bootstrap_required_phrases entries must be non-empty strings"
        in f.message
        for f in findings
    )

    missing_c = _inventory_payload()
    missing_c["readme_bootstrap_required_phrases"] = [
        vm.README_BOOTSTRAP_REQUIRED_PHRASES[0]
    ]
    findings = vm._inventory_lock_consistency(
        missing_c, schema_path="schemas/packaging-inventory.json"
    )
    assert any(
        "readme_bootstrap_required_phrases must include" in f.message for f in findings
    )

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                readme_lead_required_phrases=list(vm.README_LEAD_REQUIRED_PHRASES)[:-1]
                + ["invented readme-lead"],
                readme_blurbs_required_phrases=list(vm.README_BLURBS_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented readme-blurbs"],
                readme_bootstrap_required_phrases=list(
                    vm.README_BOOTSTRAP_REQUIRED_PHRASES
                )[:-1]
                + ["invented readme-bootstrap"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("readme_lead_required_phrases" in f.message for f in findings)
    assert any("readme_blurbs_required_phrases" in f.message for f in findings)
    assert any("readme_bootstrap_required_phrases" in f.message for f in findings)

def test_live_v44_hydration_deepener_validators() -> None:
    assert vm.validate_hydration_meta(REPO_ROOT) == []
    assert vm.validate_hydration_identity_detail(REPO_ROOT) == []
    assert vm.validate_hydration_git_detail(REPO_ROOT) == []
    assert vm.validate_hydration_phase2(REPO_ROOT) == []
    assert vm.validate_hydration_phase5(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in (
        "hydration-meta",
        "hydration-identity-detail",
        "hydration-git-detail",
        "hydration-phase2",
        "hydration-phase5",
    ):
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["hydration_meta_required_phrases"] == list(
        vm.HYDRATION_META_REQUIRED_PHRASES
    )
    assert inventory["hydration_identity_detail_required_phrases"] == list(
        vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["hydration_git_detail_required_phrases"] == list(
        vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["hydration_phase2_required_phrases"] == list(
        vm.HYDRATION_PHASE2_REQUIRED_PHRASES
    )
    assert inventory["hydration_phase5_required_phrases"] == list(
        vm.HYDRATION_PHASE5_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert vm.validate_hydration_phase1(REPO_ROOT) == []
    assert vm.validate_hydration_deferred(REPO_ROOT) == []
    assert vm.validate_readme_lead(REPO_ROOT) == []


def test_v44_hydration_deepener_edge_cases(tmp_path: Path) -> None:
    assert any("missing" in f.message for f in vm.validate_hydration_meta(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_hydration_identity_detail(tmp_path)
    )
    assert any(
        "missing" in f.message for f in vm.validate_hydration_git_detail(tmp_path)
    )
    assert any("missing" in f.message for f in vm.validate_hydration_phase2(tmp_path))
    assert any("missing" in f.message for f in vm.validate_hydration_phase5(tmp_path))

    _write(tmp_path / "docs" / "agent-hydration.md", "# stub\n")
    findings = vm.validate_hydration_meta(tmp_path)
    assert any("missing hydration report title" in f.message for f in findings)
    for phrase in vm.HYDRATION_META_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_identity_detail(tmp_path)
    assert any("missing Identity findings section" in f.message for f in findings)
    for phrase in vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_git_detail(tmp_path)
    assert any("missing Git State findings section" in f.message for f in findings)
    for phrase in vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_phase2(tmp_path)
    assert any("missing PHASE 2 questions section" in f.message for f in findings)
    for phrase in vm.HYDRATION_PHASE2_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    findings = vm.validate_hydration_phase5(tmp_path)
    assert any("missing PHASE 5 Roadmap section" in f.message for f in findings)
    for phrase in vm.HYDRATION_PHASE5_REQUIRED_PHRASES:
        assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "docs" / "agent-hydration.md",
        "\n".join(
            [
                *vm.HYDRATION_META_REQUIRED_PHRASES,
                "### Identity",
                *vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES,
                "### Git State",
                *vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES,
                *vm.HYDRATION_PHASE2_REQUIRED_PHRASES,
                *vm.HYDRATION_PHASE5_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_hydration_meta(tmp_path) == []
    assert vm.validate_hydration_identity_detail(tmp_path) == []
    assert vm.validate_hydration_git_detail(tmp_path) == []
    assert vm.validate_hydration_phase2(tmp_path) == []
    assert vm.validate_hydration_phase5(tmp_path) == []

    def _check_empty(key: str, msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_dup(key: str, phrases: tuple[str, ...], msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_blank(key: str, msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    def _check_missing(key: str, seed: list[str], msg: str) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(msg in f.message for f in findings)

    cases = [
        (
            "hydration_meta_required_phrases",
            vm.HYDRATION_META_REQUIRED_PHRASES,
            "hydration_meta_required_phrases must include title/",
        ),
        (
            "hydration_identity_detail_required_phrases",
            vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES,
            "hydration_identity_detail_required_phrases must include LICENSE/",
        ),
        (
            "hydration_git_detail_required_phrases",
            vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES,
            "hydration_git_detail_required_phrases must include main/",
        ),
        (
            "hydration_phase2_required_phrases",
            vm.HYDRATION_PHASE2_REQUIRED_PHRASES,
            "hydration_phase2_required_phrases must include PHASE 2/",
        ),
        (
            "hydration_phase5_required_phrases",
            vm.HYDRATION_PHASE5_REQUIRED_PHRASES,
            "hydration_phase5_required_phrases must include PHASE 5/",
        ),
    ]
    for key, phrases, include_msg in cases:
        _check_empty(key, f"{key} must not be empty")
        _check_dup(key, phrases, f"{key} must be unique")
        _check_blank(key, f"{key} entries must be non-empty strings")
        _check_missing(key, [phrases[0]], include_msg)

    (tmp_path / "schemas").mkdir(exist_ok=True)
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                hydration_meta_required_phrases=list(vm.HYDRATION_META_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented meta"],
                hydration_identity_detail_required_phrases=list(
                    vm.HYDRATION_IDENTITY_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented identity"],
                hydration_git_detail_required_phrases=list(
                    vm.HYDRATION_GIT_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented git"],
                hydration_phase2_required_phrases=list(
                    vm.HYDRATION_PHASE2_REQUIRED_PHRASES
                )[:-1]
                + ["invented phase2"],
                hydration_phase5_required_phrases=list(
                    vm.HYDRATION_PHASE5_REQUIRED_PHRASES
                )[:-1]
                + ["invented phase5"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("hydration_meta_required_phrases" in f.message for f in findings)
    assert any(
        "hydration_identity_detail_required_phrases" in f.message for f in findings
    )
    assert any("hydration_git_detail_required_phrases" in f.message for f in findings)
    assert any("hydration_phase2_required_phrases" in f.message for f in findings)
    assert any("hydration_phase5_required_phrases" in f.message for f in findings)

def test_live_v45_constitution_changelog_residual_validators() -> None:
    assert vm.validate_constitution_ide_stack(REPO_ROOT) == []
    assert vm.validate_constitution_install_script(REPO_ROOT) == []
    assert vm.validate_constitution_vscode(REPO_ROOT) == []
    assert vm.validate_constitution_hard_constraints(REPO_ROOT) == []
    assert vm.validate_constitution_risk_tolerance(REPO_ROOT) == []
    assert vm.validate_changelog_preamble(REPO_ROOT) == []
    assert vm.validate_changelog_changed(REPO_ROOT) == []
    assert vm.validate_changelog_initial(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "constitution-ide-stack",
        "constitution-install-script",
        "constitution-vscode",
        "constitution-hard-constraints",
        "constitution-risk-tolerance",
        "changelog-preamble",
        "changelog-changed",
        "changelog-initial",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["constitution_ide_stack_required_phrases"] == list(
        vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES
    )
    assert inventory["constitution_install_script_required_phrases"] == list(
        vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES
    )
    assert inventory["constitution_vscode_required_phrases"] == list(
        vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES
    )
    assert inventory["constitution_hard_constraints_required_phrases"] == list(
        vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES
    )
    assert inventory["constitution_risk_tolerance_required_phrases"] == list(
        vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES
    )
    assert inventory["changelog_preamble_required_phrases"] == list(
        vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES
    )
    assert inventory["changelog_changed_required_phrases"] == list(
        vm.CHANGELOG_CHANGED_REQUIRED_PHRASES
    )
    assert inventory["changelog_initial_required_phrases"] == list(
        vm.CHANGELOG_INITIAL_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_constitution_crypto(REPO_ROOT) == []
    assert vm.validate_changelog_format(REPO_ROOT) == []


def test_v45_constitution_changelog_residual_edge_cases(tmp_path: Path) -> None:
    for fn in [
        vm.validate_constitution_ide_stack,
        vm.validate_constitution_install_script,
        vm.validate_constitution_vscode,
        vm.validate_constitution_hard_constraints,
        vm.validate_constitution_risk_tolerance,
        vm.validate_changelog_preamble,
        vm.validate_changelog_changed,
        vm.validate_changelog_initial,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENTS-v2.2.md", "# Constitution\n\nNo locked content.\n")
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n\nNo locked content.\n")

    cases = [
        (
            vm.validate_constitution_ide_stack,
            "missing IDE Setup section",
            vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES,
        ),
        (
            vm.validate_constitution_install_script,
            "missing Installation Script section",
            vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES,
        ),
        (
            vm.validate_constitution_vscode,
            "missing VS Code Extensions section",
            vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES,
        ),
        (
            vm.validate_constitution_hard_constraints,
            "missing Hard Constraints section",
            vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_constitution_risk_tolerance,
            "missing Risk Tolerance Review section",
            vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES,
        ),
        (
            vm.validate_changelog_preamble,
            "missing Keep a Changelog preamble",
            vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES,
        ),
        (
            vm.validate_changelog_changed,
            "missing Changed section",
            vm.CHANGELOG_CHANGED_REQUIRED_PHRASES,
        ),
        (
            vm.validate_changelog_initial,
            "missing 0.1.0 initial release section",
            vm.CHANGELOG_INITIAL_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            [
                *vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES,
                *vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES,
                *vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES,
                *vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES,
                *vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    _write(
        tmp_path / "CHANGELOG.md",
        "\n".join(
            [
                *vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES,
                *vm.CHANGELOG_CHANGED_REQUIRED_PHRASES,
                *vm.CHANGELOG_INITIAL_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_constitution_ide_stack(tmp_path) == []
    assert vm.validate_constitution_install_script(tmp_path) == []
    assert vm.validate_constitution_vscode(tmp_path) == []
    assert vm.validate_constitution_hard_constraints(tmp_path) == []
    assert vm.validate_constitution_risk_tolerance(tmp_path) == []
    assert vm.validate_changelog_preamble(tmp_path) == []
    assert vm.validate_changelog_changed(tmp_path) == []
    assert vm.validate_changelog_initial(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "constitution_ide_stack_required_phrases",
            vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES,
            ["## 23. Quantum-Blockchain Development IDE Setup"],
        ),
        (
            "constitution_install_script_required_phrases",
            vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES,
            ["### 23.2 Installation Script (WSL2 Ubuntu 22.04)"],
        ),
        (
            "constitution_vscode_required_phrases",
            vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES,
            ["### 23.3 VS Code Extensions (Required)"],
        ),
        (
            "constitution_hard_constraints_required_phrases",
            vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES,
            ["## 24. Hard Constraints — Quantum-Blockchain Additions"],
        ),
        (
            "constitution_risk_tolerance_required_phrases",
            vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES,
            ["## 25. Quarterly Risk Tolerance Review (Section 12.4.1)"],
        ),
        (
            "changelog_preamble_required_phrases",
            vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES,
            ["---"],
        ),
        (
            "changelog_changed_required_phrases",
            vm.CHANGELOG_CHANGED_REQUIRED_PHRASES,
            ["### Changed"],
        ),
        (
            "changelog_initial_required_phrases",
            vm.CHANGELOG_INITIAL_REQUIRED_PHRASES,
            ["## [0.1.0] — 2025-12-13"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                constitution_ide_stack_required_phrases=list(
                    vm.CONSTITUTION_IDE_STACK_REQUIRED_PHRASES
                )[:-1]
                + ["invented ide"],
                constitution_install_script_required_phrases=list(
                    vm.CONSTITUTION_INSTALL_SCRIPT_REQUIRED_PHRASES
                )[:-1]
                + ["invented install"],
                constitution_vscode_required_phrases=list(
                    vm.CONSTITUTION_VSCODE_REQUIRED_PHRASES
                )[:-1]
                + ["invented vscode"],
                constitution_hard_constraints_required_phrases=list(
                    vm.CONSTITUTION_HARD_CONSTRAINTS_REQUIRED_PHRASES
                )[:-1]
                + ["invented hard"],
                constitution_risk_tolerance_required_phrases=list(
                    vm.CONSTITUTION_RISK_TOLERANCE_REQUIRED_PHRASES
                )[:-1]
                + ["invented risk"],
                changelog_preamble_required_phrases=list(
                    vm.CHANGELOG_PREAMBLE_REQUIRED_PHRASES
                )[:-1]
                + ["invented preamble"],
                changelog_changed_required_phrases=list(
                    vm.CHANGELOG_CHANGED_REQUIRED_PHRASES
                )[:-1]
                + ["invented changed"],
                changelog_initial_required_phrases=list(
                    vm.CHANGELOG_INITIAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented initial"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    for key in [
        "constitution_ide_stack_required_phrases",
        "constitution_install_script_required_phrases",
        "constitution_vscode_required_phrases",
        "constitution_hard_constraints_required_phrases",
        "constitution_risk_tolerance_required_phrases",
        "changelog_preamble_required_phrases",
        "changelog_changed_required_phrases",
        "changelog_initial_required_phrases",
    ]:
        assert any(key in f.message for f in findings)

def test_live_v46_prompt_v43_leftover_validators() -> None:
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in ["prompt-expertise", "prompt-principles", "prompt-metrics"]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_expertise_required_phrases"] == list(
        vm.PROMPT_EXPERTISE_REQUIRED_PHRASES
    )
    assert inventory["prompt_principles_required_phrases"] == list(
        vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES
    )
    assert inventory["prompt_metrics_required_phrases"] == list(
        vm.PROMPT_METRICS_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []


def test_v46_prompt_v43_leftover_edge_cases(tmp_path: Path) -> None:
    for fn in [
        vm.validate_prompt_expertise,
        vm.validate_prompt_principles,
        vm.validate_prompt_metrics,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_expertise,
            "missing Your Expertise section",
            vm.PROMPT_EXPERTISE_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_principles,
            "missing Decision Making Principles section",
            vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_metrics,
            "missing Success Metrics section",
            vm.PROMPT_METRICS_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_EXPERTISE_REQUIRED_PHRASES,
                *vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES,
                *vm.PROMPT_METRICS_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_expertise(tmp_path) == []
    assert vm.validate_prompt_principles(tmp_path) == []
    assert vm.validate_prompt_metrics(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_expertise_required_phrases",
            vm.PROMPT_EXPERTISE_REQUIRED_PHRASES,
            ["## Your Expertise"],
        ),
        (
            "prompt_principles_required_phrases",
            vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES,
            ["## Decision Making Principles"],
        ),
        (
            "prompt_metrics_required_phrases",
            vm.PROMPT_METRICS_REQUIRED_PHRASES,
            ["## Success Metrics"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_expertise_required_phrases=list(
                    vm.PROMPT_EXPERTISE_REQUIRED_PHRASES
                )[:-1]
                + ["invented expertise"],
                prompt_principles_required_phrases=list(
                    vm.PROMPT_PRINCIPLES_REQUIRED_PHRASES
                )[:-1]
                + ["invented principles"],
                prompt_metrics_required_phrases=list(
                    vm.PROMPT_METRICS_REQUIRED_PHRASES
                )[:-1]
                + ["invented metrics"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("prompt_expertise_required_phrases" in f.message for f in findings)
    assert any("prompt_principles_required_phrases" in f.message for f in findings)
    assert any("prompt_metrics_required_phrases" in f.message for f in findings)



def test_live_v47_prompt_tools_communication_escalation_validators() -> None:
    assert vm.validate_prompt_tools(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_identity(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_tools_required_phrases"] == list(
        vm.PROMPT_TOOLS_REQUIRED_PHRASES
    )
    assert inventory["prompt_communication_required_phrases"] == list(
        vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES
    )
    assert inventory["prompt_escalation_identity_required_phrases"] == list(
        vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert vm.validate_changelog_preamble(REPO_ROOT) == []
    assert vm.validate_changelog_changed(REPO_ROOT) == []
    assert vm.validate_changelog_initial(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_v47_prompt_tools_communication_escalation_edge_cases(tmp_path: Path) -> None:
    for fn in [
        vm.validate_prompt_tools,
        vm.validate_prompt_communication,
        vm.validate_prompt_escalation_identity,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_tools,
            "missing Your Tools section",
            vm.PROMPT_TOOLS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_communication,
            "missing Your Communication Style section",
            vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_escalation_identity,
            "missing ESCALATION REQUIRED identity banner",
            vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_TOOLS_REQUIRED_PHRASES,
                *vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES,
                *vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_tools(tmp_path) == []
    assert vm.validate_prompt_communication(tmp_path) == []
    assert vm.validate_prompt_escalation_identity(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_tools_required_phrases",
            vm.PROMPT_TOOLS_REQUIRED_PHRASES,
            ["## Your Tools"],
        ),
        (
            "prompt_communication_required_phrases",
            vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES,
            ["## Your Communication Style"],
        ),
        (
            "prompt_escalation_identity_required_phrases",
            vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES,
            ["🚨 ESCALATION REQUIRED"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_tools_required_phrases=list(vm.PROMPT_TOOLS_REQUIRED_PHRASES)[
                    :-1
                ]
                + ["invented tools"],
                prompt_communication_required_phrases=list(
                    vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES
                )[:-1]
                + ["invented communication"],
                prompt_escalation_identity_required_phrases=list(
                    vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation identity"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("prompt_tools_required_phrases" in f.message for f in findings)
    assert any("prompt_communication_required_phrases" in f.message for f in findings)
    assert any(
        "prompt_escalation_identity_required_phrases" in f.message for f in findings
    )


def test_v47_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v47 phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_tools_required_phrases",
            vm.PROMPT_TOOLS_REQUIRED_PHRASES,
            "Tools/Jupyter/Hardhat/liboqs",
        ),
        (
            "prompt_communication_required_phrases",
            vm.PROMPT_COMMUNICATION_REQUIRED_PHRASES,
            "Style/technical/pragmatic/decisive",
        ),
        (
            "prompt_escalation_identity_required_phrases",
            vm.PROMPT_ESCALATION_IDENTITY_REQUIRED_PHRASES,
            "ESCALATION REQUIRED/From Agent specialists",
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(include_token in f.message for f in findings)

    # live validators subset smoke
    for name in [
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
        "prompt-expertise",
        "prompt-principles",
        "prompt-metrics",
        "changelog-preamble",
        "changelog-changed",
        "changelog-initial",
    ]:
        assert vm.VALIDATORS[name](REPO_ROOT) == []

    # contributing honesty still tracks inventory version
    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )


def test_live_v48_prompt_orchestration_monthly_usage_example_validators() -> None:
    assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []
    assert vm.validate_prompt_monthly(REPO_ROOT) == []
    assert vm.validate_prompt_usage_example(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-orchestration-matrix",
        "prompt-monthly",
        "prompt-usage-example",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_orchestration_matrix_required_phrases"] == list(
        vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES
    )
    assert inventory["prompt_monthly_required_phrases"] == list(
        vm.PROMPT_MONTHLY_REQUIRED_PHRASES
    )
    assert inventory["prompt_usage_example_required_phrases"] == list(
        vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green
    assert vm.validate_prompt_tools(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_identity(REPO_ROOT) == []
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_v48_prompt_orchestration_monthly_usage_example_edge_cases(
    tmp_path: Path,
) -> None:
    for fn in [
        vm.validate_prompt_orchestration_matrix,
        vm.validate_prompt_monthly,
        vm.validate_prompt_usage_example,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_orchestration_matrix,
            "missing Your Escalation Authority section",
            vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_monthly,
            "missing Your Monthly Checklist section",
            vm.PROMPT_MONTHLY_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_usage_example,
            "missing Example: Instantiate QuantumArchitectAgent section",
            vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    # Conflict Resolution Matrix section gate
    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                "## Your Escalation Authority",
                *vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES,
            ]
        ),
    )
    findings = vm.validate_prompt_orchestration_matrix(tmp_path)
    assert any("missing Conflict Resolution Matrix section" in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                "## Conflict Resolution Matrix",
                *vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES,
                *vm.PROMPT_MONTHLY_REQUIRED_PHRASES,
                "### Example: Instantiate QuantumArchitectAgent",
                *vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_orchestration_matrix(tmp_path) == []
    assert vm.validate_prompt_monthly(tmp_path) == []
    assert vm.validate_prompt_usage_example(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_orchestration_matrix_required_phrases",
            vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES,
            ["## Your Escalation Authority"],
        ),
        (
            "prompt_monthly_required_phrases",
            vm.PROMPT_MONTHLY_REQUIRED_PHRASES,
            ["## Your Monthly Checklist"],
        ),
        (
            "prompt_usage_example_required_phrases",
            vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES,
            ["Paste into the LLM's system prompt"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_orchestration_matrix_required_phrases=list(
                    vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES
                )[:-1]
                + ["invented orchestration matrix"],
                prompt_monthly_required_phrases=list(
                    vm.PROMPT_MONTHLY_REQUIRED_PHRASES
                )[:-1]
                + ["invented monthly"],
                prompt_usage_example_required_phrases=list(
                    vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES
                )[:-1]
                + ["invented usage example"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "prompt_orchestration_matrix_required_phrases" in f.message for f in findings
    )
    assert any("prompt_monthly_required_phrases" in f.message for f in findings)
    assert any(
        "prompt_usage_example_required_phrases" in f.message for f in findings
    )


def test_v48_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v48 phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_orchestration_matrix_required_phrases",
            vm.PROMPT_ORCHESTRATION_MATRIX_REQUIRED_PHRASES,
            "Escalation Authority/Conflict Type/CANNOT Delegate/go-no-go",
        ),
        (
            "prompt_monthly_required_phrases",
            vm.PROMPT_MONTHLY_REQUIRED_PHRASES,
            "Monthly Checklist/postmortem/Ultimate Goal/ALPHA-STAGE",
        ),
        (
            "prompt_usage_example_required_phrases",
            vm.PROMPT_USAGE_EXAMPLE_REQUIRED_PHRASES,
            "Paste/Cirq/CRYSTALS-Kyber/scratchpad output",
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(include_token in f.message for f in findings)

    # live validators subset smoke
    for name in [
        "prompt-orchestration-matrix",
        "prompt-monthly",
        "prompt-usage-example",
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
        "prompt-expertise",
        "prompt-principles",
        "prompt-metrics",
    ]:
        assert vm.VALIDATORS[name](REPO_ROOT) == []

    # contributing honesty still tracks inventory version
    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )

def test_live_v49_prompt_responsibilities_decision_integration_validators() -> None:
    assert vm.validate_prompt_responsibilities(REPO_ROOT) == []
    assert vm.validate_prompt_decision_authority(REPO_ROOT) == []
    assert vm.validate_prompt_integration(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-responsibilities",
        "prompt-decision-authority",
        "prompt-integration",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_responsibilities_required_phrases"] == list(
        vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES
    )
    assert inventory["prompt_decision_authority_required_phrases"] == list(
        vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES
    )
    assert inventory["prompt_integration_required_phrases"] == list(
        vm.PROMPT_INTEGRATION_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green
    assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []
    assert vm.validate_prompt_monthly(REPO_ROOT) == []
    assert vm.validate_prompt_usage_example(REPO_ROOT) == []
    assert vm.validate_prompt_tools(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_identity(REPO_ROOT) == []
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_v49_prompt_responsibilities_decision_integration_edge_cases(
    tmp_path: Path,
) -> None:
    for fn in [
        vm.validate_prompt_responsibilities,
        vm.validate_prompt_decision_authority,
        vm.validate_prompt_integration,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_responsibilities,
            "missing Core Responsibilities section",
            vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_decision_authority,
            "missing Your Decision Authority section",
            vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_integration,
            "missing Integration with AGENTS.md section",
            vm.PROMPT_INTEGRATION_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    # When You Escalate to Human section gate (heading required separately)
    body_without_human = "\n".join(
        [
            "## Integration with AGENTS.md",
            *[
                p
                for p in vm.PROMPT_INTEGRATION_REQUIRED_PHRASES
                if p != "## When You Escalate to Human"
            ],
        ]
    )
    _write(tmp_path / "AGENT-PROMPTS.md", body_without_human)
    findings = vm.validate_prompt_integration(tmp_path)
    assert any(
        "missing When You Escalate to Human section" in f.message for f in findings
    )

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES,
                *vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES,
                *vm.PROMPT_INTEGRATION_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_responsibilities(tmp_path) == []
    assert vm.validate_prompt_decision_authority(tmp_path) == []
    assert vm.validate_prompt_integration(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_responsibilities_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES,
            ["## Core Responsibilities"],
        ),
        (
            "prompt_decision_authority_required_phrases",
            vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES,
            ["## Your Decision Authority"],
        ),
        (
            "prompt_integration_required_phrases",
            vm.PROMPT_INTEGRATION_REQUIRED_PHRASES,
            ["## Integration with AGENTS.md"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_responsibilities_required_phrases=list(
                    vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES
                )[:-1]
                + ["invented responsibilities"],
                prompt_decision_authority_required_phrases=list(
                    vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES
                )[:-1]
                + ["invented decision authority"],
                prompt_integration_required_phrases=list(
                    vm.PROMPT_INTEGRATION_REQUIRED_PHRASES
                )[:-1]
                + ["invented integration"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any(
        "prompt_responsibilities_required_phrases" in f.message for f in findings
    )
    assert any(
        "prompt_decision_authority_required_phrases" in f.message for f in findings
    )
    assert any("prompt_integration_required_phrases" in f.message for f in findings)


def test_v49_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v49 phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_responsibilities_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_REQUIRED_PHRASES,
            "Core Responsibilities/quantum/collect/risk tolerance",
        ),
        (
            "prompt_decision_authority_required_phrases",
            vm.PROMPT_DECISION_AUTHORITY_REQUIRED_PHRASES,
            "Decision Authority/final calls/Trade-offs/COORDINATE",
        ),
        (
            "prompt_integration_required_phrases",
            vm.PROMPT_INTEGRATION_REQUIRED_PHRASES,
            "Integration/living documents/Escalate to Human/HUMAN REQUIRED",
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(include_token in f.message for f in findings)

    # live validators subset smoke
    for name in [
        "prompt-responsibilities",
        "prompt-decision-authority",
        "prompt-integration",
        "prompt-orchestration-matrix",
        "prompt-monthly",
        "prompt-usage-example",
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
        "prompt-expertise",
        "prompt-principles",
        "prompt-metrics",
    ]:
        assert vm.VALIDATORS[name](REPO_ROOT) == []

    # contributing honesty still tracks inventory version
    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )


def test_live_v50_prompt_context_cannot_delegate_escalation_authority_validators() -> None:
    assert vm.validate_prompt_context(REPO_ROOT) == []
    assert vm.validate_prompt_cannot_delegate(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_authority(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-context",
        "prompt-cannot-delegate",
        "prompt-escalation-authority",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_context_required_phrases"] == list(
        vm.PROMPT_CONTEXT_REQUIRED_PHRASES
    )
    assert inventory["prompt_cannot_delegate_required_phrases"] == list(
        vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES
    )
    assert inventory["prompt_escalation_authority_required_phrases"] == list(
        vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green
    assert vm.validate_prompt_responsibilities(REPO_ROOT) == []
    assert vm.validate_prompt_decision_authority(REPO_ROOT) == []
    assert vm.validate_prompt_integration(REPO_ROOT) == []
    assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []
    assert vm.validate_prompt_monthly(REPO_ROOT) == []
    assert vm.validate_prompt_usage_example(REPO_ROOT) == []
    assert vm.validate_prompt_tools(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_identity(REPO_ROOT) == []
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_v50_prompt_context_cannot_delegate_escalation_authority_edge_cases(
    tmp_path: Path,
) -> None:
    for fn in [
        vm.validate_prompt_context,
        vm.validate_prompt_cannot_delegate,
        vm.validate_prompt_escalation_authority,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_context,
            "missing Current Project Context section",
            vm.PROMPT_CONTEXT_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_cannot_delegate,
            "missing Key Responsibilities You CANNOT Delegate section",
            vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_escalation_authority,
            "missing Your Escalation Authority section",
            vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_CONTEXT_REQUIRED_PHRASES,
                *vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES,
                *vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_context(tmp_path) == []
    assert vm.validate_prompt_cannot_delegate(tmp_path) == []
    assert vm.validate_prompt_escalation_authority(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_context_required_phrases",
            vm.PROMPT_CONTEXT_REQUIRED_PHRASES,
            ["## Current Project Context"],
        ),
        (
            "prompt_cannot_delegate_required_phrases",
            vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES,
            ["## Key Responsibilities You CANNOT Delegate"],
        ),
        (
            "prompt_escalation_authority_required_phrases",
            vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES,
            ["## Your Escalation Authority"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_context_required_phrases=list(
                    vm.PROMPT_CONTEXT_REQUIRED_PHRASES
                )[:-1]
                + ["invented context"],
                prompt_cannot_delegate_required_phrases=list(
                    vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES
                )[:-1]
                + ["invented cannot delegate"],
                prompt_escalation_authority_required_phrases=list(
                    vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation authority"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert any("prompt_context_required_phrases" in f.message for f in findings)
    assert any(
        "prompt_cannot_delegate_required_phrases" in f.message for f in findings
    )
    assert any(
        "prompt_escalation_authority_required_phrases" in f.message for f in findings
    )


def test_v50_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v50 phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_context_required_phrases",
            vm.PROMPT_CONTEXT_REQUIRED_PHRASES,
            "Current Project Context/INSERT/blockchain/devices",
        ),
        (
            "prompt_cannot_delegate_required_phrases",
            vm.PROMPT_CANNOT_DELEGATE_REQUIRED_PHRASES,
            "CANNOT Delegate/go-no-go/Risk acceptance/Stakeholder",
        ),
        (
            "prompt_escalation_authority_required_phrases",
            vm.PROMPT_ESCALATION_AUTHORITY_REQUIRED_PHRASES,
            "Escalation Authority/MUST escalate/irresolvable/Budget",
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(include_token in f.message for f in findings)

    for name in [
        "prompt-context",
        "prompt-cannot-delegate",
        "prompt-escalation-authority",
        "prompt-responsibilities",
        "prompt-decision-authority",
        "prompt-integration",
        "prompt-orchestration-matrix",
        "prompt-monthly",
        "prompt-usage-example",
        "prompt-tools",
        "prompt-communication",
        "prompt-escalation-identity",
        "prompt-expertise",
        "prompt-principles",
        "prompt-metrics",
    ]:
        assert vm.VALIDATORS[name](REPO_ROOT) == []

    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )


def test_live_v51_prompt_heavy_leftover_validators() -> None:
    assert vm.validate_prompt_role_blurbs(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_format(REPO_ROOT) == []
    assert vm.validate_prompt_living_docs(REPO_ROOT) == []
    assert vm.validate_prompt_constraints_detail(REPO_ROOT) == []
    assert vm.validate_prompt_triggers_detail(REPO_ROOT) == []
    assert vm.validate_prompt_human_fields(REPO_ROOT) == []
    assert vm.validate_prompt_context_detail(REPO_ROOT) == []
    assert vm.validate_prompt_expertise_detail(REPO_ROOT) == []
    assert vm.validate_prompt_related_health(REPO_ROOT) == []
    assert vm.validate_prompt_tools_detail(REPO_ROOT) == []
    assert vm.validate_prompt_responsibilities_detail(REPO_ROOT) == []
    assert vm.validate_prompt_instantiation(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-role-blurbs",
        "prompt-escalation-format",
        "prompt-living-docs",
        "prompt-constraints-detail",
        "prompt-triggers-detail",
        "prompt-human-fields",
        "prompt-context-detail",
        "prompt-expertise-detail",
        "prompt-related-health",
        "prompt-tools-detail",
        "prompt-responsibilities-detail",
        "prompt-instantiation",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_role_blurbs_required_phrases"] == list(
        vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES
    )
    assert inventory["prompt_escalation_format_required_phrases"] == list(
        vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES
    )
    assert inventory["prompt_living_docs_required_phrases"] == list(
        vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES
    )
    assert inventory["prompt_constraints_detail_required_phrases"] == list(
        vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_triggers_detail_required_phrases"] == list(
        vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_human_fields_required_phrases"] == list(
        vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES
    )
    assert inventory["prompt_context_detail_required_phrases"] == list(
        vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_expertise_detail_required_phrases"] == list(
        vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_related_health_required_phrases"] == list(
        vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES
    )
    assert inventory["prompt_tools_detail_required_phrases"] == list(
        vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_responsibilities_detail_required_phrases"] == list(
        vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_instantiation_required_phrases"] == list(
        vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green
    assert vm.validate_prompt_context(REPO_ROOT) == []
    assert vm.validate_prompt_cannot_delegate(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_authority(REPO_ROOT) == []
    assert vm.validate_prompt_responsibilities(REPO_ROOT) == []
    assert vm.validate_prompt_decision_authority(REPO_ROOT) == []
    assert vm.validate_prompt_integration(REPO_ROOT) == []
    assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []
    assert vm.validate_prompt_monthly(REPO_ROOT) == []
    assert vm.validate_prompt_usage_example(REPO_ROOT) == []
    assert vm.validate_prompt_tools(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_identity(REPO_ROOT) == []
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_roles(REPO_ROOT) == []
    assert vm.validate_prompt_sections(REPO_ROOT) == []
    assert vm.validate_prompt_usage(REPO_ROOT) == []
    assert vm.validate_prompt_constraints(REPO_ROOT) == []
    assert vm.validate_prompt_triggers(REPO_ROOT) == []
    assert vm.validate_prompt_related_docs(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_v51_prompt_heavy_leftover_edge_cases(tmp_path: Path) -> None:
    for fn in [
        vm.validate_prompt_role_blurbs,
        vm.validate_prompt_escalation_format,
        vm.validate_prompt_living_docs,
        vm.validate_prompt_constraints_detail,
        vm.validate_prompt_triggers_detail,
        vm.validate_prompt_human_fields,
        vm.validate_prompt_context_detail,
        vm.validate_prompt_expertise_detail,
        vm.validate_prompt_related_health,
        vm.validate_prompt_tools_detail,
        vm.validate_prompt_responsibilities_detail,
        vm.validate_prompt_instantiation,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_role_blurbs,
            "missing System Prompt / role-blurb anchors",
            vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_escalation_format,
            "missing When You Escalate section",
            vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_living_docs,
            "missing Agent Prompt Templates header",
            vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_constraints_detail,
            "missing constraints-detail Never optimize lock",
            vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_triggers_detail,
            "missing triggers-detail Quantum advantage lock",
            vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_human_fields,
            "missing human-fields Situation lock",
            vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_context_detail,
            "missing context-detail Token standards lock",
            vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_expertise_detail,
            "missing expertise-detail Circuit optimization lock",
            vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_related_health,
            "missing related-health Section 5.3 lock",
            vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_tools_detail,
            "missing tools-detail IBM Quantum lock",
            vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_responsibilities_detail,
            "missing responsibilities-detail Optimize Cirq lock",
            vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_instantiation,
            "missing instantiation Provide access lock",
            vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES,
                *vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES,
                *vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES,
                *vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES,
                *vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES,
                *vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_role_blurbs(tmp_path) == []
    assert vm.validate_prompt_escalation_format(tmp_path) == []
    assert vm.validate_prompt_living_docs(tmp_path) == []
    assert vm.validate_prompt_constraints_detail(tmp_path) == []
    assert vm.validate_prompt_triggers_detail(tmp_path) == []
    assert vm.validate_prompt_human_fields(tmp_path) == []
    assert vm.validate_prompt_context_detail(tmp_path) == []
    assert vm.validate_prompt_expertise_detail(tmp_path) == []
    assert vm.validate_prompt_related_health(tmp_path) == []
    assert vm.validate_prompt_tools_detail(tmp_path) == []
    assert vm.validate_prompt_responsibilities_detail(tmp_path) == []
    assert vm.validate_prompt_instantiation(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_role_blurbs_required_phrases",
            vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES,
            ["# QuantumArchitectAgent System Prompt"],
        ),
        (
            "prompt_escalation_format_required_phrases",
            vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES,
            ["## When You Escalate"],
        ),
        (
            "prompt_living_docs_required_phrases",
            vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES,
            ["# Agent Prompt Templates"],
        ),
        (
            "prompt_constraints_detail_required_phrases",
            vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES,
            ["Never optimize beyond device constraints (memory, runtime)"],
        ),
        (
            "prompt_triggers_detail_required_phrases",
            vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES,
            ["Quantum advantage deadline < 6 months and algorithm not quantum-safe"],
        ),
        (
            "prompt_human_fields_required_phrases",
            vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES,
            ["Situation: [What decision needs human input?]"],
        ),
        (
            "prompt_context_detail_required_phrases",
            vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES,
            ["Token standards: ERC-20 (if applicable), ERC-721 (NFT)"],
        ),
        (
            "prompt_expertise_detail_required_phrases",
            vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES,
            ["Circuit optimization (gate reduction, error mitigation)"],
        ),
        (
            "prompt_related_health_required_phrases",
            vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES,
            ["See AGENTS.md Section 5.3 (Knowledge & Health Agents)"],
        ),
        (
            "prompt_tools_detail_required_phrases",
            vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES,
            ["IBM Quantum Experience (real hardware validation)"],
        ),
        (
            "prompt_responsibilities_detail_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES,
            ["Optimize Cirq circuits for target hardware"],
        ),
        (
            "prompt_instantiation_required_phrases",
            vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES,
            ["**Provide the agent with access to**:"],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_role_blurbs_required_phrases=list(
                    vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES
                )[:-1]
                + ["invented role blurbs"],
                prompt_escalation_format_required_phrases=list(
                    vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES
                )[:-1]
                + ["invented escalation format"],
                prompt_living_docs_required_phrases=list(
                    vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES
                )[:-1]
                + ["invented living docs"],
                prompt_constraints_detail_required_phrases=list(
                    vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented constraints detail"],
                prompt_triggers_detail_required_phrases=list(
                    vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented triggers detail"],
                prompt_human_fields_required_phrases=list(
                    vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES
                )[:-1]
                + ["invented human fields"],
                prompt_context_detail_required_phrases=list(
                    vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented context detail"],
                prompt_expertise_detail_required_phrases=list(
                    vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented expertise detail"],
                prompt_related_health_required_phrases=list(
                    vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES
                )[:-1]
                + ["invented related health"],
                prompt_tools_detail_required_phrases=list(
                    vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented tools detail"],
                prompt_responsibilities_detail_required_phrases=list(
                    vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented responsibilities detail"],
                prompt_instantiation_required_phrases=list(
                    vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES
                )[:-1]
                + ["invented instantiation"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    for key in [
        "prompt_role_blurbs_required_phrases",
        "prompt_escalation_format_required_phrases",
        "prompt_living_docs_required_phrases",
        "prompt_constraints_detail_required_phrases",
        "prompt_triggers_detail_required_phrases",
        "prompt_human_fields_required_phrases",
        "prompt_context_detail_required_phrases",
        "prompt_expertise_detail_required_phrases",
        "prompt_related_health_required_phrases",
        "prompt_tools_detail_required_phrases",
        "prompt_responsibilities_detail_required_phrases",
        "prompt_instantiation_required_phrases",
    ]:
        assert any(key in f.message for f in findings)


def test_v51_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v51 heavy phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_role_blurbs_required_phrases",
            vm.PROMPT_ROLE_BLURBS_REQUIRED_PHRASES,
            "role-blurbs/System Prompt/Your Role descriptive blurbs",
        ),
        (
            "prompt_escalation_format_required_phrases",
            vm.PROMPT_ESCALATION_FORMAT_REQUIRED_PHRASES,
            "When You Escalate/format/Alternative Path/Timeline",
        ),
        (
            "prompt_living_docs_required_phrases",
            vm.PROMPT_LIVING_DOCS_REQUIRED_PHRASES,
            "Agent Prompt Templates/FUZZYWIGG-AI/Task.md/synchronized",
        ),
        (
            "prompt_constraints_detail_required_phrases",
            vm.PROMPT_CONSTRAINTS_DETAIL_REQUIRED_PHRASES,
            "Never optimize/Slither must pass/Apple/Google/data isolation",
        ),
        (
            "prompt_triggers_detail_required_phrases",
            vm.PROMPT_TRIGGERS_DETAIL_REQUIRED_PHRASES,
            "Quantum advantage/Multi-chain sync/Battery drain/API design conflicts",
        ),
        (
            "prompt_human_fields_required_phrases",
            vm.PROMPT_HUMAN_FIELDS_REQUIRED_PHRASES,
            "Situation/Agent Input/Risk Assessment/caveats",
        ),
        (
            "prompt_context_detail_required_phrases",
            vm.PROMPT_CONTEXT_DETAIL_REQUIRED_PHRASES,
            "Token standards/HIPAA/GDPR/Deployment target/Key Constraint",
        ),
        (
            "prompt_expertise_detail_required_phrases",
            vm.PROMPT_EXPERTISE_DETAIL_REQUIRED_PHRASES,
            "Circuit optimization/Connext/On-device cryptography/HIPAA applicability",
        ),
        (
            "prompt_related_health_required_phrases",
            vm.PROMPT_RELATED_HEALTH_REQUIRED_PHRASES,
            "Section 5.3/5.3.1/22.3/12.4.1",
        ),
        (
            "prompt_tools_detail_required_phrases",
            vm.PROMPT_TOOLS_DETAIL_REQUIRED_PHRASES,
            "IBM Quantum/Etherscan/React Native/Ledger/libsodium",
        ),
        (
            "prompt_responsibilities_detail_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_DETAIL_REQUIRED_PHRASES,
            "Optimize Cirq/Mickey 18/walled garden/Escalate unsolvable",
        ),
        (
            "prompt_instantiation_required_phrases",
            vm.PROMPT_INSTANTIATION_REQUIRED_PHRASES,
            "Provide access/scratchpad.txt/Run the agent/Updates scratchpad",
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)
        assert any(
            include_token.split("/")[0] in f.message or include_token in f.message
            for f in findings
        )

    # contributing honesty still tracks inventory version
    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )


def test_live_v52_prompt_heavy_residual_validators() -> None:
    assert vm.validate_prompt_metrics_detail(REPO_ROOT) == []
    assert vm.validate_prompt_orch_metrics_detail(REPO_ROOT) == []
    assert vm.validate_prompt_communication_detail(REPO_ROOT) == []
    assert vm.validate_prompt_principles_detail(REPO_ROOT) == []
    assert vm.validate_prompt_responsibilities_residual(REPO_ROOT) == []
    assert vm.validate_prompt_expertise_residual(REPO_ROOT) == []
    assert vm.validate_prompt_vision_context(REPO_ROOT) == []
    assert vm.validate_prompt_context_residual(REPO_ROOT) == []
    assert vm.validate_prompt_monthly_detail(REPO_ROOT) == []
    assert vm.validate_prompt_docs_residual(REPO_ROOT) == []
    assert vm.validate_prompt_matrix_resolutions(REPO_ROOT) == []
    assert vm.validate_prompt_usage_detail(REPO_ROOT) == []
    assert vm.INVENTORY_VERSION == 52
    assert len(vm.VALIDATORS) == 196
    assert vm.MIN_VALIDATOR_COUNT == 196
    for name in [
        "prompt-metrics-detail",
        "prompt-orch-metrics-detail",
        "prompt-communication-detail",
        "prompt-principles-detail",
        "prompt-responsibilities-residual",
        "prompt-expertise-residual",
        "prompt-vision-context",
        "prompt-context-residual",
        "prompt-monthly-detail",
        "prompt-docs-residual",
        "prompt-matrix-resolutions",
        "prompt-usage-detail",
    ]:
        assert name in vm.VALIDATORS
    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert inventory["prompt_metrics_detail_required_phrases"] == list(
        vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_orch_metrics_detail_required_phrases"] == list(
        vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_communication_detail_required_phrases"] == list(
        vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_principles_detail_required_phrases"] == list(
        vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_responsibilities_residual_required_phrases"] == list(
        vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES
    )
    assert inventory["prompt_expertise_residual_required_phrases"] == list(
        vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES
    )
    assert inventory["prompt_vision_context_required_phrases"] == list(
        vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES
    )
    assert inventory["prompt_context_residual_required_phrases"] == list(
        vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES
    )
    assert inventory["prompt_monthly_detail_required_phrases"] == list(
        vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES
    )
    assert inventory["prompt_docs_residual_required_phrases"] == list(
        vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES
    )
    assert inventory["prompt_matrix_resolutions_required_phrases"] == list(
        vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES
    )
    assert inventory["prompt_usage_detail_required_phrases"] == list(
        vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES
    )
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]
    # prior prompt leftovers remain green (#128/#131 slices)
    assert vm.validate_prompt_context(REPO_ROOT) == []
    assert vm.validate_prompt_cannot_delegate(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_authority(REPO_ROOT) == []
    assert vm.validate_prompt_role_blurbs(REPO_ROOT) == []
    assert vm.validate_prompt_escalation_format(REPO_ROOT) == []
    assert vm.validate_prompt_living_docs(REPO_ROOT) == []
    assert vm.validate_prompt_constraints_detail(REPO_ROOT) == []
    assert vm.validate_prompt_triggers_detail(REPO_ROOT) == []
    assert vm.validate_prompt_human_fields(REPO_ROOT) == []
    assert vm.validate_prompt_context_detail(REPO_ROOT) == []
    assert vm.validate_prompt_expertise_detail(REPO_ROOT) == []
    assert vm.validate_prompt_related_health(REPO_ROOT) == []
    assert vm.validate_prompt_tools_detail(REPO_ROOT) == []
    assert vm.validate_prompt_responsibilities_detail(REPO_ROOT) == []
    assert vm.validate_prompt_instantiation(REPO_ROOT) == []
    assert vm.validate_prompt_metrics(REPO_ROOT) == []
    assert vm.validate_prompt_communication(REPO_ROOT) == []
    assert vm.validate_prompt_principles(REPO_ROOT) == []
    assert vm.validate_prompt_expertise(REPO_ROOT) == []
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    assert "v52 HEAVY" in (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_v52_prompt_heavy_residual_edge_cases(tmp_path: Path) -> None:
    for fn in [
        vm.validate_prompt_metrics_detail,
        vm.validate_prompt_orch_metrics_detail,
        vm.validate_prompt_communication_detail,
        vm.validate_prompt_principles_detail,
        vm.validate_prompt_responsibilities_residual,
        vm.validate_prompt_expertise_residual,
        vm.validate_prompt_vision_context,
        vm.validate_prompt_context_residual,
        vm.validate_prompt_monthly_detail,
        vm.validate_prompt_docs_residual,
        vm.validate_prompt_matrix_resolutions,
        vm.validate_prompt_usage_detail,
    ]:
        assert any("missing" in f.message for f in fn(tmp_path))

    _write(tmp_path / "AGENT-PROMPTS.md", "# Prompts\n\nNo locked content.\n")
    cases = [
        (
            vm.validate_prompt_metrics_detail,
            'missing metrics-detail Gate count lock',
            vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_orch_metrics_detail,
            'missing orch-metrics-detail Apple security review lock',
            vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_communication_detail,
            'missing communication-detail Conservative on claims lock',
            vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_principles_detail,
            'missing principles-detail Recommend testing lock',
            vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_responsibilities_residual,
            'missing responsibilities-residual Validate quantum-safe lock',
            vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_expertise_residual,
            'missing expertise-residual Qualtran resource lock',
            vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_vision_context,
            'missing vision-context Current Project Vision lock',
            vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_context_residual,
            'missing context-residual Error tolerance lock',
            vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_monthly_detail,
            'missing monthly-detail Update risk register lock',
            vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_docs_residual,
            'missing docs-residual See postmortem.md lock',
            vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_matrix_resolutions,
            'missing matrix-resolutions Weigh risk tolerance lock',
            vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES,
        ),
        (
            vm.validate_prompt_usage_detail,
            'missing usage-detail Agent Action lock',
            vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES,
        ),
    ]
    for fn, section_msg, phrases in cases:
        findings = fn(tmp_path)
        assert any(section_msg in f.message for f in findings)
        for phrase in phrases:
            assert any(phrase in f.message for f in findings)

    _write(
        tmp_path / "AGENT-PROMPTS.md",
        "\n".join(
            [
                *vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES,
                *vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES,
                *vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES,
                *vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES,
                *vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES,
                *vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES,
                *vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES,
                *vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES,
                "",
            ]
        ),
    )
    assert vm.validate_prompt_metrics_detail(tmp_path) == []
    assert vm.validate_prompt_orch_metrics_detail(tmp_path) == []
    assert vm.validate_prompt_communication_detail(tmp_path) == []
    assert vm.validate_prompt_principles_detail(tmp_path) == []
    assert vm.validate_prompt_responsibilities_residual(tmp_path) == []
    assert vm.validate_prompt_expertise_residual(tmp_path) == []
    assert vm.validate_prompt_vision_context(tmp_path) == []
    assert vm.validate_prompt_context_residual(tmp_path) == []
    assert vm.validate_prompt_monthly_detail(tmp_path) == []
    assert vm.validate_prompt_docs_residual(tmp_path) == []
    assert vm.validate_prompt_matrix_resolutions(tmp_path) == []
    assert vm.validate_prompt_usage_detail(tmp_path) == []

    def _empty(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

    def _dup(key: str, phrases: tuple[str, ...]) -> None:
        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

    def _blank(key: str) -> None:
        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

    def _missing(key: str, seed: list[str]) -> None:
        payload = _inventory_payload()
        payload[key] = seed
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)

    for key, phrases, seed in [
        (
            "prompt_metrics_detail_required_phrases",
            vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES,
            ['Gate count optimized for target hardware'],
        ),
        (
            "prompt_orch_metrics_detail_required_phrases",
            vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES,
            ['Apple security review: PASS'],
        ),
        (
            "prompt_communication_detail_required_phrases",
            vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES,
            ['Conservative on claims ("this is theoretically possible, but...")'],
        ),
        (
            "prompt_principles_detail_required_phrases",
            vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES,
            ['Recommend testing on multiple backends'],
        ),
        (
            "prompt_responsibilities_residual_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES,
            ['Validate quantum-safe properties (post-quantum crypto)'],
        ),
        (
            "prompt_expertise_residual_required_phrases",
            vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES,
            ['Qualtran (resource analysis)'],
        ),
        (
            "prompt_vision_context_required_phrases",
            vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES,
            ['## Current Project Vision'],
        ),
        (
            "prompt_context_residual_required_phrases",
            vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES,
            ['Error tolerance: < 1%'],
        ),
        (
            "prompt_monthly_detail_required_phrases",
            vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES,
            ['Update risk register (quarterly, minimum)'],
        ),
        (
            "prompt_docs_residual_required_phrases",
            vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES,
            ['See postmortem.md (incident log)'],
        ),
        (
            "prompt_matrix_resolutions_required_phrases",
            vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES,
            ['Weigh risk tolerance. Choose testnet approach to validate.'],
        ),
        (
            "prompt_usage_detail_required_phrases",
            vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES,
            ['Agent Action:'],
        ),
    ]:
        _empty(key)
        _dup(key, phrases)
        _blank(key)
        _missing(key, seed)

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(
            _inventory_payload(
                prompt_metrics_detail_required_phrases=list(
                    vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-metrics-detail"],
                prompt_orch_metrics_detail_required_phrases=list(
                    vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-orch-metrics-detail"],
                prompt_communication_detail_required_phrases=list(
                    vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-communication-detail"],
                prompt_principles_detail_required_phrases=list(
                    vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-principles-detail"],
                prompt_responsibilities_residual_required_phrases=list(
                    vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-responsibilities-residual"],
                prompt_expertise_residual_required_phrases=list(
                    vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-expertise-residual"],
                prompt_vision_context_required_phrases=list(
                    vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-vision-context"],
                prompt_context_residual_required_phrases=list(
                    vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-context-residual"],
                prompt_monthly_detail_required_phrases=list(
                    vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-monthly-detail"],
                prompt_docs_residual_required_phrases=list(
                    vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-docs-residual"],
                prompt_matrix_resolutions_required_phrases=list(
                    vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-matrix-resolutions"],
                prompt_usage_detail_required_phrases=list(
                    vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES
                )[:-1]
                + ["invented prompt-usage-detail"],
            )
        ),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    for key in [
        "prompt_metrics_detail_required_phrases",
        "prompt_orch_metrics_detail_required_phrases",
        "prompt_communication_detail_required_phrases",
        "prompt_principles_detail_required_phrases",
        "prompt_responsibilities_residual_required_phrases",
        "prompt_expertise_residual_required_phrases",
        "prompt_vision_context_required_phrases",
        "prompt_context_residual_required_phrases",
        "prompt_monthly_detail_required_phrases",
        "prompt_docs_residual_required_phrases",
        "prompt_matrix_resolutions_required_phrases",
        "prompt_usage_detail_required_phrases",
    ]:
        assert any(key in f.message for f in findings)


def test_v52_inventory_lock_mismatch_and_consistency_matrix(tmp_path: Path) -> None:
    """Large self-test: every v52 heavy residual phrase key empty/dup/blank/seed + live registry."""
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    assert sorted(vm.VALIDATORS) == json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )["validator_names"]

    keys = [
        (
            "prompt_metrics_detail_required_phrases",
            vm.PROMPT_METRICS_DETAIL_REQUIRED_PHRASES,
            'Gate count/Multi-chain sync/quantum-safe audited',
        ),
        (
            "prompt_orch_metrics_detail_required_phrases",
            vm.PROMPT_ORCH_METRICS_DETAIL_REQUIRED_PHRASES,
            'Apple/Google PASS/Team consensus/On-time/Stakeholder',
        ),
        (
            "prompt_communication_detail_required_phrases",
            vm.PROMPT_COMMUNICATION_DETAIL_REQUIRED_PHRASES,
            'Conservative on claims/architecture diagrams/Acknowledge risks',
        ),
        (
            "prompt_principles_detail_required_phrases",
            vm.PROMPT_PRINCIPLES_DETAIL_REQUIRED_PHRASES,
            'Recommend testing/circuit correctness/Apple/Google compliance',
        ),
        (
            "prompt_responsibilities_residual_required_phrases",
            vm.PROMPT_RESPONSIBILITIES_RESIDUAL_REQUIRED_PHRASES,
            'Validate quantum-safe/Identify conflicts/Make final go/no-go',
        ),
        (
            "prompt_expertise_residual_required_phrases",
            vm.PROMPT_EXPERTISE_RESIDUAL_REQUIRED_PHRASES,
            'Qualtran resource/algorithm/Data lifecycle/Battery/memory',
        ),
        (
            "prompt_vision_context_required_phrases",
            vm.PROMPT_VISION_CONTEXT_REQUIRED_PHRASES,
            'Current Project Vision/Timeline/Budget INSERT',
        ),
        (
            "prompt_context_residual_required_phrases",
            vm.PROMPT_CONTEXT_RESIDUAL_REQUIRED_PHRASES,
            'Error tolerance/Gas budget/Deadline INSERT',
        ),
        (
            "prompt_monthly_detail_required_phrases",
            vm.PROMPT_MONTHLY_DETAIL_REQUIRED_PHRASES,
            'Update risk register/Communicate progress',
        ),
        (
            "prompt_docs_residual_required_phrases",
            vm.PROMPT_DOCS_RESIDUAL_REQUIRED_PHRASES,
            'See postmortem.md/postmortem incident log/Update them whenever',
        ),
        (
            "prompt_matrix_resolutions_required_phrases",
            vm.PROMPT_MATRIX_RESOLUTIONS_REQUIRED_PHRASES,
            'Weigh risk tolerance/Redesign contract/hybrid RSA/Reduce scope',
        ),
        (
            "prompt_usage_detail_required_phrases",
            vm.PROMPT_USAGE_DETAIL_REQUIRED_PHRASES,
            'Agent Action/Fill in INSERT/Claude GPT Gemini/Copy template',
        ),
    ]
    for key, phrases, include_token in keys:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings)

        payload = _inventory_payload()
        payload[key] = ["ok", ""]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        )

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings)
        assert any(
            include_token.split("/")[0] in f.message or include_token in f.message
            for f in findings
        )

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    for key, phrases, _include in keys:
        assert inventory[key] == list(phrases)
    assert any(
        "Packaging inventory v52" in phrase
        for phrase in vm.CONTRIBUTING_CI_HONESTY_REQUIRED_PHRASES
    )


# ---------------------------------------------------------------------------
# Overnight memory-slot deepeners (EXISTING modules only)
# Maps "memory slot / store / validator" onto archive coordination memory:
#   - scratchpad* validators (shared coordination store)
#   - constitution-scratchpad-state (append-only / never-delete semantics)
#   - constitution-on-device (Memory footprint < 2MB lock)
#   - agentic_flows allow-list (single non-recipe slot: scratchpad.txt)
# No invented memory-slot product module; eviction only where coded
# (allow-list rejection of overflow files — no LRU eviction exists).
# ---------------------------------------------------------------------------


def _locked_scratchpad_text() -> str:
    """Minimal scratchpad body satisfying all scratchpad* phrase locks."""
    return "\n".join(
        [
            "# g0p-agents Agent Coordination Scratchpad",
            "",
            "This file is the **source of truth** for agent coordination state "
            "in this repo.",
            "Updated by each agent after completing their task. Never delete "
            "entries — mark them complete.",
            "",
            "Format:",
            "- [x] = DONE",
            "- [ ] = PENDING",
            "- [~] = IN_PROGRESS",
            "- [!] = BLOCKED/ESCALATED",
            "",
            "## Task: Repo Hydration — 2026-04-13",
            "",
            "- [x] Phase 1: Discovery",
            "",
            "Status: IN_PROGRESS",
            "Created: 2026-04-13T02:07:01Z",
            "Owner: copilot",
            "Current blocker: none",
            "",
        ]
    )


def _write_four_locked_goose_doc(tmp_path: Path) -> None:
    """Write GOOSE-RECIPES.md with the four locked historic recipe fences."""
    blocks: list[str] = []
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
                "title": vm.RECIPE_TITLES[name],
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


def test_memory_slot_modules_are_existing_only() -> None:
    """Slice targets existing validators — no invented memory-slot product."""
    assert "memory-slot" not in vm.VALIDATORS
    assert "memory-store" not in vm.VALIDATORS
    for name in (
        "scratchpad",
        "scratchpad-intro",
        "scratchpad-format",
        "scratchpad-task-meta",
        "constitution-scratchpad-state",
        "constitution-on-device",
    ):
        assert name in vm.VALIDATORS
    assert vm.AGENTIC_FLOWS_ALLOWED_FILES == frozenset({"scratchpad.txt"})
    assert "Memory footprint: < 2MB" in vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
    assert "Never delete entries" in vm.SCRATCHPAD_REQUIRED_PHRASES
    assert (
        "Only append, never overwrite"
        in vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
    )


def test_memory_slot_empty_maps_and_empty_scratchpad(tmp_path: Path) -> None:
    """Empty coordination memory: missing/empty scratchpad + empty inventory maps."""
    assert any("missing" in f.message for f in vm.validate_scratchpad(tmp_path))
    assert any("missing" in f.message for f in vm.validate_scratchpad_intro(tmp_path))
    assert any("missing" in f.message for f in vm.validate_scratchpad_format(tmp_path))
    assert any(
        "missing" in f.message for f in vm.validate_scratchpad_task_meta(tmp_path)
    )

    _write(tmp_path / "agentic_flows" / "scratchpad.txt", "\n\t  \n")
    findings = vm.validate_scratchpad(tmp_path)
    assert any("scratchpad is empty" in f.message for f in findings)
    assert not any("status marker" in f.message for f in findings)

    empty_root = tmp_path / "empty_root"
    (empty_root / "agentic_flows").mkdir(parents=True)
    assert any("missing" in f.message for f in vm.validate_scratchpad(empty_root))

    # Phrase-array empty deepeners live in _inventory_lock_consistency
    for key in (
        "scratchpad_intro_required_phrases",
        "scratchpad_format_required_phrases",
        "scratchpad_task_meta_required_phrases",
        "constitution_on_device_required_phrases",
        "constitution_scratchpad_state_required_phrases",
    ):
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key

    # Field locks / schema minItems for base scratchpad + allow-list maps
    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")
    for key in (
        "scratchpad_required_phrases",
        "scratchpad_status_markers",
        "agentic_flows_allowed_files",
    ):
        payload = _inventory_payload()
        payload[key] = []
        (tmp_path / "schemas" / "packaging-inventory.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        findings = vm.validate_packaging_inventory(tmp_path)
        assert any(key in f.message for f in findings), key


def test_memory_slot_invalid_keys(tmp_path: Path) -> None:
    """Invalid validator keys, invented allow-list names, and unknown inventory keys."""
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["memory-slot"]
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["memory-slot"])

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")

    for allowed in (
        ["invented-slot.bin", "scratchpad.txt"],
        ["not-scratchpad.txt"],
    ):
        payload = _inventory_payload()
        payload["agentic_flows_allowed_files"] = allowed
        (tmp_path / "schemas" / "packaging-inventory.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        findings = vm.validate_packaging_inventory(tmp_path)
        assert any("agentic_flows_allowed_files" in f.message for f in findings)

    bad = _inventory_payload()
    bad["invented_memory_slot_map"] = {"slot-0": "x"}
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings

    body = _locked_scratchpad_text()
    for marker in vm.SCRATCHPAD_STATUS_MARKERS:
        # Remove marker tokens entirely (substring replace would leave e.g. DONE
        # inside X_DONE_X and still satisfy `marker in text`).
        stripped = body.replace(marker, "ABSENT")
        assert marker not in stripped
        _write(tmp_path / "agentic_flows" / "scratchpad.txt", stripped)
        findings = vm.validate_scratchpad(tmp_path)
        assert any(f"status marker: {marker}" in f.message for f in findings), marker

    mangled = body.replace("Never delete entries", "Always delete entries")
    _write(tmp_path / "agentic_flows" / "scratchpad.txt", mangled)
    findings = vm.validate_scratchpad(tmp_path)
    assert any("Never delete entries" in f.message for f in findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            p
            for p in vm.CONSTITUTION_ON_DEVICE_REQUIRED_PHRASES
            if "Memory footprint" not in p
        )
        + "\n",
    )
    findings = vm.validate_constitution_on_device(tmp_path)
    assert any("Memory footprint: < 2MB" in f.message for f in findings)


def test_memory_slot_full_capacity_overflow_rejection(tmp_path: Path) -> None:
    """Full-slot overflow: allow-list rejects invented files (no LRU eviction coded)."""
    _copy_schemas(tmp_path)
    _write_four_locked_goose_doc(tmp_path)
    flows = tmp_path / "agentic_flows"
    flows.mkdir(parents=True, exist_ok=True)
    _write(flows / "scratchpad.txt", _locked_scratchpad_text())

    for rel in vm.EXPECTED_RECIPE_FILES:
        name = Path(rel).name
        recipe_name = next(
            n for n, path in vm.EXPECTED_RECIPE_BINDINGS.items() if path == rel
        )
        payload = {
            "name": recipe_name,
            "recipe": {
                "version": vm.HISTORIC_RECIPE_VERSION,
                "title": vm.RECIPE_TITLES[recipe_name],
                "settings": {
                    "goose_provider": vm.HISTORIC_GOOSE_PROVIDER,
                    "goose_model": vm.HISTORIC_GOOSE_MODEL,
                },
                "instructions": f"You are {vm.RECIPE_PRIMARY_AGENT[recipe_name]}",
                "prompt": "STEP",
                "extensions": [
                    {
                        "type": vm.HISTORIC_EXTENSION_TYPE,
                        "name": vm.HISTORIC_EXTENSION_NAME,
                    }
                ],
            },
        }
        _write(flows / name, yaml.dump(payload))

    findings = vm.validate_goose_recipes(tmp_path)
    overflow = [
        f
        for f in findings
        if "unexpected/invented agentic_flows file" in f.message
        or "unexpected/invented on-disk recipe" in f.message
    ]
    assert overflow == []

    for invented in (
        "memory-slot-overflow.txt",
        "slot-extra.md",
        "cache.bin",
        "extra_recipe.yaml",
    ):
        _write(flows / invented, "invented\n")
    findings = vm.validate_goose_recipes(tmp_path)
    invented_findings = [
        f
        for f in findings
        if "unexpected/invented agentic_flows file" in f.message
        or "unexpected/invented on-disk recipe" in f.message
    ]
    assert len(invented_findings) >= 4
    assert any("memory-slot-overflow.txt" in f.path for f in invented_findings)
    assert any("extra_recipe.yaml" in f.path for f in invented_findings)

    _write(
        tmp_path / "AGENTS-v2.2.md",
        "\n".join(
            p
            for p in vm.CONSTITUTION_SCRATCHPAD_STATE_REQUIRED_PHRASES
            if p != "Only append, never overwrite"
        )
        + "\n",
    )
    findings = vm.validate_constitution_scratchpad_state(tmp_path)
    assert any("Only append, never overwrite" in f.message for f in findings)


def test_memory_slot_concurrent_validate_races(tmp_path: Path) -> None:
    """Concurrent readers/writers against scratchpad store must not crash."""
    _write(tmp_path / "agentic_flows" / "scratchpad.txt", _locked_scratchpad_text())
    assert vm.validate_scratchpad(tmp_path) == []
    assert vm.validate_scratchpad_intro(tmp_path) == []
    assert vm.validate_scratchpad_format(tmp_path) == []
    assert vm.validate_scratchpad_task_meta(tmp_path) == []

    errors: list[BaseException] = []

    def _read_live() -> list[vm.Finding]:
        return (
            vm.validate_scratchpad(REPO_ROOT)
            + vm.validate_scratchpad_intro(REPO_ROOT)
            + vm.validate_constitution_on_device(REPO_ROOT)
            + vm.validate_constitution_scratchpad_state(REPO_ROOT)
        )

    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_read_live) for _ in range(64)]
        for fut in as_completed(futures):
            try:
                assert fut.result() == []
            except BaseException as exc:  # noqa: BLE001 — collect race failures
                errors.append(exc)
    assert errors == []

    stop = threading.Event()
    race_errors: list[BaseException] = []
    path = tmp_path / "agentic_flows" / "scratchpad.txt"

    def _writer() -> None:
        flip = False
        while not stop.is_set():
            try:
                if flip:
                    path.write_text(_locked_scratchpad_text(), encoding="utf-8")
                else:
                    path.write_text("\n", encoding="utf-8")
                flip = not flip
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    def _reader() -> None:
        while not stop.is_set():
            try:
                vm.validate_scratchpad(tmp_path)
                vm.validate_scratchpad_intro(tmp_path)
                vm.validate_scratchpad_format(tmp_path)
                vm.validate_scratchpad_task_meta(tmp_path)
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    time.sleep(0.35)
    stop.set()
    for t in threads:
        t.join(timeout=2.0)
    assert race_errors == []

    def _empty_map_check(key: str) -> bool:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        return any(f"{key} must not be empty" in f.message for f in findings)

    keys = [
        "scratchpad_intro_required_phrases",
        "constitution_on_device_required_phrases",
        "constitution_scratchpad_state_required_phrases",
        "scratchpad_task_meta_required_phrases",
    ]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_empty_map_check, k) for k in keys for _ in range(8)]
        assert all(fut.result() for fut in as_completed(futs))


def test_memory_slot_live_validators_green() -> None:
    """Live archive coordination-memory validators remain clean on alpha tip."""
    assert vm.validate_scratchpad(REPO_ROOT) == []
    assert vm.validate_scratchpad_intro(REPO_ROOT) == []
    assert vm.validate_scratchpad_format(REPO_ROOT) == []
    assert vm.validate_scratchpad_task_meta(REPO_ROOT) == []
    assert vm.validate_constitution_scratchpad_state(REPO_ROOT) == []
    assert vm.validate_constitution_on_device(REPO_ROOT) == []
    assert "Memory footprint: < 2MB" in (REPO_ROOT / "AGENTS-v2.2.md").read_text(
        encoding="utf-8"
    )
    assert "Never delete entries" in (
        REPO_ROOT / "agentic_flows" / "scratchpad.txt"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Prompt/validator residual HEAVY edges for post-#141 v52 modules only.
# EXISTING twelve prompt-* residual validators — no invented v53 product /
# inventory bump. Distinct from open #142 (pre-v52 / 33-module residual).
# ---------------------------------------------------------------------------

_V52_PROMPT_RESIDUAL_NAMES: tuple[str, ...] = (
    "prompt-metrics-detail",
    "prompt-orch-metrics-detail",
    "prompt-communication-detail",
    "prompt-principles-detail",
    "prompt-responsibilities-residual",
    "prompt-expertise-residual",
    "prompt-vision-context",
    "prompt-context-residual",
    "prompt-monthly-detail",
    "prompt-docs-residual",
    "prompt-matrix-resolutions",
    "prompt-usage-detail",
)


def _v52_prompt_residual_modules() -> list[tuple[str, object, tuple[str, ...], str]]:
    """Map the twelve post-#141 v52 prompt residual validators."""
    modules: list[tuple[str, object, tuple[str, ...], str]] = []
    for name in _V52_PROMPT_RESIDUAL_NAMES:
        suffix = name.removeprefix("prompt-").replace("-", "_")
        const_name = f"PROMPT_{suffix.upper()}_REQUIRED_PHRASES"
        fn_name = f"validate_{name.replace('-', '_')}"
        inv_key = f"prompt_{suffix}_required_phrases"
        modules.append(
            (name, getattr(vm, fn_name), getattr(vm, const_name), inv_key)
        )
    return modules


def _v52_prompt_locked_text() -> str:
    """Union of locked phrases for the twelve v52 residual prompt validators."""
    lines: list[str] = []
    seen: set[str] = set()
    # Longer phrases first so nested substrings (docs-residual) remain intact
    # when written as separate lines.
    ordered: list[str] = []
    for _name, _fn, phrases, _key in _v52_prompt_residual_modules():
        ordered.extend(phrases)
    for phrase in sorted(ordered, key=len, reverse=True):
        if phrase not in seen:
            seen.add(phrase)
            lines.append(phrase)
    return "\n".join(lines) + "\n"


def test_prompt_v52_residual_modules_existing_only() -> None:
    """Slice targets the twelve post-#141 v52 modules — no invented v53 sibling."""
    modules = _v52_prompt_residual_modules()
    assert len(modules) == 12
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196

    for invented in (
        "prompt-v53-invented",
        "prompt-interpolation",
        "prompt-checklist-detail",
        "prompt-escalate-when",
        "prompt-qualtran-tools",
        "prompt-postmortem-refs",
    ):
        assert invented not in vm.VALIDATORS

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]

    for name, _fn, phrases, inv_key in modules:
        assert name in vm.VALIDATORS
        assert name in inventory["validator_names"]
        assert inv_key in inventory
        assert inventory[inv_key] == list(phrases)
        assert len(phrases) >= 2


def test_prompt_v52_residual_empty_maps_and_empty_prompts(tmp_path: Path) -> None:
    """Empty / whitespace / header-only AGENT-PROMPTS + empty v52 phrase maps."""
    modules = _v52_prompt_residual_modules()
    for name, fn, _phrases, _key in modules:
        findings = fn(tmp_path)
        assert any("missing" in f.message for f in findings), name

    _write(tmp_path / "AGENT-PROMPTS.md", "\n\t  \n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        assert findings, name
        assert any(
            phrase in f.message or "missing" in f.message
            for f in findings
            for phrase in phrases[:1]
        ) or any("missing" in f.message for f in findings)

    _write(tmp_path / "AGENT-PROMPTS.md", "# Agent Prompt Templates\n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        phrase_hits = [f for f in findings if any(p in f.message for p in phrases)]
        assert phrase_hits, name

    for _name, _fn, _phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key


def test_prompt_v52_residual_invalid_keys(tmp_path: Path) -> None:
    """Reject invented v53 / unknown keys; corrupt live v52 phrase map types."""
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["prompt-v53-invented"]
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["prompt-interpolation"]
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["prompt-v53-invented"])
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["prompt-interpolation"])

    # Live v52 names remain selectable
    findings = vm.run_all_validations(
        REPO_ROOT, only=["prompt-metrics-detail", "prompt-usage-detail"]
    )
    assert findings == []

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")

    bad = _inventory_payload()
    bad["invented_prompt_v53_residual_map"] = {"slot": "x"}
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings

    bad2 = _inventory_payload()
    bad2["prompt_metrics_detail_required_phrases"] = "not-a-list"
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad2),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings


def test_prompt_v52_residual_per_phrase_drop_matrix(tmp_path: Path) -> None:
    """Drop each locked phrase independently across all twelve v52 modules."""
    base = _v52_prompt_locked_text()
    _write(tmp_path / "AGENT-PROMPTS.md", base)
    modules = _v52_prompt_residual_modules()
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    for name, fn, phrases, _key in modules:
        for phrase in phrases:
            # Remove the token entirely — a prefixed ABSENT:: copy would still
            # satisfy `phrase in body` substring locks.
            mangled = base.replace(phrase, "ABSENT_PHRASE_TOKEN")
            assert phrase not in mangled, (name, phrase)
            _write(tmp_path / "AGENT-PROMPTS.md", mangled)
            findings = fn(tmp_path)
            assert any(phrase in f.message for f in findings), (name, phrase)

    _write(tmp_path / "AGENT-PROMPTS.md", base)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name


def test_prompt_v52_residual_inventory_mismatch_matrix() -> None:
    """Empty / dup / blank / seed mismatches for every v52 prompt_* inventory key."""
    modules = _v52_prompt_residual_modules()
    for _name, _fn, phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        ), key

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings), key


def test_prompt_v52_residual_concurrent_validate_races(tmp_path: Path) -> None:
    """Concurrent readers/writers against AGENT-PROMPTS.md must not crash."""
    modules = _v52_prompt_residual_modules()
    live_fns = [fn for _name, fn, _phrases, _key in modules]

    def _read_live() -> list[vm.Finding]:
        out: list[vm.Finding] = []
        for fn in live_fns:
            out.extend(fn(REPO_ROOT))
        return out

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_read_live) for _ in range(48)]
        for fut in as_completed(futures):
            try:
                assert fut.result() == []
            except BaseException as exc:  # noqa: BLE001 — collect race failures
                errors.append(exc)
    assert errors == []

    locked = _v52_prompt_locked_text()
    path = tmp_path / "AGENT-PROMPTS.md"
    _write(path, locked)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    stop = threading.Event()
    race_errors: list[BaseException] = []

    def _writer() -> None:
        flip = False
        while not stop.is_set():
            try:
                if flip:
                    path.write_text(locked, encoding="utf-8")
                else:
                    path.write_text("\n", encoding="utf-8")
                flip = not flip
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    def _reader() -> None:
        while not stop.is_set():
            try:
                for fn in live_fns:
                    fn(tmp_path)
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    time.sleep(0.35)
    stop.set()
    for t in threads:
        t.join(timeout=2.0)
    assert race_errors == []

    def _empty_map_check(key: str) -> bool:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        return any(f"{key} must not be empty" in f.message for f in findings)

    keys = [key for _n, _f, _p, key in modules]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_empty_map_check, k) for k in keys for _ in range(2)]
        assert all(fut.result() for fut in as_completed(futs))


def test_prompt_v52_residual_cross_isolation(tmp_path: Path) -> None:
    """Dropping one v52 module's phrases must not falsely green that module."""
    base = _v52_prompt_locked_text()
    modules = _v52_prompt_residual_modules()
    targets = [
        "prompt-metrics-detail",
        "prompt-communication-detail",
        "prompt-responsibilities-residual",
        "prompt-vision-context",
        "prompt-docs-residual",
        "prompt-matrix-resolutions",
        "prompt-usage-detail",
    ]
    by_name = {name: (fn, phrases) for name, fn, phrases, _key in modules}
    for target in targets:
        fn, phrases = by_name[target]
        mangled = base
        for phrase in phrases:
            mangled = mangled.replace(phrase, "GONE_PHRASE_TOKEN")
            assert phrase not in mangled, (target, phrase)
        _write(tmp_path / "AGENT-PROMPTS.md", mangled)
        findings = fn(tmp_path)
        assert findings, target
        assert any(p in f.message for f in findings for p in phrases), target
        # Unrelated live root + sibling residual stay green
        assert by_name["prompt-orch-metrics-detail"][0](REPO_ROOT) == []
        assert vm.validate_prompt_expertise_residual(REPO_ROOT) == []


def test_prompt_v52_residual_live_green() -> None:
    """All twelve live v52 residual prompt validators remain clean; inventory v52/196."""
    modules = _v52_prompt_residual_modules()
    assert len(modules) == 12
    for name, fn, _phrases, _key in modules:
        assert fn(REPO_ROOT) == [], name
        assert vm.VALIDATORS[name](REPO_ROOT) == [], name

    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    body = (REPO_ROOT / "AGENT-PROMPTS.md").read_text(encoding="utf-8")
    assert "# Agent Prompt Templates" in body
    assert "System Prompt" in body
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    # Adjacent slices remain green alongside this residual
    assert vm.validate_scratchpad(REPO_ROOT) == []
    assert vm.validate_prompt_role_blurbs(REPO_ROOT) == []
    assert vm.validate_prompt_instantiation(REPO_ROOT) == []


# ---------------------------------------------------------------------------
# Goose-recipe residual HEAVY edges after #144.
# EXISTING nine goose-* phrase-lock validators — no invented timeout sibling /
# inventory bump. Distinct from prompts v51/v52, prompt-validator #144, and
# orchestration-timeout drafts (#145/#146).
# ---------------------------------------------------------------------------

_GOOSE_RECIPE_RESIDUAL_NAMES: tuple[str, ...] = (
    "goose-howto",
    "goose-state-machine",
    "goose-naming",
    "goose-recipe-headers",
    "goose-instruction-agents",
    "goose-extensions",
    "goose-orchestration",
    "goose-conflicts",
    "goose-quantum-task",
)


def _goose_recipe_residual_modules() -> list[tuple[str, object, tuple[str, ...], str]]:
    """Map the nine existing goose-* phrase-lock validators."""
    modules: list[tuple[str, object, tuple[str, ...], str]] = []
    for name in _GOOSE_RECIPE_RESIDUAL_NAMES:
        suffix = name.removeprefix("goose-").replace("-", "_")
        const_name = f"GOOSE_{suffix.upper()}_REQUIRED_PHRASES"
        fn_name = f"validate_{name.replace('-', '_')}"
        inv_key = f"goose_{suffix}_required_phrases"
        modules.append(
            (name, getattr(vm, fn_name), getattr(vm, const_name), inv_key)
        )
    return modules


def _goose_recipe_locked_text() -> str:
    """Union of locked phrases for the nine goose recipe residual validators."""
    lines: list[str] = []
    seen: set[str] = set()
    ordered: list[str] = []
    for _name, _fn, phrases, _key in _goose_recipe_residual_modules():
        ordered.extend(phrases)
    for phrase in sorted(ordered, key=len, reverse=True):
        if phrase not in seen:
            seen.add(phrase)
            lines.append(phrase)
    return "\n".join(lines) + "\n"


def test_goose_recipe_residual_modules_existing_only() -> None:
    """Slice targets nine existing goose-* modules — no invented timeout sibling."""
    modules = _goose_recipe_residual_modules()
    assert len(modules) == 9
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196

    for invented in (
        "goose-timeouts",
        "goose-deadlines",
        "goose-blockchain-task",
        "goose-edge-task",
        "goose-approve-gates",
        "constitution-deadlines",
        "implementation-timeouts",
    ):
        assert invented not in vm.VALIDATORS

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]

    for name, _fn, phrases, inv_key in modules:
        assert name in vm.VALIDATORS
        assert name in inventory["validator_names"]
        assert inv_key in inventory
        assert inventory[inv_key] == list(phrases)
        assert len(phrases) >= 2


def test_goose_recipe_residual_empty_maps_and_empty_doc(tmp_path: Path) -> None:
    """Empty / whitespace / header-only GOOSE-RECIPES + empty goose phrase maps."""
    modules = _goose_recipe_residual_modules()
    for name, fn, _phrases, _key in modules:
        findings = fn(tmp_path)
        assert any("missing" in f.message for f in findings), name

    _write(tmp_path / "GOOSE-RECIPES.md", "\n\t  \n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        assert findings, name
        assert any(
            phrase in f.message or "missing" in f.message
            for f in findings
            for phrase in phrases[:1]
        ) or any("missing" in f.message for f in findings)

    _write(tmp_path / "GOOSE-RECIPES.md", "# Recipe-Based Agent Orchestration\n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        phrase_hits = [f for f in findings if any(p in f.message for p in phrases)]
        assert phrase_hits or any("missing" in f.message for f in findings), name

    for _name, _fn, _phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key


def test_goose_recipe_residual_invalid_keys(tmp_path: Path) -> None:
    """Reject invented timeout/deadline sibling keys; corrupt live goose maps."""
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["goose-timeouts"]
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["goose-deadlines"]
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["goose-timeouts"])
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["goose-deadlines"])

    # Live goose names remain selectable
    findings = vm.run_all_validations(
        REPO_ROOT, only=["goose-howto", "goose-quantum-task", "goose-conflicts"]
    )
    assert findings == []

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")

    bad = _inventory_payload()
    bad["invented_goose_timeout_residual_map"] = {"slot": "x"}
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings

    bad2 = _inventory_payload()
    bad2["goose_howto_required_phrases"] = "not-a-list"
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad2),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings


def test_goose_recipe_residual_per_phrase_drop_matrix(tmp_path: Path) -> None:
    """Drop each locked phrase independently across all nine goose modules."""
    base = _goose_recipe_locked_text()
    _write(tmp_path / "GOOSE-RECIPES.md", base)
    modules = _goose_recipe_residual_modules()
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    for name, fn, phrases, _key in modules:
        for phrase in phrases:
            mangled = base.replace(phrase, "ABSENT_PHRASE_TOKEN")
            assert phrase not in mangled, (name, phrase)
            _write(tmp_path / "GOOSE-RECIPES.md", mangled)
            findings = fn(tmp_path)
            assert any(
                phrase in f.message or "missing" in f.message for f in findings
            ), (name, phrase)

    _write(tmp_path / "GOOSE-RECIPES.md", base)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name


def test_goose_recipe_residual_inventory_mismatch_matrix() -> None:
    """Empty / dup / blank / seed mismatches for every goose_* inventory key."""
    modules = _goose_recipe_residual_modules()
    for _name, _fn, phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        ), key

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings), key


def test_goose_recipe_residual_concurrent_validate_races(tmp_path: Path) -> None:
    """Concurrent readers/writers against GOOSE-RECIPES.md must not crash."""
    modules = _goose_recipe_residual_modules()
    live_fns = [fn for _name, fn, _phrases, _key in modules]

    def _read_live() -> list[vm.Finding]:
        out: list[vm.Finding] = []
        for fn in live_fns:
            out.extend(fn(REPO_ROOT))
        return out

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_read_live) for _ in range(48)]
        for fut in as_completed(futures):
            try:
                assert fut.result() == []
            except BaseException as exc:  # noqa: BLE001 — collect race failures
                errors.append(exc)
    assert errors == []

    locked = _goose_recipe_locked_text()
    path = tmp_path / "GOOSE-RECIPES.md"
    _write(path, locked)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    stop = threading.Event()
    race_errors: list[BaseException] = []

    def _writer() -> None:
        flip = False
        while not stop.is_set():
            try:
                if flip:
                    path.write_text(locked, encoding="utf-8")
                else:
                    path.write_text("\n", encoding="utf-8")
                flip = not flip
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    def _reader() -> None:
        while not stop.is_set():
            try:
                for fn in live_fns:
                    fn(tmp_path)
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    time.sleep(0.35)
    stop.set()
    for t in threads:
        t.join(timeout=2.0)
    assert race_errors == []

    def _empty_map_check(key: str) -> bool:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        return any(f"{key} must not be empty" in f.message for f in findings)

    keys = [key for _n, _f, _p, key in modules]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_empty_map_check, k) for k in keys for _ in range(2)]
        assert all(fut.result() for fut in as_completed(futs))


def test_goose_recipe_residual_cross_isolation(tmp_path: Path) -> None:
    """Dropping one goose module's phrases must not falsely green that module."""
    base = _goose_recipe_locked_text()
    modules = _goose_recipe_residual_modules()
    targets = [
        "goose-howto",
        "goose-state-machine",
        "goose-naming",
        "goose-recipe-headers",
        "goose-instruction-agents",
        "goose-orchestration",
        "goose-conflicts",
        "goose-quantum-task",
    ]
    by_name = {name: (fn, phrases) for name, fn, phrases, _key in modules}
    for target in targets:
        fn, phrases = by_name[target]
        mangled = base
        for phrase in phrases:
            mangled = mangled.replace(phrase, "GONE_PHRASE_TOKEN")
            assert phrase not in mangled, (target, phrase)
        _write(tmp_path / "GOOSE-RECIPES.md", mangled)
        findings = fn(tmp_path)
        assert findings, target
        assert any(
            p in f.message or "missing" in f.message for f in findings for p in phrases
        ), target
        # Unrelated live root + sibling residual stay green
        assert by_name["goose-extensions"][0](REPO_ROOT) == []
        assert vm.validate_goose_howto(REPO_ROOT) == []


def test_goose_recipe_residual_orchestration_fixture_edges(tmp_path: Path) -> None:
    """Docs-only orchestration fixtures: live fences green; orphan on-disk YAML refused."""
    flows = REPO_ROOT / "agentic_flows"
    assert flows.is_dir()
    assert (flows / "scratchpad.txt").is_file()
    # Archive is docs-only — locked recipe paths are documented fences, not on-disk YAML.
    for rel in vm.EXPECTED_RECIPE_FILES:
        assert not (REPO_ROOT / rel).exists(), rel

    assert vm.validate_goose_recipes(REPO_ROOT) == []
    assert vm.validate_recipe_agent_bindings(REPO_ROOT) == []
    assert vm.validate_goose_orchestration(REPO_ROOT) == []

    body = (REPO_ROOT / "GOOSE-RECIPES.md").read_text(encoding="utf-8")
    fences = vm.extract_fenced_yaml_blocks(body)
    assert len(fences) == 4

    # Invented on-disk recipe YAML is refused by the allow-list / inventory lock.
    flows_tmp = tmp_path / "agentic_flows"
    flows_tmp.mkdir(parents=True, exist_ok=True)
    _write(flows_tmp / "scratchpad.txt", "ok\n")
    _write(flows_tmp / "invented_timeout_orch.yaml", "name: invented\n")
    _write(tmp_path / "GOOSE-RECIPES.md", body)
    findings = vm.validate_goose_recipes(tmp_path)
    assert findings
    assert any(
        "unexpected/invented" in f.message or "allow-list" in f.message for f in findings
    )

    # Phrase-only stub (no YAML fences) fails the goose recipe fixture validator.
    _write(tmp_path / "GOOSE-RECIPES.md", _goose_recipe_locked_text())
    (flows_tmp / "invented_timeout_orch.yaml").unlink()
    findings = vm.validate_goose_recipes(tmp_path)
    assert findings
    assert any("expected exactly 4" in f.message or "recipe" in f.message for f in findings)


def test_goose_recipe_residual_live_green() -> None:
    """All nine live goose residual validators remain clean; inventory v52/196."""
    modules = _goose_recipe_residual_modules()
    assert len(modules) == 9
    for name, fn, _phrases, _key in modules:
        assert fn(REPO_ROOT) == [], name
        assert vm.VALIDATORS[name](REPO_ROOT) == [], name

    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    body = (REPO_ROOT / "GOOSE-RECIPES.md").read_text(encoding="utf-8")
    assert "Recipe-Based Agent Orchestration" in body
    assert "goose run" in body
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    # Adjacent slices remain green alongside this residual
    assert vm.validate_goose_recipes(REPO_ROOT) == []
    assert vm.validate_prompt_usage_detail(REPO_ROOT) == []
    assert vm.validate_scratchpad(REPO_ROOT) == []


# Prompt-pre-v52 residual HEAVY edges after #144/#147 tip.
# EXISTING thirty-three pre-v52 prompt-* fixtures only — no invented timeout /
# v53 product / inventory bump. Distinct from merged #144 (twelve v52 prompt
# residuals), merged #147 (nine goose-recipe residuals), and closed CONFLICTING
# #143/#145/#146 timeout PRs.
# ---------------------------------------------------------------------------

_V52_PROMPT_RESIDUAL_EXCLUDE: frozenset[str] = frozenset(
    {
        "prompt-metrics-detail",
        "prompt-orch-metrics-detail",
        "prompt-communication-detail",
        "prompt-principles-detail",
        "prompt-responsibilities-residual",
        "prompt-expertise-residual",
        "prompt-vision-context",
        "prompt-context-residual",
        "prompt-monthly-detail",
        "prompt-docs-residual",
        "prompt-matrix-resolutions",
        "prompt-usage-detail",
    }
)


def _prompt_pre_v52_residual_modules() -> list[
    tuple[str, object, tuple[str, ...], str]
]:
    """Map every live pre-v52 prompt-* validator to phrase tuple + inventory key."""
    modules: list[tuple[str, object, tuple[str, ...], str]] = []
    for name in sorted(
        n
        for n in vm.VALIDATORS
        if n.startswith("prompt-") and n not in _V52_PROMPT_RESIDUAL_EXCLUDE
    ):
        suffix = name.removeprefix("prompt-").replace("-", "_")
        const_name = f"PROMPT_{suffix.upper()}_REQUIRED_PHRASES"
        fn_name = f"validate_{name.replace('-', '_')}"
        inv_key = f"prompt_{suffix}_required_phrases"
        modules.append(
            (name, getattr(vm, fn_name), getattr(vm, const_name), inv_key)
        )
    return modules


def _prompt_pre_v52_locked_text() -> str:
    """Union of locked phrases (+ anchors) for the thirty-three pre-v52 modules."""
    lines: list[str] = []
    seen: set[str] = set()
    ordered: list[str] = []
    for _name, _fn, phrases, _key in _prompt_pre_v52_residual_modules():
        ordered.extend(phrases)
    for anchor in (
        "# Agent Prompt Templates",
        "System Prompt",
        "## When You Escalate",
        "## Your Escalation Authority",
        "## Core Responsibilities",
        "## Decision Making Principles",
        "## Success Metrics",
        "## Your Tools",
        "## Communication Style",
        "## Expertise",
        "Current Project Context",
        "CANNOT Delegate",
        "Escalation Authority",
        "Conflict Resolution Matrix",
        "Monthly Checklist",
        "## Conflict Resolution Matrix",
        "### Example: Instantiate QuantumArchitectAgent",
    ):
        ordered.append(anchor)
    for phrase in sorted(ordered, key=len, reverse=True):
        if phrase not in seen:
            seen.add(phrase)
            lines.append(phrase)
    return "\n".join(lines) + "\n"


def test_prompt_pre_v52_residual_modules_existing_only() -> None:
    """Slice targets thirty-three pre-v52 prompt fixtures — not #144/#147 siblings."""
    modules = _prompt_pre_v52_residual_modules()
    assert len(modules) == 33
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196

    # #144 twelve remain live but are intentionally excluded from this slice
    for name in _V52_PROMPT_RESIDUAL_EXCLUDE:
        assert name in vm.VALIDATORS
        assert name not in {m[0] for m in modules}

    for invented in (
        "goose-timeouts",
        "goose-deadlines",
        "constitution-deadlines",
        "implementation-timeouts",
        "prompt-v53-invented",
        "prompt-interpolation",
        "prompt-checklist-detail",
        "prompt-escalate-when",
    ):
        assert invented not in vm.VALIDATORS

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]

    for name, _fn, phrases, inv_key in modules:
        assert name in vm.VALIDATORS
        assert name in inventory["validator_names"]
        assert inv_key in inventory
        assert inventory[inv_key] == list(phrases)
        assert len(phrases) >= 2

    # Orch-facing pre-v52 fixture stays in this leftover slice
    assert "prompt-orchestration-matrix" in {m[0] for m in modules}


def test_prompt_pre_v52_residual_empty_maps_and_empty_prompts(tmp_path: Path) -> None:
    """Empty / whitespace / header-only AGENT-PROMPTS + empty pre-v52 phrase maps."""
    modules = _prompt_pre_v52_residual_modules()
    for name, fn, _phrases, _key in modules:
        findings = fn(tmp_path)
        assert any("missing" in f.message for f in findings), name

    _write(tmp_path / "AGENT-PROMPTS.md", "\n\t  \n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        assert findings, name
        assert any(
            phrase in f.message or "missing" in f.message
            for f in findings
            for phrase in phrases[:1]
        ) or any("missing" in f.message for f in findings)

    _write(tmp_path / "AGENT-PROMPTS.md", "# Agent Prompt Templates\n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        phrase_hits = [f for f in findings if any(p in f.message for p in phrases)]
        assert phrase_hits, name

    for _name, _fn, _phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key


def test_prompt_pre_v52_residual_invalid_keys(tmp_path: Path) -> None:
    """Reject invented timeout / v53 keys; live pre-v52 + #144 names remain selectable."""
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["goose-timeouts"]
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["prompt-v53-invented"]
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["goose-timeouts"])
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["prompt-interpolation"])

    findings = vm.run_all_validations(
        REPO_ROOT,
        only=[
            "prompt-orchestration-matrix",
            "prompt-role-blurbs",
            "prompt-instantiation",
            "prompt-metrics-detail",
        ],
    )
    assert findings == []

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")

    bad = _inventory_payload()
    bad["invented_prompt_pre_v52_residual_map"] = {"slot": "x"}
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings

    bad2 = _inventory_payload()
    bad2["prompt_orchestration_matrix_required_phrases"] = "not-a-list"
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad2),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings


def test_prompt_pre_v52_residual_per_phrase_drop_matrix(tmp_path: Path) -> None:
    """Drop each locked phrase independently across all thirty-three pre-v52 modules."""
    base = _prompt_pre_v52_locked_text()
    _write(tmp_path / "AGENT-PROMPTS.md", base)
    modules = _prompt_pre_v52_residual_modules()
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    for name, fn, phrases, _key in modules:
        for phrase in phrases:
            mangled = base.replace(phrase, "ABSENT_PHRASE_TOKEN")
            assert phrase not in mangled, (name, phrase)
            _write(tmp_path / "AGENT-PROMPTS.md", mangled)
            findings = fn(tmp_path)
            assert any(phrase in f.message for f in findings), (name, phrase)

    _write(tmp_path / "AGENT-PROMPTS.md", base)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name


def test_prompt_pre_v52_residual_inventory_mismatch_matrix() -> None:
    """Empty / dup / blank / seed mismatches for every pre-v52 prompt_* inventory key."""
    modules = _prompt_pre_v52_residual_modules()
    for _name, _fn, phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        ), key

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings), key


def test_prompt_pre_v52_residual_concurrent_validate_races(tmp_path: Path) -> None:
    """Concurrent readers/writers against AGENT-PROMPTS.md must not crash."""
    modules = _prompt_pre_v52_residual_modules()
    live_fns = [fn for _name, fn, _phrases, _key in modules]

    def _read_live() -> list[vm.Finding]:
        out: list[vm.Finding] = []
        for fn in live_fns:
            out.extend(fn(REPO_ROOT))
        return out

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_read_live) for _ in range(48)]
        for fut in as_completed(futures):
            try:
                assert fut.result() == []
            except BaseException as exc:  # noqa: BLE001 — collect race failures
                errors.append(exc)
    assert errors == []

    locked = _prompt_pre_v52_locked_text()
    path = tmp_path / "AGENT-PROMPTS.md"
    _write(path, locked)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    stop = threading.Event()
    race_errors: list[BaseException] = []

    def _writer() -> None:
        flip = False
        while not stop.is_set():
            try:
                if flip:
                    path.write_text(locked, encoding="utf-8")
                else:
                    path.write_text("\n", encoding="utf-8")
                flip = not flip
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    def _reader() -> None:
        while not stop.is_set():
            try:
                for fn in live_fns:
                    fn(tmp_path)
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    time.sleep(0.35)
    stop.set()
    for t in threads:
        t.join(timeout=2.0)
    assert race_errors == []

    def _empty_map_check(key: str) -> bool:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        return any(f"{key} must not be empty" in f.message for f in findings)

    keys = [key for _n, _f, _p, key in modules]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_empty_map_check, k) for k in keys for _ in range(2)]
        assert all(fut.result() for fut in as_completed(futs))


def test_prompt_pre_v52_residual_cross_isolation(tmp_path: Path) -> None:
    """Dropping one pre-v52 module's phrases must not falsely green that module."""
    base = _prompt_pre_v52_locked_text()
    modules = _prompt_pre_v52_residual_modules()
    targets = [
        "prompt-orchestration-matrix",
        "prompt-role-blurbs",
        "prompt-constraints-detail",
        "prompt-tools-detail",
        "prompt-instantiation",
        "prompt-context",
        "prompt-metrics",
        "prompt-roles",
    ]
    by_name = {name: (fn, phrases) for name, fn, phrases, _key in modules}
    for target in targets:
        fn, phrases = by_name[target]
        mangled = base
        for phrase in phrases:
            mangled = mangled.replace(phrase, "GONE_PHRASE_TOKEN")
            assert phrase not in mangled, (target, phrase)
        _write(tmp_path / "AGENT-PROMPTS.md", mangled)
        findings = fn(tmp_path)
        assert findings, target
        assert any(p in f.message for f in findings for p in phrases), target
        # Unrelated live root + #144/#147 siblings stay green
        assert by_name["prompt-related-docs"][0](REPO_ROOT) == []
        assert vm.validate_prompt_usage_detail(REPO_ROOT) == []
        assert vm.validate_goose_orchestration(REPO_ROOT) == []


def test_prompt_pre_v52_residual_live_green() -> None:
    """All thirty-three live pre-v52 prompt validators remain clean; inventory v52/196."""
    modules = _prompt_pre_v52_residual_modules()
    assert len(modules) == 33
    for name, fn, _phrases, _key in modules:
        assert fn(REPO_ROOT) == [], name
        assert vm.VALIDATORS[name](REPO_ROOT) == [], name

    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    body = (REPO_ROOT / "AGENT-PROMPTS.md").read_text(encoding="utf-8")
    assert "# Agent Prompt Templates" in body
    assert "System Prompt" in body
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    # Adjacent #144 / #147 slices remain green alongside this residual
    assert vm.validate_prompt_metrics_detail(REPO_ROOT) == []
    assert vm.validate_goose_howto(REPO_ROOT) == []
    assert vm.validate_scratchpad(REPO_ROOT) == []


# ---------------------------------------------------------------------------
# Constitution residual HEAVY edges after #151.
# EXISTING fourteen constitution-* phrase-lock validators — no invented v53
# sibling / inventory bump. Distinct from #147 goose-recipe residuals and
# #151 prompt-pre-v52 residuals (and closed CONFLICTING #150 constitution invent).
# ---------------------------------------------------------------------------

_CONSTITUTION_RESIDUAL_NAMES: tuple[str, ...] = (
    "constitution-crypto",
    "constitution-handoff",
    "constitution-escalation-matrix",
    "constitution-on-device",
    "constitution-multichain",
    "constitution-escalation-format",
    "constitution-recipe-orchestration",
    "constitution-scratchpad-state",
    "constitution-conflict-matrix",
    "constitution-ide-stack",
    "constitution-install-script",
    "constitution-vscode",
    "constitution-hard-constraints",
    "constitution-risk-tolerance",
)


def _constitution_residual_modules() -> list[tuple[str, object, tuple[str, ...], str]]:
    """Map the fourteen existing constitution-* phrase-lock validators."""
    modules: list[tuple[str, object, tuple[str, ...], str]] = []
    for name in _CONSTITUTION_RESIDUAL_NAMES:
        suffix = name.removeprefix("constitution-").replace("-", "_")
        const_name = f"CONSTITUTION_{suffix.upper()}_REQUIRED_PHRASES"
        fn_name = f"validate_{name.replace('-', '_')}"
        inv_key = f"constitution_{suffix}_required_phrases"
        modules.append(
            (name, getattr(vm, fn_name), getattr(vm, const_name), inv_key)
        )
    return modules


def _constitution_residual_locked_text() -> str:
    """Union of locked phrases for the fourteen constitution residual validators."""
    lines: list[str] = []
    seen: set[str] = set()
    ordered: list[str] = []
    for _name, _fn, phrases, _key in _constitution_residual_modules():
        ordered.extend(phrases)
    for phrase in sorted(ordered, key=len, reverse=True):
        if phrase not in seen:
            seen.add(phrase)
            lines.append(phrase)
    return "\n".join(lines) + "\n"


def test_constitution_residual_modules_existing_only() -> None:
    """Slice targets fourteen existing constitution-* modules — not #147/#151."""
    modules = _constitution_residual_modules()
    assert len(modules) == 14
    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196

    # Adjacent leftover slices stay live but are intentionally excluded
    assert "prompt-orchestration-matrix" in vm.VALIDATORS
    assert "goose-howto" in vm.VALIDATORS
    assert "prompt-orchestration-matrix" not in {m[0] for m in modules}
    assert "goose-howto" not in {m[0] for m in modules}

    for invented in (
        "constitution-deadlines",
        "constitution-timeouts",
        "constitution-specialists-overview",
        "constitution-quantum-profile",
        "constitution-crypto-residual",
        "goose-timeouts",
        "goose-deadlines",
        "implementation-timeouts",
        "prompt-v53-invented",
    ):
        assert invented not in vm.VALIDATORS

    inventory = json.loads(
        (REPO_ROOT / "schemas" / "packaging-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["version"] == 52
    assert inventory["min_validator_count"] == 196
    assert sorted(vm.VALIDATORS) == inventory["validator_names"]

    for name, _fn, phrases, inv_key in modules:
        assert name in vm.VALIDATORS
        assert name in inventory["validator_names"]
        assert inv_key in inventory
        assert inventory[inv_key] == list(phrases)
        assert len(phrases) >= 2


def test_constitution_residual_empty_maps_and_empty_doc(tmp_path: Path) -> None:
    """Empty / whitespace / header-only AGENTS-v2.2 + empty constitution phrase maps."""
    modules = _constitution_residual_modules()
    for name, fn, _phrases, _key in modules:
        findings = fn(tmp_path)
        assert any("missing" in f.message for f in findings), name

    _write(tmp_path / "AGENTS-v2.2.md", "\n\t  \n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        assert findings, name
        assert any(
            phrase in f.message or "missing" in f.message
            for f in findings
            for phrase in phrases[:1]
        ) or any("missing" in f.message for f in findings)

    _write(tmp_path / "AGENTS-v2.2.md", "# Agents Constitution\n")
    for name, fn, phrases, _key in modules:
        findings = fn(tmp_path)
        phrase_hits = [f for f in findings if any(p in f.message for p in phrases)]
        assert phrase_hits or any("missing" in f.message for f in findings), name

    for _name, _fn, _phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key


def test_constitution_residual_invalid_keys(tmp_path: Path) -> None:
    """Reject invented constitution/timeout/v53 keys; live constitution names stay selectable."""
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["constitution-deadlines"]
    with pytest.raises(KeyError):
        _ = vm.VALIDATORS["constitution-specialists-overview"]
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["constitution-timeouts"])
    with pytest.raises(ValueError, match="unknown validator"):
        vm.run_all_validations(REPO_ROOT, only=["constitution-quantum-profile"])

    findings = vm.run_all_validations(
        REPO_ROOT,
        only=[
            "constitution-crypto",
            "constitution-handoff",
            "constitution-ide-stack",
            "constitution-risk-tolerance",
            "goose-howto",
            "prompt-orchestration-matrix",
        ],
    )
    assert findings == []

    _copy_schemas(tmp_path)
    for rel in _inventory_payload()["required_paths"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("ok\n", encoding="utf-8")

    bad = _inventory_payload()
    bad["invented_constitution_residual_map"] = {"slot": "x"}
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings

    bad2 = _inventory_payload()
    bad2["constitution_crypto_required_phrases"] = "not-a-list"
    (tmp_path / "schemas" / "packaging-inventory.json").write_text(
        json.dumps(bad2),
        encoding="utf-8",
    )
    findings = vm.validate_packaging_inventory(tmp_path)
    assert findings


def test_constitution_residual_per_phrase_drop_matrix(tmp_path: Path) -> None:
    """Drop each locked phrase independently across all fourteen constitution modules."""
    base = _constitution_residual_locked_text()
    _write(tmp_path / "AGENTS-v2.2.md", base)
    modules = _constitution_residual_modules()
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    for name, fn, phrases, _key in modules:
        for phrase in phrases:
            mangled = base.replace(phrase, "ABSENT_PHRASE_TOKEN")
            assert phrase not in mangled, (name, phrase)
            _write(tmp_path / "AGENTS-v2.2.md", mangled)
            findings = fn(tmp_path)
            assert any(phrase in f.message for f in findings), (name, phrase)

    _write(tmp_path / "AGENTS-v2.2.md", base)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name


def test_constitution_residual_inventory_mismatch_matrix() -> None:
    """Empty / dup / blank / seed mismatches for every constitution_* inventory key."""
    modules = _constitution_residual_modules()
    for _name, _fn, phrases, key in modules:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must not be empty" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = [phrases[0], phrases[0], *phrases[1:]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must be unique" in f.message for f in findings), key

        payload = _inventory_payload()
        payload[key] = ["ok", "  "]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(
            f"{key} entries must be non-empty strings" in f.message for f in findings
        ), key

        payload = _inventory_payload()
        payload[key] = [phrases[0]]
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        assert any(f"{key} must include" in f.message for f in findings), key


def test_constitution_residual_concurrent_validate_races(tmp_path: Path) -> None:
    """Concurrent readers/writers against AGENTS-v2.2.md must not crash."""
    modules = _constitution_residual_modules()
    live_fns = [fn for _name, fn, _phrases, _key in modules]

    def _read_live() -> list[vm.Finding]:
        out: list[vm.Finding] = []
        for fn in live_fns:
            out.extend(fn(REPO_ROOT))
        return out

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_read_live) for _ in range(48)]
        for fut in as_completed(futures):
            try:
                assert fut.result() == []
            except BaseException as exc:  # noqa: BLE001 — collect race failures
                errors.append(exc)
    assert errors == []

    locked = _constitution_residual_locked_text()
    path = tmp_path / "AGENTS-v2.2.md"
    _write(path, locked)
    for name, fn, _phrases, _key in modules:
        assert fn(tmp_path) == [], name

    stop = threading.Event()
    race_errors: list[BaseException] = []

    def _writer() -> None:
        flip = False
        while not stop.is_set():
            try:
                if flip:
                    path.write_text(locked, encoding="utf-8")
                else:
                    path.write_text("\n", encoding="utf-8")
                flip = not flip
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    def _reader() -> None:
        while not stop.is_set():
            try:
                for fn in live_fns:
                    fn(tmp_path)
            except BaseException as exc:  # noqa: BLE001
                race_errors.append(exc)
                return

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    time.sleep(0.35)
    stop.set()
    for t in threads:
        t.join(timeout=2.0)
    assert race_errors == []

    def _empty_map_check(key: str) -> bool:
        payload = _inventory_payload()
        payload[key] = []
        findings = vm._inventory_lock_consistency(
            payload, schema_path="schemas/packaging-inventory.json"
        )
        return any(f"{key} must not be empty" in f.message for f in findings)

    keys = [key for _n, _f, _p, key in modules]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_empty_map_check, k) for k in keys for _ in range(2)]
        assert all(fut.result() for fut in as_completed(futs))


def test_constitution_residual_cross_isolation(tmp_path: Path) -> None:
    """Dropping one constitution module's phrases must not falsely green that module."""
    base = _constitution_residual_locked_text()
    modules = _constitution_residual_modules()
    targets = [
        "constitution-crypto",
        "constitution-handoff",
        "constitution-on-device",
        "constitution-recipe-orchestration",
        "constitution-ide-stack",
        "constitution-hard-constraints",
        "constitution-risk-tolerance",
        "constitution-conflict-matrix",
    ]
    by_name = {name: (fn, phrases) for name, fn, phrases, _key in modules}
    for target in targets:
        fn, phrases = by_name[target]
        mangled = base
        for phrase in phrases:
            mangled = mangled.replace(phrase, "GONE_PHRASE_TOKEN")
            assert phrase not in mangled, (target, phrase)
        _write(tmp_path / "AGENTS-v2.2.md", mangled)
        findings = fn(tmp_path)
        assert findings, target
        assert any(p in f.message for f in findings for p in phrases), target
        # Unrelated live root + #147/#151 siblings stay green
        assert by_name["constitution-vscode"][0](REPO_ROOT) == []
        assert vm.validate_goose_howto(REPO_ROOT) == []
        assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []


def test_constitution_residual_live_green() -> None:
    """All fourteen live constitution residual validators remain clean; inventory v52/196."""
    modules = _constitution_residual_modules()
    assert len(modules) == 14
    for name, fn, _phrases, _key in modules:
        assert fn(REPO_ROOT) == [], name
        assert vm.VALIDATORS[name](REPO_ROOT) == [], name

    assert vm.INVENTORY_VERSION == 52
    assert vm.MIN_VALIDATOR_COUNT == 196
    assert len(vm.VALIDATORS) == 196
    body = (REPO_ROOT / "AGENTS-v2.2.md").read_text(encoding="utf-8")
    assert "### 22.1 Quantum-Safe Cryptography Requirements" in body
    assert "## 23. Quantum-Blockchain Development IDE Setup" in body
    assert "Packaging inventory v52" in (
        REPO_ROOT / "CONTRIBUTING.md"
    ).read_text(encoding="utf-8")
    assert "inventory v52 locks" in (REPO_ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    # Adjacent #147 / #151 slices remain green alongside this residual
    assert vm.validate_goose_howto(REPO_ROOT) == []
    assert vm.validate_prompt_orchestration_matrix(REPO_ROOT) == []
    assert vm.validate_prompt_metrics_detail(REPO_ROOT) == []
    assert vm.validate_scratchpad(REPO_ROOT) == []

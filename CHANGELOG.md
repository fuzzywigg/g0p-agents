# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- Agent prompts **v26** deepeners (post-#52): `prompt-roles`, `prompt-sections`,
  `prompt-usage` validators; AGENT-PROMPTS.md four-agent role/template heading
  locks, shared specialist/orchestrator section heading locks, and Usage
  Instructions / Integration with AGENTS.md locks; consistency deepeners for
  `prompt_roles_required_phrases` / `prompt_sections_required_phrases` /
  `prompt_usage_required_phrases` (91 total; historic four only — agent prompts
  slice, not goose recipes, README honesty, PR-template, contributing,
  issue-template, scratchpad, postmortem, archive snapshot, security policy,
  routing/identity, or Dependabot)

- Goose recipes **v25** deepeners (post-#51): `goose-howto`, `goose-state-machine`,
  `goose-naming` validators; GOOSE-RECIPES.md How to Use individual/master
  `goose run` path locks, Scratchpad State Machine locks, and Recipe Naming
  Convention / Adding New Recipes locks; consistency deepeners for
  `goose_howto_required_phrases` / `goose_state_machine_required_phrases` /
  `goose_naming_required_phrases` (88 total; historic four only — goose recipes
  slice, not README honesty, PR-template, contributing, issue-template,
  scratchpad, postmortem, archive snapshot, security policy, routing/identity,
  or Dependabot)

- README archive honesty **v24** deepeners (post-#47): `readme-honesty`,
  `readme-historic`, `readme-contents` validators; README.md archived-reference /
  not-a-live-hive / prompt-fiction locks, Historic prompt set four-agent role
  locks, and Contents / Cloud agents / Manifest validation / License section
  locks; consistency deepeners for `readme_honesty_required_phrases` /
  `readme_historic_required_phrases` / `readme_contents_required_phrases`
  (85 total; historic four only — README honesty slice, not PR-template,
  contributing, issue-template, scratchpad, postmortem, archive snapshot,
  security policy, routing/identity, or Dependabot).

- PR template **v23** deepeners (post-#45): `pr-summary`, `pr-acceptance`,
  `pr-notes` validators; pull_request_template.md Summary/Problem guidance locks,
  Changes/Acceptance Criteria checkbox locks, and Notes for Reviewer / routing
  placeholder locks; consistency deepeners for `pr_summary_required_phrases` /
  `pr_acceptance_required_phrases` / `pr_notes_required_phrases` (82 total;
  historic four only — PR template slice, not contributing, issue-template,
  scratchpad, postmortem, archive snapshot, security policy, routing/identity,
  or Dependabot). Also syncs `ci_required_actions` pins to setup-python@v7 /
  upload-artifact@v7 after merged Dependabot #17 (inventory lock only).

- Contributing guide **v22** deepeners (post-#44): `contributing-who`,
  `contributing-branches`, `contributing-pr` validators; CONTRIBUTING.md Who Can
  Contribute locks + Branch Strategy table locks + PR Requirements / Governance
  locks; consistency deepeners for `contributing_who_required_phrases` /
  `contributing_branch_required_phrases` / `contributing_pr_required_phrases`
  (79 total; historic four only — contributing slice, not issue-template,
  scratchpad, postmortem, archive snapshot, security policy, routing/identity,
  or Dependabot)

- GitHub issue-template **v21** deepeners (post-#42): `issue-metadata`,
  `issue-routing`, `bug-repro` validators; shared Status/Tier/Created/Owner/Edit
  policy locks across bug/feature/agent-task templates; Agent Surface Routing
  field locks (Surface/Rationale/Priority/Branch/Dependencies); bug Steps to
  Reproduce / Expected / Actual Behavior locks; consistency deepeners for
  `issue_metadata_required_phrases` / `issue_routing_required_phrases` /
  `bug_repro_required_phrases` (76 total; historic four only — issue-template
  slice, not scratchpad, postmortem, archive snapshot, security policy,
  routing/identity, or Dependabot)

- Scratchpad coordination **v20** deepeners (post-#41): `scratchpad-intro`,
  `scratchpad-format`, `scratchpad-task-meta` validators; scratchpad.txt intro/
  update mandate locks + Format legend locks + Task Repo Hydration meta locks;
  consistency deepeners for `scratchpad_intro_required_phrases` /
  `scratchpad_format_required_phrases` / `scratchpad_task_meta_required_phrases`
  (73 total; historic four only — scratchpad coordination slice, not postmortem,
  archive snapshot, security policy, routing/identity, or Dependabot)

- Postmortem decision-log **v19** deepeners (post-#38): `postmortem-intro`,
  `postmortem-fields`, `postmortem-next-steps` validators; postmortem.md intro/
  mandate locks + Decision entry field locks + Next Steps surface locks;
  consistency deepeners for `postmortem_intro_required_phrases` /
  `postmortem_field_required_phrases` / `postmortem_next_steps_required_phrases`
  (70 total; historic four only — postmortem slice, not archive snapshot,
  security policy, routing/identity, or Dependabot)

- Archive snapshot **v18** deepeners (post-#36): `implementation-quickstart`,
  `execution-specialists`, `hydration-list-b` validators; IMPLEMENTATION-GUIDE
  Quick Start surface locks + EXECUTION-SUMMARY four-specialist table locks +
  hydration LIST B HITL question locks; consistency deepeners for
  `implementation_quickstart_required_phrases` /
  `execution_specialists_required_phrases` / `hydration_list_b_required_phrases`
  (67 total; historic four only — Dec 2025 archive snapshot slice, not security
  policy or routing/identity deepeners)

- Security policy **v17** deepeners (post-#35): `security-supported`,
  `security-reporting`, `security-standards` validators; SECURITY.md Supported
  Versions surface locks + Reporting a Vulnerability channel locks + Security
  Standards domain-row locks; consistency deepeners for
  `security_supported_required_phrases` / `security_reporting_required_phrases` /
  `security_standards_required_phrases` (64 total; historic four only — security
  policy slice, not packaging-inventory meta or routing/identity deepeners)

- Agent routing / identity / escalation **v16** deepeners (post-#33):
  `routing-rationales`, `claude-metadata`, `escalation-usage` validators; CLAUDE.md
  routing-matrix rationale column locks + header Status/Tier/Owner/Created/Edit/
  Canonical locks + escalation usage intro / fenced `text` block / placeholder field
  locks; consistency deepeners for `routing_matrix_rationale_phrases` /
  `claude_metadata_required_phrases` / `escalation_usage_required_phrases`
  (61 total; historic four only — routing/identity slice, not packaging-inventory
  meta or Dependabot)

- Agent routing / identity / escalation **v15** deepeners (post-#32): `routing-matrix`,
  `repo-identity`, `escalation-format` validators; CLAUDE.md Agent Routing Matrix
  task-row locks + Repo Identity north-star/purpose locks + Escalation Format
  banner/field locks; consistency deepeners for `routing_matrix_required_phrases` /
  `repo_identity_required_phrases` / `escalation_block_required_phrases` (58 total;
  historic four only — routing/identity slice, not packaging-inventory meta or CI
  command deepeners)

- Packaging inventory **v14** deepeners (post-#31): `state-residency`, `key-files`,
  `pr-routing` validators; CLAUDE.md State Residency Rules + Key Files table locks;
  PR template Agent Surface Routing field locks (Surface / Issue / Branch /
  Priority); consistency deepeners for `state_residency_required_phrases` /
  `key_files_required_entries` / `pr_routing_required_fields` (55 total; historic
  four only — archive governance slice, not CI command deepeners)

- Packaging inventory **v13** deepeners (post-#30): `ci-pip-install`, `ci-pip-check`,
  `ci-pytest` validators; CI `python -m pip install -r requirements-dev.txt` +
  `python -m pip check` command locks; pytest cov/junitxml required marker locks;
  coverage `fail_under` exact equality lock (99); consistency deepeners for
  `ci_pip_install_command` / `ci_pip_check_command` /
  `ci_pytest_required_markers` (52 total; historic four only)

- Packaging inventory **v12** deepeners (post-#29): `ci-setup-python`, `ci-ruff`,
  `license-mit` validators; CI setup-python `cache: pip` +
  `cache-dependency-path` structured locks; `ruff check scripts tests` CI
  command lock; LICENSE MIT phrase locks (header / grant / AS IS); consistency
  deepeners for `ci_setup_python_cache` / `ci_ruff_check_command` /
  `license_required_phrases` (49 total; historic four only)

- Packaging inventory **v11** deepeners (post-#28): `ci-runs-on`, `ci-artifacts`,
  `actionlint-shell` validators; CI `runs-on` ubuntu-latest + artifact
  paths/if-no-files-found + actionlint shell/step-id locks; pyproject
  description/readme + pytest testpaths/pythonpath + coverage source locks;
  consistency deepeners for ci_runs_on / ci_artifact_paths /
  ci_artifact_if_no_files_found / ci_actionlint_shell / ci_actionlint_step_id /
  pyproject_description / pyproject_readme / pytest_testpaths /
  pytest_pythonpath / coverage_source (46 total; historic four only)

- Packaging inventory **v10** deepeners (post-#27): `link-check`, `ci-job-names`,
  `github-agent-desc` validators; CI lychee args/fail + markdown-lint
  globs/config + cache-dependency-path + job display-name locks; GitHub agent
  description lock; pyproject version/license/line-length/src + pytest addopts +
  coverage show_missing/skip_empty locks; markdownlint MD013 tables/code_blocks
  locks; consistency deepeners for ci_job_display_names / pyproject_ruff_src /
  github_agent_description / ci_link_check_args (43 total; historic four only)

- Packaging inventory **v9** deepeners (post-#26): `issue-names`, `readme-badges`,
  `quarterly-review` validators; issue template name/about locks; README badge
  phrases; CLAUDE quarterly-review phrases; CI workflow name + actionlint/text
  markers; markdownlint MD025/MD033/MD024 siblings_only locks; pyproject ruff
  lint.select lock; expanded Cursor install refs matching live
  `environment.json`; SECURITY reporting phrases; consistency deepeners for
  issue_template_names/abouts, badge/quarterly/text-marker/lint-select sets
  (40 total; historic four only)

- Packaging inventory **v8** deepeners (post-#25): `claude`, `recipe-titles`,
  `ci-actions` validators; historic recipe title locks; CI required action pins;
  CLAUDE identity/escalation-format phrases; Dependabot directory set inventory
  lock (file untouched); pyproject project-name lock; consistency deepeners for
  recipe_titles / ci_required_actions / dependabot_directories (37 total;
  historic four only)

- Packaging inventory **v7** deepeners (post-#23): hydration / execution-summary /
  implementation-guide validators; Dependabot group-name locks (file untouched);
  CI cancel-in-progress / fail-fast inventory bools; coverage branch lock; Cursor
  install required refs; license copyright marker; historic-four identity
  consistency (specialists + OrchestrationAgent); CI step markers
  `Lock inventory` / `INVENTORY_VERSION` (34 total; historic four only)

- Packaging inventory **v6** locks (rebased onto #22): changelog/postmortem/gitignore/negative-
  constraint phrases, Dependabot ecosystem set, historic recipe version,
  markdownlint MD013 line_length, CI concurrency prefix + artifact `if`,
  pyproject ruff target-version, GitHub agent name, LICENSE copyright holder,
  agentic_flows allow-list, README honesty phrases; plus #22 deepeners for
  specialist agents, schema `$schema`/`$id` prefixes, CLAUDE required sections,
  contributing branch surfaces, scratchpad status markers
- New validators: `changelog`, `postmortem`, `gitignore`, `negative-constraints`
  (31 total; historic four only)
- Coverage gate raised to **99%** (from #22) while keeping the v6 validator set
- CI deepeners: validator-count ≥31 + inventory v6 registry lock step
- Schema deepeners: Goose recipe `version` const `1.0.0`; Cursor env
  `additionalProperties: false`; markdownlint MD013.line_length const 200

- Packaging inventory **v5** locks: bug/feature template headings, archive-doc /
  yaml-config sets, cursor env name, Dependabot weekly schedule, CI permissions /
  artifact prefix / PR branch, pyproject requires-python, markdownlint default,
  scratchpad phrases, validator registry names + internal lock consistency
- New validators: `bug-template`, `feature-template` (27 total; historic four only)
- CI deepeners: refuse orphan jobs, require `contents: read` per job,
  `cancel-in-progress`, `fail-fast: false`, artifact prefix, PR→`alpha`,
  validator-count ≥27 + inventory v5 registry lock step
- Manifest step marker locks: `Smoke each`, `--only`, `junitxml`

- Packaging inventory **v4** locks: routing surfaces, constitution headings,
  prompt system-header / escalation markers, security + contributing phrases,
  agent-task issue headings, orchestration recipe name, agent-token scan doc set
- New validators: `constitution`, `routing`, `security`, `contributing`,
  `agent-task` (25 total; still only the historic four specialists)
- Prompt deepeners: ordered `# {Agent} System Prompt` fences + specialist /
  orchestration escalation identity locks
- Goose schema: `goose_provider` / `goose_model` const-locked to historic values;
  GitHub custom-agent frontmatter `additionalProperties: false`
- Coverage gate raised to **98%** (no workflow file edits that wave)

- Packaging inventory **v3** locks: recipe bindings, primary agents, schema file
  set, CI Python matrix, manifest step markers, dev packages, GitHub agent /
  issue-template file sets, PR template headings, historic Goose settings,
  coverage + validator-count floors
- New validators: `agent-tokens`, `pr-template`, `requirements-dev`, `license`,
  `readme` (20 total; no invented specialists)
- Goose deepeners: refuse orphan on-disk recipes, require all `goose run`
  examples, lock historic `anthropic` / `claude-opus-4` + `builtin/developer`
- Schema meta: enforce Draft 2020-12 `$schema` + canonical `$id` URIs
- CI: `pip check`, validator-count gate (≥20), exact Py 3.11/3.12/3.13 matrix
- Deepened packaging validators (wave 2): markdownlint + scratchpad + pyproject
  checks, recipe name↔file bindings, orphan-schema detection, non-empty agent /
  issue-template bodies, Dependabot pip ecosystem requirement, inventory lock for
  agents/recipes/CI jobs, Goose extension-type enum + timeout bounds
- `schemas/markdownlint.schema.json`; packaging inventory v2 lock fields
- CI: Python 3.13 matrix cell, per-validator smoke loop, junit artifact
- Expanded packaging validators: schema meta-check, packaging inventory,
  issue-template + Dependabot schemas, recipe/agent lock (no invented agents),
  cross-doc agent presence, CI job presence, Cursor install path refs,
  `goose run` path consistency
- `schemas/packaging-inventory.json` (+ schema), `github-issue-template.schema.json`,
  `dependabot-v2.schema.json`
- `pyproject.toml` — pytest / ruff / coverage config for validation tooling
- CI: Python 3.11/3.12 matrix, ruff, coverage gate, actionlint, JSON validation report artifact
- `schemas/` + `scripts/validate_manifests.py` + `tests/` — structural validation for documented Goose recipes, Cursor `environment.json`, GitHub custom-agent frontmatter, and known YAML configs
- `requirements-dev.txt` — jsonschema / PyYAML / pytest / pytest-cov / ruff for local + CI validation
- CI job `manifest-validate` (pytest + `scripts/validate_manifests.py`) in `.github/workflows/ci.yml`
- `.cursor/environment.json` — minimal Cloud Agent install check (docs archive; no runtime services)
- `.gitignore` — exclude local env/secret and editor noise
- `LICENSE` — MIT License (copyright 2026 Andrew Pappas / smtp.eth)
- `CLAUDE.md` — agent routing matrix and repo-specific instructions
- `CONTRIBUTING.md` — contribution guidelines for ecosystem agents and humans
- `SECURITY.md` — vulnerability reporting and security standards
- `CHANGELOG.md` — this file
- `docs/agent-hydration.md` — Phase 1–6 hydration findings report
- `.github/ISSUE_TEMPLATE/` — bug, feature, and agent-task issue templates
- `.github/pull_request_template.md` — structured PR template
- `agentic_flows/scratchpad.txt` — agent coordination state machine
- `postmortem.md` — incident and decision log (initialized)
- `.github/workflows/ci.yml` — markdown lint and link check CI pipeline

### Changed

- Inventory schema minimum version is **7**; CI validator-count gate raised to ≥34; coverage gate **99%**
- Inventory schema minimum version is **6**; CI validator-count gate raised to ≥31; coverage gate **99%**
- Inventory schema minimum version is **5**; CI validator-count gate raised to ≥27
- Coverage gate raised to 97%; inventory schema minimum version is 3
- Coverage gate raised to 95%; Dependabot now tracks pip (`requirements-dev.txt`)
  alongside github-actions
- Manifest CI requires actionlint job + ruff/`--cov` step markers and a multi-version
  Python matrix
- Expanded CI workflow: Python matrix, ruff, coverage, actionlint, validation artifacts
- Aligned `GOOSE-RECIPES.md` master `goose run` path with declared recipe **File**
- CI workflow renamed to cover manifest validation in addition to markdown lint/link check
- CI `pull_request` trigger targets `alpha` (default branch), not `main`
- `CONTRIBUTING.md` branch strategy aligned with live default branch `alpha`

---

## [0.1.0] — 2025-12-13

### Added

- `README.md` — public archive description
- `AGENTS-v2.2.md` — agent constitution with quantum-blockchain sections
- `AGENT-PROMPTS.md` — specialist agent system prompts (4 agents)
- `GOOSE-RECIPES.md` — Goose YAML recipe templates
- `IMPLEMENTATION-GUIDE.md` — step-by-step setup guide
- `EXECUTION-SUMMARY.md` — implementation summary

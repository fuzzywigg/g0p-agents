# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- CI/markdownlint residual **tests-only** leftover deepeners after tip through
  **#248** (actionlint/linkcheck leftover after #242) / **#242** / **#236** /
  **#229** / **#224** / **#219** / **#209** / **#208** / **#202** / **#200** /
  **#195** / **#188** / **#187** / **#186** (EXISTING six fixtures —
  `markdownlint` / `ci-setup-python` / `ci-ruff` / `ci-pip-install` /
  `ci-pip-check` / `ci-pytest` — no invented product / workflow / inventory
  bump): `.markdownlint.yaml` ↔ `schemas/markdownlint.schema.json` required-key
  and const lock parity, per-lock schema const mismatch, YAML structural and
  type edges (root list / string consts / empty nested maps / int-boolish
  MD025/MD033 / MD013 sequence / null consts / MD024 list / float line_length /
  directory-not-file), remaining `ci.yml` assertion matrix (setup-python
  cache/with and cache int/list type and dep-path int, ruff, pip install/check,
  pytest markers, empty/scalar steps), inventory path/schema/yaml drops and
  leftover types, `--only` isolation, concurrent races, exact Finding equality
  and case/BOM/NBSP lookalikes, pytest per-marker drop and ruff/pip lookalike
  commands, nested MD013/MD024 key drops and simultaneous multi-lock drop,
  dual-surface concurrent races, tip-after-#248 deepeners (exact CI fixture
  Finding equality, ZWSP/soft-hyphen/CRLF lookalikes, simultaneous multi-lock
  exact drops, triple-surface races, quoted bool + cache-dep lookalikes, empty
  MD013/MD024 maps + pytest marker reorder/junit lookalike, `--only` subset vs
  #248 siblings), and tip isolation against
  #248/#242/#236/#229/#224/#219/#209/#208/#202/#200 siblings. Historic four
  only; inventory unchanged (v52 / 196). Distinct from merged #248
  (actionlint/linkcheck leftover), #242 (prompts+flows leftover), #236
  (actionlint/linkcheck leftover), #229 (hydration/security+handoff edges),
  #224 (prompts+flows leftover), #219 (goose-schema), #209 leftover suite,
  #208 (goose-schema), #202/#200 (listform+flows), #195/#188/#186
  (actionlint/link-check), open #253 (prompts+flows after #248), closed
  CONFLICTING #250/#240/#237/#233/#220/#214/#210/#204/#201/#196 (same leftover
  vs stale tips), and historic v12/v13 setup-python/ruff/pip/pytest edges.

- Actionlint/workflow + link-check residual **tests-only** leftover deepeners
  after tip through **#242** (prompts+agentic_flows leftovers after #236) /
  **#236** / **#229** / **#224** / **#219** / **#209** / **#208** / **#202** /
  **#200** / **#195** / **#188** (EXISTING seven CI fixtures — `ci` /
  `ci-actions` / `link-check` / `actionlint-shell` / `ci-job-names` /
  `ci-runs-on` / `ci-artifacts` — no invented product / inventory bump; prefer
  actionlint+linkcheck niche, not markdownlint/#240): exact Finding equality
  for missing/dir-not-file `ci.yml`, missing `on:` / PR null|true / branches
  scalar / orphan job / empty jobs map, cancel|fail-fast|lychee-fail string
  identity edges, case/BOM/NBSP shell + id-hyphen + group-prefix + Warn
  lookalikes, all-four-jobs `contents: write` + contents-None, empty
  workflow/job names + empty path string, python-version reorder +
  upload-artifact `Always()` lookalike, globs/cache lookalikes via
  `link-check` fixture only, drop-job + self-hosted `runs-on`, artifact path
  int-sequence unexpected, per-pin/per-marker exact drops, non-dict step
  skip-green, dual-surface simultaneous fails, concurrent dual-mangle races,
  inventory leftover types + `run_all --only` isolation, tip isolation vs
  #242/#236/#229/#224/#219/#240 siblings. Historic four only; inventory
  unchanged (v52 / 196). Distinct from merged #242 (prompts+flows leftover),
  #236 (after229 leftover suite), #229 (hydration/handoff edges), #224
  (prompts+flows), #219 (goose-schema), #209, #195/#188/#186 (prior
  actionlint leftovers), open #240 (CI/markdownlint niche), closed
  CONFLICTING #232/#226/#218/#215/#211/#206 (same leftover vs stale tips),
  closed #244 (same leftover vs deleted head-ref), and historic v10/v11 edges.

- Prompts + agentic_flows residual **tests-only** unsaturated edge deepeners after
  tip through **#236** (actionlint leftover after #229) / **#229** / **#224** /
  **#219** / **#209** / **#208** / **#202** / **#200** / **#195** / **#188**
  (EXISTING nineteen fixtures — twelve list-form sibling `prompt-*` + seven
  agentic_flows `goose` / `recipe-agents` / `recipe-titles` / `scratchpad*` — no
  invented v53 list-form product / inventory bump): exact GOOSE missing Finding
  equality + directory-not-file on `GOOSE-RECIPES.md`, ZWSP / soft-hyphen / CRLF
  lookalikes beyond #224 case/BOM/NBSP, exact locked-phrase message formats +
  simultaneous multi-surface drops (living-docs / cannot-delegate / scratchpad /
  GOOSE_DOCS), scratchpad checkbox / status-marker / identifying-header exact
  messages with listform↔goose isolation, on-disk must-live-at + invented yaml +
  recipe-agents invent-token leftovers, inventory type leftovers (int/null/mapping)
  and `run_all --only` subset, triple-doc concurrent races, and tip isolation against
  #236/#229/#224/#219/#209/#208/#202 siblings. Historic four only; inventory
  unchanged (v52 / 196). Distinct from merged #236 (actionlint leftover), #229
  (hydration/security edges), #224 (prior prompts+flows leftover suite), #219
  (goose-schema leftover), #209 (hydration/security+handoff), #202/#200
  (listform+flows leftover / residual suites), and closed CONFLICTING
  #238/#235/#230/#221/#223 tip refills.

- Actionlint/workflow + link-check residual **tests-only** leftover deepeners
  after tip through **#229** (hydration/security+handoff edges after #224) /
  **#224** / **#219** / **#209** / **#208** / **#202** / **#200** / **#195** /
  **#188** (EXISTING seven CI fixtures — `ci` / `ci-actions` / `link-check` /
  `actionlint-shell` / `ci-job-names` / `ci-runs-on` / `ci-artifacts` — no
  invented product / inventory bump; prefer actionlint+linkcheck niche, not
  markdownlint): scalar `on:`, empty `pull_request` / branches, concurrency
  scalar/group-absent/empty/cancel-absent, jobs sequence, empty permissions /
  contents-absent, strategy/version leftover types, lychee `with: {}` +
  args-only/fail-only, markdown-lint scalar/partial via `link-check` only,
  GITHUB_TOKEN env drop green, actionlint scalar/empty/extra shell, missing
  name/runs-on + runs-on list, if-no-files-found absent + path list
  missing/extra, `ci-actions` parse-error pin scan, inventory leftover types,
  `run_all --only` isolation, tip isolation vs #229/#224/#219 siblings.
  Historic four only; inventory unchanged (v52 / 196). Distinct from merged
  #229 (hydration/handoff edges), #224 (prompts+flows), #219 (goose-schema),
  #209, #195/#188/#186 (prior actionlint leftovers), closed CONFLICTING
  #232/#226/#218/#215/#211/#206 (same leftover vs stale tips), closed
  #220/#214/#210 (CI/markdownlint slice), and historic v10/v11 edges.

- Hydration↔security + handoff unsaturated **tests-only** edge deepeners after tip
  through **#224** (prompts+agentic_flows leftover after #219) / **#219** /
  **#209** / **#208** / **#202** / **#200** / **#195** / **#188** / **#187** /
  **#186** / **#184** / **#181** (EXISTING twenty-two fixtures —
  `hydration-phase4` + ten `security*` and seven handoff-cluster
  `constitution-*` + four `scratchpad*` — no invented product / inventory bump):
  exact missing-file message + Finding.path locks, remaining handoff-cluster
  section-present (multichain / recipe-orchestration / scratchpad-state /
  conflict-matrix), SECURITY section-header drop isolation with
  hydration+handoff green, ASCII-arrow / NBSP / Memory-footprint / secrets-case
  lookalikes + historic-four SECURITY allowlist, exact locked-phrase message
  formats + simultaneous dual-phrase drops, scratchpad exact
  empty/header/checkbox/status-marker messages, inventory seed mismatches +
  `run_all --only` subset isolation, and tip live-green vs
  #224/#219/#209/#208/#202/#200 siblings. Historic four only; Packaging
  inventory unchanged (v52 / 196). Distinct from merged #209 leftover suite
  (four-doc isolation / case-BOM / inventory-types / concurrent races), merged
  #219 (goose-schema leftover), merged #224 (prompts+agentic_flows leftover),
  closed CONFLICTING #213/#217/#225 tip refills, #184 (hydration↔security +
  goose tip), #181 (memory-handoff), and not a v53 invent sibling.

- Prompts + agentic_flows residual **tests-only** leftover deepeners after tip
  through **#219** (goose-schema leftover after #209) / **#209** / **#208** /
  **#202** / **#200** / **#195** / **#188** (EXISTING nineteen fixtures —
  twelve list-form sibling `prompt-*` + seven agentic_flows `goose` /
  `recipe-agents` / `recipe-titles` / `scratchpad*` — no invented v53
  list-form product / inventory bump): exact Finding.path + missing-file
  equality (incl. `prompt-usage` asymmetry), directory-not-file for
  AGENT-PROMPTS + scratchpad, section-present/phrases-absent for all twelve
  listform siblings + scratchpad format/task-meta, case/BOM/NBSP lookalikes,
  exact section/special-lock drop messages + simultaneous multi-section drops,
  scratchpad empty Finding equality, prompts↔flows↔goose cross-isolation,
  inventory seed mismatches + `run_all --only` subset isolation, concurrent
  dual-surface races, and tip live-green vs #219/#209/#208/#202/#200 siblings.
  Historic four only; Packaging inventory unchanged (v52 / 196). Distinct from
  merged #219 (goose-schema leftover), #209 (hydration/security+handoff),
  #202 (exact phrase / goose-run / on-disk leftover), #200 (listform+flows
  residual suite), closed CONFLICTING #223/#221 (same leftover on pre-#219
  tip — tip relaunch here), closed CONFLICTING #198/#194/#193/#190,
  #153/#159/#164 invent-v53, and not a v53 invent sibling.

- Goose-recipe schema leftover **tests-only** deepeners after tip through **#209**
  (hydration/security+handoff leftover after #208) / **#208** / **#202** /
  **#200** / **#195** / **#188** / **#187** / **#186** / **#184** (goose-schema
  tip) / **#172** (goose-schema residual suite) (EXISTING three fixtures —
  `goose` / `recipe-agents` / `recipe-titles` plus
  `schemas/goose-recipe.schema.json` + `GOOSE-RECIPES.md` — no invented product
  / inventory bump): unsaturated reject leftovers (`timeout` null, name
  float/dollar, empty settings/recipe objects, version bool/list, model bool,
  instructions int, extension type `Builtin`), ACCEPT leftovers (extension name
  max 128, title min, mixed transports, deep schema self-locks for
  const/enum/minLength), live fenced YAML→schema round-trip, on-disk
  parse/historic-settings/`must live at` leftovers, **File** without `./` +
  `goose run` `.yml` path leftovers, recipe-titles missing-doc message
  asymmetry, non-string fence name / wrong-title exact / recipe non-dict agent
  skip / primary-in-title green, inventory `recipe_primary_agents` /
  `expected_recipe_names` leftovers, schema-file missing `$id` + JSON parse
  residuals, CI workflow smoke that still lists/runs the goose trio, concurrent
  races, and tip isolation against #209/#208/#202/#200/#195 siblings. Historic
  four only; Packaging inventory unchanged (v52 / 196 validators). Distinct from
  merged #209 (hydration/security+handoff), #208 (prior goose-schema leftover
  suite), closed CONFLICTING #212 (same leftover on pre-#209 tip — tip relaunch
  here), closed CONFLICTING #197 (schema-only leftover tip-burned in #208/#212
  lineage), #202/#200 (listform+flows), #184 (tip type matrix), #172 (residual
  suite), #147 (nine goose-* phrase locks), and not a v53 invent sibling or
  Dependabot bump.

- Hydration↔security + memory-slot/agent-handoff residual **tests-only** leftover
  deepeners after tip through **#208** (goose-schema leftover after #200) /
  **#202** / **#200** / **#195** / **#188** / **#187** / **#186** / **#184** /
  **#181** (EXISTING twenty-two fixtures — `hydration-phase4` + ten
  `security` / `security-*` + four `scratchpad*` + seven handoff-cluster
  `constitution-*` — no invented memory-slot / handoff-timeout /
  hydration-security-cross product / inventory bump): four-doc isolation,
  section-present/phrases-absent, missing vs directory-not-file, case/BOM
  lookalikes, invented-agent isolation, inventory leftover types,
  `run_all --only` subset, concurrent four-doc races, and tip isolation
  against #208/#202/#200/#195/#188 siblings. Historic four only; inventory
  unchanged (v52 / 196). Distinct from merged #208 (goose-schema leftover),
  #202/#200 (listform+flows), #184 (hydration↔security + goose-schema),
  #181 (memory-handoff residual), closed #207/#205/#189/#191/#183/#179, and
  #187 (docs-cross tip).

- Goose-recipe schema leftover **tests-only** deepeners after tip through **#202**
  (prompts+agentic_flows leftover after #200) / **#200** / **#195** / **#188** /
  **#187** / **#186** / **#184** (goose-schema tip) / **#172** (goose-schema
  residual suite) (EXISTING three fixtures — `goose` / `recipe-agents` /
  `recipe-titles` plus `schemas/goose-recipe.schema.json` + `GOOSE-RECIPES.md`
  — no invented product / inventory bump): root/name type + pattern leftovers
  beyond #172/#184 matrices, settings/version/title/prompt type leftovers,
  extension item-shape leftovers (missing type / non-object items / optional
  timeout green), `GOOSE-RECIPES.md` parse/mapping/unquoted-**File**/single-run/
  extra-run leftovers, titles/agents phrase + on-disk `.yml`/list mapping
  leftovers, inventory lock leftovers (`historic_recipe_version` / swapped
  bindings / extension_name), schema-file `$schema`/`$id`/root residuals,
  concurrent races, and tip isolation against #202/#200/#195/#184 siblings.
  Historic four only; Packaging inventory unchanged (v52 / 196 validators).
  Distinct from merged #202/#200 (listform+flows leftovers), #184 (goose-schema
  tip type matrix), #172 (goose-schema residual suite), #147 (nine goose-*
  phrase locks), and not a v53 invent sibling, contributing/goose-howto
  leftover, or Dependabot bump.

- Prompts + agentic_flows residual **tests-only** leftover deepeners after tip
  through **#200** (prompts listform + agentic_flows leftover after #195) /
  **#195** / **#188** / **#187** / **#186** (EXISTING nineteen fixtures —
  twelve list-form sibling `prompt-*` + seven agentic_flows `goose` /
  `recipe-agents` / `recipe-titles` / `scratchpad*` — no invented v53
  list-form product / inventory bump): exact missing-file / locked-phrase
  message locks (incl. `prompt-usage` `AGENT-PROMPTS.md missing` asymmetry),
  multi-phrase simultaneous listform drops, undeclared + missing `goose run`
  path edges, on-disk locked recipe happy path + schema/must-live-at binding
  edges (tmp only; no repo YAML product), scratchpad checkbox / status-marker
  / identifying-header exact messages, `GOOSE_DOCS` packaging phrase drop +
  recipe/allow-list inventory mismatch matrix, prompts↔flows↔GOOSE_DOCS
  cross-isolation, concurrent dual-surface races, and tip isolation against
  #200/#195/#188 siblings. Historic four only; inventory unchanged
  (v52 / 196). Distinct from merged #200 (prior mixed listform+flows suite),
  closed CONFLICTING #198 (flows-only unsaturated edges tip-burned here),
  #194/#193/#190/#153/#159/#164, merged #195/#188 (actionlint leftovers),
  #187 (docs-cross), #151 (prompt-pre-v52), #144 (v52 prompt residuals),
  #181 (memory-handoff), and #147 (goose-recipe).

- Prompts list-form + agentic_flows residual **tests-only** deepeners after tip
  through **#195** (actionlint leftover after #188) / **#188** / **#187** /
  **#186** / **#184** / **#181** (EXISTING nineteen fixtures — twelve
  list-form sibling `prompt-*` + seven agentic_flows `goose` /
  `recipe-agents` / `recipe-titles` / `scratchpad*` — no invented v53
  list-form product / inventory bump): invent-key rejection for closed
  CONFLICTING #153/#159/#164 list-form names, empty/whitespace/header-only
  AGENT-PROMPTS + scratchpad, per-phrase drop matrices, inventory mismatch
  matrix, agentic_flows allow-list / path / binding edges beyond #181/#147,
  prompts↔flows cross-isolation, concurrent dual-surface races, and tip
  isolation against #195/#188/#187/#186 siblings. Historic four only;
  inventory unchanged (v52 / 196). Distinct from closed CONFLICTING
  #194/#193/#190/#153/#159/#164, open #198 (agentic_flows-only leftover),
  merged #195/#188 (actionlint leftovers), #187 (docs-cross), #151
  (prompt-pre-v52), #144 (v52 prompt residuals), #181 (memory-handoff),
  and #147 (goose-recipe).

- Actionlint/workflow + link-check residual **tests-only** leftover deepeners
  after tip through **#188** (actionlint/workflow + link-check leftover) /
  **#187** (docs-cross) / **#186** / **#184** / **#181** / **#178** /
  **#176** / **#174** (EXISTING seven CI fixtures — `ci` / `ci-actions` /
  `link-check` / `actionlint-shell` / `ci-job-names` / `ci-runs-on` /
  `ci-artifacts` — no invented product / inventory bump): `pull_request.branches`
  as a scalar (not a list), non-string `concurrency.group`, non-mapping
  `strategy.matrix` + matrix missing `python-version`, `permissions.contents`
  write on all four jobs, markdownlint missing `with:` on locked yaml,
  setup-python uses-dropped / `with:`-absent cache lock-not-found, scalar
  `steps` on link-check/actionlint, per-job drop from live yaml, jobs empty
  mapping, `ci-actions` name-absent, upload `if:` key absent + path type
  (mapping/int/empty) + upload step deleted, incomplete inventory lists +
  int/empty leftover locks, `run_all --only` isolation, and tip isolation
  against #188/#187/#186 siblings. Historic four only; inventory unchanged
  (v52 / 196). Distinct from merged #188 (prior leftover suite), #187
  (docs-cross tip), #186 (residual suite), #184 (hydration↔security +
  goose-schema), and historic v10/v11 link-check/actionlint edge suites.

- Actionlint/workflow + link-check residual **tests-only** leftover deepeners
  after tip through **#187** (docs-cross) / **#186** (actionlint/workflow +
  link-check) / **#184** / **#181** / **#178** / **#176** / **#174**
  (EXISTING seven CI fixtures — `ci` / `ci-actions` / `link-check` /
  `actionlint-shell` / `ci-job-names` / `ci-runs-on` / `ci-artifacts` — no
  invented product / inventory bump): YAML parse errors across the seven,
  missing `concurrency.group`, scalar `pull_request`, missing permissions
  mapping, matrix python-version single/wrong/absent, per-marker
  `REQUIRED_MANIFEST_STEP_MARKERS` drop, lychee/`markdownlint` missing
  `with:` + globs/config/cache lock-not-found (≠ wrong values), integer
  lychee `fail`, actionlint non-dict steps + shell-absent/id-absent
  explicit msgs, per-pin/per-marker `ci-actions` matrix, all four job
  display names + all four `runs-on`, unexpected extra artifact + upload
  `with:` missing, `run_all --only` subset + inventory type mismatches,
  and tip isolation against #187/#186/#184/#181 siblings. Historic four
  only; inventory unchanged (v52 / 196). Distinct from merged #187
  (docs-cross tip), #186 (prior actionlint/link-check residual suite),
  #184 (hydration↔security + goose-schema), #181 (memory-handoff), #178
  (implementation), #176 (changelog), #174 (contributing), and historic
  v10/v11 link-check/actionlint edge suites.

- Docs-cross tip residual **tests-only** deepeners after tip through **#186**
  (actionlint/workflow + link-check) / **#184** / **#181** / **#178** /
  **#176** / **#174** / **#166** / **#147** (EXISTING contributing /
  changelog / implementation / memory-handoff / execution / goose fixtures
  residual-burned but not tip-burned — no invented product / inventory bump):
  contributing↔goose cross-doc isolation, changelog↔impl/exec/goose/
  contributing cross, implementation↔goose/scratchpad cross,
  memory-handoff↔goose scratchpad-state cross, section-present /
  phrases-absent tip matrix, concurrent multi-doc races, invalid/invented
  tip sibling keys, and tip isolation against #186/#184/#181 siblings.
  Historic four only; inventory unchanged (v52 / 196). Distinct from merged
  #186 (actionlint/link-check), #184 (hydration↔security + goose-schema),
  #181 (memory-handoff residual), #178 (implementation residual), #176
  (changelog residual), #174 (contributing residual), #166 (execution↔goose),
  and #147 (goose-recipe residual).

- Actionlint/workflow + link-check residual **tests-only** deepeners after tip
  through **#184** (hydration↔security + goose-schema) / **#181** / **#178** /
  **#176** / **#174** / post-#172 (EXISTING seven CI fixtures —
  `ci` / `ci-actions` / `link-check` / `actionlint-shell` / `ci-job-names` /
  `ci-runs-on` / `ci-artifacts` — no invented product / inventory bump):
  workflow structural edges beyond v10/v11 (orphan jobs, PR-branch,
  concurrency cancel, permissions, fail-fast, string lychee `fail`, mixed
  actionlint shells), per-lock mangle matrix, inventory mismatch matrix,
  concurrent `ci.yml` races, invalid/invented tip sibling keys, and tip
  isolation against #184/#181/#178/#176/#174 siblings. Historic four only;
  inventory unchanged (v52 / 196). Distinct from merged #184 (hydration↔
  security + goose-schema), #181 (memory-handoff), #178 (implementation),
  #176 (changelog), #174 (contributing), #172 (goose-schema+security), #166
  (execution), and historic v10/v11 link-check/actionlint edge suites.

- Hydration↔security cross + goose-schema tip residual **tests-only** deepeners
  after tip through **#181** (memory-handoff) / **#178** / **#176** / **#174** /
  post-#172 (EXISTING `hydration-phase4` + ten `security` / `security-*` +
  `goose` / `recipe-agents` / `recipe-titles` / `goose-recipe.schema.json`
  edges — no invented product / inventory bump): hydration↔security cross-doc
  isolation (`Add SECURITY.md` / `Add CONTRIBUTING.md` locks), goose-schema tip
  JSON Schema type/missing matrix beyond #172, goose↔security doc mangling
  isolation, concurrent paired-doc races, phase4 inventory mismatch edges,
  invalid/invented tip sibling keys, and tip isolation against #181
  memory-handoff / #178 implementation / #176 changelog / #174 contributing
  siblings. Historic four only; inventory unchanged (v52 / 196). Distinct from
  merged #181 (memory-handoff), #178 (implementation), #176 (changelog), #174
  (contributing), #172 (goose-schema+security residual suite), #166
  (execution↔goose cross), #161 (hydration residual suite), and open
  CONFLICTING #182 tip refill (not MERGEABLE).

- Memory-slot / agent-handoff residual **tests-only** deepeners after tip through
  **#178** (implementation) / post-#176/#174/#172/#166/#161 (EXISTING eleven
  coordination modules — four `scratchpad*` + seven handoff-cluster
  `constitution-*` — no invented memory-slot / handoff-timeout product /
  inventory bump): concurrent dual-doc races, empty/whitespace/header-only
  AGENTS + scratchpad, invalid/invented memory-slot+handoff+goose/security keys,
  per-phrase drop matrix, inventory mismatch matrix, failed rollback / reverse-
  arrow edges, slot-overflow allow-list rejection, and cross-isolation.
  Historic four only; inventory unchanged (v52 / 196). Distinct from merged
  #134 (memory-slot basics), #156 (constitution), #161 (hydration), #166
  (execution), #172 (goose-schema+security), #174 (contributing), #176
  (changelog), #178 (implementation), and open CONFLICTING #179 memory-handoff
  tip refill / closed #136/#173/#177.

- Implementation residual **tests-only** deepeners after tip through **#176**
  (EXISTING eight `implementation-*` phrase-lock validators — historic #101
  leftover sibling; no invented product / inventory bump): concurrent validate
  races, empty/whitespace/header-only `IMPLEMENTATION-GUIDE.md`,
  invalid/invented implementation-timeout keys, per-phrase drop matrix,
  inventory mismatch matrix, and cross-isolation against
  `implementation-guide` / `implementation-quickstart` /
  `implementation-phases` / `implementation-tools` /
  `implementation-success` / `implementation-issues` /
  `implementation-faq` / `implementation-support`. Historic four only;
  inventory unchanged (v52 / 196). Distinct from merged #176 (changelog),
  #174 (contributing), #172 (goose-schema+security), #166 (execution),
  #161 (hydration), #156 (constitution), #151 (prompt-pre-v52),
  #147 (goose-recipe), and closed CONFLICTING #177 memory-slot tip refill.

- Changelog residual **tests-only** deepeners after tip through **#174** / post-#172
  (EXISTING seven `changelog` / `changelog-*` phrase-lock validators — constitution's
  historic Keep-a-Changelog lock sibling from #116; no invented product / inventory bump):
  concurrent validate races, empty/whitespace/header-only `CHANGELOG.md`,
  invalid/invented changelog-timeout keys, per-phrase drop matrix, inventory
  mismatch matrix, and cross-isolation against `changelog` / `changelog-format` /
  `changelog-unreleased` / `changelog-release` / `changelog-preamble` /
  `changelog-changed` / `changelog-initial`. Historic four only; inventory
  unchanged (v52 / 196). Distinct from merged #174 (contributing), #172
  (goose-schema+security), #166 (execution), #161 (hydration), #156 (constitution),
  #151 (prompt-pre-v52), #147 (goose-recipe), and closed CONFLICTING #171 changelog
  tip refill / #150/#158 invent/security siblings.

- Contributing residual **tests-only** deepeners after **#156** tip / post-#172
  (EXISTING ten `contributing` / `contributing-*` phrase-lock validators —
  no invented product / inventory bump): concurrent validate races,
  empty/whitespace/header-only CONTRIBUTING.md, invalid/invented
  contributing-timeout sibling keys, per-phrase drop matrix, inventory
  mismatch matrix (base `contributing_required_phrases` lock-mismatch-only),
  and cross-isolation against `contributing` / `contributing-who` /
  `contributing-branches` / `contributing-pr` / `contributing-issues` /
  `contributing-local` / `contributing-governance` / `contributing-metadata` /
  `contributing-surfaces` / `contributing-ci-honesty`. Historic four only;
  inventory unchanged (v52 / 196). Distinct from merged constitution #156,
  hydration #161, execution #166, goose-schema+security #172, and closed
  CONFLICTING #157/#158/#169 leftovers.

- Goose-recipe schema + security residual **tests-only** deepeners after #166
  tip (EXISTING `goose` / `recipe-agents` / `recipe-titles` +
  `goose-recipe.schema.json` edges, and ten `security` / `security-*`
  phrase-lock validators — no invented product / inventory bump): concurrent
  validate races, empty/whitespace/header-only docs, invalid/invented
  schema/timeout sibling keys, HEAVY JSON Schema edge matrix, fence/binding
  residual matrix, inventory mismatch matrix, security per-phrase drop matrix,
  and cross-isolation. Historic four only; inventory unchanged (v52 / 196).
  Distinct from merged #147 (goose-* phrase locks), #151 (prompt-pre-v52),
  #156 (constitution), #161 (hydration), #166 (execution), and closed
  CONFLICTING #155/#165/#167 tip refills.

- Execution residual **tests-only** deepeners after **#161** tip (EXISTING eight
  `execution-*` phrase-lock validators + distinct execution↔goose cross-doc
  isolation — no invented product / inventory bump): concurrent validate races,
  empty/whitespace/header-only EXECUTION-SUMMARY, invalid/invented
  execution-timeout sibling keys, per-phrase drop matrix, inventory mismatch
  matrix, cross-isolation, historic-four invented-agent fixture edges, and
  goose cross-doc isolation against `execution-summary` /
  `execution-specialists` / `execution-timeline` / `execution-technologies` /
  `execution-workflow` / `execution-ide` / `execution-innovations` /
  `execution-next48`. Historic four only; inventory unchanged (v52 / 196).
  Distinct from merged hydration #161, constitution #156, goose-recipe #147,
  prompt-pre-v52 #151, prompt-v52 #144, closed CONFLICTING #154/#160/#162
  execution tip refills, and orch-timeout invent drafts.

- Hydration residual **tests-only** deepeners after **#151** tip / post-#156
  (EXISTING eleven `hydration-*` phrase-lock fixtures plus the live `hydration`
  report lock — no invented product / inventory bump): concurrent validate races,
  empty/whitespace/header-only `docs/agent-hydration.md`, invalid/invented
  timeout+v53 keys, per-phrase drop matrix, inventory mismatch matrix,
  cross-isolation, and historic-four report fixture edges. Historic four only;
  inventory unchanged (v52 / 196). Distinct from merged #156 (constitution),
  merged #151 (prompt-pre-v52), merged #147 (goose-recipe), merged #144 (v52
  prompt residuals), and closed CONFLICTING #152 timeout invent.

- Constitution residual **tests-only** deepeners after **#151** (EXISTING fourteen
  `constitution-*` phrase-lock validators only — no invented product / inventory
  bump): concurrent validate races, empty/whitespace/header-only AGENTS-v2.2,
  invalid/invented constitution-timeout + closed-#150 sibling keys, per-phrase
  drop matrix, inventory mismatch matrix, and cross-isolation against
  `constitution-crypto` / `constitution-handoff` / `constitution-escalation-matrix`
  / `constitution-on-device` / `constitution-multichain` /
  `constitution-escalation-format` / `constitution-recipe-orchestration` /
  `constitution-scratchpad-state` / `constitution-conflict-matrix` /
  `constitution-ide-stack` / `constitution-install-script` /
  `constitution-vscode` / `constitution-hard-constraints` /
  `constitution-risk-tolerance`. Historic four only; inventory unchanged
  (v52 / 196). Distinct from merged #147 (nine goose-recipe residuals), merged
  #151 (thirty-three prompt-pre-v52 residuals), and closed CONFLICTING #150
  constitution invent.

- Prompt-pre-v52 residual **tests-only** deepeners after #144/#147 tip (EXISTING
  thirty-three pre-v52 `prompt-*` fixtures only, including
  `prompt-orchestration-matrix` — no invented product / inventory bump):
  concurrent validate races, empty/whitespace/header-only AGENT-PROMPTS,
  invalid/invented timeout+v53 keys, per-phrase drop matrix, inventory mismatch
  matrix, and cross-isolation. Historic four only; inventory unchanged
  (v52 / 196). Distinct from merged #144 (twelve v52 prompt residuals), merged
  #147 (nine goose-recipe residuals), and closed CONFLICTING #143/#145/#146
  timeout PRs.

- Goose-recipe residual **tests-only** deepeners after **#144** (EXISTING nine
  `goose-*` phrase-lock validators only — no invented product / inventory bump):
  concurrent validate races, empty/whitespace/header-only GOOSE-RECIPES,
  invalid/invented goose-timeout sibling keys, per-phrase drop matrix, inventory
  mismatch matrix, and cross-isolation against `goose-howto` /
  `goose-state-machine` / `goose-naming` / `goose-recipe-headers` /
  `goose-instruction-agents` / `goose-extensions` / `goose-orchestration` /
  `goose-conflicts` / `goose-quantum-task`. Historic four only; inventory
  unchanged (v52 / 196). Distinct from prompts v51/v52, prompt-validator #144,
  and orchestration-timeout drafts.

- Prompt/validator residual **tests-only** deepeners for post-#141 **v52** modules
  (EXISTING twelve only — no invented product / inventory bump): concurrent
  validate races, empty/whitespace/header-only AGENT-PROMPTS, invalid/invented
  v53 keys, per-phrase drop matrix, inventory mismatch matrix, and cross-isolation
  against `prompt-metrics-detail` / `prompt-orch-metrics-detail` /
  `prompt-communication-detail` / `prompt-principles-detail` /
  `prompt-responsibilities-residual` / `prompt-expertise-residual` /
  `prompt-vision-context` / `prompt-context-residual` / `prompt-monthly-detail` /
  `prompt-docs-residual` / `prompt-matrix-resolutions` / `prompt-usage-detail`.
  Historic four only; inventory unchanged (v52 / 196). Distinct from open #142
  (pre-v52 / 33-module residual on tip before #141).

- Prompts residual **v52 HEAVY** deepeners / **v51 leftovers continued** (post-#134 tip; distinct from closed CONFLICTING #133/#135):
  `prompt-metrics-detail`, `prompt-orch-metrics-detail`, `prompt-communication-detail`,
  `prompt-principles-detail`, `prompt-responsibilities-residual`, `prompt-expertise-residual`,
  `prompt-vision-context`, `prompt-context-residual`, `prompt-monthly-detail`,
  `prompt-docs-residual`, `prompt-matrix-resolutions`, `prompt-usage-detail`
  validators; AGENT-PROMPTS.md leftover locks across metrics-detail / orch-metrics /
  communication-detail / principles-detail / responsibilities-residual / expertise-residual /
  vision-context / context-residual / monthly-detail / docs-residual / matrix-resolutions /
  usage-detail; consistency deepeners for matching `*_required_phrases` inventory keys
  (Packaging inventory 196 total; historic four only — prompts v52 heavy residuals slice,
  not #128/#131 context/cannot-delegate/escalation-authority/role-blurbs/constraints-detail
  slices, not memory-slot #134, not constitution/changelog/hydration/README/security/
  contributing/goose/postmortem, or Dependabot)

- Memory-slot **tests-only** deepeners (EXISTING modules only — no invented product):
  concurrent validate races, empty scratchpad/inventory maps, invalid registry/
  allow-list keys, and full-capacity agentic_flows overflow rejection against
  scratchpad* / constitution-scratchpad-state / constitution-on-device /
  agentic_flows allow-list (single non-recipe slot `scratchpad.txt`; no LRU
  eviction coded). Historic four only; inventory version unchanged (v51 / 184).

- Prompts residual **v51 HEAVY** deepeners / **v50 leftovers max** (post-#128 prompts context/cannot-delegate/escalation-authority v50):
  `prompt-role-blurbs`, `prompt-escalation-format`, `prompt-living-docs`,
  `prompt-constraints-detail`, `prompt-triggers-detail`, `prompt-human-fields`,
  `prompt-context-detail`, `prompt-expertise-detail`, `prompt-related-health`,
  `prompt-tools-detail`, `prompt-responsibilities-detail`, `prompt-instantiation`
  validators; AGENT-PROMPTS.md leftover locks across role blurbs / escalation format /
  living-docs / constraints-detail / triggers-detail / human-fields / context-detail /
  expertise-detail / related-health / tools-detail / responsibilities-detail /
  instantiation; consistency deepeners for matching `*_required_phrases` inventory keys
  (Packaging inventory 184 total; historic four only — prompts v51 heavy leftovers slice,
  not constitution/changelog v45, hydration, README, implementation-guide, security,
  contributing, goose recipes, postmortem, or Dependabot)

- Prompts residual **v50** deepeners / **v49 leftovers continued** (post-#124 prompts responsibilities/decision/integration v49):
  `prompt-context`, `prompt-cannot-delegate`, `prompt-escalation-authority` validators; AGENT-PROMPTS.md
  Current Project Context / CANNOT Delegate / Escalation Authority leftovers; consistency deepeners
  for matching `*_required_phrases` inventory keys
  (Packaging inventory 172 total; historic four only — prompts context/cannot-delegate/escalation-authority
  leftovers slice, not constitution/changelog v45, hydration, README, implementation-guide,
  security, contributing, goose recipes, postmortem, or Dependabot)

- Prompts residual **v49** deepeners / **v48 leftovers continued** (post-#120 prompts orchestration/monthly/usage-example v48):
  `prompt-responsibilities`, `prompt-decision-authority`, `prompt-integration` validators; AGENT-PROMPTS.md
  Core Responsibilities / Decision Authority / Integration+human-escalation leftovers; consistency deepeners
  for matching `*_required_phrases` inventory keys
  (Packaging inventory 169 total; historic four only — prompts responsibilities/decision/integration
  leftovers slice, not constitution/changelog v45, hydration, README, implementation-guide,
  security, contributing, goose recipes, postmortem, or Dependabot)

- Prompts residual **v48** deepeners / **v47 leftovers continued** (post-#119 prompts tools/communication/escalation-identity v47):
  `prompt-orchestration-matrix`, `prompt-monthly`, `prompt-usage-example` validators; AGENT-PROMPTS.md
  Escalation Authority / Conflict Resolution Matrix / Monthly Checklist / usage-example leftovers
  (from closed #118, never landed); consistency deepeners for matching `*_required_phrases`
  inventory keys
  (Packaging inventory 166 total; historic four only — prompts orchestration/monthly/usage-example
  leftovers slice, not constitution/changelog v45, hydration, README, implementation-guide,
  security, contributing, goose recipes, postmortem, or Dependabot)

- Prompts residual **v47** deepeners / **v43 leftovers continued** (post-#117 prompts expertise/principles/metrics v46):
  `prompt-tools`, `prompt-communication`, `prompt-escalation-identity` validators; AGENT-PROMPTS.md
  Your Tools / Communication Style / escalation-identity leftovers; consistency deepeners
  for matching `*_required_phrases` inventory keys
  (Packaging inventory 163 total; historic four only — prompts tools/communication/escalation
  leftovers slice, not constitution/changelog v45, hydration, README, implementation-guide,
  security, contributing, goose recipes, or Dependabot)

- Prompts residual **v46** deepeners / **v43 leftovers** (post-#116 constitution+changelog v45):
  `prompt-expertise`, `prompt-principles`, `prompt-metrics` validators; AGENT-PROMPTS.md
  Expertise / Decision Making Principles / Success Metrics leftovers; consistency deepeners
  for matching `*_required_phrases` inventory keys
  (Packaging inventory 160 total; historic four only — prompts v43 leftovers slice, not
  constitution/changelog v45, hydration v43/v44, README v43, implementation-guide, security,
  contributing, goose recipes, or Dependabot)

- Constitution + changelog residual **v45** deepeners (post-#115 hydration v44 / #111 README v43):
  `constitution-ide-stack`, `constitution-install-script`, `constitution-vscode`,
  `constitution-hard-constraints`, `constitution-risk-tolerance`, `changelog-preamble`,
  `changelog-changed`, `changelog-initial` validators; AGENTS-v2.2.md §23 IDE stack /
  install / VS Code leftovers, §24 hard-constraints / §25 risk-tolerance leftovers, and
  CHANGELOG.md preamble / Changed / 0.1.0 leftovers; consistency deepeners for the
  matching `*_required_phrases` inventory keys
  (Packaging inventory 157 total; historic four only — constitution/changelog residuals
  slice, not hydration v44, README v43, implementation-guide v41, prompts, security,
  contributing, goose recipes, execution-summary, or Dependabot)

- Hydration report **v44** deepeners (post-#111 README v43; NEW after #108
  CONFLICTING closed): `hydration-meta`, `hydration-identity-detail`,
  `hydration-git-detail`, `hydration-phase2`, `hydration-phase5` validators;
  docs/agent-hydration.md header Status/Owner leftovers, Identity LICENSE/manifest
  leftovers, Git State branch/shallow leftovers, PHASE 2 questions crypto/Andrew/Notion
  leftovers, and PHASE 5 Roadmap leftovers; consistency deepeners for
  `hydration_meta_required_phrases` / `hydration_identity_detail_required_phrases` /
  `hydration_git_detail_required_phrases` / `hydration_phase2_required_phrases` /
  `hydration_phase5_required_phrases`
  (Packaging inventory 149 total; historic four only — hydration leftovers slice,
  not README v43, hydration v42, implementation-guide v41, constitution v40,
  security v39, contributing v38, goose recipes, execution-summary, agent prompts,
  changelog, or Dependabot)

- README **v43** deepeners (post-#106 hydration v42; NEW PR after #109
  CONFLICTING closed): `readme-lead`, `readme-blurbs`, `readme-bootstrap` validators;
  README.md Docs-only / Oracle-Style lead leftovers, Contents blurb leftovers, and
  Note/Cloud/Manifest/License bootstrap-closing leftovers; consistency deepeners for
  `readme_lead_required_phrases` / `readme_blurbs_required_phrases` /
  `readme_bootstrap_required_phrases`
  (Packaging inventory 144 total; historic four only — README leftovers
  slice, not hydration v42, implementation-guide v41, constitution v40, security,
  contributing, postmortem, goose recipes, execution-summary, agent prompts, or
  Dependabot)

- Hydration report **v42** deepeners (post-#101 implementation-guide v41): `hydration-phase1`,
  `hydration-list-a`, `hydration-resolved`, `hydration-phase4`, `hydration-deferred`
  validators; docs/agent-hydration.md PHASE 1 findings category leftovers, LIST A
  Goose/Kyber/liboqs/stimgery leftovers, PHASE 3 resolved LIST A leftovers, PHASE 4
  issues-generated leftovers, and LIST B deferred-to-Andrew leftovers; consistency
  deepeners for `hydration_phase1_required_phrases` / `hydration_list_a_required_phrases` /
  `hydration_resolved_required_phrases` / `hydration_phase4_required_phrases` /
  `hydration_deferred_required_phrases`
  (Packaging inventory 141 total; historic four only — hydration leftovers slice,
  not implementation-guide v41, constitution v40, security v39, contributing v38,
  goose recipes, execution-summary, agent prompts, changelog, or Dependabot)

- Implementation guide **v41** deepeners (post-#96 constitution v40): `implementation-issues`,
  `implementation-faq`, `implementation-support` validators; IMPLEMENTATION-GUIDE.md
  Common Issues 1–5 / Qualtran / rollups / classical-fallback / scratchpad append-only
  locks, FAQ quantum-computer / LLM / AGENTS.md / parallel / quality locks, and Support
  & Resources docs + Cirq / Hardhat / Goose URL locks; consistency deepeners for
  `implementation_issues_required_phrases` / `implementation_faq_required_phrases` /
  `implementation_support_required_phrases`
  (Packaging inventory 136 total; historic four only — implementation-guide leftovers
  slice, not constitution v40, hydration v40, security v39, contributing v38, goose
  recipes, execution-summary, agent prompts, changelog, or Dependabot)

- Constitution **v40** deepeners (post-#94 security v39): `constitution-recipe-orchestration`,
  `constitution-scratchpad-state`, `constitution-conflict-matrix` validators;
  AGENTS-v2.2.md §22.5 Recipe-Based Orchestration Structure locks, §22.6 Scratchpad
  State Machine locks, and §22.7 Conflict Resolution Matrix locks; consistency
  deepeners for `constitution_recipe_orchestration_required_phrases` /
  `constitution_scratchpad_state_required_phrases` /
  `constitution_conflict_matrix_required_phrases`
  (Packaging inventory 133 total; historic four only — constitution leftovers
  slice, not security v39, contributing v38, goose recipes, execution-summary,
  implementation-guide, agent prompts, changelog, or Dependabot)

- Security policy **v39** deepeners (post-#92 contributing v38): `security-scope`,
  `security-reporting-channel`, `security-compliance-detail` validators; SECURITY.md
  Supported Versions scope/injection leftovers, Reporting channel/contact leftovers,
  and Standards preamble / Keys RAM / future-rename leftovers; consistency deepeners
  for `security_scope_required_phrases` / `security_reporting_channel_required_phrases` /
  `security_compliance_detail_required_phrases`
  (Packaging inventory 130 total; historic four only — security leftovers slice,
  not contributing v38, constitution, goose recipes, execution-summary,
  implementation-guide, agent prompts, changelog, or Dependabot)

- Contributing guide **v38** deepeners (post-#90; #89 conflict closed): `contributing-metadata`,
  `contributing-surfaces`, `contributing-ci-honesty` validators; CONTRIBUTING.md title /
  Status / Edit-policy locks, agent-surface duty list / branch-purpose leftovers, and PR
  CI-gate names / packaging-inventory honesty leftovers; consistency deepeners for
  `contributing_metadata_required_phrases` / `contributing_surfaces_required_phrases` /
  `contributing_ci_honesty_required_phrases`
  (Packaging inventory 127 total; historic four only — contributing leftovers slice,
  not constitution v37, goose recipes, execution-summary, hydration, implementation-guide,
  security policy, agent prompts, changelog, or Dependabot)

- Constitution **v37** deepeners (post-#88): `constitution-on-device`,
  `constitution-multichain`, `constitution-escalation-format` validators;
  AGENTS-v2.2.md §22.2 On-Device Quantum Logic Execution locks, §22.3
  Multi-Chain State Consistency locks, and §22.4.3 Escalation Format locks;
  consistency deepeners for `constitution_on_device_required_phrases` /
  `constitution_multichain_required_phrases` /
  `constitution_escalation_format_required_phrases`
  (Packaging inventory 124 total; historic four only — constitution leftovers
  slice, not goose recipes, execution-summary, hydration, implementation-guide,
  contributing, security policy, agent prompts, changelog, or Dependabot)

- Goose recipes **v36** deepeners (post-#84): `goose-orchestration`,
  `goose-conflicts`, `goose-quantum-task` validators; GOOSE-RECIPES.md
  Master Orchestration Task STEP locks, Conflict Type PERFORMANCE/SECURITY/
  TIMELINE + decision outcome locks, and Quantum Algorithm Design Task STEP
  locks; consistency deepeners for `goose_orchestration_required_phrases` /
  `goose_conflicts_required_phrases` / `goose_quantum_task_required_phrases`
  (121 total; historic four only — goose recipes slice, not execution-summary
  v35, agent prompts v34, hydration/implementation-guide open deepeners,
  Dependabot, changelog, constitution, security, contributing, README honesty,
  PR-template, issue-template, scratchpad, postmortem, or routing/identity)

- Execution-summary **v35** deepeners (post-#81): `execution-ide`,
  `execution-innovations`, `execution-next48` validators; EXECUTION-SUMMARY.md
  IDE & Software Setup locks, What Makes This Different / Key Innovations locks,
  and Success Indicators / Common Pitfalls / Next 48 Hours locks; consistency
  deepeners for `execution_ide_required_phrases` /
  `execution_innovations_required_phrases` / `execution_next48_required_phrases`
  (118 total; historic four only — execution-summary slice, not agent prompts,
  hydration/goose/constitution/security v34 bundle, Dependabot, changelog,
  contributing, implementation guide, README honesty, PR-template,
  issue-template, scratchpad, postmortem, archive snapshot, or routing/identity)

- Agent prompts **v34** deepeners (post-#80): `prompt-constraints`,
  `prompt-triggers`, `prompt-related-docs` validators; AGENT-PROMPTS.md
  never-violate constraint locks across specialists, escalation-trigger /
  human-escalation locks, and AGENTS.md Section 22 related-docs / Remember
  locks; consistency deepeners for `prompt_constraints_required_phrases` /
  `prompt_triggers_required_phrases` / `prompt_related_docs_required_phrases`
  (115 total; historic four only — agent prompts slice, not goose recipes,
  changelog, hydration, constitution, security policy, contributing,
  execution-summary, implementation guide, README honesty, PR-template,
  issue-template, scratchpad, postmortem, archive snapshot, routing/identity,
  or Dependabot)

- Goose recipes **v33** deepeners (post-#78): `goose-recipe-headers`,
  `goose-instruction-agents`, `goose-extensions` validators; GOOSE-RECIPES.md
  Recipe 1–4 heading / File-path locks, historic four instruction-agent identity
  locks, and builtin developer extension / timeout 300+600 locks; consistency
  deepeners for `goose_recipe_headers_required_phrases` /
  `goose_instruction_agents_required_phrases` /
  `goose_extensions_required_phrases` (112 total; historic four only — goose
  recipes slice, not changelog, hydration, constitution, security policy,
  contributing, execution-summary, implementation guide, agent prompts, README
  honesty, PR-template, issue-template, scratchpad, postmortem, archive
  snapshot, routing/identity, or Dependabot)

- Changelog **v32** deepeners (post-#75): `changelog-format`, `changelog-unreleased`,
  `changelog-release` validators; CHANGELOG.md Keep a Changelog / Unreleased / Added
  format locks, Unreleased packaging/historic-four/Dependabot honesty locks, and
  Changed / 0.1.0 release / AGENTS/AGENT-PROMPTS/GOOSE-RECIPES archive locks;
  consistency deepeners for `changelog_format_required_phrases` /
  `changelog_unreleased_required_phrases` / `changelog_release_required_phrases`
  (109 total; historic four only — changelog slice, not constitution, security
  policy, contributing, execution-summary, hydration, implementation guide,
  agent prompts, goose recipes, README honesty, PR-template, issue-template,
  scratchpad, postmortem, archive snapshot, routing/identity, or Dependabot)

- Constitution **v31** deepeners (post-#69): `constitution-crypto`,
  `constitution-handoff`, `constitution-escalation-matrix` validators;
  AGENTS-v2.2.md §22.1 Quantum-Safe Cryptography (Kyber/Dilithium/SPHINCS+/
  liboqs/RSA-ECDSA/hybrid) locks, §22.4.1 Handoff Sequence Phase 1–4 /
  postmortem decision locks, and §22.4.2 Escalation Triggers per-agent
  matrix locks; consistency deepeners for
  `constitution_crypto_required_phrases` /
  `constitution_handoff_required_phrases` /
  `constitution_escalation_matrix_required_phrases` (106 total; historic four
  only — constitution slice, not security policy, contributing,
  execution-summary, implementation guide, agent prompts, goose recipes,
  README honesty, PR-template, issue-template, scratchpad, postmortem,
  archive snapshot, routing/identity, or Dependabot)

- Security policy **v30** deepeners (post-#63): `security-header`,
  `security-fips`, `security-known-non-issues` validators; SECURITY.md
  Status/Tier/Created/Edit-policy header locks, Standards-table FIPS
  (ML-KEM/ML-DSA/SLH-DSA) / Slither / Apple-Google / `.env` locks, and
  Known Non-Issues CRYSTALS→NIST rename locks; consistency deepeners for
  `security_header_required_phrases` / `security_fips_required_phrases` /
  `security_known_non_issues_required_phrases` (103 total; historic four only —
  security policy slice, not contributing, execution-summary, implementation
  guide, agent prompts, goose recipes, README honesty, PR-template,
  issue-template, scratchpad, postmortem, archive snapshot, routing/identity,
  or Dependabot)

- Contributing guide **v29** deepeners (post-#61): `contributing-issues`,
  `contributing-local`, `contributing-governance` validators; CONTRIBUTING.md
  Issue Reporting / Bug / Feature / Agent Task locks, Local validation
  (pip/ruff/validate_manifests/pytest) locks, and Governance structural /
  Andrew-approval / CLAUDE.md locks; consistency deepeners for
  `contributing_issues_required_phrases` / `contributing_local_required_phrases` /
  `contributing_governance_required_phrases` (100 total; historic four only —
  contributing slice, not execution-summary, implementation guide, agent
  prompts, goose recipes, README honesty, PR-template, issue-template,
  scratchpad, postmortem, archive snapshot, security policy, routing/identity,
  or Dependabot)

- Execution summary **v28** deepeners (post-#56): `execution-timeline`,
  `execution-technologies`, `execution-workflow` validators; EXECUTION-SUMMARY.md
  Implementation Timeline / Week 1 / By End of Month locks, Key Technologies
  (Cirq/Hardhat/liboqs/Goose) locks, and Workflow Overview single/multi/escalation
  locks; consistency deepeners for `execution_timeline_required_phrases` /
  `execution_technologies_required_phrases` / `execution_workflow_required_phrases`
  (97 total; historic four only — execution-summary slice, not implementation
  guide, agent prompts, goose recipes, README honesty, PR-template, contributing,
  issue-template, scratchpad, postmortem, archive snapshot, security policy,
  routing/identity, or Dependabot)

- Implementation guide **v27** deepeners (post-#54): `implementation-phases`,
  `implementation-tools`, `implementation-success` validators; IMPLEMENTATION-GUIDE.md
  Full Implementation Phase 1–6 / agent prompt path / recipe path locks; Tools &
  Software Checklist locks; Success Criteria / Common Issues / FAQ / Next Steps
  locks; consistency deepeners for `implementation_phases_required_phrases` /
  `implementation_tools_required_phrases` / `implementation_success_required_phrases`
  (94 total; historic four only — implementation guide slice, not agent prompts,
  goose recipes, README honesty, PR-template, contributing, issue-template,
  scratchpad, postmortem, archive snapshot, security policy, routing/identity,
  execution-summary, or Dependabot)

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

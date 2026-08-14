---
name: audit-project-docs
description: Audit CLAUDE.md and docs/ against the current codebase and return an evidence-backed update plan. Use for project-wide audits, module-specific audits, and staged-diff documentation checks before preparing or creating a commit.
---

# Audit Project Docs

Audit project documentation against the codebase, report every relevant gap, and update documentation only after explicit user approval. Write all prose output in Taiwan Traditional Chinese unless the project requires another language.

## Guardrails

- Treat source code, build configuration, tests, and version-control history as evidence. Keep source code unchanged.
- Limit writes to `CLAUDE.md` and `docs/`. Exclude `README.md` unless the user explicitly expands the scope.
- Record the codebase as it exists. Separate observations from recommendations and avoid inferred or idealized architecture.
- Prefer the smallest sufficient documentation change. Put local implementation details in code comments; reserve project docs for module responsibilities, integration contracts, architectural decisions, external constraints, and cross-module guidance.
- Preserve unrelated user changes. Ask before proceeding when the working tree or requested scope makes safe attribution uncertain.

## Select the audit mode

Choose exactly one mode from the user's request and available repository state:

1. **Pre-commit**: Use when preparing a commit or checking staged changes. Treat the staged snapshot as the gate. Use branch history only as context, and report unstaged changes separately without letting unrelated unstaged work block the staged commit.
2. **Module-specific**: Use when the user names a module, feature, API, or directory. Inspect that scope and only the directly related contracts and cross-module documentation.
3. **Project-wide**: Use when no narrower scope is provided. Inspect the project entry documentation, documentation tree, module boundaries, public interfaces, tests, build configuration, and existing conventions.

If the user explicitly requests a branch or commit-range audit, use the stated range. Resolve or ask for the intended baseline instead of assuming `origin/main`, especially for long-lived branches.

## Audit workflow

### 1. Establish context

1. Resolve the repository root and any nested repositories involved in the requested scope.
2. Read `CLAUDE.md` and `AGENTS.md` when present, then follow their documentation pointers.
3. Inventory existing files under `docs/` without assuming a fixed documentation tree.
4. Identify the source files, tests, configuration, and history that can verify each relevant documentation claim.

Completion criterion: the audit scope, repository boundary, documentation entry points, and evidence sources are explicit.

### 2. Collect mode-specific evidence

For **pre-commit** mode:

1. Inspect `git diff --staged --name-status`, `git diff --staged --stat`, and the staged diff in the selected repository.
2. Group staged files into coherent change units rather than reviewing files independently.
3. Inspect unstaged changes only to identify overlap or warn about required documentation that is not staged.
4. Read branch history only when needed to understand an aggregation, generated artifact, or public behavior change.

For **module-specific** mode:

1. Inspect the requested module's public surface, internal boundaries, tests, and directly connected modules.
2. Follow existing documentation links for that module and its contracts.

For **project-wide** mode:

1. Identify project purpose, technology stack, module boundaries, public interfaces, build and verification commands, and non-obvious constraints.
2. Compare those findings with the navigation and coverage in `CLAUDE.md` and `docs/`.

Completion criterion: every source change or code area in scope belongs to a named change unit or documentation topic.

### 3. Classify documentation impact

Classify every change unit or documentation topic as one of:

- **No docs impact**: the change is local implementation detail and current documentation remains accurate.
- **Docs current**: documentation impact exists, but the required documentation already matches the evidence and is included where needed.
- **Docs update required**: documentation is missing, stale, misleading, or not included in the staged snapshot.
- **Unable to determine**: evidence is insufficient or contradictory; identify the exact question that requires user or domain-expert input.

For each classification, cite concrete file paths, symbols, tests, configuration, or commits. Do not use an unsupported conclusion such as "no documentation needed."

Completion criterion: every change unit or topic has exactly one classification and evidence.

### 4. Return the audit report

Use this structure:

```markdown
## 文件稽核結果

狀態：PASS | DOCS_UPDATE_REQUIRED | UNABLE_TO_DETERMINE

### 稽核範圍
- 模式：pre-commit | module-specific | project-wide
- Repository／模組：...
- Evidence：...

### 變更與文件影響
| 變更單元／主題 | 分類 | 依據 | 相關文件 |
|---|---|---|---|
| ... | ... | ... | ... |

### 文件更新計畫
| 目標路徑 | 動作 | 具體更新內容 | 資訊來源 | 工作量 |
|---|---|---|---|---|
| ... | 新增／更新 | 可直接執行的段落、條列或內容大綱 | ... | 小／中／大 |
```

Set the overall status as follows:

- `PASS`: every item is `No docs impact` or `Docs current`.
- `DOCS_UPDATE_REQUIRED`: at least one item is `Docs update required`.
- `UNABLE_TO_DETERMINE`: at least one unresolved item prevents a reliable audit result.

Make the update plan executable: name exact paths and state the actual facts, headings, links, tables, or diagrams to add or revise. Keep optimization suggestions outside the proposed documentation content.

## Approval and updates

When the status is `DOCS_UPDATE_REQUIRED`, present the report and ask:

> 計畫確認？回覆 `APPROVED` 開始更新文件。

Treat an equivalent explicit instruction to apply the displayed plan as approval. Without approval, leave files unchanged.

When invoked as a prerequisite of a commit workflow, return the status and plan, then stop. Let the parent workflow block the commit; do not request approval or edit files inside that commit attempt.

After approval in an interactive documentation workflow:

1. Update only the approved `CLAUDE.md` and `docs/` files.
2. Keep `CLAUDE.md` concise and navigation-first; target at most 200 lines unless project rules require otherwise. Put details behind precise links to `docs/`.
3. Give each document one H1, a short purpose statement, and a shallow heading hierarchy. Prefer tables for mappings and diagrams only when they clarify a real multi-step flow or relationship.
4. Avoid duplicating facts across documents. Link to the single source of truth.
5. Verify every changed claim against source evidence and validate every relative documentation link.
6. Re-run the same audit scope and report the final status, changed files, remaining uncertainty, and observations that should not be written into project docs.

Completion criterion: every approved plan item is implemented and verified, or explicitly reported as unresolved; the final audit status is stated.

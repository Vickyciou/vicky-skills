---
name: gen-commit
description: Prepare Git commits after completing an authorized task by partitioning changes, staging or unstaging intended hunks, and writing scoped English Conventional Commit messages. Use when the user invokes gen-commit, asks for commit messages, or asks the agent to commit completed work.
---

# Generate Commits

Inspect the repository, divide changes into cohesive commits, and produce scoped Conventional Commit messages. Match repository mutations to the authority already granted by the caller.

## Choose the Mode

- **Message mode:** Use when asked only to analyze staged changes or propose messages. Read the index and return a commit plan without changing it.
- **Commit mode:** Use when the current task explicitly authorizes creating commits. Stage or unstage the task's changes, then create the planned commits.

## Inspect the Changes

1. Run:

   ```bash
   git status --short
   git diff
   git diff --staged --stat
   ```

2. In message mode, if `git diff --staged --stat` produces no output, reply exactly:

   ```text
   目前沒有 staged 的變更，請先 `git add` 要 commit 的檔案
   ```

   Stop immediately.

3. Run `git diff --staged` and inspect the complete output. Inspect the contents of each in-scope untracked file before assigning it to a partition.

4. In commit mode, distinguish changes created for the current task from pre-existing or unrelated work. If ownership of a staged hunk is unclear, leave the index unchanged and report the blocker. If `git status --short` is empty, report that there is nothing to commit and stop.

5. Account for every in-scope hunk and partition the changes into the smallest set of cohesive commits that preserves buildable, understandable intermediate states. Every in-scope hunk must appear in exactly one partition.

## Set Commit Boundaries

Group changes when they serve one purpose or must land together to keep the repository working. Include directly supporting tests, documentation, generated project-file updates, and required configuration with the behavior they support.

Split changes when they have independent intent and can be reviewed or reverted independently, including:

- unrelated product behavior or bug fixes
- a behavior change and an independent refactor
- standalone dependency, build, or tooling maintenance
- unrelated formatting or documentation

When one file contains multiple concerns, assign its hunks to the appropriate partitions. Keep coupled changes together when splitting would create a broken or misleading intermediate commit, and state the coupling in the breakdown.

## Stage and Commit

Perform this section only in commit mode.

1. Prepare the next partition with explicit paths or hunks:

   ```bash
   git add -- <path>
   git add -p -- <path>
   git restore --staged -- <path>
   git restore --staged -p -- <path>
   ```

   Use whole-path commands when the entire file belongs to one partition and patch mode for mixed files. Keep unrelated changes outside the index.

2. Run both commands and inspect their complete output before each commit:

   ```bash
   git diff --staged --stat
   git diff --staged
   ```

   Commit only when every staged hunk belongs to the current partition and the staged diff is non-empty.

3. When the user or applicable project instructions require a documentation gate and this final staged partition contains source, build, or configuration changes, invoke `audit-project-docs` in pre-commit mode. Continue only on `PASS`; otherwise return its report or unresolved question, preserve the staged partition, and stop. Treat an unavailable audit skill as a blocker.

4. Create the commit with the approved message. Allow repository hooks to run. If a hook fails or changes files, inspect the resulting status and resolve only issues within the current task's authority.

5. Capture the committed partition for the local worklog when `worklog` is available:

   - On the first successful commit, run `worklog capture --help` exactly once and retain its output as the live input contract for every partition in this run.
   - Resolve the repository root and new commit hash. Build exactly one JSON object that follows the retained contract, using only facts supported by the inspected committed diff and task context. State the outcome in Taiwan Traditional Chinese; include optional approach, decisions and reasons, remaining steps, public technologies, or source metadata only when supported. Keep secrets, credentials, raw code, and personal identities out.
   - Pass the JSON through stdin to `worklog capture <repo-root> <commit>`. Keep this integration limited to that generic contract.
   - A help or capture failure does not undo or rewrite a successful Git commit. Retain the exact error and report a matching next action, such as installing or exposing `worklog`, correcting the JSON against the retained help, or resolving an existing-note conflict before retrying capture.

   Completion criterion: the commit has a worklog Git note, or the unavailable command or actionable capture error is retained for the final report.

6. Run `git status --short`, then repeat for the next partition.

7. Finish only when every in-scope hunk was committed exactly once and unrelated changes remain uncommitted and unmodified. Report each created commit's short hash and subject, worklog recording status, plus any remaining changes.

## Write the Message

Use a scope when one short affected area accurately names the partition:

```text
<type>(<scope>): <subject>

- <change or reason>
- <change or reason>
```

Omit the parentheses when no single useful scope applies:

```text
<type>: <subject>
```

Choose one type by the partition's dominant impact:

| Type | Use for |
| --- | --- |
| `feat` | New functionality, screen, or API call |
| `fix` | Corrected bug or incorrect behavior |
| `refactor` | Structural or naming changes with unchanged behavior |
| `docs` | Documentation-only changes |
| `chore` | Build settings, dependencies, project files, or non-product maintenance |
| `test` | Test-only changes |
| `style` | Formatting-only changes with no logic impact |
| `perf` | Performance improvements |

Prefer `feat` when one cohesive partition contains both a new feature and its fixes. Otherwise choose the type that describes the partition's primary effect.

Mark a breaking change by appending `!` after the type or scope (`feat(auth)!: ...`) and adding a `BREAKING CHANGE: <migration>` footer describing what callers must change. Reserve this for a partition that removes or alters a public contract.

Choose an optional scope as a short lowercase noun naming the affected area, such as `auth`, `dashboard`, or `deps`. Prefer the repository's established scope vocabulary when visible in recent commit subjects. Omit the scope for broad changes or when a precise scope would be forced.

Write the subject in English, start with a base-form verb such as `add`, `fix`, `refactor`, `remove`, `update`, `extract`, or `rename`, keep it at 72 characters or fewer, and omit the final period.

Default to a subject-only message. Add an English bullet body only when the subject cannot capture reviewer-relevant motivation, constraints, migration impact, or risk. The number of changed files or modules does not justify a body.

When a body is necessary:

- Write one or two bullets, each a single sentence of at most 20 words.
- Capture the outcome or reason at commit level rather than inventorying implementation details.
- Keep only details whose absence could cause a reviewer to misunderstand the change.
- Move file paths, symbol lists, upstream hashes, build-setting details, validation evidence, and unchanged behavior to the breakdown or task report.
- Remove any bullet that merely repeats the subject. If no bullet survives this compression pass, omit the body.

For example, summarize a multi-file dependency migration as:

```text
chore(toast): vendor Toast 4.1.1 in the SDK

- Remove the CocoaPods dependency while preserving privacy and license delivery
```

## Report the Result

In message mode, start with `Commit breakdown`. List each proposed commit with the files or hunks it owns and one concise rationale, then show its message in a fenced text block. Label multiple commits `Commit 1`, `Commit 2`, and so on in the recommended order. Keep explanations outside message blocks so each message can be copied verbatim.

In commit mode, report the commits actually created rather than repeating the proposal. Include each short hash and full subject, and identify any intentionally uncommitted changes.

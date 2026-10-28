---
name: create-pr
description: Create a project-formatted GitLab merge request from the current branch into a specified target branch, or rewrite an existing MR's title and description in the same format. Use when creating an MR, or when updating, rewriting, or tidying an MR description after new commits.
---

# Create GitLab Merge Request

Create one GitLab merge request (MR) from the checked-out branch, or update the open MR for the
same source and target:

```text
/create-pr <target-branch>
```

Write MR titles in English and user-facing explanations in Taiwan Traditional Chinese.

## Workflow

1. **Resolve the repository and target.** Treat the current working tree as the repository:

   ```bash
   git rev-parse --show-toplevel
   git branch --show-current
   ```

   Stop if the directory is not a Git worktree or `HEAD` is detached. Take the target branch
   from the invocation argument. When it is missing, ask the user for it and wait. Validate it
   with `git check-ref-format --branch <target>` and stop when it equals the source branch.

   Resolve the remote from the source branch's upstream. Fall back to `origin` only when that
   remote exists; if no upstream is configured and `origin` does not exist, show `git remote`
   and ask the user which remote to use. Use that same remote throughout this run.

   Completion criterion: `<repo>`, `<source>`, `<target>`, and `<remote>` each resolve to one
   unambiguous value.

2. **Run the remote preflight.** Run Git commands with `git -C <repo>` and GitLab commands with
   `<repo>` as their working directory.

   - Require `glab` and a successful `glab auth status`. Report the failing prerequisite and
     stop if either is unavailable.
   - Verify the target exists with
     `git ls-remote --exit-code --heads <remote> <target>`. A missing remote target is an error;
     do not substitute a similarly named branch.
   - Verify the source exists with
     `git ls-remote --exit-code --heads <remote> <source>`. If it does not, stop and tell the
     user to run `git push --set-upstream <remote> <source>` before invoking the skill again.
   - Fetch both branches into their remote-tracking refs:

     ```bash
     git -C <repo> fetch <remote> \
       +refs/heads/<target>:refs/remotes/<remote>/<target> \
       +refs/heads/<source>:refs/remotes/<remote>/<source>
     ```

     Then compare
     `refs/remotes/<remote>/<source>...HEAD` with `git rev-list --left-right --count`. Continue
     only when both counts are zero. Local-only commits still need to be pushed; remote-only or
     divergent commits require the user to synchronize the branch first.
   - Report uncommitted files from `git status --short` as excluded from the MR; analyze only the
     committed, pushed branch state.
   - Query open MRs with
     `glab mr list --source-branch <source> --target-branch <target> --output json`. If one
     exists, switch to **update mode** and never create a duplicate. Read its current title and
     description with `glab mr view <iid> --output json`. Keep facts the conversation cannot
     reproduce, such as earlier test results, and redraft both in steps 4 and 5 from the whole
     MR diff instead of appending the latest commits.

   Completion criterion: the remote source matches local `HEAD`, the target exists, and the mode
   is decided: create (no open MR) or update (one open MR with a known `iid`).

3. **Inspect every MR change.** Use the fetched target ref as `<base>`:

   ```bash
   git -C <repo> log --no-merges --oneline <base>..HEAD
   git -C <repo> diff --stat <base>...HEAD
   git -C <repo> diff --name-status <base>...HEAD
   git -C <repo> diff --check <base>...HEAD
   git -C <repo> diff --find-renames --find-copies <base>...HEAD
   ```

   The two-dot commit range selects commits introduced by the source. The three-dot diff selects
   changes since the merge base, matching the MR content. If both the commit list and diff are
   empty, stop because there is nothing to merge. For a very large diff, use the stat and
   name-status output to divide it into logical change units, then inspect targeted file diffs;
   account for every changed path before drafting.

   Completion criterion: every title, summary, change bullet, risk, and test claim is supported
   by the committed diff, commit history, or test output available in the current conversation.

4. **Draft the title.** Use `type: description`: lowercase type, a concise imperative English
   description, and no trailing period. Infer one type from the dominant purpose:

   | Type | Use when |
   |---|---|
   | `feat` | Add user-visible capability |
   | `fix` | Correct definite wrong behavior |
   | `docs` | Change documentation only |
   | `test` | Add or correct tests only |
   | `refactor` | Restructure code without changing behavior |
   | `perf` | Improve performance |
   | `style` | Change formatting without changing behavior |
   | `build` | Change the build system or external dependencies |
   | `ci` | Change CI configuration or automation |
   | `chore` | Make other maintenance changes |
   | `revert` | Revert an earlier change |

5. **Draft the description.** Write concise Taiwan Traditional Chinese in this project format:

   ```markdown
   ## Summary（必填）
   <此次解決的問題或動機，1～2 行；有對應 issue 於此連結>

   ## Changes（必填）
   - <高階做法與行為影響，勿逐行複述 diff>
   - <其他核心邏輯、UI、bug fix 或 dependency 變更>

   ## Impact（必填）
   - 相容性：<向後相容，或破壞性變更並列出所需 migration 步驟>
   - 風險等級：<低 / 中 / 高，及理由>

   ## Notes
   <reviewer 建議重點看的檔案或順序、限制或後續工作>

   ## Test Scope
   - [ ] Device / OS：<裝置與 OS，或「未執行」及原因>
   - [ ] UI Check：<Dark mode、螢幕尺寸、橫豎屏，或未執行>
   - [ ] Edge Cases：<斷網、權限拒絕、空資料、慢速網路等，或未執行>
   - [ ] Regression：<受影響功能的 regression 結果，或未執行>

   ## Reference
   - <GitLab Issue、Notion、相關 MR 或文件連結>
   ```

   Write for the reviewer. Each line answers one of these: what problem this solves, what
   behavior changes, what the reviewer must check, or what was and was not verified. Cut
   anything the reviewer already gets from the diff or the commit list:

   - Changes: one bullet per behavior change a reviewer would judge separately. Merge bullets
     that describe one change from different files. Name at most the one symbol or file a
     reviewer needs to find it. No parameter lists, renamed locals, or deleted lines. More than
     about 5 bullets after merging suggests the MR mixes concerns: say so in Notes, but keep
     every bullet.
   - Notes: only items the reviewer must act on or read first. No commit-by-commit order and no
     mapping of commits to review findings; those belong in commit messages.
   - Test Scope: one line per box with the result and any gap. Do not enumerate every case,
     count, hash, or duration.

   When brevity conflicts with completeness, keep the gap or risk and drop the detail.

   `Impact` 必填：即使無風險也要正面表態（例如「無破壞性變更、向後相容」），不得靜默省略。
   Omit `Notes` and `Reference` when empty. Omit `Test Scope` for documentation-only changes.
   Mark a checkbox `[x]` only when the corresponding check has evidence; otherwise keep `[ ]`
   and state what was not run. Never infer test execution from the presence of test files.

6. **Create or update the MR.** In update mode, run
   `glab mr update <iid> --title <title> --description <description>` instead of the create
   command below, and do not change the MR's branches, reviewers, or labels. In create mode,
   pass the complete title and multiline description as single arguments:

   ```bash
   glab mr create \
     --source-branch <source> \
     --target-branch <target> \
     --title <title> \
     --description <description> \
     --yes
   ```

   This invocation authorizes creating or updating the MR, so no extra confirmation is required.
   Do not push, force-push, edit commits, or create a source branch as part of this skill. If the
   command fails, report the exact error and leave repository state unchanged.

7. **Report the result.** Return the MR URL, source and target branches, title, and whether it
   was created or updated. If the command output does not contain a URL, retrieve the matching
   MR with the same filtered `glab mr list` query and return its `web_url`.

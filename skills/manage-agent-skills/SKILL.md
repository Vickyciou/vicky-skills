---
name: manage-agent-skills
description: Manage personal AI-agent skills in central collections and keep them linked across Claude and Agents/Codex. Use when creating, installing, importing, validating, grouping, linking, synchronizing, inspecting, or repairing Vicky's shared skills.
---

# Manage Agent Skills

Keep each real skill under a collection in `~/Developer/Skills`. Expose skills through symlinks in `~/.claude/skills` and `~/.agents/skills`.

Run every manager command with working directory `~/Developer/Skills/vicky-skills/skills/manage-agent-skills`.

## Guardrails

- Keep the central copy authoritative; keep agent-specific destinations as symlinks.
- Preserve real files, real directories, and unrelated symlinks found at a destination.
- Preserve third-party source. Report platform-specific frontmatter or validator warnings before proposing an adaptation.
- Resolve conflicts with the user before renaming, merging, replacing, or removing anything.

## Workflow

### 1. Select the source root

- For Vicky's skills, use `~/Developer/Skills/vicky-skills/skills`.
- For another collection, use `~/Developer/Skills/<collection-name>`.

Pass the selected directory as `--central-root`. Keep every managed skill as its direct child, named in lowercase hyphen-case and containing `SKILL.md`.

Complete this step when every requested skill has one unambiguous destination under the selected source root.

### 2. Prepare the source

Inspect the selected destination before writing. Create, install, or import the complete skill there only when the destination is free. When generation requires a temporary directory, validate there first and then copy the complete directory into the source root.

Use the relevant skill validator. If it cannot start, report the tool failure separately from source validity and use an equivalent local schema check when safe. Treat a third-party platform extension as a compatibility finding: preserve it, explain which validator rejects it, and request approval before changing vendor content.

Complete this step when each requested directory contains `SKILL.md` and every validation result is either successful or reported as a specific preserved compatibility finding.

### 3. Preflight the links

For one skill, run:

```bash
python3 scripts/manage_skills.py --central-root "<source-root>" link "<skill-name>" --dry-run
```

For every direct child of a source root, run:

```bash
python3 scripts/manage_skills.py --central-root "<source-root>" sync --dry-run
```

Proceed when every destination is missing or already linked to the exact source. A real file, real directory, or differently targeted symlink is a conflict: stop, identify its type and target, and ask the user to choose its disposition.

### 4. Create the links

Repeat the successful preflight command without `--dry-run`. Use `link` for a single skill and `sync` for the whole selected source root.

The manager creates missing target directories and links, preserves correct links, and returns a nonzero status for conflicts.

### 5. Verify completion

Run:

```bash
python3 scripts/manage_skills.py --central-root "<source-root>" status
```

Complete the task only when `status` exits zero and both destination links for every requested skill resolve to its exact central source. Report the source root, skill count, link count, and any preserved compatibility findings.

## Isolated checks

For testing, repeat `--target <test-directory>` before the subcommand. Supplying any `--target` values replaces the default Claude and Agents destinations. Keep all global options before `link`, `sync`, or `status`.

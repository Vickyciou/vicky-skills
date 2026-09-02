#!/usr/bin/env python3
"""Safely expose centrally managed skills through symbolic links."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_CENTRAL_ROOT = Path("~/Developer/Skills/vicky-skills/skills").expanduser()
DEFAULT_TARGETS = (Path.home() / ".claude/skills", Path.home() / ".agents/skills")


@dataclass(frozen=True)
class LinkState:
    label: str
    healthy: bool


def lexists(path: Path) -> bool:
    return os.path.lexists(path)


def central_skills(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError(f"Central skills directory does not exist: {root}")
    return sorted(
        (
            item
            for item in root.iterdir()
            if not item.name.startswith(".")
            and item.is_dir()
            and (item / "SKILL.md").is_file()
        ),
        key=lambda item: item.name,
    )


def named_skill(root: Path, name: str) -> Path:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("Skill name must be one direct child name")
    skill = root / name
    if not skill.is_dir():
        raise ValueError(f"Skill directory does not exist: {skill}")
    if not (skill / "SKILL.md").is_file():
        raise ValueError(f"Skill is missing SKILL.md: {skill}")
    return skill


def link_state(destination: Path, source: Path) -> LinkState:
    if not lexists(destination):
        return LinkState("missing", False)
    if not destination.is_symlink():
        kind = "directory" if destination.is_dir() else "file"
        return LinkState(f"conflict ({kind})", False)
    try:
        raw_target = os.readlink(destination)
        resolved_target = (destination.parent / raw_target).resolve(strict=False)
    except OSError as error:
        return LinkState(f"conflict (unreadable symlink: {error})", False)
    expected = source.resolve(strict=True)
    if resolved_target == expected:
        return LinkState("linked", True)
    return LinkState(f"conflict (symlink -> {raw_target})", False)


def ensure_link(source: Path, target_root: Path, dry_run: bool) -> LinkState:
    destination = target_root / source.name
    state = link_state(destination, source)
    if state.healthy:
        print(f"OK       {destination} -> {source}")
        return state
    if state.label != "missing":
        print(f"CONFLICT {destination}: {state.label}", file=sys.stderr)
        return state
    if dry_run:
        print(f"CREATE   {destination} -> {source} (dry run)")
        return LinkState("would create", True)
    target_root.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source, target_is_directory=True)
    print(f"CREATED  {destination} -> {source}")
    return LinkState("linked", True)


def link_skills(skills: Iterable[Path], targets: Iterable[Path], dry_run: bool) -> int:
    healthy = True
    for skill in skills:
        for target in targets:
            healthy = ensure_link(skill, target, dry_run).healthy and healthy
    return 0 if healthy else 1


def show_status(skills: Iterable[Path], targets: Iterable[Path]) -> int:
    healthy = True
    for skill in skills:
        print(skill.name)
        for target in targets:
            destination = target / skill.name
            state = link_state(destination, skill)
            marker = "OK" if state.healthy else "ISSUE"
            print(f"  {marker:<5} {destination}: {state.label}")
            healthy = state.healthy and healthy
    return 0 if healthy else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Link centrally managed skills into Claude and Agents skill directories."
    )
    parser.add_argument(
        "--central-root",
        type=Path,
        default=DEFAULT_CENTRAL_ROOT,
        help=f"central source directory (default: {DEFAULT_CENTRAL_ROOT})",
    )
    parser.add_argument(
        "--target",
        action="append",
        type=Path,
        dest="targets",
        help="destination skills directory; repeat to use multiple targets",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="link every valid central skill")
    sync_parser.add_argument("--dry-run", action="store_true", help="show changes only")

    link_parser = subparsers.add_parser("link", help="link one central skill")
    link_parser.add_argument("skill_name", help="name of a direct child of central root")
    link_parser.add_argument("--dry-run", action="store_true", help="show changes only")

    subparsers.add_parser("status", help="report link health for all central skills")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.central_root.expanduser().resolve(strict=False)
    targets = tuple(
        target.expanduser().resolve(strict=False)
        for target in (args.targets if args.targets else DEFAULT_TARGETS)
    )
    try:
        if args.command == "link":
            return link_skills([named_skill(root, args.skill_name)], targets, args.dry_run)
        skills = central_skills(root)
        if not skills:
            print(f"No skill directories containing SKILL.md found in {root}", file=sys.stderr)
            return 1
        if args.command == "sync":
            return link_skills(skills, targets, args.dry_run)
        return show_status(skills, targets)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

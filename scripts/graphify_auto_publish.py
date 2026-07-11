#!/usr/bin/env python3
"""Commit and push durable Graphify outputs after a successful rebuild."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path, PurePosixPath


COMMIT_MESSAGE = """chore: Refresh Graphify snapshot

- Record durable knowledge-graph outputs after a source change
- Keep generated project context synchronized with the upstream branch
"""

_DURABLE_DOTFILES = {
    ".graphify_analysis.json",
    ".graphify_labels.json",
    ".graphify_labels.json.sig",
}
_LOCAL_NAMES = {
    ".graphify_python",
    ".graphify_root",
    ".vocab.txt",
    ".graphify_learning.json",
    ".needs_update",
}
_LOCAL_DIRECTORIES = {"memory", "reflections"}
_BACKUP_COMPONENT = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T_-].*)?$")


class PublishError(RuntimeError):
    """A safe publishing precondition was not met."""


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_paths(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [item.decode("utf-8", "surrogateescape") for item in result.stdout.split(b"\0") if item]


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(result.stdout.strip()).resolve()


def is_durable_graphify_path(path: str) -> bool:
    item = PurePosixPath(path)
    if not item.parts or item.parts[0] != "graphify-out" or len(item.parts) == 1:
        return False

    relative_parts = item.parts[1:]
    name = relative_parts[-1]
    if name in _LOCAL_NAMES or name == "stat-index.json":
        return False
    if any(part in _LOCAL_DIRECTORIES for part in relative_parts[:-1]):
        return False
    if any(_BACKUP_COMPONENT.fullmatch(part) for part in relative_parts[:-1]):
        return False
    if name.endswith(".lock") or "rebuild-lock" in name:
        return False

    if relative_parts[0] == "cache":
        return len(relative_parts) >= 3 and relative_parts[1] == "ast" and name.endswith(".json")

    if name.startswith(".graphify_"):
        return name in _DURABLE_DOTFILES
    return True


@contextmanager
def publisher_lock(root: Path):
    lock_path_text = _git(root, "rev-parse", "--git-path", "graphify-auto-publish.lock").stdout.strip()
    lock_path = Path(lock_path_text)
    if not lock_path.is_absolute():
        lock_path = root / lock_path
    try:
        lock_path.mkdir(parents=False)
    except FileExistsError as exc:
        raise PublishError(f"another Graphify publisher holds {lock_path}") from exc
    try:
        yield
    finally:
        lock_path.rmdir()


def _require_branch_and_upstream(root: Path) -> tuple[str, str]:
    branch_result = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch_result.returncode != 0:
        raise PublishError("refusing to publish from detached HEAD")
    branch = branch_result.stdout.strip()

    upstream_result = _git(
        root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    )
    if upstream_result.returncode != 0 or not upstream_result.stdout.strip():
        raise PublishError(f"branch {branch!r} has no configured upstream")
    return branch, upstream_result.stdout.strip()


def _durable_changes(root: Path) -> list[str]:
    tracked = _git_paths(root, "diff", "--name-only", "-z", "--", "graphify-out")
    untracked = _git_paths(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        "graphify-out",
    )
    return sorted({path for path in tracked + untracked if is_durable_graphify_path(path)})


def publish() -> int:
    root = repository_root()
    branch, upstream = _require_branch_and_upstream(root)

    with publisher_lock(root):
        staged = _git_paths(root, "diff", "--cached", "--name-only", "-z", "--", "graphify-out")
        if staged:
            formatted = "\n  ".join(staged)
            raise PublishError(
                "refusing to overwrite manually staged Graphify files:\n  " + formatted
            )

        paths = _durable_changes(root)
        if not paths:
            print("[graphify publish] no durable Graphify changes to publish")
            return 0

        _git(root, "add", "-A", "--", *paths)
        env = os.environ.copy()
        env["GRAPHIFY_SKIP_HOOK"] = "1"
        commit = subprocess.run(
            ["git", "commit", "--only", "-F", "-", "--", *paths],
            cwd=root,
            env=env,
            input=COMMIT_MESSAGE,
            text=True,
        )
        if commit.returncode != 0:
            raise PublishError("failed to create the Graphify snapshot commit")

        pushed = subprocess.run(["git", "push"], cwd=root)
        if pushed.returncode != 0:
            raise PublishError(
                "push was rejected; the local Graphify snapshot commit remains at HEAD "
                f"on {branch!r}. Resolve the upstream divergence from {upstream!r} and push normally."
            )

        print(f"[graphify publish] committed and pushed {len(paths)} durable file(s) on {branch}")
        return 0


def main() -> int:
    try:
        return publish()
    except (PublishError, subprocess.CalledProcessError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.strip() if exc.stderr else str(exc)
        else:
            detail = str(exc)
        print(f"[graphify publish] ERROR: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

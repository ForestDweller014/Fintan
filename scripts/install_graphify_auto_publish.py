#!/usr/bin/env python3
"""Extend Graphify's installed post-commit hook with automatic publishing."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


START_MARKER = "    # graphify-auto-publish-start"
END_MARKER = "    # graphify-auto-publish-end"
REBUILD_ANCHOR = "    _rebuild_code(_root, changed_paths=changed, force=_force)\n"
FOLLOWING_ANCHOR = "    # Refresh the work-memory lessons doc when saved Q&A outcomes exist\n"
INJECTION = f"""{START_MARKER}
    import subprocess as _graphify_publish_subprocess
    _publisher = _root / 'scripts' / 'graphify_auto_publish.py'
    if not _publisher.is_file():
        print(f'[graphify hook] publisher not found: {{_publisher}}')
        sys.exit(1)
    _published = _graphify_publish_subprocess.run([sys.executable, str(_publisher)], cwd=_root)
    if _published.returncode != 0:
        print(f'[graphify hook] publisher failed with exit code {{_published.returncode}}')
        sys.exit(_published.returncode)
{END_MARKER}
"""


class InstallError(RuntimeError):
    """The hook is absent or does not match the supported Graphify layout."""


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(result.stdout.strip()).resolve()


def hook_path(root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks/post-commit"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else root / path


def patch_hook(path: Path) -> bool:
    if not path.is_file():
        raise InstallError("Graphify post-commit hook is missing; run 'graphify hook install' first")

    content = path.read_text(encoding="utf-8")
    has_start = START_MARKER in content
    has_end = END_MARKER in content
    if has_start and has_end:
        return False
    if has_start or has_end:
        raise InstallError("found an incomplete Graphify auto-publish marker block")

    if content.count("# graphify-hook-start") != 1 or content.count("# graphify-hook-end") != 1:
        raise InstallError("post-commit hook does not contain one recognized Graphify block")
    expected = REBUILD_ANCHOR + FOLLOWING_ANCHOR
    if content.count(REBUILD_ANCHOR) != 1 or expected not in content:
        raise InstallError(
            "unknown Graphify hook layout; reinstall Graphify's hook or update this installer"
        )

    updated = content.replace(REBUILD_ANCHOR, REBUILD_ANCHOR + INJECTION, 1)
    original_mode = stat.S_IMODE(path.stat().st_mode)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(updated)
        temporary_path = Path(temporary.name)
    try:
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return True


def main() -> int:
    try:
        root = repository_root()
        changed = patch_hook(hook_path(root))
    except (InstallError, subprocess.CalledProcessError) as exc:
        print(f"[graphify auto-publish installer] ERROR: {exc}", file=sys.stderr)
        return 1

    if changed:
        print("Installed Graphify automatic commit-and-push extension.")
    else:
        print("Graphify automatic commit-and-push extension is already installed.")
    print("Rerun this installer after Graphify reinstalls or upgrades its post-commit hook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

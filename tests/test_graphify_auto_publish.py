import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.install_graphify_auto_publish import (
    END_MARKER,
    START_MARKER,
    patch_hook,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = PROJECT_ROOT / "scripts" / "graphify_auto_publish.py"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class PublisherIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.remote = base / "remote.git"
        self.repo = base / "work"
        git(base, "init", "--bare", str(self.remote))
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Graphify Test")
        git(self.repo, "config", "user.email", "graphify@example.com")

        (self.repo / ".gitignore").write_text(
            "graphify-out/.graphify_python\n"
            "graphify-out/.graphify_root\n"
            "graphify-out/cache/stat-index.json\n",
            encoding="utf-8",
        )
        (self.repo / "graphify-out").mkdir()
        (self.repo / "graphify-out" / "graph.json").write_text("old\n", encoding="utf-8")
        (self.repo / "source.py").write_text("old = True\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "test: Seed repository")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        git(self.repo, "push", "-u", "origin", "main")

    def run_publisher(self, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(PUBLISHER)],
            cwd=self.repo,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_commits_and_pushes_only_durable_outputs(self):
        (self.repo / "graphify-out" / "graph.json").write_text("new\n", encoding="utf-8")
        (self.repo / "graphify-out" / "graph.html").write_text("<html/>\n", encoding="utf-8")
        ast = self.repo / "graphify-out" / "cache" / "ast" / "v1"
        ast.mkdir(parents=True)
        (ast / "entry.json").write_text("{}\n", encoding="utf-8")

        (self.repo / "source.py").write_text("new = True\n", encoding="utf-8")
        git(self.repo, "add", "source.py")

        local_files = [
            self.repo / "graphify-out" / ".graphify_python",
            self.repo / "graphify-out" / ".graphify_root",
            self.repo / "graphify-out" / "cache" / "stat-index.json",
        ]
        for path in local_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("local\n", encoding="utf-8")

        result = self.run_publisher()

        self.assertIn("committed and pushed 3 durable file(s)", result.stdout)
        self.assertEqual(
            git(self.repo, "log", "-1", "--format=%s").stdout.strip(),
            "chore: Refresh Graphify snapshot",
        )
        self.assertIn(
            "Record durable knowledge-graph outputs",
            git(self.repo, "log", "-1", "--format=%b").stdout,
        )
        self.assertEqual(
            git(self.repo, "diff", "--cached", "--name-only").stdout.strip(),
            "source.py",
        )
        self.assertEqual(
            git(self.repo, "rev-parse", "HEAD").stdout,
            git(self.repo, "rev-parse", "origin/main").stdout,
        )
        remote_head = git(self.remote, "rev-parse", "refs/heads/main").stdout
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout, remote_head)

        committed = set(git(self.repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines())
        self.assertEqual(
            committed,
            {
                "graphify-out/cache/ast/v1/entry.json",
                "graphify-out/graph.html",
                "graphify-out/graph.json",
            },
        )
        for path in local_files:
            self.assertTrue(path.exists())
            tracked = git(self.repo, "ls-files", "--error-unmatch", str(path.relative_to(self.repo)), check=False)
            self.assertNotEqual(tracked.returncode, 0)

    def test_refuses_manually_staged_graphify_files(self):
        graph = self.repo / "graphify-out" / "graph.json"
        graph.write_text("manual\n", encoding="utf-8")
        git(self.repo, "add", "graphify-out/graph.json")

        result = self.run_publisher(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manually staged Graphify files", result.stderr)
        self.assertEqual(git(self.repo, "rev-list", "--count", "HEAD").stdout.strip(), "1")


class HookInstallerTest(unittest.TestCase):
    HOOK = """#!/bin/sh
# graphify-hook-start
\"$GRAPHIFY_PYTHON\" -c \"_src = '''
from graphify.watch import _rebuild_code
    _rebuild_code(_root, changed_paths=changed, force=_force)
    # Refresh the work-memory lessons doc when saved Q&A outcomes exist
'''\"
# graphify-hook-end
"""

    def test_patches_after_rebuild_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            hook = Path(directory) / "post-commit"
            hook.write_text(self.HOOK, encoding="utf-8")
            hook.chmod(0o751)

            self.assertTrue(patch_hook(hook))
            first = hook.read_text(encoding="utf-8")
            self.assertFalse(patch_hook(hook))
            self.assertEqual(first, hook.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(hook.stat().st_mode), 0o751)
            self.assertEqual(first.count(START_MARKER), 1)
            self.assertEqual(first.count(END_MARKER), 1)
            self.assertLess(first.index("_rebuild_code("), first.index(START_MARKER))
            self.assertLess(first.index(END_MARKER), first.index("# Refresh the work-memory"))
            self.assertIn("[sys.executable, str(_publisher)]", first)


if __name__ == "__main__":
    unittest.main()

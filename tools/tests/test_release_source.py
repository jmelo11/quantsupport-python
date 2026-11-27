"""Regression checks for release/Pages ordering and complete Excel downloads."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/release"))

import release_source as downloads


class ReleaseSelectionTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="release-selection-")
        self.addCleanup(directory.cleanup)
        self.repository = Path(directory.name)
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "Release test")
        self.git("config", "user.email", "release-test@example.invalid")
        self.first = self.reserve("0.1.12", "42")
        self.latest = self.reserve("0.1.13", "99")
        self.git("update-ref", "refs/remotes/origin/main", self.latest)

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repository, text=True
        ).strip()

    def reserve(self, version, run):
        (self.repository / "Cargo.toml").write_text(
            f'[workspace.package]\nversion = "{version}"\n'
        )
        self.git("add", "Cargo.toml")
        self.git(
            "commit",
            "--quiet",
            "-m",
            f"Version {version}",
            "-m",
            f"Release-Run-ID: {run}",
        )
        self.git("tag", f"v{version}")
        return self.git("rev-parse", "HEAD")

    def command(self, *args):
        if args[0] == "git":
            return self.git(*args[1:])
        self.assertEqual(
            args, ("gh", "release", "view", "--repo", "owner/repo", "--json", "tagName")
        )
        return json.dumps({"tagName": "v0.1.13"})

    def test_release_run_keeps_its_version_after_a_newer_main_push(self):
        with patch.object(downloads, "command", side_effect=self.command):
            self.assertEqual(
                downloads.resolve("owner/repo", run_id="42"),
                {"tag": "v0.1.12", "ref": self.first},
            )

    def test_manual_tag_selects_the_same_source_as_the_downloads(self):
        with patch.object(downloads, "command", side_effect=self.command):
            self.assertEqual(
                downloads.resolve("owner/repo", tag="v0.1.12"),
                {"tag": "v0.1.12", "ref": self.first},
            )
            self.assertEqual(
                downloads.resolve("owner/repo"), {"tag": "v0.1.13", "ref": self.latest}
            )

    def test_missing_version_commit_and_wrong_tag_fail_explicitly(self):
        with patch.object(downloads, "command", side_effect=self.command):
            with self.assertRaisesRegex(RuntimeError, "No version commit found.*123"):
                downloads.resolve("owner/repo", run_id="123")
            self.git("tag", "--force", "v0.1.12", self.latest)
            with self.assertRaisesRegex(
                RuntimeError, "does not point to Release workflow 42"
            ):
                downloads.resolve("owner/repo", run_id="42")


if __name__ == "__main__":
    unittest.main()

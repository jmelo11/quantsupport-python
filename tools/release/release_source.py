"""Resolve a completed local Release run or published tag for documentation."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import tomllib


def command(*arguments):
    result = subprocess.run(arguments, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or f"Command failed: {arguments[0]}"
        )
    return result.stdout.strip()


def resolve(repository, run_id=None, tag=None):
    """A release run reserves its version in a signed commit with this trailer."""
    if run_id:
        if not run_id.isdecimal():
            raise ValueError("Expected a numeric Release workflow run ID")
        if tag:
            raise ValueError("Select either a Release workflow run or a tag")
        ref = command(
            "git",
            "log",
            "origin/main",
            "--format=%H",
            "-1",
            f"--grep=^Release-Run-ID: {run_id}$",
        )
        if not ref:
            raise RuntimeError(f"No version commit found for Release workflow {run_id}")
        manifest = tomllib.loads(command("git", "show", f"{ref}:Cargo.toml"))
        tag = "v" + manifest["workspace"]["package"]["version"]
    else:
        ref = None
        if not tag:
            tag = json.loads(
                command(
                    "gh", "release", "view", "--repo", repository, "--json", "tagName"
                )
            )["tagName"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", tag):
        raise ValueError(f"Invalid release tag: {tag!r}")
    tagged_ref = command("git", "rev-parse", f"refs/tags/{tag}^{{commit}}")
    if ref and tagged_ref != ref:
        raise RuntimeError(
            f"{tag} does not point to Release workflow {run_id}'s version commit"
        )
    return {"ref": tagged_ref, "tag": tag}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--tag")
    args = parser.parse_args()
    selected = resolve(args.repository, args.run_id or None, args.tag or None)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        for key, value in selected.items():
            output.write(f"{key}={value}\n")
    print(f"Selected {selected['tag']} ({selected['ref']})")

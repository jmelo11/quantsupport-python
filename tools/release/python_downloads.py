"""Stage Python release assets and generate their standalone hosted page."""

import argparse
import json
import os
import re
import shutil
import subprocess
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote


def command(*arguments):
    result = subprocess.run(arguments, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or f"Command failed: {arguments[0]}"
        )
    return result.stdout.strip()


PYTHONS = ("3.11", "3.12", "3.13", "3.14")
PLATFORMS = (
    ("Windows", "Intel / AMD x64"),
    ("Windows", "ARM64"),
    ("macOS", "Apple silicon ARM64"),
    ("Linux", "Intel / AMD x64"),
    ("Linux", "ARM64"),
)


def version(tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"Expected a stable release tag, got {tag!r}")
    return tuple(map(int, tag[1:].split(".")))


def packages(release):
    """Read actual uploaded assets; never invent links for missing packages."""
    tag = release["tagName"]
    version(tag)
    available = {
        asset["name"]
        for asset in release["assets"]
        if asset.get("size", 0) > 0 and asset.get("state") == "uploaded"
    }
    result = {}
    for name in sorted(available):
        match = re.fullmatch(
            rf"quantsupport-{re.escape(tag[1:])}-cp(311|312|313|314)-cp\1-(.+)\.whl",
            name,
        )
        if not match:
            continue
        python = f"3.{match[1][1:]}"
        platform = match[2]
        if platform == "win_amd64":
            target = PLATFORMS[0]
        elif platform == "win_arm64":
            target = PLATFORMS[1]
        elif platform.startswith("macosx_") and platform.endswith("_arm64"):
            target = PLATFORMS[2]
        elif platform.startswith("manylinux_") and platform.endswith("_x86_64"):
            target = PLATFORMS[3]
        elif platform.startswith("manylinux_") and platform.endswith("_aarch64"):
            target = PLATFORMS[4]
        else:
            continue
        key = (*target, python)
        if key in result:
            raise RuntimeError(f"Release {tag}: multiple wheels for {key}")
        portable = name.removesuffix(".whl") + "-portable.zip"
        result[key] = {
            "wheel": name,
            "portable": portable if portable in available else None,
        }
    return result


def release(repository, tag):
    result = json.loads(
        command(
            "gh",
            "release",
            "view",
            tag,
            "--repo",
            repository,
            "--json",
            "tagName,assets",
        )
    )
    if result["tagName"] != tag:
        raise RuntimeError(f"Requested {tag}, received {result['tagName']}")
    return result


def select(repository, tag):
    """Anchor to the deployed source, even if another release has just finished."""
    current = release(repository, tag)
    current_packages = packages(current)
    missing = [
        (os, arch, python)
        for os, arch in PLATFORMS
        for python in PYTHONS
        if not current_packages.get((os, arch, python), {}).get("portable")
    ]
    if missing:
        raise RuntimeError(
            f"Release {tag} is missing Python wheels or folder ZIPs: {missing}"
        )
    listing = json.loads(
        command(
            "gh",
            "release",
            "list",
            "--repo",
            repository,
            "--limit",
            "100",
            "--exclude-drafts",
            "--exclude-pre-releases",
            "--json",
            "tagName",
        )
    )
    candidates = [
        item["tagName"]
        for item in listing
        if re.fullmatch(r"v\d+\.\d+\.\d+", item["tagName"])
        and version(item["tagName"]) < version(tag)
    ]
    selected = [(tag, current_packages)]
    for previous in sorted(set(candidates), key=version, reverse=True):
        previous_packages = packages(release(repository, previous))
        if previous_packages:
            selected.append((previous, previous_packages))
            break
    return selected


PACKAGE_INTRODUCTION = """<p>Choose your operating system, architecture and Python version below.
Both wheels and folder ZIPs contain the compiled library, the Python modules,
the type stubs (<code>.pyi</code>) and the <code>py.typed</code> marker.
Keep all of these files together.</p>
<p>To use a folder ZIP, install pandas with
<code>python -m pip install pandas</code>, extract the ZIP and add its
<code>site-packages</code> directory to Python's search path.</p>
"""

NO_RELEASE_NOTICE = """<p>No packages have been published yet. Until the first release,
<a href="guide/first-valuation.html">build QuantSupport from source</a>.</p>
"""


def render(repository, selected, local_prefix=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected repository owner/name")
    tables = []
    for tag, entries in selected:
        rows = []
        for operating_system, arch in PLATFORMS:
            cells = []
            for python in PYTHONS:
                entry = entries.get((operating_system, arch, python))
                links = []
                for kind, label in (("portable", "Folder ZIP"), ("wheel", "Wheel")):
                    if entry and entry.get(kind):
                        if local_prefix is not None and tag == selected[0][0]:
                            url = f"{local_prefix}/{quote(tag, safe='')}/{quote(entry[kind], safe='')}"
                        else:
                            url = (
                                f"https://github.com/{repository}/releases/download/"
                                f"{quote(tag, safe='')}/{quote(entry[kind], safe='')}"
                            )
                        links.append(f'<a href="{escape(url, quote=True)}">{label}</a>')
                cells.append("<td>" + ("<br>".join(links) or "Unavailable") + "</td>")
            rows.append(
                f'<tr><th scope="row">{escape(operating_system)} · {escape(arch)}</th>'
                + "".join(cells)
                + "</tr>"
            )
        headers = '<th scope="col">Operating system / architecture</th>' + "".join(
            f'<th scope="col">Python {python}</th>' for python in PYTHONS
        )
        tables.append(
            f'<h2 id="{tag}">{escape(tag)}</h2>\n'
            f'<div style="overflow-x:auto"><table><caption>QuantSupport {escape(tag)}</caption>'
            f"<thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        )
    return "\n".join(tables)


def stage(repository, tag, page, destination):
    page = Path(page)
    destination = Path(destination)
    selected = select(repository, tag)
    names = sorted(
        {name for entry in selected[0][1].values() for name in entry.values() if name}
    )
    with TemporaryDirectory(prefix="quantsupport-python-assets-") as temporary:
        arguments = [
            "gh",
            "release",
            "download",
            tag,
            "--repo",
            repository,
            "--dir",
            temporary,
        ]
        for name in names:
            arguments.extend(["--pattern", name])
        command(*arguments)
        downloaded = Path(temporary)
        for name in names:
            asset = downloaded / name
            if not asset.is_file() or asset.stat().st_size == 0:
                raise RuntimeError(f"Release {tag}: download missing or empty: {name}")
        # Stage the selected release alongside Excel's files. Previous releases
        # remain hosted on GitHub so Pages retains one set of large binaries.
        release_directory = destination / tag
        release_directory.mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copy2(downloaded / name, release_directory / name)
    prefix = Path(os.path.relpath(destination, page.parent)).as_posix()
    tables = render(repository, selected, local_prefix=prefix)
    write_page(page, PACKAGE_INTRODUCTION + tables)


def write_placeholder(page):
    """Write the download page for a site published before the first release."""
    write_page(page, NO_RELEASE_NOTICE)


def write_page(page, body):
    source = (
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuantSupport Python packages</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 72rem; margin: 3rem auto; padding: 0 1rem; }
table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
th, td { padding: .75rem; border-bottom: 1px solid #ddd; text-align: left; }
caption { text-align: left; margin-bottom: .75rem; }
a { color: #1763a6; }
pre { padding: 1rem; background: #f5f5f5; overflow-x: auto; }
nav { margin-bottom: 2rem; }
</style>
</head>
<body><h1>QuantSupport Python packages</h1>
<nav aria-label="Python documentation">
<a href="guide/first-valuation.html">Installation and first valuation</a> ·
<a href="../autoapi/quantsupport/index.html">Classes and methods</a> ·
<a href="#editor-support">Autocomplete and linting setup</a>
</nav>
"""
        + body
        + """
<h2 id="editor-support">Autocomplete and linting for folder ZIPs</h2>
<p>Adding the directory with <code>sys.path.insert</code> lets your code import
the package. Editors and type checkers also need the directory to show methods,
parameter hints and type errors. In your editor, select the same Python
interpreter that runs your code.</p>
<p>For VS Code/Pylance, add the extracted directory to your workspace's
<code>.vscode/settings.json</code> (merge with existing settings):</p>
<pre><code>{
  "python.analysis.extraPaths": ["/path/to/extracted-folder/site-packages"]
}</code></pre>
<p>For command-line Pyright, use the same directory in
<code>pyrightconfig.json</code> under <code>extraPaths</code>.
For mypy, add it to your project's <code>mypy.ini</code>:</p>
<pre><code>[mypy]
mypy_path = /path/to/extracted-folder/site-packages</code></pre>
<p>Optional editor dependencies can be installed separately:</p>
<pre><code>python -m pip install pandas-stubs "typing-extensions&gt;=4.15"</code></pre>
<p>Check which package your application actually imports:</p>
<pre><code>import quantsupport as qs
print(qs.__file__)
help(qs.PricingContext.evaluate)</code></pre>
<p>Browse the <a href="../autoapi/quantsupport/index.html">API reference</a>
for constructors, methods, properties and accepted parameters.</p>
</body>
</html>
"""
    )
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(source, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", help="Release to stage; omit to write the no-release page")
    parser.add_argument("--page", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.tag:
        stage(args.repository, args.tag, args.page, args.destination)
    else:
        write_placeholder(args.page)


if __name__ == "__main__":
    main()

"""Force a consistent React version across the invenio_assets.webpack bundle merge.

Several upstream Invenio packages we depend on transitively declare mismatched
"react"/"react-dom" npm version ranges (some ^16.x, some already ^17.x) --
either inline in a webpack.py dict, or (oarepo's own bundle) indirected
through a react-dependencies.json file loaded by its webpack.py. flask-
webpackext merges every registered NpmPackage's "dependencies" into one
package.json when `invenio webpack create` runs, and raises
MergeConflictError if two packages declare incompatible ranges for the same
npm package. Bumping all of them to an agreeing ^17.0.0 avoids that.

This patches installed site-packages directly (not pyproject.toml/uv.lock),
because none of these packages are otherwise forked or pinned locally --
`uv sync` always re-fetches them fresh, silently reverting this. Idempotent:
safe to run after every install/reset. Recurses under each package's install
directory rather than assuming a single top-level webpack.py, since the exact
file (and even which of webpack.py/react-dependencies.json is authoritative)
has been observed to vary by resolved version.
"""

import importlib.util
import re
import sys
from pathlib import Path

TARGET_VERSION = "^17.0.0"

PACKAGES = [
    "invenio_collections",
    "invenio_communities",
    "invenio_rdm_records",
    "invenio_requests",
    "invenio_search_ui",
    "oarepo",
]

PATCH_FILENAME_GLOBS = ("webpack.py", "react-dependencies*.json")

VERSION_LINE_RE = re.compile(r'("react(?:-dom)?"\s*:\s*)"[^"]*"')


def patch_file(path):
    original = path.read_text()
    patched, count = VERSION_LINE_RE.subn(rf'\g<1>"{TARGET_VERSION}"', original)
    if count == 0:
        return "no react/react-dom keys found", False
    if patched == original:
        return "already up to date", False
    path.write_text(patched)
    return f"patched {count} version line(s)", True


def main():
    changed_any = False
    for package_name in PACKAGES:
        spec = importlib.util.find_spec(package_name)
        if spec is None or spec.origin is None:
            print(f"[skip] {package_name}: not installed")
            continue
        root = Path(spec.origin).parent

        matched_paths = sorted(
            {
                path
                for glob_pattern in PATCH_FILENAME_GLOBS
                for path in root.rglob(glob_pattern)
            }
        )
        if not matched_paths:
            print(f"[skip] {package_name}: no webpack.py/react-dependencies*.json under {root}")
            continue

        for path in matched_paths:
            status, changed = patch_file(path)
            changed_any = changed_any or changed
            print(f"[{'patched' if changed else 'ok'}] {package_name}:{path.relative_to(root)}: {status}")

    if changed_any:
        print(
            "\nReact version patch applied -- rerun `invenio webpack create` "
            "(and `build`) if the assets project was already created."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

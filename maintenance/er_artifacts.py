# SPDX-License-Identifier: Apache-2.0
"""Hash the ER CI handoff and verify it before installing its exact wheels."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

MANIFEST = "er-artifacts.json"


def inventory(root):
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlinks are not portable handoff artifacts")
        if path.is_file() and path != root / MANIFEST:
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not files:
        raise ValueError("empty handoff")
    return files


def commit(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("supply the full lowercase immutable compatible host commit")
    return value


def create(root, host_commit):
    data = {"format": 1, "host_commit": commit(host_commit), "sha256": inventory(root)}
    (root / MANIFEST).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def verify(root, host_commit):
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if data.get("format") != 1 or data.get("host_commit") != commit(host_commit):
        raise ValueError("handoff format/host commit mismatch")
    for name, digest in data.get("sha256", {}).items():
        # Never use an unverified manifest path to open a file.
        p = PurePosixPath(name)
        if (p.is_absolute() or str(p) != name or ".." in p.parts or
                any(c in name for c in "\\:") or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("invalid handoff inventory")
    if inventory(root) != data.get("sha256"):
        raise ValueError("handoff bytes or file inventory changed")
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["create", "verify"])
    p.add_argument("root", type=Path)
    p.add_argument("--host-commit", required=True)
    args = p.parse_args()
    result = (create if args.operation == "create" else verify)(args.root, args.host_commit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Prepare an immutable catalog entry after a reviewed wheel release. No upload."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from texstage.plugins.collection import validate_index
from texstage.plugins.manifest import digest, load_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--url", required=True, help="immutable HTTPS release asset URL")
    parser.add_argument("--output", type=Path, default=Path("catalog/index.json"))
    args = parser.parse_args()
    with zipfile.ZipFile(args.wheel) as wheel:
        path = next(n for n in wheel.namelist() if n.endswith(".dist-info/texstage-plugin.json"))
        manifest = load_manifest(wheel.read(path))
        metadata = wheel.read(path.rsplit("/", 1)[0] + "/METADATA").decode()
        distribution = next(line[6:] for line in metadata.splitlines() if line.startswith("Name: "))
    record = {"id": manifest["id"], "version": manifest["version"], "distribution": distribution,
              "plugin_api": 1, "payload": digest(manifest), "url": args.url,
              "sha256": hashlib.sha256(args.wheel.read_bytes()).hexdigest(), "license": manifest["license"], "withdrawn": False}
    index = json.loads(args.output.read_text()) if args.output.exists() else {"format": 1, "releases": []}
    if any((r["id"], r["version"]) == (record["id"], record["version"]) for r in index["releases"]):
        raise SystemExit("release already listed; never replace a version's bytes")
    index["releases"].append(record)
    validate_index(index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Prepared {args.output}; review and commit it after publishing the verified wheel")


if __name__ == "__main__": main()

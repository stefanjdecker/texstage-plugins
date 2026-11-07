# SPDX-License-Identifier: Apache-2.0
"""Transfer identical FD release-test artifacts between operating systems."""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import re
import shutil
import sys
import zipfile

PROVIDER = "io.github.stefanjdecker.fdlab"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def commit(value):
    if not re.fullmatch(r"[a-f0-9]{40}", value or ""):
        raise ValueError("An exact 40-character host commit is required")
    return value


def inventory(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not permitted in the artifact handoff")
        name = path.relative_to(root).as_posix()
        if path.is_file() and name != "handoff.json":
            result[name] = {"sha256": digest(path), "size": path.stat().st_size}
    return result


def safe(root, name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("Invalid artifact path")
    if any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("Invalid artifact path")
    path = Path(root).joinpath(*name.split("/"))
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("Artifact path escaped the handoff")
    return path


def verify(root, expected_commit):
    root = Path(root).resolve()
    data = json.loads((root / "handoff.json").read_text(encoding="utf-8"))
    assert data["format"] == 1
    assert commit(data["host_commit"]) == commit(expected_commit), "Wrong host commit"
    for name in data["files"]:
        safe(root, name)
    assert inventory(root) == data["files"], "Artifact bytes differ from producer inventory"
    for key in ("host_wheel", "plugin_wheel", "plugin_sdist"):
        assert data[key] in data["files"] and safe(root, data[key]).is_file()
    assert data["host_wheel"].endswith("-py3-none-any.whl")
    assert data["plugin_wheel"].endswith("-py3-none-any.whl")
    for language in ("en", "de"):
        deck = safe(root, f"bundles/{language}/lesson.bundle/deck.json")
        assert json.loads(deck.read_text(encoding="utf-8"))["language"] == language
    assert safe(root, "requirements/dev.txt").is_file()
    assert safe(root, "requirements/build.txt").is_file()
    return data


def installed(root, data):
    from texstage.plugins.catalog import discover
    providers = discover()
    assert {p.id for p in providers} == {PROVIDER}, "Use an FD-only test environment"
    provider = providers[0]
    provider.verify()
    assert provider.requirement() == data["provider"], "Wrong provider payload"
    for key, package in (("host_wheel", "texstage"), ("plugin_wheel", "texstage_fd_lab")):
        module = importlib.import_module(package)
        package_root = Path(module.__file__).resolve().parent
        assert package_root.is_relative_to(Path(sys.prefix).resolve()), "Use installed wheels"
        with zipfile.ZipFile(safe(root, data[key])) as wheel:
            for name in wheel.namelist():
                if name.startswith(package + "/"):
                    relative = name[len(package) + 1:]
                    assert safe(package_root, relative).read_bytes() == wheel.read(name), name


def create(args):
    from texstage.plugins.catalog import discover
    providers = discover()
    assert {p.id for p in providers} == {PROVIDER}, "Use an FD-only producer"
    out = Path(args.output).resolve()
    assert not out.exists(), "Choose a fresh handoff directory"
    out.mkdir(parents=True)
    data = {"format": 1, "host_commit": commit(args.host_commit),
            "provider": providers[0].requirement()}
    for key in ("host_wheel", "plugin_wheel", "plugin_sdist"):
        source = Path(getattr(args, key)).resolve()
        target = out / "wheels" / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        data[key] = target.relative_to(out).as_posix()
    shutil.copytree(args.requirements, out / "requirements")
    shutil.copytree(args.bundles, out / "bundles")
    data["files"] = inventory(out)
    (out / "handoff.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    verify(out, args.host_commit)
    installed(out, data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    produce = sub.add_parser("create")
    for name in ("host-wheel", "plugin-wheel", "plugin-sdist", "requirements", "bundles", "output"):
        produce.add_argument("--" + name, required=True)
    produce.add_argument("--host-commit", required=True)
    for name in ("verify", "installed"):
        consumer = sub.add_parser(name)
        consumer.add_argument("path")
        consumer.add_argument("--host-commit", required=True)
    args = parser.parse_args()
    if args.command == "create":
        data = create(args)
    else:
        data = verify(args.path, args.host_commit)
        if args.command == "installed":
            installed(args.path, data)
    print(json.dumps({"host_commit": data["host_commit"], "provider": data["provider"],
                      "files_verified": len(data["files"])}, indent=2))


if __name__ == "__main__":
    main()

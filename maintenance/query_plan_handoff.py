# SPDX-License-Identifier: Apache-2.0
"""Create and verify a portable Query-plan CI handoff without rebuilding consumers."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import zipfile

PROVIDER = "io.github.stefanjdecker.queryplan"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    root = Path(root).resolve()
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise ValueError(f"Linked handoff entry: {p.relative_to(root)}")
        if p.is_file() and p.relative_to(root).as_posix() != "handoff.json":
            result[p.relative_to(root).as_posix()] = {"sha256": digest(p), "size": p.stat().st_size}
    return result


def commit(value):
    if not re.fullmatch(r"[a-f0-9]{40}", value or ""):
        raise ValueError("Supply the full reviewed compatible TeXStage commit SHA; branches and tags are not release pins.")
    return value


def installed():
    import texstage
    from texstage.plugins.catalog import discover
    providers = discover()
    assert {p.id for p in providers} == {PROVIDER}, "Use a Query-plan-only environment"
    provider = providers[0]
    provider.verify()
    assert provider.root.resolve().is_relative_to(Path(sys.prefix).resolve()), "Use installed wheels"
    host = Path(texstage.__file__).resolve().parent
    assert host.is_relative_to(Path(sys.prefix).resolve()), "Use an installed host wheel"
    files = {p.relative_to(host).as_posix(): digest(p) for p in sorted(host.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts}
    return {"provider": provider.requirement(),
            "host_version": importlib.metadata.version("texstage"),
            "host_resources_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def safe(root, relative):
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("Invalid artifact path")
    parts = relative.split("/")
    if not relative or any(x in ("", ".", "..") for x in parts):
        raise ValueError("Invalid artifact path")
    p = Path(root).joinpath(*parts)
    if not p.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("Artifact path escaped the handoff")
    return p


def verify(root, expected_commit=None):
    root = Path(root).resolve()
    data = json.loads((root / "handoff.json").read_text(encoding="utf-8"))
    assert data["format"] == 1
    commit(data["host_commit"])
    if expected_commit:
        assert data["host_commit"] == commit(expected_commit), "Wrong host commit"
    for name in data["files"]:
        safe(root, name)
    assert inventory(root) == data["files"], "Handoff bytes differ from the producer inventory"
    for name in ("host_wheel", "plugin_wheel", "plugin_sdist"):
        p = safe(root, data[name])
        assert p.is_file() and data[name] in data["files"]
    assert data["host_wheel"].endswith("-py3-none-any.whl")
    assert data["plugin_wheel"].endswith("-py3-none-any.whl")
    assert (safe(root, data["bundle"]) / "deck.json").is_file()
    assert safe(root, "requirements/dev.txt").is_file()
    assert safe(root, "requirements/build.txt").is_file()
    return data


def create(args):
    identity = installed()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    host, plugin, sdist = map(Path, (args.host_wheel, args.plugin_wheel, args.plugin_sdist))
    for p in (host, plugin):
        assert p.name.endswith("-py3-none-any.whl")
    with zipfile.ZipFile(plugin) as z:
        n = next(n for n in z.namelist() if n.endswith(".dist-info/texstage-plugin.json"))
        manifest = json.loads(z.read(n))
        assert manifest["id"] == PROVIDER and manifest["version"] == identity["provider"]["version"]
        from texstage.plugins.manifest import digest as json_digest
        assert json_digest(manifest) == identity["provider"]["payload"], "Plugin wheel differs from installed provider"
        for name, spec in manifest["resources"].items():
            raw = z.read(name)
            assert len(raw) == spec["size"] and hashlib.sha256(raw).hexdigest() == spec["sha256"]
    with zipfile.ZipFile(host) as z:
        files = {n.removeprefix("texstage/"): hashlib.sha256(z.read(n)).hexdigest()
                 for n in sorted(z.namelist()) if n.startswith("texstage/") and not n.endswith("/")}
        fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
        assert fingerprint == identity["host_resources_sha256"], "Host wheel differs from installed runtime"
    paths = {"host_wheel": "host/" + host.name, "plugin_wheel": "plugins/" + plugin.name,
             "plugin_sdist": "plugins/" + sdist.name, "bundle": "lesson.bundle"}
    for name, source in (("host_wheel", host), ("plugin_wheel", plugin), ("plugin_sdist", sdist)):
        target = out / paths[name]
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copytree(args.requirements, out / "requirements")
    shutil.copytree(args.bundle, out / paths["bundle"])
    data = {"format": 1, "host_commit": commit(args.host_commit), **identity, **paths, "files": inventory(out)}
    (out / "handoff.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    verify(out, args.host_commit)
    return data


def install(root, expected_commit=None):
    data = verify(root, expected_commit)
    assert sys.prefix != sys.base_prefix, "Create an isolated virtual environment first"
    root = Path(root).resolve()
    subprocess.run([sys.executable, "-m", "pip", "install", "--require-hashes", "--only-binary=:all:",
                    "-r", str(root / "requirements/dev.txt"), "-r", str(root / "requirements/build.txt")], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps",
                    str(safe(root, data["host_wheel"])), str(safe(root, data["plugin_wheel"]))], check=True)
    check_installed(data)
    return data


def check_installed(data):
    actual = installed()
    for key in ("provider", "host_version", "host_resources_sha256"):
        assert actual[key] == data[key], f"Installed artifact differs: {key}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    make = commands.add_parser("create")
    for name in ("host-wheel", "plugin-wheel", "plugin-sdist", "requirements", "bundle", "host-commit", "output"):
        make.add_argument("--" + name, required=True)
    for action in ("verify", "install", "installed"):
        sub = commands.add_parser(action)
        sub.add_argument("root", type=Path)
        sub.add_argument("--host-commit")
    args = p.parse_args()
    if args.command == "create":
        data = create(args)
    elif args.command == "install":
        data = install(args.root, args.host_commit)
    else:
        data = verify(args.root, args.host_commit)
        if args.command == "installed":
            check_installed(data)
    print(json.dumps({k: data[k] for k in ("host_commit", "host_resources_sha256", "provider")}, indent=2))


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Build independent wheels and prove source-distribution payload parity."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def manifest(path):
    with zipfile.ZipFile(path) as wheel:
        name = next(n for n in wheel.namelist() if n.endswith(".dist-info/texstage-plugin.json"))
        return json.loads(wheel.read(name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    packages = sorted(p.name for p in (ROOT / "plugins").iterdir() if (p / "pyproject.toml").is_file())
    parser.add_argument("--package", action="append", choices=packages,
                        help="Build only this package; repeat for an isolated test scenario.")
    args = parser.parse_args()
    out = ROOT / "dist"; out.mkdir(exist_ok=True)
    reports = []
    for source in sorted((ROOT / "plugins").iterdir()):
        if not (source / "pyproject.toml").is_file(): continue
        if args.package and source.name not in args.package: continue
        subprocess.run([sys.executable, "-m", "build", "--wheel", "--sdist", "--no-isolation"], cwd=source, check=True)
        wheels = list((source / "dist").glob("*.whl"))
        assert len(wheels) == 1, "use a clean checkout for release builds"
        wheel = wheels[0]
        assert wheel.name.endswith("-py3-none-any.whl")
        sdists = list((source / "dist").glob("*.tar.gz")); assert len(sdists) == 1
        with tempfile.TemporaryDirectory(prefix="texstage-plugin-sdist-") as temp:
            temp = Path(temp)
            with tarfile.open(sdists[0]) as archive: archive.extractall(temp, filter="data")
            unpacked = next(p for p in temp.iterdir() if p.is_dir())
            subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation"], cwd=unpacked, check=True)
            rebuilt = next((unpacked / "dist").glob("*.whl"))
            assert manifest(rebuilt) == manifest(wheel), "sdist rebuild changed provider payload"
        for artifact in (wheel, sdists[0]): shutil.copyfile(artifact, out / artifact.name)
        reports.append({"wheel": wheel.name, "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                        "id": manifest(wheel)["id"], "sdist_parity": True})
    (out / "build-report.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__": main()

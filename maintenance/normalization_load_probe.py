# SPDX-License-Identifier: Apache-2.0
"""Build a synthetic one-/two-item workload with the installed workshop wheel."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from texstage.build.builder import BuildOptions, build
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    source = out / "source"
    source.mkdir(parents=True, exist_ok=True)
    provider = next(p for p in discover() if p.id == "io.github.stefanjdecker.normalizationworkshop")
    provider.verify()
    shutil.copytree(ROOT / "examples/normalization/activities", source / "activities", dirs_exist_ok=True)
    sidecar = json.loads((ROOT / "examples/normalization/lesson.activities.json").read_text(encoding="utf-8"))
    sidecar["items"] = [item for item in sidecar["items"] if item["id"] in ("registration", "classify")]
    (source / "load.activities.json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8", newline="\n")
    tex = r"""\documentclass[aspectratio=169]{beamer}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{texstage}
\usepackage{texstage-normalization-workshop}
\setbeamertemplate{navigation symbols}{}
\begin{document}
\begin{frame}{Synthetic load: one activity}
\normalizationworkshop{registration}{.96\linewidth}{.78\textheight}
\end{frame}
\begin{frame}{Synthetic load: two active activities}
\normalizationworkshop{registration}{.96\linewidth}{.34\textheight}
\normalizationworkshop{classify}{.96\linewidth}{.34\textheight}
\end{frame}
\end{document}
"""
    (source / "load.tex").write_text(tex, encoding="utf-8", newline="\n")
    profile = out / "profile"
    enable(profile, provider.id, provider.version, provider.payload)
    result = build(source / "load.tex", out / "build", BuildOptions(
        stage=True, key="synthetic-load", activities=source / "load.activities.json",
        plugin_data=profile, height=540))
    assert not result.problems, result.problems
    record = {"provider_version": provider.version, "payload": provider.payload,
              "bundle": str(result.bundle), "synthetic": True,
              "files": {str(p.relative_to(result.bundle)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(result.bundle.rglob("*")) if p.is_file()}}
    (out / "build.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record | {"files": len(record["files"])}))


if __name__ == "__main__":
    main()

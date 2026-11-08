# SPDX-License-Identifier: Apache-2.0
"""Inspect, then explicitly enable this example's installed providers."""
import argparse
import json
from pathlib import Path
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.lock import write_lock
from texstage.plugins.policy import catalog_for, enable, read_profile

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable-reviewed", action="store_true",
                        help="Explicitly enable the listed trusted packages in this example's profile.")
    args = parser.parse_args()
    expected = json.loads((ROOT / "required-plugins.json").read_text(encoding="utf-8"))["providers"]
    installed = {p.id: p for p in discover()}
    selected = []
    for req in expected:
        provider = installed.get(req["id"])
        if provider is None or provider.version != req["version"]:
            raise PluginError(f"Install {req['package']}=={req['version']} from the reviewed collection first.")
        selected.append(provider)
    profile = ROOT / "texquiz-out/profile"
    extra = {p["id"] for p in read_profile(profile)["enabled"]} - {p.id for p in selected}
    if extra:
        raise PluginError("Example profile contains unrelated providers: " + ", ".join(sorted(extra)))
    print(json.dumps([p.requirement() for p in selected], indent=2))
    if not args.enable_reviewed:
        print("Inspection only. After review, run with --enable-reviewed.")
        return
    order = {"org.example.distance": 0, "io.github.stefanjdecker.transactionengine": 1}
    for provider in sorted(selected, key=lambda p: (order.get(p.id, 2), p.id)):
        enable(profile, provider.id, provider.version, provider.payload)
    lock = ROOT / "texquiz-out/plugins.lock.json"
    write_lock(lock, catalog_for(profile))
    print(f"Enabled {len(selected)} providers. Lock: {lock}")

if __name__ == "__main__":
    try:
        main()
    except (PluginError, OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

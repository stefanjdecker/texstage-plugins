# SPDX-License-Identifier: Apache-2.0
"""Disposable, loopback-only server for browser conformance tests."""
import argparse
import json
from pathlib import Path

from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable, catalog_for
from texstage.server.app import ServerConfig, create_app
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument("--bundle", type=Path, required=True)
parser.add_argument("--data", type=Path, required=True)
parser.add_argument("--port", type=int, default=18747)
args = parser.parse_args()
for provider in discover(): enable(args.data, provider.id, provider.version, provider.payload)
catalog = catalog_for(args.data)
provider, engine = catalog.capability("org.example.distance.euclidean", engine=True)
(args.data / "test-context.json").write_text(json.dumps({"engine": engine | {
    "url": f"/plugins/{provider.payload}/{engine['module']}", "assets": {}},
    "binding": {"seed": "{}", "references": []}, "text": "3,4", "namespace": "0" * 64}))
app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
    public_url=f"http://127.0.0.1:{args.port}", presenter_key="plugin-demo-key"))
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")

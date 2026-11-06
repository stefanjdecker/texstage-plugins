# SPDX-License-Identifier: Apache-2.0
"""Disposable loopback server for the prepared relational lesson."""
import argparse
from pathlib import Path
import uvicorn
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable
from texstage.server.app import ServerConfig, create_app

parser = argparse.ArgumentParser()
parser.add_argument("--bundle", type=Path, required=True)
parser.add_argument("--data", type=Path, required=True)
parser.add_argument("--port", type=int, default=18749)
args = parser.parse_args()
for provider in discover():
    enable(args.data, provider.id, provider.version, provider.payload)
app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
    public_url=f"http://127.0.0.1:{args.port}", presenter_key="plugin-demo-key"))
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


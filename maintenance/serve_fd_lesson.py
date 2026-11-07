# SPDX-License-Identifier: Apache-2.0
"""Disposable FD test server with a reserved port and private readiness file."""
import argparse
import json
from pathlib import Path
import socket

import uvicorn
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable
from texstage.server.app import ServerConfig, create_app

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle', type=Path, required=True)
parser.add_argument('--data', type=Path, required=True)
parser.add_argument('--port', type=int, default=0)
args = parser.parse_args()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    listener.bind(('127.0.0.1', args.port))
    listener.listen(128)
    port = listener.getsockname()[1]
    for provider in discover():
        enable(args.data, provider.id, provider.version, provider.payload)
    app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
        public_url=f'http://127.0.0.1:{port}', presenter_key='plugin-demo-key'))
    (args.data / 'fd-ready.json').write_text(json.dumps({'port': port}), encoding='utf-8')
    uvicorn.Server(uvicorn.Config(app, log_level='warning')).run(sockets=[listener])

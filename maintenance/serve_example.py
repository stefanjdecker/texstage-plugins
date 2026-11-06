# SPDX-License-Identifier: Apache-2.0
"""Disposable, loopback-only server for browser conformance tests."""
import argparse
import json
from pathlib import Path

from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable, catalog_for
from texstage.plugins.contracts import result_contract
from texstage.server.app import ServerConfig, create_app
import uvicorn
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

parser = argparse.ArgumentParser()
parser.add_argument("--bundle", type=Path, required=True)
parser.add_argument("--data", type=Path, required=True)
parser.add_argument("--fault-file", type=Path, help="Local test-only engine response override")
parser.add_argument("--port", type=int, default=18747)
args = parser.parse_args()
for provider in discover(): enable(args.data, provider.id, provider.version, provider.payload)
catalog = catalog_for(args.data)
provider, engine = catalog.capability("org.example.distance.euclidean", engine=True)
(args.data / "test-context.json").write_text(json.dumps({"engine": engine | {
    "url": f"/plugins/{provider.payload}/{engine['module']}", "assets": {},
    "result_contract": result_contract(provider, engine)},
    "binding": {"seed": "{}", "references": []}, "text": "3,4", "namespace": "0" * 64}))
app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
    public_url=f"http://127.0.0.1:{args.port}", presenter_key="plugin-demo-key"))
if args.fault_file:
    # Test harness only: worker requests bypass Playwright route interception in
    # Firefox. Override one engine here, never the evaluator worker or its CSP.
    target = f"/plugins/{provider.payload}/{engine['module']}"

    async def inject_test_engine(request, call_next):
        if request.url.path == target and args.fault_file.is_file():
            return Response(args.fault_file.read_text(encoding="utf-8"),
                            media_type="application/javascript",
                            headers={"Cache-Control": "no-store"})
        response = await call_next(request)
        if request.url.path == target:
            response.headers["Cache-Control"] = "no-store"
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=inject_test_engine)

uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")

# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only A/B probe for WebKit Inspector's conditional-response crash."""
import os

WORKER_PATHS = {
    "/static/stage/plugin-evaluator-worker.js",
    "/static/stage/plugin-contracts-worker.mjs",
}


def wrap_http_diagnostics(app, emit):
    mode = os.environ.get("TEXSTAGE_DIAGNOSTIC_HTTP")
    if not mode:
        return app
    if mode not in {"observe", "worker-200"}:
        raise ValueError("Unknown diagnostic HTTP mode")

    async def wrapped(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        path = scope.get("path", "")
        headers = scope.get("headers", [])
        conditional = any(key in {b"if-none-match", b"if-modified-since"} for key, _ in headers)
        targeted = path in WORKER_PATHS
        if mode == "worker-200" and targeted:
            scope = scope | {"headers": [(key, value) for key, value in headers
                if key not in {b"if-none-match", b"if-modified-since"}]}

        async def measured_send(message):
            if message["type"] == "http.response.start" and path.startswith(("/static/", "/plugins/")):
                response_headers = dict(message.get("headers", []))
                emit("http", path=path, status=message["status"], conditional=conditional,
                     mode=mode, targeted=targeted,
                     csp=response_headers.get(b"content-security-policy", b"").decode())
            await send(message)
        await app(scope, receive, measured_send)
    return wrapped

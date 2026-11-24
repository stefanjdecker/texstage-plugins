# SPDX-License-Identifier: Apache-2.0
"""Run against installed host and provider wheels with the host's dev dependencies, TeX and Chrome."""
import json
import os
from contextlib import contextmanager
from importlib import resources
import re
import secrets
import shutil
import socket
import subprocess
import sysconfig
import threading
import time

from playwright.sync_api import expect, sync_playwright
import uvicorn
from websockets.sync.client import connect

from texstage.server.app import ServerConfig, create_app


@contextmanager
def classroom(bundle, data, key):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        app = create_app(ServerConfig(bundles=[bundle], data_dir=data, presenter_key=key,
                                      public_url=url, workers=1, pool={"spare": False}))
        server = uvicorn.Server(uvicorn.Config(app, log_level="warning", timeout_graceful_shutdown=1))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 30
            while not server.started:
                assert thread.is_alive() and time.monotonic() < deadline, "classroom server did not start"
                time.sleep(0.05)
            yield url
        finally:
            server.should_exit = True
            thread.join(15)
            assert not thread.is_alive(), "classroom server did not stop"


def reply(ws, **message):
    ws.send(json.dumps(message))
    while True:
        result = json.loads(ws.recv(timeout=10))
        if result.get("re") == message["id"]:
            return result


def join(browser, url, pin, name):
    page = browser.new_page(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    page.goto(f"{url}/play?pin={pin}&lang=en")
    page.locator("#nick").fill(name)
    page.locator("#join button").click()
    expect(page.get_by_text("You're in!", exact=True)).to_be_visible()
    return page


def submit(page, text):
    page.locator("#step-line").fill(text)
    page.locator("form.act button[type=submit]").click()


def test_installed_example_from_build_to_reveal(tmp_path):
    cli = shutil.which("texstage", path=sysconfig.get_path("scripts"))
    assert cli is not None, "install the TeXStage wheel in this Python environment"
    source = tmp_path / "closure.tex"
    source.write_bytes(resources.files("texstage_kinds_fd").joinpath("examples/closure.tex").read_bytes())
    key = secrets.token_urlsafe(24)
    data, out = tmp_path / "server", tmp_path / "out"
    subprocess.run([cli, "build", str(source), "--data", str(data), f"--key={key}",
                    "--height", "480", "-o", str(out)], cwd=tmp_path, check=True)
    bundle = out / "closure.bundle"
    deck = json.loads((bundle / "deck.json").read_text(encoding="utf-8"))
    keys = json.loads((bundle / "keys.json").read_text(encoding="utf-8"))["items"]["activity"]["booking"]
    assert deck["kinds"]["fd-closure"]["package"] == "texstage-kinds-fd"
    assert deck["kinds"]["fd-closure"]["api"] == 1
    assert keys["reference"] == keys["referenceKeys"] == ["Booking,Room,Floor"]
    public = json.dumps(deck)
    assert all(private not in public for private in ("referenceKeys", "Booking,Room,Floor"))

    with classroom(bundle, data, key) as url, connect(url.replace("http://", "ws://") + "/ws") as host:
        welcome = reply(host, t="hello", role="host", key=key, deck=deck["deck"], bundle=deck["bundle"], id="hello")
        assert welcome["t"] == "welcome", welcome
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=os.environ.get("TEXSTAGE_BROWSER", "chrome"))
            try:
                ada = join(browser, url, welcome["pin"], "Ada")
                bea = join(browser, url, welcome["pin"], "Bea")
                presenter = browser.new_page()
                presenter.goto(f"{url}/stage?bundle={deck['bundle']}")
                expect(presenter.locator("#pin")).to_have_text(re.compile(r"PIN \d"))
                assert reply(host, t="slide", slide=deck["slides"][0]["id"], id="open")["t"] == "ok"
                submit(ada, "Unknown")
                expect(ada.locator("[data-role=mine]")).to_contain_text("no attribute named Unknown", timeout=15000)
                submit(ada, "{Floor, Booking, Room}")
                submit(bea, "Booking")
                for page in (ada, bea):
                    mine = page.locator("[data-role=mine]")
                    expect(mine).to_contain_text("Set received", timeout=15000)
                    expect(mine).not_to_contain_text("Right ✓")
                    expect(mine).not_to_contain_text("Not right")
                    expect(page.locator("[data-role=award]")).to_be_empty()
                presenter.keyboard.press("ArrowRight")
                expect(ada.locator("[data-role=mine]")).to_contain_text("Right ✓")
                expect(ada.locator("[data-role=award]")).to_have_text("1000 activity points", timeout=15000)
                expect(bea.locator("[data-role=mine]")).to_contain_text("Not right")
                expect(bea.locator("[data-role=award]")).to_have_text("0 activity points", timeout=15000)
            finally:
                browser.close()

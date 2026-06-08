from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable

from streamlit.web import bootstrap


DEFAULT_PORT = 8501
PORT_FILE_NAME = "dashboard_port.txt"


def resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent / "_internal"
    return Path(__file__).resolve().parent.parent


def resolve_app_path(base_dir: Path) -> Path:
    return base_dir / "app.py"


def resolve_port() -> int:
    requested = int(os.environ.get("WORLD_CUP_DASHBOARD_PORT", str(DEFAULT_PORT)))
    if _port_is_available(requested):
        _write_runtime_port(resolve_base_dir(), requested)
        return requested
    for port in range(requested + 1, requested + 25):
        if _port_is_available(port):
            _write_runtime_port(resolve_base_dir(), port)
            return port
    _write_runtime_port(resolve_base_dir(), requested)
    return requested


def runtime_port_path(base_dir: Path) -> Path:
    return base_dir / PORT_FILE_NAME


def _write_runtime_port(base_dir: Path, port: int) -> None:
    try:
        runtime_port_path(base_dir).write_text(str(port), encoding="utf-8")
    except OSError:
        pass


def _port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def configure_environment(base_dir: Path) -> None:
    os.environ.setdefault("DASHBOARD_DATA_DIR", str(base_dir))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


def configure_streamlit_for_current_thread() -> None:
    if threading.current_thread() is threading.main_thread():
        return

    # Streamlit registers process signal handlers during startup. Python only
    # allows that from the main thread, while these launchers keep their UI or
    # readiness watcher alive by starting Streamlit in a worker thread.
    bootstrap._set_up_signal_handler = lambda server: None  # type: ignore[attr-defined]


def wait_for_server(port: int, timeout_seconds: float = 90.0) -> bool:
    deadline = time.time() + timeout_seconds
    health_url = f"http://127.0.0.1:{port}/_stcore/health"

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.5)
    return False


def open_browser(port: int) -> None:
    webbrowser.open(f"http://127.0.0.1:{port}")


def run_streamlit(base_dir: Path, port: int) -> None:
    app_path = resolve_app_path(base_dir)
    if not app_path.exists():
        raise FileNotFoundError(f"Arquivo principal nao encontrado: {app_path}")

    configure_environment(base_dir)
    configure_streamlit_for_current_thread()
    bootstrap.run(
        str(app_path),
        False,
        [],
        {
            "global.developmentMode": False,
            "server.headless": True,
            "server.fileWatcherType": "none",
            "server.port": port,
            "browser.serverPort": port,
            "browser.gatherUsageStats": False,
            "theme.base": "dark",
        },
    )


def start_streamlit_thread(base_dir: Path, port: int) -> threading.Thread:
    thread = threading.Thread(target=run_streamlit, args=(base_dir, port), daemon=False)
    thread.start()
    return thread


def wait_and_notify(
    port: int,
    on_status: Callable[[str], None] | None = None,
    on_ready: Callable[[], None] | None = None,
    on_failure: Callable[[], None] | None = None,
) -> bool:
    if on_status:
        on_status("Subindo servidor local...")

    ready = wait_for_server(port)
    if ready:
        if on_status:
            on_status("Servidor pronto. Abrindo navegador...")
        if on_ready:
            on_ready()
        return True

    if on_status:
        on_status("Nao foi possivel iniciar o servidor.")
    if on_failure:
        on_failure()
    return False

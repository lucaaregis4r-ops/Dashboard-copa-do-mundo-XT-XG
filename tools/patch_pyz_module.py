from __future__ import annotations

import marshal
import struct
import sys
import zlib
from pathlib import Path


def read_toc(data: bytes) -> tuple[int, list[tuple[str, tuple[int, int, int]]]]:
    if not data.startswith(b"PYZ\0"):
        raise ValueError("Not a PyInstaller PYZ archive")
    toc_offset = struct.unpack("!i", data[8:12])[0]
    return toc_offset, marshal.loads(data[toc_offset:])


def patch_bootstrap_source(source: str) -> str:
    source = source.replace("import threading\n", "")
    source = source.replace(
        '    if threading.current_thread() is not threading.main_thread():\n'
        '        _LOGGER.debug("Skipping signal handler setup outside the main thread")\n'
        "        return\n\n",
        "",
    )
    old = (
        "    signal.signal(signal.SIGTERM, signal_handler)\n"
        "    signal.signal(signal.SIGINT, signal_handler)\n"
        '    if sys.platform == "win32":\n'
        "        signal.signal(signal.SIGBREAK, signal_handler)\n"
        "    else:\n"
        "        signal.signal(signal.SIGQUIT, signal_handler)"
    )
    new = (
        "    try:\n"
        "        signal.signal(signal.SIGTERM, signal_handler)\n"
        "        signal.signal(signal.SIGINT, signal_handler)\n"
        '        if sys.platform == "win32":\n'
        "            signal.signal(signal.SIGBREAK, signal_handler)\n"
        "        else:\n"
        "            signal.signal(signal.SIGQUIT, signal_handler)\n"
        "    except ValueError:\n"
        '        _LOGGER.debug("Skipping signal handlers outside main thread")'
    )
    if old not in source:
        raise ValueError("Expected signal handler block was not found")
    return source.replace(old, new)


def patch_pyz(pyz_path: Path, source_path: Path) -> None:
    data = bytearray(pyz_path.read_bytes())
    _, toc = read_toc(data)
    entries = dict(toc)
    module_name = "streamlit.web.bootstrap"
    module_type, offset, length = entries[module_name]
    if module_type != 0:
        raise ValueError(f"Unexpected module type for {module_name}: {module_type}")

    source = patch_bootstrap_source(source_path.read_text(encoding="utf-8"))
    code = compile(source, "streamlit\\web\\bootstrap.py", "exec")
    payload = zlib.compress(marshal.dumps(code), level=9)
    if len(payload) > length:
        raise ValueError(f"Patched module is too large: {len(payload)} > {length}")

    data[offset : offset + length] = payload + (b"\0" * (length - len(payload)))
    pyz_path.write_bytes(data)
    print(f"Patched {pyz_path} ({len(payload)} of {length} bytes)")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_pyz_module.py <PYZ-00.pyz> <bootstrap.py>")
    patch_pyz(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()

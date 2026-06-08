from __future__ import annotations

import marshal
import re
import struct
import sys
import zlib
from pathlib import Path


def compact_runner_source(source: str) -> str:
    source = re.sub(
        r"\n\ndef configure_streamlit_for_current_thread\(\).*?"
        r"bootstrap\._set_up_signal_handler = lambda server: None  # type: ignore\[attr-defined\]\n",
        "\n",
        source,
        flags=re.S,
    )
    return source.replace("    configure_streamlit_for_current_thread()\n", "")


def patch_pyz(pyz_path: Path, source_path: Path) -> None:
    data = bytearray(pyz_path.read_bytes())
    if not data.startswith(b"PYZ\0"):
        raise ValueError("Not a PyInstaller PYZ archive")

    toc_offset = struct.unpack("!i", data[8:12])[0]
    entries = dict(marshal.loads(data[toc_offset:]))
    module_type, offset, length = entries["src.runner"]
    if module_type != 0:
        raise ValueError(f"Unexpected module type for src.runner: {module_type}")

    source = compact_runner_source(source_path.read_text(encoding="utf-8"))
    code = compile(source, "src\\runner.py", "exec")
    payload = zlib.compress(marshal.dumps(code), level=9)
    if len(payload) > length:
        raise ValueError(f"Patched module is too large: {len(payload)} > {length}")

    data[offset : offset + length] = payload + (b"\0" * (length - len(payload)))
    pyz_path.write_bytes(data)
    print(f"Patched {pyz_path} ({len(payload)} of {length} bytes)")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_pyz_runner.py <PYZ-00.pyz> <runner.py>")
    patch_pyz(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()

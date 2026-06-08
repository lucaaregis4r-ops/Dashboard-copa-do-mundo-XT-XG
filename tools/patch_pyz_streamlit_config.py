from __future__ import annotations

import marshal
import struct
import sys
import zlib
from pathlib import Path


def patch_pyz(pyz_path: Path, source_path: Path) -> None:
    data = bytearray(pyz_path.read_bytes())
    if not data.startswith(b"PYZ\0"):
        raise ValueError("Not a PyInstaller PYZ archive")

    toc_offset = struct.unpack("!i", data[8:12])[0]
    entries = dict(marshal.loads(data[toc_offset:]))
    module_type, offset, length = entries["streamlit.config"]
    if module_type != 0:
        raise ValueError(f"Unexpected module type for streamlit.config: {module_type}")

    code = compile(source_path.read_text(encoding="utf-8"), "streamlit\\config.py", "exec")
    payload = zlib.compress(marshal.dumps(code), level=9)
    if len(payload) > length:
        raise ValueError(f"Patched module is too large: {len(payload)} > {length}")

    data[offset : offset + length] = payload + (b"\0" * (length - len(payload)))
    pyz_path.write_bytes(data)
    print(f"Patched {pyz_path} ({len(payload)} of {length} bytes)")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_pyz_streamlit_config.py <PYZ-00.pyz> <config.py>")
    patch_pyz(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()

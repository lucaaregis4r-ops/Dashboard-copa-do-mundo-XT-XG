from __future__ import annotations

import sys
from pathlib import Path


def replace_once(target_path: Path, old_path: Path, new_path: Path) -> None:
    target = target_path.read_bytes()
    old = old_path.read_bytes()
    new = new_path.read_bytes()
    if len(old) != len(new):
        raise ValueError(f"Archive sizes differ: {len(old)} != {len(new)}")

    first = target.find(old)
    if first < 0:
        raise ValueError(f"Original archive was not found in {target_path}")
    second = target.find(old, first + 1)
    if second >= 0:
        raise ValueError(f"Original archive appears more than once in {target_path}")

    target_path.write_bytes(target[:first] + new + target[first + len(old) :])
    print(f"Patched {target_path} at offset {first}")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: replace_embedded_pyz.py <target> <old-pyz> <new-pyz>")
    replace_once(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))


if __name__ == "__main__":
    main()

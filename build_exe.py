from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def build_launcher(script_name: str, exe_name: str, windowed: bool) -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        exe_name,
        "--onedir",
        "--windowed" if windowed else "--console",
        "--collect-all",
        "streamlit",
        "--collect-submodules",
        "plotly",
        "--exclude-module",
        "torch",
        "--exclude-module",
        "transformers",
        "--exclude-module",
        "tensorflow",
        "--exclude-module",
        "matplotlib",
        "--hidden-import",
        "sklearn.utils._cython_blas",
        "--hidden-import",
        "sklearn.neighbors._partition_nodes",
        "--add-data",
        f"{ROOT / 'app.py'};.",
        "--add-data",
        f"{ROOT / 'src'};src",
        "--add-data",
        f"{ROOT / 'matches'};matches",
        "--add-data",
        f"{ROOT / 'events'};events",
        "--add-data",
        f"{ROOT / 'three-sixty'};three-sixty",
        str(ROOT / script_name),
    ]
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> None:
    build_launcher("launcher_window.py", "WorldCupActionFlow", True)
    build_launcher("launcher_console.py", "WorldCupActionFlowConsole", False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run bundled full_process.py inside this skill.")
    parser.add_argument(
        "--core-root",
        default=None,
        help="Optional core root override. Default: skill bundled assets/wos-review-core.",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    skill_root = script_path.parents[1]
    core_root = Path(args.core_root) if args.core_root else (skill_root / "assets" / "wos-review-core")
    full_process = core_root / "full_process.py"

    if not full_process.exists():
        raise FileNotFoundError(f"Missing bundled full_process.py: {full_process}")

    os.chdir(core_root)
    cmd = [sys.executable, str(full_process)]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

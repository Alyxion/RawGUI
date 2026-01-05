#!/usr/bin/env python3
"""Run NiceGUI samples with RawGUI.

Usage:
    python run.py <sample.py>
    python run.py menu_and_tabs.py
    python run.py todo_list.py
"""

import sys
import os
from pathlib import Path

# Ensure rawgui is importable
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Inject RawGUI as nicegui BEFORE any imports
from rawgui.compat import inject
inject()

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <sample.py>")
        print("\nAvailable samples:")
        for f in Path(__file__).parent.glob("*.py"):
            if f.name != "run.py":
                print(f"  {f.name}")
        sys.exit(1)

    sample = sys.argv[1]
    sample_path = Path(__file__).parent / sample

    if not sample_path.exists():
        print(f"Sample not found: {sample}")
        sys.exit(1)

    # Execute the sample
    print(f"Running {sample} with RawGUI...")
    print("-" * 40)

    # Read and exec the sample
    code = sample_path.read_text()

    # Set up globals for exec
    exec_globals = {
        "__name__": "__main__",
        "__file__": str(sample_path),
    }

    exec(compile(code, sample_path, "exec"), exec_globals)


if __name__ == "__main__":
    main()

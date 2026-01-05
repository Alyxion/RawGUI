"""Screenshot utilities for all RawGUI renderers.

Provides unified screenshot capture for:
- TUI (Terminal): PTY-based capture with pyte
- Tkinter/PIL: Direct Pillow rendering
- NiceGUI: Selenium browser capture

Usage:
    from rawgui.testing.screenshots import capture_tui, capture_pil, capture_nicegui

    # TUI screenshot
    img = capture_tui("examples/counter.py", "screenshots/counter_tui.png")

    # PIL/Tkinter screenshot (headless)
    img = capture_pil("examples/counter.py", "screenshots/counter_pil.png")

    # NiceGUI screenshot (requires browser)
    img = capture_nicegui("examples/counter.py", "screenshots/counter_nicegui.png")
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PIL import Image

if TYPE_CHECKING:
    pass


def capture_tui(
    script_path: str,
    output_path: str,
    width: int = 80,
    height: int = 24,
    wait_text: Optional[str] = None,
    timeout: float = 5.0,
) -> Path:
    """Capture a TUI screenshot by running the script in a PTY.

    Args:
        script_path: Path to the Python script
        output_path: Path for the output PNG
        width: Terminal width in columns
        height: Terminal height in rows
        wait_text: Text to wait for before capturing (optional)
        timeout: Timeout for waiting

    Returns:
        Path to the saved screenshot
    """
    from .subprocess_terminal import SubprocessTerminal

    script = Path(script_path).resolve()
    output = Path(output_path)

    command = f"poetry run python {script}"

    with SubprocessTerminal(command, rows=height, cols=width) as term:
        # Wait for content to appear
        if wait_text:
            term.wait_for_text(wait_text, timeout=timeout)
        else:
            # Default: wait for any substantial content
            time.sleep(1.0)

        # Capture screenshot
        term.screenshot(output)

    return output


def capture_pil(
    script_path: str,
    output_path: str,
    width: int = 800,
    height: int = 600,
) -> Path:
    """Capture a PIL/Tkinter screenshot by rendering headlessly.

    This runs the script's page builder and renders to PIL without
    opening a window.

    Args:
        script_path: Path to the Python script
        output_path: Path for the output PNG
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Path to the saved screenshot
    """
    from ..adapters import TkinterAdapter
    from ..app import app
    from ..client import Client
    from ..page import router

    script = Path(script_path).resolve()
    output = Path(output_path)

    # Add script directory to path
    script_dir = str(script.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Reset app state completely
    app._routes = {}
    app._auto_index_client = None
    app._startup_handlers = []
    app._shutdown_handlers = []
    app._connect_handlers = []
    app._disconnect_handlers = []
    app._pending_navigation = None

    # Clear the router
    router.routes = []

    # Execute script to register pages (but don't call ui.run())
    with open(script) as f:
        code = f.read()
        # Remove ui.run() calls to prevent blocking
        lines = code.split("\n")
        filtered = []
        skip_if_main = False
        for line in lines:
            # Skip the entire if __name__ == "__main__": block
            if '__name__' in line and '__main__' in line:
                skip_if_main = True
                continue
            if skip_if_main:
                # Check if we're still in the if block (indented)
                if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    skip_if_main = False
                else:
                    continue
            if "ui.run(" in line:
                continue
            filtered.append(line)
        code = "\n".join(filtered)

        exec(compile(code, script, "exec"), {"__name__": "__script__", "__file__": str(script)})

    # Create adapter
    adapter = TkinterAdapter(width=width, height=height, title="Screenshot", dark=True)

    # Create client and build page
    client = Client()

    async def build():
        # Run startup
        await app._run_startup()
        app._run_connect(client)

        # Try to match root page
        match = router.match("/")

        # Check for implicit root page
        if not match and app._auto_index_client:
            auto_client = app._auto_index_client
            roots = [el for el in auto_client.elements.values() if el.parent_slot is None]
            if roots:
                for el in list(auto_client.elements.values()):
                    el.client = client
                    client.register_element(el)
                return roots[0] if len(roots) == 1 else roots[0]

        if match:
            route, params = match
            await route.build(client, params)
            roots = [el for el in client.elements.values() if el.parent_slot is None]
            if roots:
                return roots[0] if len(roots) == 1 else roots[0]

        return None

    root = asyncio.run(build())

    if root:
        # Render headlessly
        img = adapter.render_headless(root)

        # Save
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output))

    return output


def capture_nicegui(
    script_path: str,
    output_path: str,
    width: int = 800,
    height: int = 600,
    wait_seconds: float = 2.0,
    headless: bool = True,
) -> Path:
    """Capture a NiceGUI screenshot using Selenium.

    This starts the NiceGUI server, opens a browser, and captures
    the rendered page.

    Args:
        script_path: Path to the Python script
        output_path: Path for the output PNG
        width: Browser width in pixels
        height: Browser height in pixels
        wait_seconds: Time to wait for page to render
        headless: Run browser in headless mode

    Returns:
        Path to the saved screenshot
    """
    import subprocess
    import socket

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    script = Path(script_path).resolve()
    output = Path(output_path)

    # Find a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    # Start NiceGUI server in background
    env = {"RAWGUI_RENDERER": "nicegui"}
    env.update(__import__("os").environ)

    process = subprocess.Popen(
        ["poetry", "run", "python", str(script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server to start
        time.sleep(2.0)

        # Set up Chrome
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--window-size={width},{height}")

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(f"http://localhost:8080")
            time.sleep(wait_seconds)

            # Take screenshot
            output.parent.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(output))

        finally:
            driver.quit()

    finally:
        process.terminate()
        process.wait(timeout=5)

    return output


def capture_all_renderers(
    script_path: str,
    output_dir: str,
    name: Optional[str] = None,
) -> dict:
    """Capture screenshots from all available renderers.

    Args:
        script_path: Path to the Python script
        output_dir: Directory for output PNGs
        name: Base name for files (defaults to script name)

    Returns:
        Dict mapping renderer name to output path
    """
    script = Path(script_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    base_name = name or script.stem

    results = {}

    # TUI
    try:
        tui_path = capture_tui(
            str(script),
            str(output / f"{base_name}_tui.png"),
        )
        results["tui"] = tui_path
        print(f"  TUI: {tui_path}")
    except Exception as e:
        print(f"  TUI: Failed - {e}")

    # PIL/Tkinter
    try:
        pil_path = capture_pil(
            str(script),
            str(output / f"{base_name}_pil.png"),
        )
        results["pil"] = pil_path
        print(f"  PIL: {pil_path}")
    except Exception as e:
        print(f"  PIL: Failed - {e}")

    # NiceGUI (optional - requires selenium and chrome)
    try:
        nicegui_path = capture_nicegui(
            str(script),
            str(output / f"{base_name}_nicegui.png"),
        )
        results["nicegui"] = nicegui_path
        print(f"  NiceGUI: {nicegui_path}")
    except Exception as e:
        print(f"  NiceGUI: Skipped - {e}")

    return results


if __name__ == "__main__":
    # Quick test
    import argparse

    parser = argparse.ArgumentParser(description="Capture screenshots")
    parser.add_argument("script", help="Script to capture")
    parser.add_argument("-o", "--output", default="screenshots", help="Output directory")
    parser.add_argument("-r", "--renderer", choices=["tui", "pil", "nicegui", "all"], default="pil")
    args = parser.parse_args()

    if args.renderer == "all":
        capture_all_renderers(args.script, args.output)
    elif args.renderer == "tui":
        capture_tui(args.script, f"{args.output}/{Path(args.script).stem}_tui.png")
    elif args.renderer == "pil":
        capture_pil(args.script, f"{args.output}/{Path(args.script).stem}_pil.png")
    elif args.renderer == "nicegui":
        capture_nicegui(args.script, f"{args.output}/{Path(args.script).stem}_nicegui.png")

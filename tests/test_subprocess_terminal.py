"""Tests for SubprocessTerminal testing utility."""

import pytest
from pathlib import Path

from rawgui.testing import SubprocessTerminal, run_terminal_test


class TestSubprocessTerminal:
    """Tests for SubprocessTerminal class."""

    def test_create_terminal(self):
        """Test creating a terminal instance."""
        term = SubprocessTerminal("echo hello", rows=24, cols=80)
        assert term.rows == 24
        assert term.cols == 80

    def test_run_simple_command(self):
        """Test running a simple command."""
        with SubprocessTerminal("echo 'Hello World'") as term:
            term.wait_for_text("Hello World", timeout=5)
            assert term.contains("Hello World")

    def test_find_text(self):
        """Test finding text positions."""
        with SubprocessTerminal("echo 'Test Line'") as term:
            term.wait_for_text("Test", timeout=5)
            positions = term.find_text("Test")
            assert len(positions) >= 1

    def test_send_keys(self):
        """Test sending keystrokes."""
        # Use cat to echo input
        with SubprocessTerminal("cat") as term:
            term.send_text("hello")
            term.wait_for_text("hello", timeout=5)
            assert term.contains("hello")

    def test_screenshot(self, tmp_path):
        """Test taking a screenshot."""
        with SubprocessTerminal("echo 'Screenshot Test'") as term:
            term.wait_for_text("Screenshot", timeout=5)
            path = term.screenshot(tmp_path / "test.png")
            assert path.exists()
            assert path.suffix == ".png"


class TestRunTerminalTest:
    """Tests for run_terminal_test convenience function."""

    def test_basic_test(self):
        """Test basic terminal test."""
        content = run_terminal_test(
            "echo 'Hello Test'",
            [
                ("wait", "Hello"),
                ("delay", 0.1),
            ],
        )
        assert "Hello" in content

    def test_with_assertions(self):
        """Test with assertions."""
        content = run_terminal_test(
            "echo 'Expected Text'",
            [
                ("wait", "Expected"),
                ("assert", "Expected Text"),
                ("assert_not", "Not Present"),
            ],
        )
        assert "Expected Text" in content

    def test_assertion_failure(self):
        """Test assertion failure raises error."""
        with pytest.raises(AssertionError):
            run_terminal_test(
                "echo 'Actual'",
                [
                    ("wait", "Actual"),
                    ("assert", "NotPresent"),
                ],
            )

"""Tests for `kicad_parts_placer` package."""

import unittest

from click.testing import CliRunner

import kicad_parts_placer
from kicad_parts_placer import cli, file_io
import tempfile

class TestKicad_parts_placer(unittest.TestCase):
    """Tests for `kicad_parts_placer` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 2
        assert "main" in result.output
        help_result = runner.invoke(cli.main, ["--help"])
        assert help_result.exit_code == 0
        assert "Show this message and exit." in help_result.output


if __name__ == "__main__":
    unittest.main()

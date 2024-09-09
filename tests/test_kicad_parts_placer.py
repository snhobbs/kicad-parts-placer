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


class TestFileIO(unittest.TestCase):
    def test_read_csv_to_df_comma(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "w") as f:
                f.write("hello,world\na,b")

            df = file_io.read_csv_to_df(f.name)
            assert len(df) == 1
            assert df.columns[0] == "hello"
            assert df.columns[1] == "world"

    def test_read_csv_to_df_semicolon(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "w") as f:
                f.write("hello;world\na;b")

            df = file_io.read_csv_to_df(f.name)
            assert len(df) == 1
            assert df.columns[0] == "hello"
            assert df.columns[1] == "world"

    def test_read_csv_to_df_tab(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "w") as f:
                f.write("hello\tworld\na\tb")

            df = file_io.read_csv_to_df(f.name)
            assert len(df) == 1
            assert df.columns[0] == "hello"
            assert df.columns[1] == "world"

    def test_read_csv_to_df_sep(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "w") as f:
                f.write("hello\tworld\na\tb")

            df = file_io.read_csv_to_df(f.name, sep="\t")
            assert len(df) == 1
            assert df.columns[0] == "hello"
            assert df.columns[1] == "world"

    def test_read_csv_to_df_delimiter(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "w") as f:
                f.write("hello\tworld\na\tb")

            df = file_io.read_csv_to_df(f.name, delimiter="\t")
            assert len(df) == 1
            assert df.columns[0] == "hello"
            assert df.columns[1] == "world"


if __name__ == "__main__":
    unittest.main()

"""Tests for `kicad_parts_placer` package."""

import unittest
from kicad_parts_placer import file_io
import tempfile

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

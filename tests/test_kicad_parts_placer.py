"""Tests for `kicad_parts_placer` package."""

import logging
import tempfile
import unittest
import pandas as pd

from click.testing import CliRunner

from kicad_parts_placer import cli, file_io, kicad_parts_placer

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

    def test_translate_header(self):
        logging.info(kicad_parts_placer.translate_header(["ref des"]) )
        self.assertEqual(kicad_parts_placer.translate_header(["posx"]), ("x",))
        self.assertEqual(kicad_parts_placer.translate_header(["midx"]), ("x",))
        self.assertEqual(kicad_parts_placer.translate_header(["posy"]), ("y",))
        self.assertEqual(kicad_parts_placer.translate_header(["midy"]), ("y",))
        self.assertEqual(kicad_parts_placer.translate_header(["rot"]), ("rotation",))
        self.assertEqual(kicad_parts_placer.translate_header(["Rot"]), ("rotation",))
        self.assertEqual(kicad_parts_placer.translate_header(["ROT "]), ("rotation",))
        self.assertEqual(kicad_parts_placer.translate_header(["RO"]), ("RO",))
        self.assertEqual(kicad_parts_placer.translate_header(["rotation"]), ("rotation",))
        self.assertEqual(kicad_parts_placer.translate_header([" Rotation"]), ("rotation",))
        self.assertEqual(kicad_parts_placer.translate_header(["side"]), ("side",))
        self.assertEqual(kicad_parts_placer.translate_header(["layer"]), ("side",))
        self.assertEqual(kicad_parts_placer.translate_header(["ref des"]), ("refdes",))
        self.assertEqual(kicad_parts_placer.translate_header(["reference designator"]), ("refdes",))

    def test_check_input_pass(self):
        components_df = pd.DataFrame({"refdes": ["C1", "C2"], "x": [1,2], "y": [2,3], "rotation": [0, 90], "side": ["front", "back"]})
        valid, errors = kicad_parts_placer.check_input_valid(components_df)
        assert not len(errors)
        self.assertTrue(valid)

    def test_check_input_fails_side_text_wrong(self):
        components_df = pd.DataFrame({"refdes": ["C1", "C2"], "x": [1,2], "y": [2,3], "rotation": [0, 90], "side": ["ront", "back"]})
        valid, errors = kicad_parts_placer.check_input_valid(components_df)
        assert len(errors)
        self.assertFalse(valid)

    def test_check_input_fails_missing_column(self):
        components_df = pd.DataFrame({"x": [1,2], "y": [2,3], "rotation": [0, 90], "side": ["ront", "back"]})
        valid, errors = kicad_parts_placer.check_input_valid(components_df)
        assert len(errors)
        self.assertFalse(valid)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

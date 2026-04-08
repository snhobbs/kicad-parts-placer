"""Tests for `kicad_parts_placer` package."""

import logging
import unittest
from unittest.mock import MagicMock

import pandas as pd
from click.testing import CliRunner
from kicad_parts_placer import cli
from kicad_parts_placer.kicad_parts_placer import (
    ComponentRow,
    SideEnum,
    check_input_valid,
    get_missing_references,
    setup_dataframe,
    translate_header,
)


class TestKicad_parts_placer(unittest.TestCase):
    """Tests for `kicad_parts_placer` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    # -------------------------------------------------------------------------
    # CLI
    # -------------------------------------------------------------------------

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 2
        assert "main" in result.output
        help_result = runner.invoke(cli.main, ["--help"])
        assert help_result.exit_code == 0
        assert "Show this message and exit." in help_result.output

    # -------------------------------------------------------------------------
    # translate_header
    # -------------------------------------------------------------------------

    def test_translate_header(self):
        logging.info(translate_header(["ref des"]))
        self.assertEqual(translate_header(["posx"]), ("x",))
        self.assertEqual(translate_header(["midx"]), ("x",))
        self.assertEqual(translate_header(["posy"]), ("y",))
        self.assertEqual(translate_header(["midy"]), ("y",))
        self.assertEqual(translate_header(["rot"]), ("rotation",))
        self.assertEqual(translate_header(["Rot"]), ("rotation",))
        self.assertEqual(translate_header(["ROT "]), ("rotation",))
        self.assertEqual(translate_header(["RO"]), ("RO",))
        self.assertEqual(translate_header(["rotation"]), ("rotation",))
        self.assertEqual(translate_header([" Rotation"]), ("rotation",))
        self.assertEqual(translate_header(["side"]), ("side",))
        self.assertEqual(translate_header(["layer"]), ("side",))
        self.assertEqual(translate_header(["ref des"]), ("refdes",))
        self.assertEqual(translate_header(["reference designator"]), ("refdes",))

    def test_translate_header_empty(self):
        self.assertEqual(translate_header([]), ())

    def test_translate_header_unknown_passthrough(self):
        self.assertEqual(translate_header(["custom_field"]), ("custom_field",))

    def test_translate_header_duplicate_synonyms(self):
        # Both posx and midx map to x — documents behaviour with duplicate columns
        self.assertEqual(translate_header(["posx", "midx"]), ("x", "x"))

    # -------------------------------------------------------------------------
    # check_input_valid
    # -------------------------------------------------------------------------

    def test_check_input_pass(self):
        components_df = pd.DataFrame(
            {
                "refdes": ["C1", "C2"],
                "x": [1, 2],
                "y": [2, 3],
                "rotation": [0, 90],
                "side": ["front", "back"],
            }
        )
        valid, errors = check_input_valid(components_df)
        self.assertFalse(errors)
        self.assertEqual(len(errors), 0)
        self.assertTrue(valid)

    def test_check_input_fails_side_text_wrong(self):
        components_df = pd.DataFrame(
            {
                "refdes": ["C1", "C2"],
                "x": [1, 2],
                "y": [2, 3],
                "rotation": [0, 90],
                "side": ["ront", "back"],
            }
        )
        valid, errors = check_input_valid(components_df)
        self.assertTrue(errors)
        self.assertEqual(len(errors), 1)
        self.assertFalse(valid)

    def test_check_input_fails_missing_column(self):
        components_df = pd.DataFrame(
            {"x": [1, 2], "y": [2, 3], "rotation": [0, 90], "side": ["front", "back"]}
        )
        valid, errors = check_input_valid(components_df)
        self.assertTrue(errors)
        self.assertEqual(len(errors), 1)
        self.assertFalse(valid)

    def test_check_input_fails_multiple_missing_columns(self):
        components_df = pd.DataFrame({"refdes": ["C1"]})
        valid, errors = check_input_valid(components_df)
        self.assertFalse(valid)
        self.assertGreater(len(errors), 1)  # x, y, rotation, side all missing

    def test_check_input_fails_empty_refdes(self):
        components_df = pd.DataFrame(
            {
                "refdes": ["", "C2"],
                "x": [1, 2],
                "y": [2, 3],
                "rotation": [0, 90],
                "side": ["front", "back"],
            }
        )
        valid, errors = check_input_valid(components_df)
        self.assertFalse(valid)
        self.assertEqual(len(errors), 1)

    def test_check_input_empty_dataframe(self):
        components_df = pd.DataFrame(columns=["refdes", "x", "y", "rotation", "side"])
        valid, errors = check_input_valid(components_df)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_check_input_accepts_synonym_headers(self):
        # Synonym translation happens inside check_input_valid via setup_dataframe,
        # so synonym column names should pass validation without errors.
        components_df = pd.DataFrame(
            {
                "ref": ["C1"],
                "posx": [1],
                "posy": [2],
                "rot": [0],
                "layer": ["front"],
            }
        )
        valid, errors = check_input_valid(components_df)
        self.assertFalse(errors)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_check_input_multiple_invalid_rows(self):
        components_df = pd.DataFrame(
            {
                "refdes": ["C1", "C2"],
                "x": [1, 2],
                "y": [2, 3],
                "rotation": [0, 90],
                "side": ["ront", "bck"],  # both invalid
            }
        )
        valid, errors = check_input_valid(components_df)
        self.assertFalse(valid)
        self.assertEqual(len(errors), 2)

    # -------------------------------------------------------------------------
    # setup_dataframe
    # -------------------------------------------------------------------------

    def test_setup_dataframe_normalizes_side_front(self):
        df = pd.DataFrame(
            {"refdes": ["C1"], "x": [1], "y": [2], "rotation": [0], "side": ["front"]}
        )
        result = setup_dataframe(df)
        self.assertEqual(result["side"][0], SideEnum.top)

    def test_setup_dataframe_normalizes_side_back(self):
        df = pd.DataFrame(
            {"refdes": ["C1"], "x": [1], "y": [2], "rotation": [0], "side": ["back"]}
        )
        result = setup_dataframe(df)
        self.assertEqual(result["side"][0], SideEnum.bottom)

    def test_setup_dataframe_side_case_insensitive(self):
        df = pd.DataFrame(
            {"refdes": ["C1"], "x": [1], "y": [2], "rotation": [0], "side": ["FRONT"]}
        )
        result = setup_dataframe(df)
        self.assertEqual(result["side"][0], SideEnum.top)

    def test_setup_dataframe_adds_default_rotation(self):
        df = pd.DataFrame({"refdes": ["C1"], "x": [1], "y": [2], "side": ["front"]})
        result = setup_dataframe(df)
        self.assertIn("rotation", result.columns)
        self.assertEqual(result["rotation"][0], 0.0)

    def test_setup_dataframe_adds_default_side(self):
        df = pd.DataFrame({"refdes": ["C1"], "x": [1], "y": [2], "rotation": [0]})
        result = setup_dataframe(df)
        self.assertEqual(result["side"][0], SideEnum.current)

    def test_setup_dataframe_does_not_mutate_input(self):
        df = pd.DataFrame(
            {"refdes": ["C1"], "x": [1], "y": [2], "rotation": [0], "side": ["front"]}
        )
        original_side = df["side"][0]
        setup_dataframe(df)
        self.assertEqual(df["side"][0], original_side)

    def test_setup_dataframe_synonym_headers_renamed(self):
        df = pd.DataFrame(
            {"ref": ["C1"], "posx": [1], "posy": [2], "rot": [0], "layer": ["front"]}
        )
        result = setup_dataframe(df)
        self.assertIn("refdes", result.columns)
        self.assertIn("x", result.columns)
        self.assertIn("side", result.columns)

    def test_setup_dataframe_all_side_synonyms(self):
        """All recognised side strings should map to a SideEnum, not be left as strings."""
        synonyms = {
            "front": SideEnum.top,
            "top": SideEnum.top,
            "f.cu": SideEnum.top,
            "back": SideEnum.bottom,
            "bottom": SideEnum.bottom,
            "b.cu": SideEnum.bottom,
        }
        for side_str, expected_enum in synonyms.items():
            with self.subTest(side=side_str):
                df = pd.DataFrame(
                    {
                        "refdes": ["C1"],
                        "x": [1],
                        "y": [2],
                        "rotation": [0],
                        "side": [side_str],
                    }
                )
                result = setup_dataframe(df)
                self.assertEqual(result["side"][0], expected_enum)

    def test_setup_dataframe_rotation_cast_to_float(self):
        df = pd.DataFrame(
            {
                "refdes": ["C1"],
                "x": [1],
                "y": [2],
                "rotation": ["45"],
                "side": ["front"],
            }
        )
        result = setup_dataframe(df)
        self.assertIsInstance(result["rotation"][0], float)
        self.assertEqual(result["rotation"][0], 45.0)

    # -------------------------------------------------------------------------
    # ComponentRow
    # -------------------------------------------------------------------------

    def test_component_row_from_series(self):
        s = pd.Series(
            {"refdes": "C1", "x": 1, "y": 2, "rotation": 90, "side": SideEnum.top}
        )
        row = ComponentRow.from_series(s)
        self.assertEqual(row.refdes, "C1")
        self.assertEqual(row.x, 1.0)
        self.assertEqual(row.y, 2.0)
        self.assertEqual(row.rotation, 90.0)
        self.assertEqual(row.side, SideEnum.top)

    def test_component_row_numeric_fields_cast_to_float(self):
        s = pd.Series(
            {
                "refdes": "C1",
                "x": "1.5",
                "y": "2.5",
                "rotation": "45",
                "side": SideEnum.top,
            }
        )
        row = ComponentRow.from_series(s)
        self.assertIsInstance(row.x, float)
        self.assertIsInstance(row.y, float)
        self.assertIsInstance(row.rotation, float)
        self.assertEqual(row.x, 1.5)
        self.assertEqual(row.rotation, 45.0)

    def test_component_row_from_series_preserves_side_enum(self):
        for side in SideEnum:
            with self.subTest(side=side):
                s = pd.Series(
                    {"refdes": "R1", "x": 0, "y": 0, "rotation": 0, "side": side}
                )
                row = ComponentRow.from_series(s)
                self.assertIsInstance(row.side, SideEnum)
                self.assertEqual(row.side, side)

    # -------------------------------------------------------------------------
    # get_missing_references
    # -------------------------------------------------------------------------

    def test_get_missing_references_some_missing(self):
        board = MagicMock()
        board.FindFootprintByReference.side_effect = (
            lambda ref: MagicMock() if ref == "C1" else None
        )
        components = [
            ComponentRow(refdes="C1", x=1, y=2, rotation=0, side=SideEnum.top),
            ComponentRow(refdes="C2", x=3, y=4, rotation=0, side=SideEnum.top),
        ]
        missing = get_missing_references(board, components)
        self.assertEqual(missing, ["C2"])

    def test_get_missing_references_all_present(self):
        board = MagicMock()
        board.FindFootprintByReference.return_value = MagicMock()
        components = [
            ComponentRow(refdes="C1", x=1, y=2, rotation=0, side=SideEnum.top),
            ComponentRow(refdes="C2", x=3, y=4, rotation=0, side=SideEnum.top),
        ]
        missing = get_missing_references(board, components)
        self.assertEqual(missing, [])

    def test_get_missing_references_all_missing(self):
        board = MagicMock()
        board.FindFootprintByReference.return_value = None
        components = [
            ComponentRow(refdes="C1", x=1, y=2, rotation=0, side=SideEnum.top),
            ComponentRow(refdes="C2", x=3, y=4, rotation=0, side=SideEnum.top),
        ]
        missing = get_missing_references(board, components)
        self.assertEqual(missing, ["C1", "C2"])

    def test_get_missing_references_empty_components(self):
        board = MagicMock()
        missing = get_missing_references(board, [])
        self.assertEqual(missing, [])
        board.FindFootprintByReference.assert_not_called()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

#!/usr/bin/env python3
"""
kicad_parts_placer
Command line tool which sets the position of components from a spreadsheet
"""

import logging

import click
import pcbnew

from . import file_io
from .kicad_parts_placer import place_parts, mirror_parts, group_parts

_log = logging.getLogger("kicad_parts_placer")

@click.command(
    help="Takes a PCB & configuration data in mm, sets rotation and location on a new pcb"
)
@click.option("--pcb", type=str, required=True, help="PCB file to edit")
@click.option(
    "--config", type=str, required=True, help="Spreadsheet configuration file"
)
@click.option(
    "--out", "-o", type=str, required=False, help="PCB file to write output to"
)
@click.option("--inplace", "-i", is_flag=True, help="Edit pcb file in place")
@click.option("--drill_center", is_flag=True, help="Use drill/file/AUX center as reference point")
# @click.option("--center-on-board", is_flag=True, help="Center group on board bounding box")
# @click.option("--mirror", is_flag=True, help="Mirror parts, required for matching up the front and back of two boards")
@click.option(
    "--flip",
    is_flag=True,
    help="Mirror parts, required for matching up the front and back of two boards",
)
@click.option(
    "--group", "group_name", type=str, help="name of parts group, defaults to file name"
)
@click.option("--debug", is_flag=True, help="")
@click.version_option()
def main(pcb, config, out, inplace, drill_center, flip, group_name, debug):
    logging.basicConfig()
    _log.setLevel(logging.INFO)
    if debug:
        _log.setLevel(logging.DEBUG)

    if inplace:
        out = pcb
    elif out is None:
        msg = "Either the inplace flag needs to be set or the --out option set"
        raise ValueError(msg)

    board = pcbnew.LoadBoard(pcb)
    # bounding_box = board.GetBoardEdgesBoundingBox() #  FIXME use this to check placement

    origin = (0,0)
    if drill_center:
        origin=pcbnew.ToMM(board.GetDesignSettings().GetAuxOrigin())

    components = file_io.read_file_to_df(config)

    if group_name is None:
        group_name = config.split(".")[0]

    board = place_parts(
        board=board,
        components_df=components,
        origin=origin
    )

    board = group_parts(
        board=board,
        group_name=group_name,
        origin=origin)

    if flip:
        board = mirror_parts(
            board=board,
            group_name=group_name,
            origin=origin)

    board.Save(out)
    return 0


if __name__ == "__main__":
    main()

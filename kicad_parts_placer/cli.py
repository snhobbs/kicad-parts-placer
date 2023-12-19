#!/usr/bin/env python3
'''
kicad_parts_placer
Command line tool which sets the position of components from a spreadsheet
'''

import logging
import pcbnew
import click
import spreadsheet_wrangler
import numpy as np
from .kicad_parts_placer import scale_from_mm, group_components, move_modules


@click.command(help="Takes a PCB & configuration data in mm, sets rotation and location on a new pcb")
@click.option("--pcb", type=str, required=True, help="PCB file to edit")
@click.option("--config", type=str, required=True, help="Spreadsheet configuration file")
@click.option("--out", "-o", type=str, required=False, help="PCB file to write output to")
@click.option("--inplace", "-i", is_flag=True, help="Edit pcb file in place")
@click.option("-x", type=float, default=0, help="x offset for placement")
@click.option("-y", type=float, default=0, help="y offset for placement")
# @click.option("--center-on-board", is_flag=True, help="Center group on board bounding box")
# @click.option("--mirror", is_flag=True, help="Mirror parts, required for matching up the front and back of two boards")
@click.option("--flip", is_flag=True, help="Mirror parts, required for matching up the front and back of two boards")
@click.option("--group", "group_name", type=str, help="name of parts group, defaults to file name")
@click.option("--debug", is_flag=True, help="")
def main(pcb, config, out, inplace, x, y, flip, group_name, debug):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if inplace:
        out = pcb
    else:
        if out is None:
            raise ValueError("Either the inplace flag needs to be set or the --out option set")

    board = pcbnew.LoadBoard(pcb)
    # bounding_box = board.GetBoardEdgesBoundingBox() #  FIXME use this to check placement

    components = spreadsheet_wrangler.read_file_to_df(config)
    components['rotation'] = np.array(components['rotation'], dtype=float)

    #  Scale input to kicad native units
    #  Scale input to kicad native units
    components["x"] = scale_from_mm(components["x"])
    mult = 1 - 2 * int(flip)
    components["y"] = scale_from_mm(components["y"])*mult

    # if center_on_board:
    #    components = center_component_location_on_bounding_box(components, bounding_box=bounding_box, mirror=mirror)

    # set offset
    offset = (scale_from_mm(x), scale_from_mm(y))
    components["x"] = components["x"] + offset[0]
    components["y"] = components["y"] + offset[1]

    if min(components["x"]) < 0:
        components["x"] = components["x"] - min(components["x"])

    if min(components["y"]) < 0:
        components["y"] = components["y"] - min(components["y"])

    # There are no negative positions on a kicad schematic
    assert min(components["x"]) >= 0
    assert min(components["y"]) >= 0

    # group
    if group_name is None:
        group_name = config.split(".")[0]
    pcb_group = pcbnew.PCB_GROUP(None)
    pcb_group.SetName(group_name)
    board.Add(pcb_group)
    group_components(components, board, pcb_group)

    board = move_modules(components, board)
    board.Save(out)


if __name__ == "__main__":
    main()

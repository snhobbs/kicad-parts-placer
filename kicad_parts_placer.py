'''
kicad_parts_placer
Command line tool which sets the position of components from a spreadsheet
'''


import logging
import pcbnew
import pandas
import click
import spreadsheet_wrangler
import numpy as np


# the internal coorinate space of pcbnew is 1E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000
SCALE = 1/1e-6


def group_components(components: pandas.DataFrame, board: pcbnew.BOARD, group: pcbnew.PCB_GROUP):
    for _, component in components.iterrows():
        ref_des = component["ref des"]
        module = board.FindFootprintByReference(ref_des)
        if module is not None:
            group.AddItem(module)
    return components


def move_modules(components: pandas.DataFrame, board: pcbnew.BOARD) -> pcbnew.BOARD:
    '''
    components: pandas data frame containing fields:
        ref des, value, x, y, rotation
    board: pcbnew.BOARD object to edit

    Cycle through all parts on the board.
    Read the footprints reference
    If the ref des is in components["ref des"] then enter to update
    Update the parts position to the schematics plus the offset
    Update the label to with a configuration table passed to a function
    '''
    for _, component in components.iterrows():
        ref_des = component["ref des"]

        module = board.FindFootprintByReference(ref_des)
        if module is None:
            logging.warning("%s not found", ref_des)
            continue

        logging.debug("%s found", ref_des)

        if module.IsLocked():
            logging.debug("%s locked, skip", ref_des)
            continue

        center = module.GetCenter()  #  pdbnew.wxPoint
        new_pos = pcbnew.wxPoint(component['x'], component['y'])
        logging.info(f"{ref_des}: Move from {center} to {new_pos}, {component['x'], component['y']}")

        rotation_multiple=10  #  divides by 10?
        module.Rotate(module.GetCenter(), component['rotation']*rotation_multiple)
        logging.info(f"{ref_des}: rotate {component['rotation']} about {new_pos}")
        module.SetPosition(new_pos)
    return board


def center_component_location_on_bounding_box(components: pandas.DataFrame, bounding_box, mirror: bool) -> pandas.DataFrame:
    '''
    Takes a bounding box and a set of components. Components
    so they fit in the xy center of the box
    '''

    def get_offset(pos, ref):
        '''
        pos: collection of component positions
        ref: board edges
        Takes the difference between the limits of the parts and the
        board edges, this gives the spacing from the edge of the board
        to the start of the parts to center the grouping
        '''
        return ((max(pos) - min(pos)) - (max(ref)-min(ref)))/2

    offset = (get_offset(components["x"], (bounding_box.GetLeft(), bounding_box.GetRight())),
              get_offset(components["y"], (bounding_box.GetBottom(), bounding_box.GetTop())))

    components["x"] = components["x"] + bounding_box.GetRight() - offset[0]
    components["y"] = components["y"] + bounding_box.GetTop() + offset[1]
    return components


def unify_position_reference_to_board_top():
    '''
    The top and bottom sides of a centroid are referenced to the same
    '''

def mirror_components(components: pandas.DataFrame) -> pandas.DataFrame:
    components['x'] = max(components['x']) - components['x']
    return components


@click.command(help="Takes a PCB & configuration data in mm, sets rotation and location on a new pcb")
@click.option("--pcb", type=str, required=True, help="PCB file to edit")
@click.option("--config", type=str, required=True, help="Spreadsheet configuration file")
@click.option("--out", "-o", type=str, required=False, help="PCB file to write output to")
@click.option("--inplace", "-i", is_flag=True, help="Edit pcb file in place")
@click.option("-x", type=float, default=0, help="x offset for placement")
@click.option("-y", type=float, default=0, help="y offset for placement")
#@click.option("--center-on-board", is_flag=True, help="Center group on board bounding box")
#@click.option("--mirror", is_flag=True, help="Mirror parts, required for matching up the front and back of two boards")
@click.option("--group", "group_name", type=str, help="name of parts group, defaults to file name")
@click.option("--debug", is_flag=True, help="")
def main(pcb, config, out, inplace, x, y, group_name, debug):
    scale = SCALE
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
    bounding_box = board.GetBoardEdgesBoundingBox()

    components = spreadsheet_wrangler.read_file_to_df(config)
    components['rotation'] = np.array(components['rotation'], dtype=float)

    #  Scale input to kicad native units
    components["x"] = (components["x"])*scale
    components["y"] = (components["y"])*scale

    #if center_on_board:
    #    components = center_component_location_on_bounding_box(components, bounding_box=bounding_box, mirror=mirror)

    # set offset
    offset = (x*scale, y*scale)
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

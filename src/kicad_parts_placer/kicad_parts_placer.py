import logging

import numpy as np
import pandas as pd
import pcbnew


def group_components(
    components: pd.DataFrame, board: pcbnew.BOARD, group: pcbnew.PCB_GROUP
) -> pd.DataFrame:
    for _, component in components.iterrows():
        ref_des = component["ref des"]
        module = board.FindFootprintByReference(ref_des)
        if module is not None:
            group.AddItem(module)
    return components


def flip_module(ref_des: str, board: pcbnew.BOARD, side: str = "front") -> pcbnew.BOARD:
    """
    Move and rotate a part on a board
    :param str ref_def: Reference Designator of part
    :param pcbnew.BOARD board: Target board
    :param bool side: front, back, current
    """
    module = board.FindFootprintByReference(ref_des)
    if module is None:
        logging.warning("%s not found", ref_des)
        return None

    logging.debug("%s found", ref_des)

    if module.IsLocked():
        logging.debug("%s locked, skip", ref_des)
        return None

    # Set the correct side of the part, reflected over the y axis, correct the rotation later
    if (side.lower() == "front" and module.GetLayerName() != "F.Cu") or (
        side.lower() == "back" and module.GetLayerName() == "F.Cu"
    ):
        module.Flip(module.GetCenter(), aFlipLeftRight=True)

    return board


def move_module(
    ref_des: str, position: tuple, rotation: float, board: pcbnew.BOARD
) -> pcbnew.BOARD:
    """
    Move and rotate a part on a board
    :param str ref_def: Reference Designator of part
    :param tuple(float x, float y) position: Desired center of part in mm
    :param float rotation: Desired rotation of part
    :param pcbnew.BOARD board: Target board
    """
    module = board.FindFootprintByReference(ref_des)
    if module is None:
        logging.warning("%s not found", ref_des)
        return None

    logging.debug("%s found", ref_des)

    if module.IsLocked():
        logging.debug("%s locked, skip", ref_des)
        return None

    center = module.GetCenter()  # pdbnew.wxPoint
    new_pos = pcbnew.wxPoint(position[0], position[1])
    msg = f"{ref_des}: Move from {center} to {new_pos}, {position}"
    logging.info(msg)

    module.SetOrientationDegrees(rotation)
    module.SetPosition(pcbnew.VECTOR2I(*new_pos))

    # module.Rotate(module.GetCenter(), component['rotation']*10)
    msg = f"{ref_des}: rotate {rotation} about {new_pos}"
    logging.info(msg)
    return board


def move_modules(components: pd.DataFrame, board: pcbnew.BOARD) -> pcbnew.BOARD:
    """
    components: pd data frame containing fields:
        ref des, value, x, y, rotation
    board: pcbnew.BOARD object to edit

    Cycle through all parts on the board.
    Read the footprints reference
    If the ref des is in components["ref des"] then enter to update
    Update the parts position to the schematics plus the offset
    Update the label to with a configuration table passed to a function
    """

    for _, component in components.iterrows():
        ref_des = component["ref des"]
        position = (component["x"], component["y"])
        move_module(ref_des, position, component["rotation"], board)
    return board


def flip_modules(components: pd.DataFrame, board: pcbnew.BOARD) -> pcbnew.BOARD:
    for _, component in components.iterrows():
        ref_des = component["ref des"]
        flip_module(ref_des, side=component["side"], board=board)
    return board


def center_component_location_on_bounding_box(
    components: pd.DataFrame, bounding_box, mirror: bool
) -> pd.DataFrame:
    """
    Takes a bounding box and a set of components. Components
    so they fit in the xy center of the box
    """

    def get_offset(pos, ref):
        """
        pos: collection of component positions
        ref: board edges
        Takes the difference between the limits of the parts and the
        board edges, this gives the spacing from the edge of the board
        to the start of the parts to center the grouping
        """
        return ((max(pos) - min(pos)) - (max(ref) - min(ref))) / 2

    offset = (
        get_offset(components["x"], (bounding_box.GetLeft(), bounding_box.GetRight())),
        get_offset(components["y"], (bounding_box.GetBottom(), bounding_box.GetTop())),
    )

    components["x"] = components["x"] + bounding_box.GetRight() - offset[0]
    components["y"] = components["y"] + bounding_box.GetTop() + offset[1]
    return components


def place_parts(
    board: pcbnew.BOARD,
    components_df: pd.DataFrame,
    group_name: str | None = None,
    mirror: bool = False,
    origin: tuple[float, float] = (0,0)
) -> pcbnew.BOARD:
    """
    :param: pcbnew.BOARD board:
    :param: str group_name:
    :param: bool mirror: reflect parts over y axis
    :param: origin: reference point in mm

    Done as if looking down on the top of the board. Input can either be absolute or aux origin.
    The input must be in cartesian coordinates. Check that all the mapped output are within the positive
    natural coordinates.
    """
    # Short circuit exit if there's no components, this allows an improperly formated dataframe to be entered if it's empty
    if len(components_df) == 0:
        return board

    if "rotation" not in components_df.columns:
        components_df["rotation"] = 0
    components_df["rotation"] = np.array(components_df["rotation"], dtype=float)

    if mirror:
        components_df["rotation"] = (components_df["rotation"] + 180)%360

    #  Scale input to kicad native units
    components_df["x"] = [pcbnew.FromMM(pt) for pt in (components_df["x"] + origin[0])]
    mult = 1 if mirror else -1  # normally mirrored relative to cartesian coordinates
    components_df["y"] = [pcbnew.FromMM(pt) for pt in (components_df["y"]* mult + origin[1])]

    #if min(components_df["x"]) < 0:
    #    components_df["x"] = components_df["x"] - min(components_df["x"])

    #if min(components_df["y"]) < 0:
    #    components_df["y"] = components_df["y"] - min(components_df["y"])

    # There are no negative positions on a kicad schematic
    #assert min(components_df["x"]) >= 0
    #assert min(components_df["y"]) >= 0

    # add a default that won't change the side of the parts
    if "side" not in components_df.columns:
        components_df["side"] = "current"

    pseudonyms = {"front": ["front", "top", "f.cu"], "back": ["back", "bottom", "b.cu"]}

    sides = []
    for pt in components_df["side"]:
        if pt.lower() in pseudonyms["front"]:
            sides.append("front")
        elif pt.lower() in pseudonyms["back"]:
            sides.append("back")
        else:
            sides.append("current")

    # group
    if group_name is None:
        group_name = ""  # FIXME name the groups by group_{{INT}}
    pcb_group = pcbnew.PCB_GROUP(None)
    pcb_group.SetName(group_name)
    board.Add(pcb_group)
    group_components(components_df, board, pcb_group)

    board = flip_modules(components_df, board)
    return move_modules(components_df, board)

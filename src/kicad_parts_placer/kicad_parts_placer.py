"""
kicad_parts_placer: Place parts programatically
"""

import logging
import copy
from typing import Union
try:
    from pandas import DataFrame
except ImportError:
    DataFrame = None
import pcbnew

_log = logging.getLogger("kicad_parts_placer")

_header_pseudonyms = {
    "x": ["posx", "positionx", "xpos", "xposition", "midx", "xmid", "x"],
    "y": ["posy", "positiony", "ypos", "yposition", "midy", "ymid", "y"],
    "rotation": ["rot", "angle", "rotate", "rotation"],
    "side": ["layer", "side"],
    "refdes": ["designator", "referencedesignator", "ref", "refdes"],
}

_pseudonyms_invert = {}
for key, value_array in _header_pseudonyms.items():
    for value in value_array:
        _pseudonyms_invert[value] = key

_required_columns = ("x", "y", "refdes")

def flip_module(ref_des: str, board: pcbnew.BOARD, side: str = "front") -> pcbnew.BOARD:
    """
    Move and rotate a part on a board
    :param str ref_def: Reference Designator of part
    :param pcbnew.BOARD board: Target board
    :param bool side: front, back, current
    """
    module = board.FindFootprintByReference(ref_des)
    if module is None:
        _log.warning("%s not found", ref_des)
        return None

    _log.debug("%s found", ref_des)

    if module.IsLocked():
        _log.info("%s locked, skip", ref_des)
        return None

    # Set the correct side of the part, reflected over the y axis, correct the rotation later
    _log.debug("Side: %s", side)
    if (side == "front" and module.GetLayerName() != "F.Cu") or (
        side == "back" and module.GetLayerName() == "F.Cu"
    ):
        _log.debug("Flip")
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

    Read the footprints reference
    If the refdes is in components["refdes"] then enter to update
    Update the parts position to the schematics plus the offset
    Update the label to with a configuration table passed to a function
    """

    module = board.FindFootprintByReference(ref_des)
    if module is None:
        _log.warning("%s not found", ref_des)
        return None

    _log.debug("%s found", ref_des)

    if module.IsLocked():
        _log.info("%s locked, skip", ref_des)
        return None

    center = module.GetCenter()  # pdbnew.wxPoint
    new_pos = pcbnew.wxPoint(position[0], position[1])
    msg = f"{ref_des}: Move from {center} to {new_pos}, {position}"
    _log.debug(msg)

    module.SetOrientationDegrees(rotation)
    module.SetPosition(pcbnew.VECTOR2I(*new_pos))

    # module.Rotate(module.GetCenter(), component['rotation']*10)
    msg = f"{ref_des}: rotate {rotation} about {new_pos}"
    _log.debug(msg)
    return board


def center_component_location_on_bounding_box(
    components: DataFrame, bounding_box
) -> DataFrame:
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

    components["x"] = [pt + bounding_box.GetRight() - offset[0] for pt in components["x"]]
    components["y"] = [pt + bounding_box.GetTop() + offset[1] for pt in components["y"]]
    return components


def group_parts(
    board: pcbnew.BOARD,
    components_df: DataFrame,
    group_name: Union[str, None] = None,
) -> pcbnew.BOARD:
    """
    Put all parts in dataframe into a single group
    """
    if group_name is None:
        group_name = ""  # FIXME name the groups by group_{{INT}}

    if len(components_df) == 0:
        return board

    assert isinstance(group_name, str)
    group = pcbnew.PCB_GROUP(None)
    group.SetName(group_name)
    board.Add(group)
    for _, component in components_df.iterrows():
        ref_des = component["refdes"]
        module = board.FindFootprintByReference(ref_des)
        if module is not None:
            group.AddItem(module)

    return board


def translate_header(header):
    """
    Translate the header to a standardized form.
    If the tag cannot be found then just return it unchanged
    """

    header_dict = {col.lower().replace(" ", "") : col for col in header}
    logging.error(_pseudonyms_invert)
    return tuple([_pseudonyms_invert.get(key, header_dict[key]) for key in header_dict])


def place_parts(
    board: pcbnew.BOARD,
    components_df: DataFrame,
    origin: tuple[float, float] = (0, 0),
) -> pcbnew.BOARD:
    """
    :param: pcbnew.BOARD board:
    :param: str group_name:
    :param: bool mirror: reflect parts over y axis
    :param: origin: reference point in mm

    Done as if looking down on the top of the board.
    Input can either be absolute or aux origin.
    The input must be in cartesian coordinates.
    Check that all the mapped output are within the positive natural coordinates.
    """
    # Short circuit exit if there are no components
    # this allows an improperly formated dataframe to be entered if it's empty
    components_df = copy.deepcopy(components_df)
    components_df.columns = [pt.lower().strip() for pt in components_df.columns]
    if len(components_df) == 0:
        return board

    components_df.columns = translate_header(components_df.columns)

    if "rotation" not in components_df.columns:
        components_df["rotation"] = 0
    components_df["rotation"] = [float(pt) for pt in components_df["rotation"]]

    # if mirror:
    #    components_df["rotation"] = (components_df["rotation"] + 180)%360

    #  Scale input to kicad native units
    components_df["x"] = [
        pcbnew.FromMM(float(pt + origin[0])) for pt in (components_df["x"])
    ]
    components_df["y"] = [
        pcbnew.FromMM(float(-1*pt + origin[1])) for pt in (components_df["y"])
    ]  # cartesian -> pixel

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
    components_df["_side"] = sides

    for _, component in components_df.iterrows():
        ref_des = component["refdes"]
        flip_module(ref_des, side=component["_side"], board=board)

    for _, component in components_df.iterrows():
        ref_des = component["refdes"]
        position = (component["x"], component["y"])
        move_module(ref_des, position, component["rotation"], board)

    return board


def mirror_parts(
    board: pcbnew.BOARD,
    components_df: DataFrame,
    origin: tuple[float, float] = (0, 0),
):
    """
    Mirror parts in an entire dataframe
    """

    components_df = copy.deepcopy(components_df)
    components_df["x"] = [-1*pt for pt in components_df["x"]]
    place_parts(board, components_df, origin)
    return board

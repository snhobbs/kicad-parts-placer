"""
kicad_parts_placer: Place parts programatically
"""

import copy
import logging
from enum import Enum, IntEnum
from typing import Any
from dataclasses import dataclass

_log = logging.getLogger(__name__)

BoardType: type = object
KICAD_FOUND = False
try:
    import pcbnew

    BoardType: type = pcbnew.BOARD

    KICAD_FOUND = True
except ImportError:
    _log.warning("KiCAD Not Available")


class SideEnum(Enum):
    top = "TOP"
    bottom = "BOTTOM"
    current = "CURRENT"


_HEADER_PSEUDONYMS = {
    "refdes": ["designator", "referencedesignator", "ref", "refdes"],
    "x": ["posx", "positionx", "xpos", "xposition", "midx", "xmid", "x"],
    "y": ["posy", "positiony", "ypos", "yposition", "midy", "ymid", "y"],
    "rotation": ["rot", "angle", "rotate", "rotation"],
    "side": ["layer", "side"],
}


_PSEUDONYMS_INVERT = {
    alias: key for key, aliases in _HEADER_PSEUDONYMS.items() for alias in aliases
}

_SIDE_PSEUDONYMS = {
    "front": SideEnum.top,
    "top": SideEnum.top,
    "f.cu": SideEnum.top,
    "back": SideEnum.bottom,
    "bottom": SideEnum.bottom,
    "b.cu": SideEnum.bottom,
}


@dataclass
class ComponentRow:
    refdes: str
    x: float
    y: float
    rotation: float
    side: SideEnum

    @classmethod
    def from_series(cls, s) -> "ComponentRow":
        return cls(
            refdes=s["refdes"],
            x=float(s["x"]),
            y=float(s["y"]),
            rotation=float(s["rotation"]),
            side=s["side"],
        )


def translate_header(header):
    header_dict = {col.lower().replace(" ", ""): col.strip() for col in header}
    return tuple(_PSEUDONYMS_INVERT.get(key, val) for key, val in header_dict.items())


def setup_dataframe(components_df):
    """
    Change the dataframe into a standard form
    """
    components_df = copy.deepcopy(components_df)
    components_df.columns = [pt.lower().strip() for pt in components_df.columns]
    components_df.columns = translate_header(components_df.columns)

    if "rotation" not in components_df.columns:
        components_df["rotation"] = [0] * len(components_df)
    components_df["rotation"] = [float(pt) for pt in components_df["rotation"]]

    # if mirror:
    #    components_df["rotation"] = (components_df["rotation"] + 180)%360

    # add a default that won't change the side of the parts
    if "side" not in components_df.columns:
        components_df["side"] = [SideEnum.current] * len(components_df)

    sides = []
    for pt in components_df["side"]:
        if isinstance(pt, SideEnum):
            sides.append(pt)
        else:
            resolved = _SIDE_PSEUDONYMS.get(pt.lower().strip())
            sides.append(resolved if resolved is not None else pt)
    components_df["side"] = sides
    return components_df


def to_component_rows(components_df) -> list[ComponentRow]:
    components_df = setup_dataframe(components_df)
    return [ComponentRow.from_series(row) for _, row in components_df.iterrows()]


def check_input_valid(components_df):
    components_df = setup_dataframe(components_df)
    missing = set(_HEADER_PSEUDONYMS.keys()).difference(set(components_df.columns))
    if len(missing):
        return False, [f"Missing Field {pt}" for pt in missing]

    errors = []
    for i, line in components_df.iterrows():
        row = ComponentRow.from_series(line)
        if not isinstance(row.side, SideEnum):
            errors.append(f"Row {i}: invalid side value {line['side']!r}")
        if not row.refdes:
            errors.append(f"Row {i}: empty refdes")

    return len(errors) == 0, errors


class FLIP_DIRECTION(IntEnum):
    LEFT_RIGHT = 0  # , ///< Flip left to right (around the Y axis)
    TOP_BOTTOM = 1  #  ///< Flip top to bottom (around the X axis)


def flip_module(
    ref_des: str, board: BoardType, side: SideEnum = SideEnum.top
) -> BoardType:
    """
    Move and rotate a part on a board
    :param str ref_def: Reference Designator of part
    :param pcbnew.BOARD board: Target board
    :param bool side: front, back, current
    """
    _log.debug("flip_module called: side=%s type=%s", side, type(side))
    assert isinstance(side, SideEnum)
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
    if (side == SideEnum.top and module.GetLayerName() != "F.Cu") or (
        side == SideEnum.bottom and module.GetLayerName() == "F.Cu"
    ):
        _log.debug(f"Flip {ref_des}")
        kwargs = {"aFlipLeftRight": True}
        if pcbnew.Version()[0] == "9":
            kwargs = {"aFlipDirection": int(FLIP_DIRECTION.TOP_BOTTOM)}

        module.Flip(module.GetCenter(), **kwargs)

    return board


def move_module(
    ref_des: str, position: tuple, rotation: float, board: BoardType
) -> BoardType:
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


def center_component_location_on_bounding_box(components, bounding_box):
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

    components["x"] = [
        pt + bounding_box.GetRight() - offset[0] for pt in components["x"]
    ]
    components["y"] = [pt + bounding_box.GetTop() + offset[1] for pt in components["y"]]
    return components


def _place_part(
    board: BoardType, component: ComponentRow, origin: tuple[float, float] = (0, 0)
):
    location = (component.x, component.y)
    #  Scale input to kicad native units
    x_mm = pcbnew.FromMM(float(location[0]) + origin[0])

    # cartesian -> pixel
    y_mm = pcbnew.FromMM(-1 * float(location[1]) + origin[1])
    ref_des = component.refdes

    if x_mm < 0 or y_mm < 0:
        msg = f"Placement of REF {ref_des} outside of legal range. Origin: {origin}, location: {location} -> ({x_mm}, {y_mm})"
        raise ValueError(msg)
    flip_module(ref_des, side=component.side, board=board)
    move_module(ref_des, (x_mm, y_mm), component.rotation, board=board)

    return board


def place_parts(
    board: BoardType,
    components: list[ComponentRow],
    origin: tuple[float, float] = (0, 0),
) -> BoardType:
    if not components:
        _log.warning("No parts provided")
        return board
    for component in components:
        _place_part(board=board, component=component, origin=origin)
    return board


def mirror_parts(
    board: BoardType,
    components: list[ComponentRow],
    origin: tuple[float, float] = (0, 0),
) -> BoardType:
    mirrored = [replace(c, x=-c.x) for c in components]  # dataclasses.replace
    return place_parts(board, mirrored, origin)


def get_missing_references(
    board: BoardType, components: list[ComponentRow]
) -> list[str]:
    return [
        c.refdes for c in components if board.FindFootprintByReference(c.refdes) is None
    ]


def group_parts(
    board: BoardType,
    components: list[ComponentRow],
    group_name: str = "",
) -> BoardType:
    if not components:
        return board
    group = pcbnew.PCB_GROUP(None)
    group.SetName(group_name)
    board.Add(group)
    for component in components:
        module = board.FindFootprintByReference(component.refdes)
        if module is not None:
            group.AddItem(module)
    return board

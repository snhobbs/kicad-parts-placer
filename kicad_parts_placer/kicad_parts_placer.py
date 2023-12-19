import pcbnew
import pandas
import logging


# the internal coorinate space of pcbnew is 1E-6 mm. (a millionth of a mm)
# the coordinate 121550000 corresponds to 121.550000
def get_scale():
    return 1/1e-6


def group_components(components: pandas.DataFrame, board: pcbnew.BOARD, group: pcbnew.PCB_GROUP):
    for _, component in components.iterrows():
        ref_des = component["ref des"]
        module = board.FindFootprintByReference(ref_des)
        if module is not None:
            group.AddItem(module)
    return components


def scale_to_mm(unit):
    return unit/get_scale()


def scale_from_mm(mm):
    return mm*get_scale()


def move_module(ref_des: str, position: tuple, rotation: float, board: pcbnew.BOARD):
    '''
    Move and rotate a part on a board
    :param str ref_def: Reference Designator of part
    :param tuple(float x, float y) position: Desired center of part in mm
    :param float rotation: Desired rotation of part
    :param pcbnew.BOARD board: Target board
    '''
    module = board.FindFootprintByReference(ref_des)
    if module is None:
        logging.warning("%s not found", ref_des)
        return

    logging.debug("%s found", ref_des)

    if module.IsLocked():
        logging.debug("%s locked, skip", ref_des)
        return

    center = module.GetCenter()  # pdbnew.wxPoint
    new_pos = pcbnew.wxPoint(position[0], position[1])
    logging.info(f"{ref_des}: Move from {center} to {new_pos}, {position}")
    module.SetOrientationDegrees(rotation)

    # module.Rotate(module.GetCenter(), component['rotation']*10)
    logging.info(f"{ref_des}: rotate {rotation} about {new_pos}")
    module.SetPosition(pcbnew.VECTOR2I(*new_pos))
    return board


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
        position = (component['x'], component['y'])
        move_module(ref_des, position, component['rotation'], board)
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

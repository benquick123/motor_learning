import numpy as np


def compute_cbos(markers):
    marker_keys = {"Left_foot_heel", "Left_foot2", "Left_foot3", "Right_foot_heel", "Right_foot2", "Right_foot3"}
    marker_positions = []
    for key in marker_keys:
        marker_positions.append(markers[key])

    marker_positions = np.stack(marker_positions, axis=0)
    return np.mean(marker_positions, axis=0)
import numpy as np


def compute_cbos(markers):
    # https://stackoverflow.com/questions/75699024/finding-the-centroid-of-a-polygon-in-python
    # markers must be in the order that forms a convex polygon
    marker_keys = ["Left_foot2", "Left_foot3", "Left_foot_heel", "Right_foot_heel", "Right_foot3", "Right_foot2"]
    marker_positions = []
    for key in marker_keys:
        marker_positions.append(markers[key])

    marker_positions = np.stack(marker_positions, axis=0)
    marker_positions2 = np.roll(marker_positions, -1, axis=0)

    signed_areas = 0.5 * np.cross(marker_positions, marker_positions2)
    centroids = (marker_positions + marker_positions2) / 3.0

    return np.average(centroids, axis=0, weights=signed_areas)
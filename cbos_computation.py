import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial._qhull import QhullError


def compute_cbos(markers):
    # https://stackoverflow.com/questions/31562534/scipy-centroid-of-convex-hull
    # markers must be in the order that forms a convex polygon
    marker_keys = ["Left_foot2", "Left_foot3", "Left_foot_heel", "Right_foot_heel", "Right_foot3", "Right_foot2"]
    marker_positions = []
    for key in marker_keys:
        marker_positions.append(markers[key])
    
    marker_positions = np.stack(marker_positions, axis=0)

    try:
        hull = ConvexHull(marker_positions)
        centroid = np.mean(hull.points[hull.vertices], axis=0)
    except QhullError:
        centroid = np.zeros(3)

    return centroid
import numpy as np


NOMINAL_HEIGHT = 1.78 # m
NOMINAL_WEIGHT = 77.9 # kg
NOMINAL_LH2 = 0.1488 # m
NOMINAL_LH3 = 0.0825 # m

def compute_com(left_thigh, right_thigh, neck, adjustment_ratio):
    lh2 = adjustment_ratio * NOMINAL_LH2
    lh3 = adjustment_ratio * NOMINAL_LH3

    # get the marker positions relative to the centre of bos:
    # left_thigh -= cbos
    # right_thigh -= cbos
    # neck -= cbos
    
    # get the lower_back point position
    midpoint = 0.5 * (left_thigh + right_thigh)
    
    # we derive the left-right thigh angle
    # assuming y axis is the one we are not interested in
    thigh_displacement = right_thigh - left_thigh
    thigh_angle = np.arctan(thigh_displacement[2] / thigh_displacement[0]) # in radians
    lower_back = midpoint.copy()
    lower_back[0] += np.sin(thigh_angle) * lh2
    lower_back[2] += np.cos(thigh_angle) * lh2
    
    # get the actual center of mass
    # first, get the angle in y plane of the line going through lower and upper back
    back_displacement = neck - lower_back
    back_angle = np.arctan(back_displacement[2] / thigh_displacement[0])
    # from the angle, get the COM
    com = lower_back.copy()
    com[0] += np.sin(back_angle) * lh3
    com[1] = None
    com[2] += np.cos(back_angle) * lh3

    return com

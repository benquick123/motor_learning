import numpy as np


NOMINAL_WEIGHT = 77.9 # kg
NOMINAL_TORSO_WEIGHT = 37.8264 # kg
NOMINAL_PELVIS_WEIGHT = 8.8101 # kg
NOMINAL_FOOT_WEIGHT = 1.0688 # kg
NOMINAL_SHANK_WEIGHT = 3.3794 # kg
NOMINAL_THIGH_WEIGHT = 11.1826 # kg

NOMINAL_HEIGHT = 1.78 # m
NOMINAL_LH2 = 0.1488 # m
NOMINAL_LB = 0.4432 # m
NOMINAL_LC = 0.4312 # m
NOMINAL_LD = 0.1650 # m
NOMINAL_RHOB = 0.1976 # m
NOMINAL_RHOC = 0.1766 # m
NOMINAL_RHOA1 = 0.0461 # m
NOMINAL_RHOA2 = 0.0284 # m
NOMINAL_RHOD2 = 0.0578 # m
NOMINAL_RHOH2 = 0.1488 # m


def create_marker_dict(positions, measurement_idx, ignore={}):
    markers = {}
    for k, v in positions.items():
        if k in ignore:
            continue
        markers[k] = v[measurement_idx]

    return markers

def compute_com(markers, height_adjustment_ratio, weight_adjustment_ratio, plot=False):
    # get adjusted lengths
    lh2 = height_adjustment_ratio * NOMINAL_LH2
    ld = height_adjustment_ratio * NOMINAL_LD
    lb = height_adjustment_ratio * NOMINAL_LB
    rhob = height_adjustment_ratio * NOMINAL_RHOB
    rhoc = height_adjustment_ratio * NOMINAL_RHOC
    rhoa1 = height_adjustment_ratio * NOMINAL_RHOA1
    rhoa2 = height_adjustment_ratio * NOMINAL_RHOA2
    rhod2 = height_adjustment_ratio * NOMINAL_RHOD2
    rhoh2 = height_adjustment_ratio * NOMINAL_RHOH2

    # get adjusted weights
    torso_weight = weight_adjustment_ratio * NOMINAL_TORSO_WEIGHT
    pelvis_weight = weight_adjustment_ratio * NOMINAL_PELVIS_WEIGHT
    foot_weight = weight_adjustment_ratio * NOMINAL_FOOT_WEIGHT
    shank_weight = weight_adjustment_ratio * NOMINAL_SHANK_WEIGHT
    thigh_weight = weight_adjustment_ratio * NOMINAL_THIGH_WEIGHT

    # get the positions of all missing markers
    midpoint = 0.5 * (markers["Upper_body_left_thigh"] + markers["Upper_body_right_thigh"])

    inner_thigh_ratio = (ld / 2) / (np.linalg.norm(midpoint - markers["Upper_body_left_thigh"]) + 1e-8) # should be the same for left and right
    inner_thigh_left = midpoint * inner_thigh_ratio + markers["Upper_body_left_thigh"] * (1 - inner_thigh_ratio)
    inner_thigh_right = midpoint * inner_thigh_ratio + markers["Upper_body_right_thigh"] * (1 - inner_thigh_ratio)
    
    knee_ratio_left = lb / (np.linalg.norm(inner_thigh_left - markers["Left_foot_heel"]) + 1e-8)
    knee_left = markers["Left_foot_heel"] * knee_ratio_left + inner_thigh_left * (1 - knee_ratio_left)
    knee_ratio_right = lb / (np.linalg.norm(inner_thigh_right - markers["Right_foot_heel"]) + 1e-8)
    knee_right = markers["Right_foot_heel"] * knee_ratio_right + inner_thigh_right * (1 - knee_ratio_right)
    
    # obtain lower back marker position
    # assuming y axis is the one we are not interested in
    hip_distance = np.linalg.norm(markers["Upper_body_right_thigh"] - markers["Upper_body_left_thigh"])
    lower_back_x = -lh2 * (markers["Upper_body_left_thigh"][2] - markers["Upper_body_right_thigh"][2]) / (hip_distance + (markers["Upper_body_left_thigh"][0] + markers["Upper_body_right_thigh"][0]) / 2 + 1e-8)
    lower_back_z = lh2 * (markers["Upper_body_left_thigh"][0] - markers["Upper_body_right_thigh"][0]) / (hip_distance + (markers["Upper_body_left_thigh"][2] + markers["Upper_body_right_thigh"][2]) / 2 + 1e-8)
    lower_back = midpoint.copy()
    lower_back[0] = lower_back_x
    lower_back[2] = lower_back_z

    # get COMs of all the lower body parts
    thigh_left_com_ratio = rhoc / (np.linalg.norm(knee_left - inner_thigh_left) + 1e-8)
    thigh_left_com = inner_thigh_left * thigh_left_com_ratio + knee_left * (1 - thigh_left_com_ratio) # C*
    thigh_right_com_ratio = rhoc / (np.linalg.norm(knee_right - inner_thigh_right) + 1e-8)
    thigh_right_com = inner_thigh_right * thigh_right_com_ratio + knee_right * (1 - thigh_right_com_ratio) # E*

    shank_left_com_ratio = rhob / (np.linalg.norm(knee_left - markers["Left_foot_heel"]) + 1e-8)
    shank_left_com = knee_left * shank_left_com_ratio + markers["Left_foot_heel"] * (1 - shank_left_com_ratio) # F*
    shank_right_com_ratio = rhob / (np.linalg.norm(knee_right - markers["Right_foot_heel"]) + 1e-8)
    shank_right_com = knee_right * shank_right_com_ratio + markers["Right_foot_heel"] * (1 - shank_right_com_ratio) # B*

    foot_left_com = np.array(markers["Left_foot_heel"])
    foot_left_com[1] -= rhoa1
    foot_left_com[2] -= rhoa2
    
    foot_right_com = np.array(markers["Right_foot_heel"])
    foot_right_com[1] -= rhoa1
    foot_right_com[2] -= rhoa2

    # get COMs of all the upper body parts
    pelvis_com_ratio = rhod2 / lh2
    pelvis_com = midpoint * pelvis_com_ratio + lower_back * (1 - pelvis_com_ratio)

    torso_com_ratio = rhoh2 / (np.linalg.norm(lower_back - markers["Upper_body_neck"]) + 1e-8)
    torso_com = lower_back * torso_com_ratio + markers["Upper_body_neck"] * (1 - torso_com_ratio)

    # get the actual center of mass
    all_coms = np.array([torso_com, pelvis_com, thigh_left_com, thigh_right_com, shank_left_com, shank_right_com, foot_left_com, foot_right_com])
    all_weights = np.array([torso_weight, pelvis_weight, thigh_weight, thigh_weight, shank_weight, shank_weight, foot_weight, foot_weight]).reshape(-1, 1)
    com = (all_coms * all_weights).sum(axis=0) / all_weights.sum()


    if plot:
        import matplotlib.pyplot as plt
        ax = plt.figure().add_subplot(projection='3d')
        for k, m in markers.items():
            ax.scatter(m[0], m[1], m[2], color="b")
            ax.text(m[0],m[1],m[2], k, size=10, zorder=1, color='k')

        ax.scatter(midpoint[0], midpoint[1], midpoint[2])
        ax.text(midpoint[0], midpoint[1], midpoint[2], "midpoint", size=10, zorder=1, color='k') 

        ax.scatter(lower_back[0], lower_back[1], lower_back[2])
        ax.text(lower_back[0], lower_back[1], lower_back[2], "lower_back", size=10, zorder=1, color='k') 

        ax.scatter(inner_thigh_left[0], inner_thigh_left[1], inner_thigh_left[2])
        ax.text(inner_thigh_left[0], inner_thigh_left[1], inner_thigh_left[2], "inner_thigh_left", size=10, zorder=1, color='k')
        ax.scatter(inner_thigh_right[0], inner_thigh_right[1], inner_thigh_right[2])
        ax.text(inner_thigh_right[0], inner_thigh_right[1], inner_thigh_right[2], "inner_thigh_right", size=10, zorder=1, color='k')
        
        ax.scatter(knee_left[0], knee_left[1], knee_left[2])
        ax.text(knee_left[0], knee_left[1], knee_left[2], "knee_left", size=10, zorder=1, color='k')
        ax.scatter(knee_right[0], knee_right[1], knee_right[2])
        ax.text(knee_right[0], knee_right[1], knee_right[2], "knee_right", size=10, zorder=1, color='k')
        
        ax.scatter(thigh_left_com[0], thigh_left_com[1], thigh_left_com[2], color="k", s=int(thigh_weight * 20), alpha=0.5)
        ax.text(thigh_left_com[0], thigh_left_com[1], thigh_left_com[2], "thigh_left_com", size=10, zorder=1, color='k')
        ax.scatter(thigh_right_com[0], thigh_right_com[1], thigh_right_com[2], color="k", s=int(thigh_weight * 20), alpha=0.5)
        ax.text(thigh_right_com[0], thigh_right_com[1], thigh_right_com[2], "thigh_right_com", size=10, zorder=1, color='k')
        
        ax.scatter(shank_left_com[0], shank_left_com[1], shank_left_com[2], color="k", s=int(shank_weight * 20), alpha=0.5)
        ax.text(shank_left_com[0], shank_left_com[1], shank_left_com[2], "shank_left_com", size=10, zorder=1, color='k')
        ax.scatter(shank_right_com[0], shank_right_com[1], shank_right_com[2], color="k", s=int(shank_weight * 20), alpha=0.5)
        ax.text(shank_right_com[0], shank_right_com[1], shank_right_com[2], "shank_right_com", size=10, zorder=1, color='k')
        
        ax.scatter(foot_left_com[0], foot_left_com[1], foot_left_com[2], color="k", s=int(foot_weight * 20), alpha=0.5)
        ax.text(foot_left_com[0], foot_left_com[1], foot_left_com[2], "foot_left_com", size=10, zorder=1, color='k')
        ax.scatter(foot_right_com[0], foot_right_com[1], foot_right_com[2], color="k", s=int(foot_weight * 20), alpha=0.5)
        ax.text(foot_right_com[0], foot_right_com[1], foot_right_com[2], "foot_right_com", size=10, zorder=1, color='k')
        
        ax.scatter(pelvis_com[0], pelvis_com[1], pelvis_com[2], color="k", s=int(pelvis_weight * 20), alpha=0.5)
        ax.text(pelvis_com[0], pelvis_com[1], pelvis_com[2], "pelvis_com", size=10, zorder=1, color='k')
        ax.scatter(torso_com[0], torso_com[1], torso_com[2], color="k", s=int(torso_weight * 20), alpha=0.5)
        ax.text(torso_com[0], torso_com[1], torso_com[2], "torso_com", size=10, zorder=1, color='k')
        
        ax.scatter(com[0], com[1], com[2], color="k", s=int(all_weights.sum() * 20), alpha=0.9)
        ax.text(com[0], com[1], com[2], "com", size=10, zorder=1, color='k')

        plt.tight_layout()
        plt.show()
        exit()

    return com

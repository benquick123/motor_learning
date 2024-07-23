# Motor learning experiment with VICON and pullers

## Experimental setup instructions

0. Turn on and calibrate the VICON system.
1. From the perspective of the screen, the wand determining the origin should be placed in the middle of the two force plates and facing away from it.
2. The code is located in the folder `D:\motor_learning_code`. To run the code, move to that folder by opening the Command Prompt (`cmd`) and typing:
```
D: <Press Enter>
cd motor_learning_code <Press Enter>
```
3. Before starting the experiment, check the current code branch. This determines whether "time" or "trial" mode will be employed. You do so by opening Command Prompt (`cmd`), and typing `git status` and checking the first line of the output.
    - If the text says "On branch master", the experiment will run in time mode.
    - If the text says "On branch trial_mode", the experiment will run in trial mode.
    - If the currently open branch does not match the desired mode, change it by typing `git checkout <branch_name>` and pressing Enter. 
    - In case the files have changed on the current branch (e.g. `experiment_config.json`), it is recommended to force checkout and discard changes when asked by the prompt.

4. Input the participant parameters and experiment values into the `experiment_config.json` file.
5. Do the particpant feet placement and COM estimation using `python do_before.py`. Follow the instructions in the terminal window. After the estimation is done, the results should be available in the folder specified in the configuration file.
6. Run the experiment by starting `python do_experiment.py`. 
7. Make sure to start the recording in VICON as per instructions on the screen. The network trigger has to be enabled and armed under the `Capture` tab in VICON before starting the recording.

Everytime the experiment is executed, the index of the logged experiment configuration and trajectory data gets incremented to avoid losing any data. Keep this in mind if you run the script multiple times.

## Configuration example:

```json
{
    "results_path": "./trial_results",
    "participant": {
        "id": 1,
        "height": 1.84,
        "weight": 73,
        "gender": "m",
        "age": 29
    },
    "experiment_pause_duration": 10,
    "experiment": [
        {
            "total_time": 0,
            "total_trials": 50,
            "desired_trial_time": [0.8, 1.2],
            "state_wait_time_range": [1, 3],
            "force_amplification": 3.5,
            "force_direction": "forward",
            "force_mode": "none",
            "catch_trial_idxs": [],
            "channel_trial_idxs": [],
            "channel_amplification": 1.0
        },
        {
            "total_time": 0,
            "total_trials": 50,
            "desired_trial_time": [0.8, 1.2],
            "state_wait_time_range": [1, 3],
            "force_amplification": 3.5,
            "force_direction": "forward",
            "force_mode": "regular",
            "catch_trial_idxs": [],
            "channel_trial_idxs": [],
            "channel_amplification": 1.0
        },
        ...
    ],
    "interface": {
        "pixels_per_m": 3200,
        "display_scaling": 2.0
    },
    "refresh_frequency": 200
}
```

Above, "experiment" field contains list of blocks and determines majority of the parameters necessary for running the experiment. Each block is followed by an experiment pause, after which the next one is executed. Below are the parameters:
- `total_time`: total time available for the experiment. Only used in the master (time mode) branch. 
- `total_trials`: total trials to be executed by the participant. Only used in the trial_mode branch.
- `desired_trial_time`: an array determining the interval of the desired time for the completion of the movement. Only used in the trial_mode branch.
- `force_direction`: either "forward" or "backward". Determines the direction of the perturbation. Used only when "force_mode" is "regular". 
- `force_mode`: either "regular", "none" depending on whether we want to create perturbations (regular mode), no perturbation (none mode).
- `force_multiplication`: the coefficient for the force generated by the pullers used when "force_mode" is "regular" or "channel". 
- `catch_trial_idxs`: the trials in which the perturbation is "randomly" turned off. Only used in the trial_mode branch. If empty, there are no catch trials. Indices of the catch trials start from 0.
- `channel_trial_idxs`: the indexes of the trials in which the force helps the participant. If empty, there are not catch trials. Indices of the catch trials start from 0.
- `channel_amplification`: determines the corrective force coefficient used in the channel trials.

Variable "experiment_pause_duration" determines the duration of the pauses in seconds between blocks in the "experiment" field.

Variable "pixels_per_m" has to be changed every time the screen size or resolution changes. It can be changed by multiplying the number of horizontal pixels with the width of the screen in meters. "display_scaling" determines the scaling of the display.

Field "participant" contains information about the participant. The subfields "id", "height" and "weight" are neccessary, however, any other entry can be added or removed in addition to these without breaking the experimental code. **Make sure that the "id" field is different for every subject.**

It is recommented to keep the "refresh_frequency" at the specificed value.
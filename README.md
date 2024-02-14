# Motor learning experiment with VICON and pullers

## Experimental setup instructions

0. Turn on and calibrate the VICON system.
1. From the perspective of the screen, the wand determining the origin should be placed in the middle of the two force plates end facing away from it.
2. The code is located in the folder `D:\motor_learning_code`. To run the code, move to that folder by opening the Command Prompt (`cmd`) and typing:
```
D: <Press Enter>
cd motor_learning_code <Press Enter>
```
3. Before starting the experiment, check the current code branch. This determines whether "time" or "trial" mode will be employed. You do so by opening Command Prompt (`cmd`), and typing `git status` and checking the first line of the output.
    - If the text says "On branch master", the experiment will run in time mode.
    - If the text says "On branch trial_mode", the experiment will run in trial mode.
    - If the currently open branch does not match the desired mode, change it by typing `git checkout <branch_name>` and pressing Enter.
4. Input the participant parameters and experiment values into the `experiment_config.json` file.
5. Do the particpant feet placement and COM estimation using `python do_before.py`. Follow the instructions in the terminal window. After the estimation is done, the results should be available in the `results` folder.
6. Run the experiment by starting `python do_experiment.py`.

Everytime the experiment is executed, the index of the logged experiment configuration and trajectory data gets incremented to avoid losing any data. Keep this in mind if you run the script multiple times.

## Configuration example:

```json
{
    "results_path": "./results",
    "participant": {
        "id": 0,
        "height": 1.63,
        "weight": 58,
        "gender": "m",
        "age": 27
    },
    "experiment": {
        "total_time": 200,
        "total_trials": 0,
        "desired_trial_time": [1, 3],
        "state_wait_time_range": [1, 3],
        "force_amplification": 3.5,
        "force_direction": "forward",
        "force_mode": "regular",
        "catch_trial_idxs": [],
        "pause_frequency": 50,
        "pause_duration": 10
    },
    "interface": {
        "pixels_per_m": 3200
    },
    "refresh_frequency": 200
}
```

Above, "experiment" field determines majority of the parameters necessary for running the experiment. Below are the explanations:
- `total_time`: total time available for the experiment. Only used in the master (time mode) branch. 
- `total_trials`: total trials to be executed by the participant. Only used in the trial_mode branch.
- `desired_trial_time`: an array determining the interval of the desired time for the completion of the movement. Only used in the trial_mode branch.
- `force_direction`: either "forward" or "backward". Determines the direction of the perturbation. Used only when "force_mode" is "regular". 
- `force_mode`: either "regular", "none" or "channel" depending on whether we want to create perturbations (regular mode), no perturbation (none mode) or help the participant (channel mode).
- `force_multiplication`: the coefficient of the perturbation, used when "force_mode" is "regular" or "channel". 
- `catch_trial_idxs`: the trials in which the perturbation is "randomly" turned off. Only used in the trial_mode branch. If empty, there are no catch trials. Indices of the catch trials start from 0.
- `pause_frequency`: the frequency of pauses in number of trials. Only used in the trial_mode branch.
- `pause_duration`: the duration of the pauses in seconds between blocks, as frequent as specified by the "pause_frequency" parameter. Only used in the trial_mode branch.

Variable "pixels per m" has to be changed every time the screen size or resolution changes. It can be changed by multiplying the number of horizontal pixels with the width of the screen in meters.

Field "participant" contains information about the participant. The subfields "id", "height" and "weight" are neccessary, however, any other entry can be added or removed in addition to these without breaking the experimental code.

It is recommented to keep the "refresh_frequency" at the specificed value.
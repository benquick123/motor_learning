# Motor learning experiment with VICON and pullers

## Experimental setup instructions

0. Turn on and calibrate the VICON system.
1. From the perspective of the screen, the wand determining the origin should be placed in the middle of the two force plates end facing away from it.
2. Input the participant parameters and experiment values into the `experiment_config.json` file.
3. Do the particpant feet placement and COM estimation using `python do_before.py`. After the estimation is done, the results should be available in the `results` folder.
4. Run the experiment by starting `python do_experiment.py`.

## Config example:

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
        "state_wait_time_range": [1, 3],
        "force_amplification": 3.5,
        "force_direction": "forward",
        "force_mode": "regular"
    },
    "interface": {
        "pixels_per_m": 3200
    },
    "refresh_frequency": 200
}
```

Above, "force_direction" can be either "forward" or "backward". Variable "force_mode" can be either "regular" or "channel" depending on whether we want to create perturbations (regular mode) or help the participant (channel mode).

Variable "pixels per m" has to be changed every time the screen size or resolution changes. It can be changed by multiplying the number of horizontal pixels with the width of the screen in meters.

## TODO

- change colors
- get frequency
- reverse x-axis direction of the COM.
- create an interface for determining the width of participant's feet relative to the width of their hips.
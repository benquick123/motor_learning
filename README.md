# Motor learning experiment using VICON and pullers

## Experimental setup instructions

0. Turn on and calibrate the VICON system.
1. From the perspective of the screen, the wand determining the origin should be placed in the middle of the two force plates end facing away from it.
2. Input the participant parameters and experiment values into the `experiment_config.json` file.
3. Do the particpant feet placement and COM estimation using `python do_before.py`. After the estimation is done, the results should be available in the `results` folder.
4. Run the experiment by starting `python do_experiment.py`.

## TODO

- change colors
- get frequency
- reverse x-axis direction of the COM.
- create an interface for determining the width of participant's feet relative to the width of their hips.
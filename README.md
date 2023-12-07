# Motor learning experiment using VICON and pullers

## Experimental setup instructions

0. Turn on and calibrate the VICON system.
1. From the perspective of the screen, the wand determining the origin should be placed with the long end facing towards it. It should be placed on the rear right corner of the duct-tape-made rectangle on the platform.
2. Input the participant parameters and experiment values into the `experiment_config.json` file.
3. Do the COM estimation using `python do_com.py`. After the estimation is done, the results should be available in the `results` folder.

## TODO

- update the sizes (magic numbers in interface:update) to correspond to whatever is measured on the screen.
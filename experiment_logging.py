import os
import json


class Logger:
    
    def __init__(self, results_path, participant_id, no_log):
        self.results_path = results_path
        self.participant_id = participant_id
        self.participant_folder = "participant_%03d" % self.participant_id
        self.no_log = no_log
        
        if not self.no_log:
            os.makedirs(self.results_path, exist_ok=True)
            os.makedirs(os.path.join(self.results_path, self.participant_folder), exist_ok=False)
    
    def save_experiment_config(self, experiment_config):
        if not self.no_log:
            json.dump(experiment_config, open(os.path.join(self.results_path, self.participant_folder, "experiment_config.json"), "w"), indent=4, sort_keys=True)
        
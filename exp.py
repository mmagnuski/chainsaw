# -*- encoding: utf-8 -*-
from __future__ import division, print_function

import os
import six
import yaml
import types
import random
import warnings

import numpy as np
import pandas as pd

from psychopy import visual, event, core, gui


# Experiment properties:
# window       - psychopy window
# clock        - psychopy clock used for timing responses
# exp_clock    - psychopy clock used for timing the whole experiment
# settings - read from a yaml file, see settings.yaml and settings.md
# stim     - dictionary str -> psychopy object containing all the stimuli used
#            in the experiment
# triggers - dictionary mapping between stimuli names and trigger values
#
# subject  - dictionary containing subject info, has to contain 'id' key
#            containing a string with subject identifier
#

# more about settings
# port_adress?
# quitopt?
#

# consider:
# start exp without a window
# change how subject and port stuff is held in Experiment

# resp_keys and resp_mapping
# classical setup is True / False
# but could be for example: ['triangle', 'square', 'circle']
# there should be a method for that - so one could override

class Experiment(object):

    def __init__(self, base_dir=None, frame_time=None):

        # ADD auto set base_dir if None
        self.base_dir = base_dir
        self.data_dir = base_dir / 'data'

        # if data dir does not exist -> create
        if not self.data_dir.exists():
            os.mkdir(self.data_dir)

        # load settings
        config_file = base_dir / 'settings.yaml'
        read_settings(self, config_file)
        self.set_resp()

        self.clock = core.Clock()
        self.exp_clock = core.Clock()
        self.current_trial = 0

        self.trigger_log = {'time': list(), 'trigger': list(), 'trial': list()}
        self.trigger_device, self.send_trigger = set_up_triggers(
            self.send_triggers)


    def set_window(self, window):
        '''Change window for all stimuli and experiment object.'''
        self.window = window

        for stim in self.stim.values():
            stim.win = window

    def save_data(self):
        full_path = os.path.join('data', self.subject['id'])
        self.df.to_csv(full_path + '.csv')
        self.df.to_excel(full_path + '.xls')





# time
# ----
def get_frame_time(win, frames=25):
    frame_rate = win.getActualFrameRate(nIdentical = frames)
    if frame_rate is None:
        # try one more time
        frame_rate = win.getActualFrameRate(nIdentical = frames)
    return 1.0 / frame_rate


def s2frames(time_in_seconds, frame_time):
    assert isinstance(time_in_seconds, dict)
    time_in_frames = dict()
    toframes = lambda x: int(round(x / frame_time))
    for k, v in six.iteritems(time_in_seconds):
        if isinstance(v, list):
            time_in_frames[k] = map(toframes, v)
        else:
            time_in_frames[k] = toframes(v)
    return time_in_frames


# utils
# -----
# - [ ] add numpy NaN
def isnull(x):
    if x is None:
        return True
    elif isinstance(x, (list, np.ndarray)):
        return len(x) == 0
    else:
        return False

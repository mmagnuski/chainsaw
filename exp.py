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
# window   - psychopy window
# clock    - psychopy clock
# settings - read from a yaml file, see settings.yaml and settings.md
# stim     - all stimuli objects
# triggers - mapping between stimuli and trigger values
# ...
# subject?
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

    def __init__(self, window, paramfile, frame_time=None):
        self.window = window
        if frame_time is None:
            self.frame_time = get_frame_time(window)
        else:
            self.frame_time = frame_time

        file_name = os.path.join(os.getcwd(), paramfile)
        with open(file_name, 'r') as f:
            settings = yaml.load(f)

        self.resp_keys = settings['resp_keys']
        self.times = s2frames(settings['times'], self.frame_time)
        self.settings = settings

        rnd = random.sample([True, False], 1)[0]
        self.resp_mapping = {self.resp_keys[0]: rnd}
        self.resp_mapping.update({self.resp_keys[1]: not rnd})

        self.quitopt = settings['quit']
        if self.quitopt['enable']:
            self.resp_keys.append(self.quitopt['button'])

        self.clock = core.Clock()
        self.current_trial = 0

        self.subject = dict()
        self.subject['id'] = 'test_subject'
        self.num_trials = self.df.shape[0]

        self.send_triggers = self.settings['send_triggers']
        self.port_adress = self.settings['port_adress']
        self.triggers = self.settings['triggers']
        self.clear_trigger = 2 # clear during second frame

        self.create_trials()
        self.create_stimuli()
        self.set_up_ports()

    def create_trials(self):
        pass

    def create_stimuli(self):
        pass

    def set_window(self, window):
        self.window = window
        self.fix.win = window
        for d in self.digits:
            d.win = window
        for st in self.stim.values():
            st.win = window

    def get_random_time(self, time, key):
        if time == None:
            time = random.randint(*self.times[key])
        return time

    def show_all_trials(self):
        trials_without_break = 0
        self.show_keymap()
        for t in range(1, self.num_trials+1):
            self.show_trial(t)
            self.save_data()
            trials_without_break += 1
            if trials_without_break >= self.settings['break_every_trials']:
                trials_without_break = 0
                self.present_break()
                self.show_keymap()
        core.quit()

    def run_trials(self, trials):
        for t in trials:
            self.show_trial(t)
            self.window.flip()
            break_time = random.uniform(self.times['inter_trial'][0],
                self.times['inter_trial'][1]+0.0001)
            core.wait(round(break_time, 3))

    def show_feedback(self, corr):
        corr = int(corr)
        stims = ['feedback_incorrect', 'feedback_correct']
        fdb = self.stim[stims[corr]]
        fdb.draw()
        self.window.flip()
        core.wait(0.7) # TODO - this could be a variable

    # this shouldn't be needed
    def show_fix(self, fix_time=None):
        if fix_time is None:
            fix_time = self.get_random_time(fix_time, 'fix')
        self.set_trigger(self.triggers['fix'])
        if isinstance(self.fix, list):
            for t in range(fix_time):
                if t == 2:
                    self.set_trigger(0)
                for el in self.fix:
                    el.draw()
                self.window.flip()
        else:
            for t in range(fix_time):
                if t == 2:
                    self.set_trigger(0)
                self.fix.draw()
                self.window.flip()

    def show_element(self, elem, time):
        '''show given stimulus for given number of frames.'''
        elem_show = True
        is_list = isinstance(elem, list)
        if not is_list and elem not in self.stim:
            elem_show = False
        # draw element
        if elem_show:
            if not is_list:
                elem = [elem]
            self.set_trigger(elem[0])
        for f in range(time):
            if elem_show:
                if f == self.clear_trigger:
                    self.set_trigger(0)
                for el in elem:
                    self.stim[el].draw()
            self.window.flip()

    # TODO: could change getKeys to check only quit-relevant keys
    def check_quit(self, key=None):
        '''Checks whether quit is enabled and relevant quit button has been
        pressed.'''
        if self.quitopt['enable']:
            # check keys
            if key is None:
                key = event.getKeys()

            # no keys pressed
            if key is None or len(key) == 0:
                return

            # convert keys
            if isinstance(key[0], tuple):
                key = [k[0] for k in key]
            if isinstance(key, tuple):
                key, _ = key

            # check quit
            if self.quitopt['button'] in key:
                core.quit()

    def save_data(self):
        full_path = os.path.join('data', self.subject['id'])
        self.df.to_csv(full_path + '.csv')
        self.df.to_excel(full_path + '.xls')

    def present_break(self):
        text = self.settings['tekst_przerwy']
        text = text.replace('\\n', '\n')
        text = visual.TextStim(self.window, text=text)
        k = False
        while not k:
            text.draw()
            self.window.flip()
            k = event.getKeys()
            self.check_quit(key=k)

    # TODO: that should be modifiable
    def show_keymap(self):
        args = {'units': 'deg', 'height':self.settings['text_size']}
        show_map = {k: bool_to_pl(v)
            for k, v in six.iteritems(self.resp_mapping)}
        text = u'Odpowiadasz klawiszami:\nf: {}\nj: {}'.format(
            show_map['f'], show_map['j'])
        stim = visual.TextStim(self.window, text=text, **args)
        stim.draw()
        self.window.flip()
        k = event.waitKeys()
        self.check_quit(key=k)

    # TODO: that should be modifiable
    def get_subject_id(self):
        myDlg = gui.Dlg(title="Subject Info", size = (800,600))
        myDlg.addText('Informacje o osobie badanej')
        myDlg.addField('ID:')
        myDlg.addField('wiek:', 30)
        myDlg.addField(u'płeć:', choices=[u'kobieta', u'mężczyzna'])
        myDlg.show()  # show dialog and wait for OK or Cancel

        if myDlg.OK:  # Ok was pressed
            self.subject['id'] = myDlg.data[0]
            self.subject['age'] = myDlg.data[1]
            self.subject['sex'] = myDlg.data[2]
        else:
            core.quit()

    # TODO: could be modified to use psychopy
    def set_up_ports(self):
        if self.send_triggers:
            try:
                from ctypes import windll
                windll.inpout32.Out32(self.port_adress, 111)
                core.wait(0.1)
                windll.inpout32.Out32(self.port_adress, 0)
                self.inpout32 = windll.inpout32
            except:
                warnings.warn('Could not send test trigger. :(')
                self.send_triggers = False

    # send trigger could be lower-level
    # set trigger - higher level
    def send_trigger(self, code):
        self.inpout32.Out32(self.port_address, code)


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
def isnull(x):
    if x is None:
        return True
    elif isinstance(x, list):
        return len(x) == 0
    else:
        return False


# instructions
# ------------
# TODO:
# - [ ] this only does functions and images, the original could handle
#       yaml files too.
# - [ ] add option to skip function with relevant keys
class Instructions:
    def __init__(self, win, instrfiles):
        self.win = win
        self.nextpage   = 0
        self.navigation = {'left': 'prev', 'right': 'next',
            'space': 'next'}

        # get instructions from file:
        self.imagefiles = instrfiles
        self.images = []
        self.generate_images()
        self.stop_at_page = len(self.images)

    def generate_images(self):
        self.images = []
        for imfl in self.imagefiles:
            if not isinstance(imfl, types.FunctionType):
                self.images.append(visual.ImageStim(self.win,
                    image=imfl, size=[1169, 826], units='pix',
                    interpolate=True))
            else:
                self.images.append(imfl)

    def present(self, start=None, stop=None):
        if not isinstance(start, int):
            start = self.nextpage
        if not isinstance(stop, int):
            stop = len(self.images)

        # show pages:
        self.nextpage = start
        while self.nextpage < stop:
            # create page elements
            action = self.show_page()

            # go next/prev according to the response
            if action == 'next':
                self.nextpage += 1
            else:
                self.nextpage = max(0, self.nextpage - 1)

    def show_page(self, page_num=None):
        if not isinstance(page_num, int):
            page_num = self.nextpage

        img = self.images[page_num]
        if not isinstance(img, types.FunctionType):
            img.draw()
            self.win.flip()

            # wait for response
            k = event.waitKeys(keyList=self.navigation.keys())[0]
            return self.navigation[k]
        else:
            img()
            return 'next'

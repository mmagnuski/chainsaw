import os, yaml, random
import os.path as op

import numpy as np
import pandas as pd

from psychopy import visual, event, core, gui

# experiment-specific libraries:
from .instructions import Instructions
from .io_utils import (check_quit, set_trigger, set_up_triggers,
                       set_up_response_box, save_beh_data, save_trigger_log,
                       waitKeys, getKeys)


class Experiment(object):
    def __init__(self, base_dir):
        self.window = None
        self.frame_time = None
        self.trials = None
        self.beh = None

        # row indices of last save - used to save only the new rows
        # `self.current_idx` is used to track which trial should be shown next
        # (the next one is current_idx + 1, which evaluates to 0 for first
        #  trial)
        # document how current_idx and current_trial (and current_loc) are used!
        self.last_beh_save = 0
        self.last_log_save = 0
        self.current_idx = -1
        self.current_trial = 0

        self.base_dir = base_dir
        self.data_dir = base_dir / 'data'

        # TODO: move this to save time?
        # if data dir does not exist -> create
        if not self.data_dir.exists():
            os.mkdir(self.data_dir)

        # TODO: maybe add support for img_dir, but it is not necessary now
        # self.image_dir = base_dir / 'img'

        # load settings
        config_file = base_dir / 'settings.yaml'
        read_settings(self, config_file)

        # setup responses
        self.set_responses()

        # create two clocks, the `self.clock` is used to track time elasped
        # from presentation of experimental stimuli while the `self.exp_clock`
        # is only used to measure global experiment time (time that passed
        # from experiment start).
        self.clock = core.Clock()
        self.exp_clock = core.Clock()

        # port stuff
        # ----------
        # set up trigger log and trigger device
        device = (self.settings['trigger_device']
                  if 'trigger_device' in self.settings else None)
        self.trigger_log = {'time': list(), 'trigger': list(), 'trial': list()}
        self.trigger_device, self.send_trigger = set_up_triggers(
            self.send_triggers, device=device, xid_devices=self.devices)

    def create_stimuli(self, window):
        '''Create stimuli used in the experiment. You need to override this
        method in your own experiment class (inheriting from Experiment).'''
        pass

    def reset_beh(self):
        '''Reset internal trial counters and clean trigger log.
        
        Also copies trials dataframe as self.beh, which is used for behavioral
        data storage and saving. Should be used whenever self.trials is replaced
        with another dataframe.
        ''' 
        self.last_beh_save = 0
        self.last_log_save = 0
        self.current_idx = -1
        self.current_trial = 0
        # self.current_loc?
        self.beh = self.trials.copy()
        self.trigger_log = {'time': list(), 'trigger': list(), 'trial': list()}

    # TODO - if more than two times in list - draw one of the elements
    #        so one value -> fixed time; two values -> range; more than two
    #        values -> list of possible times
    # TODO: add some convert time function that turns seconds to frames?
    def get_time(self, stim):
        '''Get time of specific stimulus/event from the config.

        If the config specifies a signle value - this value, specified in
        frames is drawn. If the time in config is a two-element list,
        a random value from that interval is drawn.

        Parameters
        ----------
        stim : str
            Name of the stimulus/event - just like in the config file.

        Returns
        -------
        time : int
            Time in frames.
        '''
        time = self.times[stim]

        # if time is a two-element list - draw random int from range
        if isinstance(time, list) and len(time) == 2:
            time = random.randint(*time)
        return time

    def check_quit(self, key=None):
        '''Exit procedure if quit key was pressed.

        Checks whether quit key, as specified in settings.yaml was pressed.
        Quits procedure if it was pressed.

        Parameters
        ----------
        key : str | list of str
            Optional list of pressed keys - if the keyboard buffer was already
            checked.
        '''
        check_quit(self, key=key)

    def set_window(self, window, frame_time=None, translate_times=None):
        # set window, hide mouse
        self.window = window
        window.mouseVisible = False

        # "please wait" info
        lang = self.settings['language']
        info_text = 'Please wait...' if lang == 'eng' else 'Proszę czekać...'
        wait_text = visual.TextStim(window, text=info_text, height=0.075,
                                    units='height')
        wait_text.autoDraw = True
        window.flip()

        # check screen refresh rate
        if self.frame_time is None:
            if frame_time is None:
                frame_time = get_frame_time(window)

            # update stimuli times
            if translate_times is None:
                translate_times = ['times']

            for field in translate_times:
                tms = seconds_to_frames(self.settings[field], frame_time)
                setattr(self, field, tms)
            self.frame_time = frame_time

        # turn off autodraw
        wait_text.autoDraw = False

    def set_responses(self):
        # check if Cedrus response box is available, else keyboard is used
        self.response_device, self.devices = set_up_response_box()
        if (self.response_device is None
            and self.settings['error_when_no_response_box']):
            raise RuntimeError('Could not find Cedrus response box.')

        # pick key mappings depending on available device
        if self.response_device is None:
            self.resp_keys = self.settings['resp_keys']
        else:
            # cedrus response box keys
            self.resp_keys = self.settings['resp_keys_box']

        self.resp_names = self.settings['resp_names']
        self.resp_mapping = {key: name for name, key in
                             zip(self.resp_names, self.resp_keys)}

        # set triggers to keys, not descriptions:
        for idx, key in enumerate(self.resp_keys):
            descr = self.resp_names[idx]
            trig = self.triggers.pop(descr)
            self.triggers[key] = trig

        # add quit button to responses
        if self.quitopt['enable']:
            quit_key = self.quitopt['button']
            self.resp_keys.append(quit_key)
            self.resp_names.append('quit')
            self.resp_mapping[quit_key] = 'quit'

    # DISPLAY
    # -------
    # TODO: doesn't make sense to present break after last trial...
    # TODO: 
    # to break from a loop when in subfunction:
    # TODO: change the tests for loop break into one try-except
    # see: https://stackoverflow.com/questions/16073396/breaking-while-loop-with-function
    def show_all_trials(self, feedback=False, stop_at_corr=None,
                        n_consecutive=None, min_trials=None,
                        subject_postfix='', staircase=None,
                        staircase_param=None, break_args=dict(),
                        post_tri_fun=None, **args):
        """Present all trials in the experiment.

        Requires the experiment to have:
        * ``.trials`` attribute with DataFrame specifying consecutive trials to
          present.
        * ``.show_trial()`` method that takes one row from the trials
          dataframe and optional ``feedback`` argument.

        If you want a break to be shown every n trials the settings files
        needs to have:
        * ``break_every_n_trials`` informing how often a break is shown
          (every n trials).

        If ``stop_at_corr`` is used then there are additional requirements:
        * the experiment object needs to have a ``.beh`` attribute with
          a dataframe of behavioral responses.
        * that dataframe needs to have a ``trial``

        Parameters
        ----------
        feedback : bool
            Whether to show feedback (color circle) after the response.
        stop_at_corr : float | None
            If not ``None`` - stop trials presentation after some correctness
            has been attained.
        n_consecutive : int | None
            If not ``None`` and ``stop_at_corr`` is not None: how many trials
            the correctness has to be above the ``stop_at_corr`` threshold to
            finish presentation. Useful for training.
        min_trials : int | None
            Additional constraint if ``stop_at_corr`` is not None: how many
            trials the participant has to complete to allow for correctness
            based training termination.
        subject_postfix : str
            Postfix to add to the subject identifier when saving the data to
            disk. Useful for different experiment parts for example for
            training: ``subject_postfix='_train'``. Defaults to ``''`` (no
            postfix).
        staircase : psychopy Staircase | None
            Staircase to use to fit intensity of the independent variable of
            interest. This can be any object with ``.next()`` method
            (returning stimulus intensity for the next trial) and
            ``.addResponse`` method that takes correctness of the behavioral
            response as input. If you are using ``staircase`` argument, you
            need to also set the ``staircase_param`` (see below).
        staircase_param : str | None
            Column name in the ``.trials`` and ``.beh`` DataFrame of the
            experiment to change based on values returned by the staircase.
            The staircase stimulus intensity values are passed to
            ``.show_trial()`` through the ``.trials`` dataframe.
        break_args : dict
            Additional arguments passed to ``.present_break()`` method.
            See the docs of ``.present_break()`` for more information.
        post_tri_fun : function
            Function evaluated after the trial is finished. Has to accept the
            Experiment object as the input argument.
        """
        # TODO: perform error checks at the beginning
        if staircase is not None and staircase_param is None:
            raise ValueError('If you pass a staircase object to '
                             '`run_all_trials`, you have to also define '
                             'the `staircase_param` argument.')

        # set up variables for correctness checks
        disp_corr = None
        trials_without_break = 0
        if stop_at_corr is not None:
            n_above = 0
            min_trials = 0 if min_trials is None else min_trials
            n_consecutive = 1 if n_consecutive is None else n_consecutive

        start_trial_idx = self.current_idx + 1
        n_trials = self.trials.shape[0]
        elasped_trials = 0

        # show consecutive trials
        for t_idx in range(start_trial_idx, n_trials):
            self.current_idx = t_idx
            self.current_loc = self.trials.index[t_idx]
            self.current_trial = self.trials.iloc[t_idx, :].trial

            # get data from staircase
            if_continue = handle_staircase(self, staircase, staircase_param)
            if not if_continue:
                break

            # present trial
            trial_info = self.trials.loc[self.current_loc, :]
            self.show_trial(trial_info, feedback=feedback, **args)
            elasped_trials += 1

            # inform the staircase about the outcome
            if staircase is not None:
                ifcorr = int(self.beh.loc[self.current_loc, 'ifcorrect'])
                staircase.addResponse(ifcorr)

            # save data after each trial
            save_beh_data(self, postfix=subject_postfix)
            save_trigger_log(self, postfix=subject_postfix)

            # post trial function
            if post_tri_fun is not None:
                post_tri_fun(self)

            # calculate correctness if needed
            if stop_at_corr is not None:
                n_above, disp_corr = _check_correctness(
                    self, n_above, stop_at_corr)
                if n_above >= n_consecutive and elasped_trials >= min_trials:
                    break

            # whether to show a break
            trials_without_break = _check_break(
                self, trials_without_break, corr=disp_corr,
                **break_args)

    def show_trial(self, trial, feedback=False):
        '''Present a single trial.

        You need to overwrite this method in you Experiment subclass.
        '''
        pass

    def present_break(self, img=None, text=None, corr=None, corr_pos=None):
        '''Start a break that is controlled by the subject.

        Parameters
        ----------
        img : psychopy.visual.ImageStim | None
            Image that should be presented on the screen during break.
        text : str | None
            Text that should be presented on the screen during break.
        corr : tuple | None
            If not ``None`` then has to be tuple of ``(n_trials, n_correct)``
            format. The correctness will be displayed in the lower section
            of the screen.
        corr_pos : tuple | None
            Position of the correctness text (in relevant window units).
        '''
        # prepare break trigger
        if 'break' in self.triggers:
            set_trigger(self, 'break')

        # show image
        if img is not None:
            img.draw()

        # additional text
        if isinstance(text, str):
            # TODO: make text positioning smarter?
            y_pos = -2.5 if img is not None else 0
            text = visual.TextStim(self.window, text=text, pos=(0, y_pos),
                                   color=(-1, -1, -1))
            text.wrapWidth = 30
            text.draw()
        elif isinstance(text, visual.TextStim):
            text.draw()

        if corr is not None:
            lang = 'pl'
            if 'language' in self.settings:
                lang = self.settings['language']

            if lang == 'pl':
                template = '{} / {} poprawnych wyborów ({:.1f}%)'
            elif lang == 'eng':
                template = '{} / {} correct choices ({:.1f}%)'

            if corr_pos is None:
                corr_pos = (0, -5)

            correctness = corr[1] / corr[0] * 100
            text = template.format(corr[1], corr[0], correctness)
            text = visual.TextStim(self.window, text=text, pos=corr_pos,
                                   color=(-1, -1, -1))
            text.wrapWidth = 30
            text.draw()

        self.window.flip()
        k = waitKeys(self.response_device)
        self.check_quit(key=k)

        if 'after_break' in self.times:
            self.show_element('', self.get_time('after_break'))
        elif 'after_response' in self.times:
            self.show_element('', self.get_time('after_response'))

    # TODO - throw warning when elem is a str of len > 0 and is not present in
    #        self.stim dictionary.
    def show_element(self, elem, time=None, trigger=None, reset_clock=False,
                     await_response=False, trigger_off_time=None):
        '''Show stimuli for given time (in frames).

        Parameters
        ----------
        elem : str | list of str | psychopy object | list of psychopy objects
            Elements to simultaneously present. If the element is a string or
            list of strings than the strings are interpreted as referring to
            ``Experiment.stim`` dictionary.
        time : int | np.inf | None
            Number of frames to show the stimuli for. If np.inf then the time
            is indefinite - until subject response (only when `await_response`
            is True). If ``None`` the time is drawn from the settings.
        trigger : int | str | bool | None
            Trigger value to show or string used to check the trigger value in
            the experiment settings. If ``False`` the trigger is not sent even
            if there is a stimulus-trigger mapping in the settings file.
        reset_clock : bool | psychopy.core.Clock
            Stimulus timing clock that should be reset at stimulus presentation
            at refresh time.
        await_response : bool
            Whether to gather responses when showing stimuli and stop
            presentation once response is made.
        trigger_off_time : int | None
            Time in frames after which the trigger will be turned off.
        '''
        needs_drawing = True
        is_list = isinstance(elem, list)
        if not is_list and elem not in self.stim:
            needs_drawing = False
        if not is_list:
            elem = [elem]

        # prepare clock reset (psychopy or Cedurs response box)
        if isinstance(reset_clock, bool):
            if reset_clock:
                # if Cedrus response box, then pass the response box to reset
                clock = (self.clock if self.response_device is None
                         else self.response_device)
            else:
                clock = False
        else:
            clock = reset_clock

        # set trigger
        if (trigger is not None or elem[0] in self.triggers) and not trigger:
            trigger = trigger if trigger is not None else elem[0]
            clock_to_reset = None if clock == False else clock
            set_trigger(self, trigger, clock=clock_to_reset)

        n_frames = time
        if time is None:
            n_frames = self.get_time(elem[0])

        if n_frames == np.inf and not await_response:
            raise RuntimeError('If `time` is indefinite (`np.inf`) then '
                               '`await_response` should be True.')

        if trigger_off_time is not None and trigger_off_time >= time:
            # CONSIDER - show warning, error?
            # trigger_off_time = min(time - )
            trigger_off_time = None

        # frames loop
        # -----------
        frame_idx = 0
        while frame_idx < n_frames:
            # for LPT devices - reset trigger after a number of frames
            if trigger_off_time is not None:
                if frame_idx == trigger_off_time:
                    set_trigger(self, 0)

            # draw elements and flip the window
            if needs_drawing:
                for el in elem:
                    if isinstance(el, str):
                        self.stim[el].draw()
                    else:
                        el.draw()
            self.window.flip()

            # check for responses if await_response
            if await_response:
                out = getKeys(
                    self.response_device, keyList=self.resp_keys,
                    timeStamped=clock)
                if not (isinstance(out, list) and len(out) == 0):
                    return out
            
            # move to the next frame
            frame_idx += 1

        if await_response:
            return None, np.nan

    # TODO: consider adding session field (saved in filename)
    def get_subject_info(self, window_size=(800, 600), age=True, gender=True,
                         additional=None):
        '''Open gui to gather information about the subject.'''
        randval = np.random.randint(1000)
        subj_initial = f'test_{randval:03d}'

        subj_fields = ['id']
        exp_fields = list()
        myDlg = gui.Dlg(title="Subject Info", size=window_size)
        myDlg.addText('Participatn information')
        myDlg.addField('ID:', initial=subj_initial)

        if age:
            subj_fields.append('age')
            myDlg.addField('age:')

        if gender:
            choices = (['female', 'male'] if isinstance(gender, bool)
                       else gender)
            subj_fields.append('gender')
            myDlg.addField('gender:', choices=choices)

        if additional is None:
            additional = {'skip training': False}
        elif isinstance(additional, bool) and not additional:
            additional = {}

        if additional:
            myDlg.addText('Experiment setup')
            for fld, init in additional.items():
                exp_fields.append(fld)
                myDlg.addField(fld, initial=init)

        myDlg.show()  # show dialog and wait for OK or Cancel

        subject = dict()
        if myDlg.OK:  # Ok was pressed
            for idx, fld in enumerate(subj_fields):
                subject[fld] = myDlg.data[idx]
            self.subject = subject

            for idx, fld in enumerate(exp_fields, start=idx + 1):
                self.settings[fld] = myDlg.data[idx]
        else:
            core.quit()


def _check_break(exp, trials_without_break, **args):
    '''Check whether to show the break.'''
    if 'break_every_n_trials' in exp.settings:
        trials_without_break += 1
        brk_evr = exp.settings['break_every_n_trials']
        if_show_break = (brk_evr > 0 and trials_without_break >= brk_evr)
        if if_show_break:
            trials_without_break = 0
            exp.present_break(**args)
    return trials_without_break


# TODO: allow for a start trial;
# TODO: allow for a different correctness attribute than ``.ifcorrect``?
def _check_correctness(exp, n_above, stop_at_corr):
    corr = exp.beh.query('trial <= {}'.format(exp.current_trial)).ifcorrect
    n_resp, n_corr = corr.shape[0], (corr == True).sum()
    disp_corr = (n_resp, n_corr)

    # check if correctness conditions are fullfilled
    correctness = n_corr / n_resp
    n_above = n_above + 1 if correctness >= stop_at_corr else 0
    return n_above, disp_corr


# time
# ----
def get_frame_time(win, frames=25):
    frame_rate = win.getActualFrameRate(nIdentical=frames)
    if frame_rate is None:
        # try one more time
        frame_rate = win.getActualFrameRate(nIdentical=frames)
    return 1.0 / frame_rate


def seconds_to_frames(time_in_seconds, frame_time):
    assert isinstance(time_in_seconds, dict)
    time_in_frames = dict()
    toframes = lambda x: int(round(x / frame_time))
    for key, val in time_in_seconds.items():
        if isinstance(val, list):
            time_in_frames[key] = list(map(toframes, val))
        else:
            time_in_frames[key] = toframes(val)
    return time_in_frames


def read_settings(exp, config_file):
    with open(config_file, 'r') as f:
        exp.settings = yaml.load(f)

    exp.send_triggers = exp.settings['send_triggers']
    exp.triggers = exp.settings['triggers'].copy()

    if 'times' in exp.settings:
        exp.times = exp.settings['times']

    # key mappings
    exp.quitopt = exp.settings['quit']


# TODO: make universal
def prepare_instructions(exp, subdir=None):
    '''Find instruction images specific to participants gender.'''
    # check language and gender:
    if 'language' in self.settings:
        lang = self.settings['language']
    else:
        lang = 'eng'

    resp_subdir = 'keyboard' if exp.response_device is None else 'response_box'
    instr_dir = exp.base_dir / 'instr' / lang / resp_subdir
    if subdir is not None:
        instr_dir = instr_dir / subdir
    all_files = os.listdir(instr_dir)

    def good_img(fname, hasnot=None):
        isgood = 'Slajd' in fname or 'Slide' in fname
        isgood = isgood and fname.lower().endswith('.png')

        if hasnot is not None:
            isgood = isgood and hasnot not in fname
        return isgood

    if lang == 'pl':
        isfem = exp.subject['gender'] == 'kobieta'
        hasnot = 'mal' if isfem else 'fem'
    else:
        hasnot = None

    instr = [op.join(instr_dir, fname) for fname in instr
             if good_img(fname, hasnot=hasnot)]
    return instr


def prepare_navigation(exp):
    '''
    Prepare navigation for instructions.

    Left and right keys are mapped to previous and next instructions actions.
    '''
    navig = dict()
    for key, direction in zip(['left', 'right'], ['prev', 'next']):
        navig[exp.resp_inv_mapping[key]] = direction
    return navig


# TODO: could only return the value and fill the df's
#       and the error would be caught outside (try-except)
#       or a different, more specific error would be raised here
def handle_staircase(exp, staircase, staircase_param):
    if staircase is not None:
        try:
            value = staircase.next()
        except StopIteration:  # we got a StopIteration error
            return False
        exp.trials.loc[exp.current_loc, staircase_param] = value
        exp.beh.loc[exp.current_loc, staircase_param] = value
    return True


def generate_intensity_steps_from_questplus_weibull(staircase, corr=None):
    '''Create instensity steps from finished quest plus object.

    Requires ``questplus`` package.

    Parameters
    ----------
    staircase : psychopy.data.QuestPlusHandler
        Psychopy quest plus object to use.
    corr : list-like | None
        The returned stimulus intensity values will correspond to these
        correctness (hit rate) steps in the weibull model fit by the
        quest plus procedure.
    scale : str | None
        Can be: ``'linear'``, FIX...

    Returns
    -------
    intensity : numpy.ndarray
        Numpy vector with instensity values corresponding to the required
        correctness steps.
    '''
    from questplus.psychometric_function import weibull

    corr = [0.55, 0.65, 0.75, 0.85, 0.95] if corr is None else corr

    params = staircase.paramEstimate
    keys = ['threshold', 'slope', 'lapseRate']
    thresh, slope, lapse = [params[key] for key in keys]

    intensity_domain = np.linspace(0.000001, 1, num=10_000)
    prop_corr = weibull(intensity=intensity_domain, threshold=thresh,
                        slope=slope, lower_asymptote=0.5, lapse_rate=lapse,
                        scale='linear')
    prop_corr = np.squeeze(prop_corr.values)

    idxs = [np.abs(prop_corr - x).argmin() for x in corr]
    intensity = intensity_domain[idxs]
    return intensity

from numbers import Integral
from pathlib import Path
import yaml

import numpy as np
import pandas as pd

from psychopy import visual, core, event
from psychopy.clock import Clock
from psychopy.hardware.keyboard import KeyPress


# TODO - clean up and test LPT device mode
def set_up_triggers(send_triggers, device='lpt', xid_devices=None,
                    port_address=None):
    '''Prepare procedure for sending triggers.

    Find Cedrus C-POD device and send a test trigger. Requires the pyxid2
    library to be installed and working.

    Parameters
    ----------
    send_triggers : bool
        Whether to send triggers. If ``False`` only function for logging
        triggers to a text file is returned. Otherwise, if ``True`` a function
        that sends triggers through c-pod (and also logs the triggers to a
        file) is returned.
    device : str
        The device to use to send triggers. Can be:
        * ``'lpt'`` - to use LPT port
        * ``'cpod'`` - to use Cedrus CPOD
    xid_devices : list
        Relevant for CPOD. If list of xid devices has been obtained earlier
        (when setting up response box for example) - it can be passed through
        this argument. This option is mostly useful for avoiding a rare bug
        when trying to obtain the list of xid devices two times results in an
        error the second time.
    port_address : str
        Relevant for LPT. String containing the address of the LPT port.

    Returns
    -------
    device : c-pod device object
        Cedrus c-pod device interface. If ``send_triggers`` is ``False`` then
        ``device`` is ``None``.
    trigger_fun : function
        Function used to send triggers. Uses experiment object and trigger
        value as inputs.
    '''
    if not send_triggers:
        return None, register_trigger

    if device == 'cpod':
        import pyxid2

        # szukamy c-pod'a w liście urządzeń xid
        if xid_devices is None:
            xid_devices = pyxid2.get_xid_devices()
        has_cedrus_cpod = ["Cedrus C-POD" in str(dev) for dev in xid_devices]

        if not any(has_cedrus_cpod):
            raise RuntimeError('Could not find the Cedrus c-pod device!')

        cpod_idx = np.where(has_cedrus_cpod)[0][0]
        device = xid_devices[cpod_idx]

        # we set pulse duration to be 30 ms by default
        device.set_pulse_duration(30)
        device.activate_line(bitmask=255)
        return device, send_trigger_cpod
    elif device == 'lpt':
        assert port_address, 'You need to specify port_adress to use LPT port.'

        try:
            # psychopy interface for LPT port
            from psychopy import parallel
            port = parallel.ParallelPort(address=port_address)

            # test port
            port.setData(4)
            core.wait(0.05)
            assert port.getData() == 4
            port.setData(0)
            return port, send_trigger_lpt
        except:
            try:
                # older way using inpout32 dll (requires installation)
                from ctypes import windll
                windll.inpout32.Out32(self.port_adress, 111)
                core.wait(0.1)
                windll.inpout32.Out32(self.port_adress, 0)
                return windll.inpout32,
            except:
                # add info about what was tried
                raise RuntimeError('Could not send triggers via LPT port.')


# send trigger
def send_trigger_cpod(exp, code, clock=None):
    '''Send trigger via c-pod and register trigger time to log.'''
    exp.trigger_device.activate_line(bitmask=code)
    register_trigger(exp, code, clock=clock)


def send_trigger_lpt_inpout(exp, code, clock=None):
    '''Send trigger via LPT port.

    Uses inpout32 library and register trigger time to log.'''
    self.inpout32.Out32(self.port_address, code)
    register_trigger(exp, code, clock=clock)


def register_trigger(exp, code, clock=None):
    '''Add trigger time and value to log.'''
    reset_clock(clock)
    time = exp.exp_clock.getTime()
    exp.trigger_log['trigger'].append(code)
    exp.trigger_log['time'].append(time)
    exp.trigger_log['trial'].append(exp.current_trial)


def reset_clock(clock):
    if clock is not None:
        if isinstance(clock, Clock):
            clock.reset()
        elif isinstance(clock, CedrusResponseBox):
            clock.device.reset_rt_timer()
        else:
            # Cedrus response box
            clock.reset_rt_timer()


def set_trigger(exp, event, clock=None):
    '''Prepare trigger to be sent to be activated during next window flip.'''
    if isinstance(event, Integral):
        exp.window.callOnFlip(exp.send_trigger, exp, event, clock=clock)
    elif event in exp.triggers:
        trig = exp.triggers[event]
        exp.window.callOnFlip(exp.send_trigger, exp, trig, clock=clock)


# responses
# ---------
def set_up_response_box(match="Cedrus RB-", error=True, xid_devices=None):
    '''Set up Cedrus response box.'''
    try:
        import pyxid2
    except:
        return None, None

    # szukamy c-pod'a w liście urządzeń xid
    if xid_devices is None:
        for n in range(15):
            try:
                xid_devices = pyxid2.get_xid_devices()
                buttonBox = xid_devices[0]
                break
            except Exception:
                core.wait(0.15)

    has_cedrus_response_box = [match in str(dev) for dev in xid_devices]
    if any(has_cedrus_response_box):
        device_idx = has_cedrus_response_box.index(True)
        response_box = xid_devices[device_idx]
        assert response_box.is_response_device()
        response_box.reset_base_timer()
        response_box.reset_rt_timer()
        return response_box, xid_devices
    else:
        if error:
            if len(xid_devices) == 0:
                raise RuntimeError('Could not find any Cedrus devices.')
            else:
                msg = ('Could not find any Cedrus device matching {} string.'
                       ' Found the following devices:')
                msg = msg.format(match)
                for dev in xid_devices:
                    msg += '\n* ' + str(dev)
                raise RuntimeError(msg)
        else:
            return None, None


def reformat_keys(keys, timeStamped):
    if timeStamped:
        if len(keys) > 0:
            keys = [(key.name, key.rt) for key in keys]
    else:
        if len(keys) > 0:
            keys = [key.name for key in keys]
    return keys


# TODO: remove the inner Cedrus loop and use the Cedrus object .waitKeys
# TODO: do not use event.waitKeys
def waitKeys(device, keyList=None, timeStamped=False):
    '''Emulates event.waitKeys for Cedrus response box or keyboard.

    Gets only the first key that was pressed (not released).
    '''
    from psychopy.hardware.keyboard import Keyboard

    if device is None:
        keys = event.waitKeys(keyList=keyList, timeStamped=timeStamped)
    elif isinstance(device, Keyboard):
        keys = device.waitKeys(keyList=keyList, waitRelease=False)
        keys = reformat_keys(keys, timeStamped=timeStamped)
    else: # assumes Cedrus response box
        if isinstance(device, CedrusResponseBox):
            device = device.device

        response_ok = False
        while not response_ok:
            while not device.has_response():
                device.poll_for_response()
            response = device.get_next_response()
            # response['key'], response['pressed'], response['time']
            key_ok = True if keyList is None else response['key'] in keyList
            response_ok = response['pressed'] and key_ok
        key, rt = response['key'], response['time'] / 1000
        if timeStamped:
            return (key, rt)
        else:
            return key
    if len(keys) > 0 and isinstance(keys, (list, tuple)):
        keys = keys[0]
    return keys


# TODO: remove the inner Cedrus loop and use the Cedrus object .getKeys
# TODO: do not use event.waitKeys
def getKeys(device, keyList=None, timeStamped=False, only_first=True):
    '''Emulates event.waitKeys for Cedrus response box or keyboard.

    Get all the pressed keys waiting in the buffer.
    '''
    from psychopy.hardware.keyboard import Keyboard

    if device is None:
        keys = event.getKeys(keyList=keyList, timeStamped=timeStamped)
    elif isinstance(device, Keyboard):
        keys = device.getKeys(keyList=keyList, waitRelease=False)
        keys = reformat_keys(keys, timeStamped=timeStamped)

    else:
        if isinstance(device, CedrusResponseBox):
            device = device.device
        keys = list()
        device.poll_for_response()
        while len(device.response_queue):
            key_event = device.get_next_response()
            if key_event['pressed'] and (keyList is None
                                         or key_event['key'] in keyList):
                key, rt = key_event['key'], key_event['time'] / 1000
                if timeStamped:
                    keys.append((key, rt))
                else:
                    keys.append(key)
            device.poll_for_response()
        device.clear_response_queue()

    if len(keys) > 0 and only_first:
        keys = keys[0]
    return keys


# TODO - check / clean
def check_quit(exp, key=None):
    '''Check if quit key has been pressed.'''
    if exp.quitopt['enable']:
        if key is None or exp.response_device is not None:
            # quit button never enabled on response pad - to avoid errors
            key = event.getKeys(keyList=[exp.quitopt['button']])
        if key is None or len(key) == 0:
            return
        if isinstance(key[0], tuple):
            key = [k[0] for k in key]
        if isinstance(key, tuple):
            key, _ = key
        if exp.quitopt['button'] in key or 'quit' in key:
            core.quit()


def get_device_clock(exp):
    from psychopy.hardware.keyboard import Keyboard

    # if Cedrus response box, then pass the response box to reset
    if exp.response_device is None:
        clock = exp.clock
    elif isinstance(exp.response_device, Keyboard):
        clock = exp.response_device.clock
    else:
        # Cedrus response box
        clock = exp.response_device
    return clock


# TODO: check if universal
def handle_responses(exp, correct_resp=None, key=None, rt=None, row=None,
                     send_trigger=True, prefix=None):
    '''Wait for the response given by subject and check its correctness.

    This function uses ``.current_idx`` attribute of the Experiment to locate
    the ``.beh`` dataframe row to which responses should be saved.

    Parameters
    ----------
    exp : Experiment
        Experiment object - response keys, timings and experiment clock are
        taken from this object.
    correct_resp : str
        Correct response for this question.
    rt : float | None
        Response time. If ``None``, then ``waitKeys`` is used to get reaction
        time.
    row : int | None
        Row index in ``.beh`` dataframe. If ``None``, then ``exp.current_idx``
        is used.
    send_trigger : bool
        Whether to send response trigger.
    prefix : str | None
        Prefix added to the column name. If ``None``, then no prefix is
        added.

    Returns
    -------
    resp : str
        Response key.
    ifcorrect : bool
        Whether the response is correct.
    RT : float
        Reaction time in seconds.
    '''
    if key is None and rt is None:
        key, rt = waitKeys(exp.response_device, keyList=exp.resp_keys,
                           timeStamped=exp.clock)

    no_response = key is None and np.isnan(rt)
    if send_trigger and not no_response:
        exp.send_trigger(exp, exp.triggers[key])
    exp.check_quit(key=key)

    if no_response:
        response, ifcorrect = None, False
    else:
        # check if answer is correct:
        correct_resp = (correct_resp if correct_resp is not None
                        else exp.trials.iloc[exp.current_idx, :].correct_resp)
        response = exp.resp_mapping[key]
        ifcorrect = response == correct_resp if key is not None else False

    prefix = '' if prefix is None else prefix
    row = exp.beh.index[exp.current_idx] if row is None else row
    exp.beh.loc[row, prefix + 'key'] = key
    exp.beh.loc[row, prefix + 'resp'] = response
    exp.beh.loc[row, prefix + 'ifcorrect'] = ifcorrect
    exp.beh.loc[row, prefix + 'RT'] = rt
    return key, ifcorrect, rt


def clear_buffer(device=None):
    '''Clear buffer of the keyboard or the Cedurs response box.'''
    from psychopy.hardware.keyboard import Keyboard

    if device is None:
        event.getKeys()
    elif isinstance(device, Keyboard):
        device.getKeys()
    elif isinstance(device, CedrusResponseBox):
        device.getKeys()  # only once?
    else:
        # taken from psychopy builder script:
        device.poll_for_response()
        while len(device.response_queue):
            device.clear_response_queue()
            device.poll_for_response()  # often there are more resps waiting!


# read settings
# -------------
def read_settings(config):
    '''Read experiment settings from .yaml file or python module.

    Parameters
    ----------
    config : str, module
        Name of the .yaml file or python module.

    Returns
    -------
    settings : dict
        Dictionary containing experiment settings.
    '''
    from types import ModuleType, FunctionType
    if isinstance(config, (str, Path)):
        # yaml file
        with open(config_file, 'r') as f:
            settings = yaml.load(f)
    elif isinstance(config, ModuleType):
        # python module
        settings = dict()
        attrs = [atr for atr in dir(config) if not atr.startswith('_')]
        for attr_name in attrs:
            value = getattr(config, attr_name)
            if not isinstance(value, (FunctionType, ModuleType)):
                settings[attr_name] = value
    else:
        raise TypeError('The `config` should be either a filename or'
                        ' python module, got {}.'.format(config))
    return settings


def apply_settings(exp, settings):
    '''Apply settings to the experiment object.'''
    exp.settings = settings
    exp.quitopt = exp.settings['quit']
    exp.send_triggers = exp.settings['send_triggers']
    exp.triggers = exp.settings['triggers'].copy()


# saving data
# -----------
def save_trigger_log(exp, postfix=''):
    '''Write trigger log to a .csv file.

    Triggers are saved to default data directory (``exp.data_dir``).'''
    from_idx = exp.last_log_save
    columns = ['time', 'trial', 'trigger']
    part_save = {key: exp.trigger_log[key][from_idx:] for key in columns}
    df = pd.DataFrame(part_save, columns=columns)
    fname = exp.data_dir / (exp.subject['id'] + postfix + '_trig.log')
    df.to_csv(fname, index=False, mode='a', header=from_idx == 0)
    exp.last_log_save = len(exp.trigger_log[columns[0]])


def save_beh_data(exp, postfix=''):
    '''Save current behavioral data to .csv file in data directory.'''
    fname = exp.data_dir / (exp.subject['id'] + postfix + '.csv')
    save_beh = exp.beh.iloc[exp.last_beh_save:exp.current_idx + 1, :]
    save_beh.to_csv(fname, mode='a', header=exp.current_idx == 0)
    exp.last_beh_save = exp.current_idx + 1


# TODOs:
# - [ ] add docs
# - [ ] add waitKeys
# - [ ] add waitRelease=True
class CedrusResponseBox(object):
    def __init__(self, device):
        self.device = device
        self.pressed = dict()  # keys awaiting release action

    def getKeys(self, keyList=None, waitRelease=False, clear=True):
        if waitRelease:
            raise NotImplementedError('waitRelease=True is not yet supported')
        return get_responses(self, keyList=keyList, clear=clear)

    def waitKeys():
        pass


# FIX: make two lists for pressed - in general and pressed_now
def get_responses(rbox, keyList=None, clear=True):

    device = rbox.device
    device.poll_for_response()
    keys = list()

    if len(device.response_queue) > 0:
        clear_idx = list()
        pressed_now = dict()

        # iterate through responses
        for idx, response in enumerate(device.response_queue):
            if keyList is None or response['key'] in keyList:
                name, rt = response['key'], response['time'] / 1000

                if clear:
                    clear_idx.append(idx)

                if response['pressed']:
                    pressed_now[name] = len(keys)

                    # compose key
                    key = KeyPress(name, tDown=rt)
                    key.name = name
                    key.rt = rt
                    key.duration = None

                    if name not in rbox.pressed:
                        rbox.pressed[name] = key

                    keys.append(key)
                else:
                    # button was released
                    # if there is no matching onset we ignore the key
                    if name in rbox.pressed:
                        key = rbox.pressed.pop(name)
                        key.duration = response['time'] / 1000 - key.rt

                        if name in pressed_now:
                            use_idx = pressed_now.pop(name)

                            # CHECK
                            # maybe not necessary due to in-place operations
                            keys[use_idx] = key
                        else:
                            keys.append(key)

                    elif not clear:
                        clear_idx.append(idx)

        if len(clear_idx) > 0:
            for idx in clear_idx[::-1]:
                device.response_queue.pop(idx)
    return keys


# TODO: integrate with show_break / present_break
def forced_break(window, device, time_min=180, skip_key='x'):

    def time_to_min_sec(time):
        minutes = int(np.floor(time / 60))
        seconds = int(time - minutes * 60)
        return minutes, seconds


    def time_to_text(time):
        minutes, seconds = time_to_min_sec(time)
        text = f'{minutes:02d}:{seconds:02d}'
        return text


    old_text = time_to_text(time_min)
    minutes, _ = time_to_min_sec(time_min)
    main_text = f'You have to take at least a {minutes}-minute break now.'
    txt = visual.TextStim(window, text=old_text, height=0.06, units='height')
    main_txt = visual.TextStim(window, text=main_text, height=0.05,
                               pos=(0, 0.25), units='height')

    pie = visual.Pie(window, radius=0.125, start=360, end=0, lineWidth=0.01,
                     lineColor='limegreen', interpolate=True,
                     fillColor='limegreen', units='height')


    clock = core.Clock()
    time = 0
    while time < time_min:
        # set timer text
        time_left = time_min - time
        new_text = time_to_text(time_left)

        if not new_text == old_text:
            txt.setText(new_text)
            old_text = new_text

        # set pie angle
        angle = 360 * (time / time_min)
        pie.setEnd(angle)

        # draw
        pie.draw()
        txt.draw()
        main_txt.draw()
        window.flip()

        # make sure it is possible to skip the break with keyboard
        keys = getKeys(None, only_first=False)
        if skip_key in keys:
            break

        # check time
        time = clock.getTime()

    main_txt.setText('You can proceed now, if you are ready.\nPress any key to'
                     ' do so.')
    main_txt.draw()
    txt.draw()
    window.flip()
    waitKeys(device)

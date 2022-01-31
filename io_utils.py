from numbers import Integral
from pathlib import Path
import yaml

import numpy as np
import pandas as pd

from psychopy import core, event
from psychopy.clock import Clock


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
        assert port_adress, 'You need to specify port_adress to use LPT port.'

        try:
            # psychopy interface for LPT port
            from psychopy import parallel
            port = parallel.ParallelPort(address=port_adress)

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


# - [ ] consider timing Cedrus responses with psychopy clock
#       if timeStamped is provided
def waitKeys(device, keyList=None, timeStamped=False):
    '''Emulates event.waitKeys for Cedrus response box or keyboard.

    Gets only the first key that was pressed (not released).
    '''
    if device is None:
        return event.waitKeys(keyList=keyList, timeStamped=timeStamped)[0]
    else: # assumes Cedrus response box
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


# TODO - make sure timeStamped works for Cedrus and keyboard
def getKeys(device, keyList=None, timeStamped=False, only_first=True):
    '''Emulates event.waitKeys for Cedrus response box or keyboard.

    Get all the pressed keys waiting in the buffer.
    '''
    if device is None:
        keys = event.getKeys(keyList=keyList, timeStamped=timeStamped)
    else:
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
        if exp.quitopt['button'] in key:
            core.quit()


# TODO: check if universal
def handle_responses(exp, correct_resp=None, key=None, rt=None, row=None,
                     send_trigger=True):
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
    if send_trigger:
        exp.send_trigger(exp, exp.triggers[key])
    exp.check_quit(key=key)

    # check if answer is correct:
    correct_resp = (correct_resp if correct_resp is not None
                    else exp.trials.iloc[exp.current_idx, :].correct_resp)
    response = exp.resp_mapping[key]
    ifcorrect = response == correct_resp if key is not None else False

    row = exp.beh.index[exp.current_idx] if row is None else row
    exp.beh.loc[row, 'key'] = key
    exp.beh.loc[row, 'resp'] = response
    exp.beh.loc[row, 'ifcorrect'] = ifcorrect
    exp.beh.loc[row, 'RT'] = rt
    return key, ifcorrect, rt


def clear_buffer(device=None):
    '''Clear buffer of the keyboard or the Cedurs response box.'''
    if device is None:
        event.getKeys()
    else:
        # taken from psychopy builder script:
        device.poll_for_response()
        while len(device.response_queue):
            device.clear_response_queue()
            device.poll_for_response()  # often there are more resps waiting!


# REMOVE - it is defined somewhere else default get_subject_info()
def get_subject_info(exp):
    myDlg = gui.Dlg(title="Subject Info", size=(800,600))
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

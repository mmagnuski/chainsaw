from pathlib import Path
import yaml

import numpy as np


def set_up_triggers(send_triggers, device='lpt', port_adress=None):
    '''Prepare procedure for sending triggers.

    Find Cedrus C-POD device and send a test trigger. Requires the pyxid2
    library to be installed and working.

    Parameters
    ----------
    send_trigger : bool
        Whether to send triggers. If ``False`` only function for logging
        triggers to a text file is returned. Otherwise, if ``True`` a function
        that sends triggers through c-pod (and also logs the triggers to a
        file) is returned.

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
        devices = pyxid2.get_xid_devices()
        has_cedrus_cpod = ["Cedrus C-POD" in str(dev) for dev in devices]

        if not any(has_cedrus_cpod):
            raise RuntimeError('Could not find the Cedrus c-pod device!')

        cpod_idx = np.where(has_cedrus_cpod)[0][0]
        device = devices[cpod_idx]

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
    if clock is not None:
        clock.reset()
    time = exp.exp_clock.getTime()
    exp.trigger_log['trigger'].append(code)
    exp.trigger_log['time'].append(time)
    exp.trigger_log['trial'].append(exp.current_trial)


def set_trigger(exp, event, clock=None):
    '''Prepare trigger to be sent to be activated during next window flip.'''
    if isinstance(event, int):
        exp.window.callOnFlip(exp.send_trigger, exp, event, clock=None)
    elif event in exp.triggers:
        trig = exp.triggers[event]
        exp.window.callOnFlip(exp.send_trigger, exp, trig, clock=None)


def set_up_response_box(match="Cedrus RB-", error=True):
    '''Set up Cedrus response box.'''
    import pyxid2

    # szukamy c-pod'a w liście urządzeń xid
    devices = pyxid2.get_xid_devices()
    has_cedrus_response_box = [match in str(dev) for dev in devices]
    if any(has_cedrus_response_box):
        device_idx = has_cedrus_response_box.index(True)
        response_box = devices[device_idx]
        assert response_box.is_response_device()
        response_box.reset_base_timer()
        response_box.reset_rt_timer()
        return response_box
    else:
        if error:
            if len(devices) == 0:
                raise RuntimeError('Could not find any Cedrus devices.')
            else:
                msg = ('Could not find any Cedrus device matching {} string.'
                       ' Found the following devices:')
                msg = msg.format(match)
                for dev in devices:
                    msg += '\n* ' + str(dev)
                raise RuntimeError(msg)
        else:
            return None


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
        return response['key'], response['time'] / 1000


def getKeys(device, keyList=None):
    '''Get all the pressed keys waiting in the buffer.'''
    if device is None:
        return event.getKeys(keyList=keyList)
    else:
        keys, RTs = list(), list()
        device.poll_for_response()
        while len(device.response_queue):
            key_event = device.get_next_response()
            if key_event['pressed'] and (keyList is None
                                         or key_event['key'] in keyList):
                keys.append(key_event['key'])
                RTs.append(key_event['time'])
            device.poll_for_response()
        device.clear_response_queue()
        if len(keys) == 0:
            keys, RTs = None, np.nan
        return keys, RTs


# default get_subject_info()
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
def save_trigger_log(exp):
    '''Write trigger log to a .csv file.

    Triggers are saved to default data directory (``exp.data_dir``)'''
    df = pd.DataFrame(exp.trigger_log, columns=['time', 'trigger'])
    fname = exp.data_dir / (exp.subject['id'] + '_trig.log')
    df.to_csv(fname, index=False)


def save_beh_data(exp):
    '''Save current behavioral data to .csv file in data directory.'''
    fname = exp.data_dir / (exp.subject['id'] + '.csv')
    exp.beh = exp.beh.infer_objects()
    exp.beh.to_csv(fname)
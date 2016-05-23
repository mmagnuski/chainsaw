import os
import time


def file_path(fl):
    file_path = os.path.join(*(fl.split('\\')[:-1]))
    return file_path.replace(':', ':\\')


def get_subject_id():
    from psychopy import gui
    myDlg = gui.Dlg(title="Subject Info", size = (800,600))
    myDlg.addText('Participant ID')
    myDlg.addField('ID:')
    myDlg.show()  # show dialog and wait for OK or Cancel
    
    if myDlg.OK:  # Ok was pressed
    return myDlg.data[0]
else:
    return None


# triggers
# --------
def test_triggers(settings, signal=111):
    if settings['send_triggers']:
        return False
    try:
        from ctypes import windll
        windll.inpout32.Out32(settings['port_adress'], signal)
        time.sleep(0.1)
        windll.inpout32.Out32(settings['port_adress'], 0)
        return True
    except:
        warnings.warn('Could not send test trigger. :(')
        return False


def send_trigger(settings, code):
    if settings['send_triggers']:
        windll.inpout32.Out32(settings['port_adress'], code)

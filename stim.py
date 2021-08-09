import numpy as np

from psychopy import visual


# stimuli
# -------
def fix(win, height=0.3, width=0.1, shape='circle', color=(0.5, 0.5, 0.5)):
    args = {'fillColor': color, 'lineColor': color,
        'interpolate': True, 'units': 'deg'}
    if shape == 'circle':
        fix_stim = visual.Circle(win, radius=height/2,
            edges=32, **args)
    else:
        h, w = (height/2, width/2)
        vert = np.array([[w, -h], [w, h], [-w, h], [-w, -h]])

        args.update(closeShape=True)
        fix_stim = [visual.ShapeStim(win, vertices=v, **args)
                    for v in [vert, np.fliplr(vert)]]
    return fix_stim


# - [ ] place in chainsaw (this is better than what is in exp_linord)
def show_element(exp, elem, time, trigger=None, clock=None,
                 trigger_off_time=None):
    '''Show stimuli for given time.

    Parameters
    ----------
    elem : str | list of str | list of psychopy objects
        Elements to simultaneously present. If the element is a string or
        list of strings than the strings are interpreted as referring to
        ``LinOrdExperiment.stim`` dictionary.
    time : int
        Number of frames to show the stimuli for.
    trigger : int | str
        Trigger value to show or string used to check the trigger value in
        the experiment settings.
    clock : psychopy.core.Clock
        Stimulus timing clock that should be reset at stimulus presentation
        at refresh time.
    '''
    elem_show = True
    is_list = isinstance(elem, list)
    if not is_list and elem not in exp.stim:
        elem_show = False
    if not is_list and isinstance(elem, str):
        elem = [elem]

    # turn string descriptions of stimuli to psychopy stimuli
    for idx, el in enumerate(elem):
        if isinstance(el, str):
            elem[idx] = exp.stim[el]

    if trigger_off_time >= time:
        # CONSIDER - show warning
        # trigger_off_time = min(time - )
        trigger_off_time = None

    # set trigger
    if elem_show:
        # if no trigger is set
        trigger = trigger if trigger is not None else elem[0]
        set_trigger(exp, trigger, clock=clock)

    for frame in range(time):
        if elem_show:
            if trigger_off_time is not None and frame == trigger_off_time:
                # after specific number of frames the trigger is turned off
                set_trigger(exp, 0)
            for el in elem:
                el.draw()
        exp.window.flip()


# maybe
def show_feedback(self, corr):
    stims = ['feedback_incorrect', 'feedback_correct']
    if any([stim not in self.stim for stim in stims]):
        raise RuntimeError('...')
    corr = int(corr)
    fdb = self.stim[stims[corr]]
    fdb.draw()
    self.window.flip()
    core.wait(0.7) # TODO - this could be a variable


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

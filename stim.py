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

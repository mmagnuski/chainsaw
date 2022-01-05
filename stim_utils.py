import numpy as np
from psychopy import visual


def fix(window, height=0.3, width=0.1, shape='circle', color=(0.5, 0.5, 0.5),
        **args):
    '''Create fixation dot or fixation cross.

    Parameters
    ----------
    window : psychopy.visual.Window
        Window to display the stimulus on.
    height : float
        Height of the fixation. For fixation circle this defines the diameter
        of the fixation; for fixation cross - the arm length.
    width : float
        Used only for fixation cross - defines the arm width.
    shape : str
        Shape of the fixation:
        * ``'circle'`` - fixation circle (default)
        * ``'cross'`` - fixation cross
    color : str | listlike
        Name of the color or RGB list-like. This sets both the fillColor and
        the lineColor.
    '''

    args = {'fillColor': color, 'lineColor': color,
            'interpolate': True, **args}

    if shape == 'circle':
        fix_stim = visual.Circle(window, radius=height/2,
            edges=32, **args)
    else:
        h, w = (height / 2, width / 2)
        vert = np.array([[w, -h], [w, h], [-w, h], [-w, -h]])

        args.update(closeShape=True)
        fix_stim = [visual.ShapeStim(window, vertices=v, **args)
                    for v in [vert, np.fliplr(vert)]]
    return fix_stim


def feedback_circles(window, radius=1.5, units='deg'):
    feedback_colors = (np.array([[0, 147, 68], [190, 30, 45]],
            dtype='float') / 255 - 0.5) * 2
    args = dict(height=radius, units=units)
    circ_corr = fix(window, color=tuple(feedback_colors[0, :]), **args)
    circ_incorr = fix(window, color=tuple(feedback_colors[1, :]), **args)
    return circ_corr, circ_incorr


# colors
# ------

# equiluminant colors (for phase info for example)
r = np.array([0.718, 0.847, 0.527, 0.000, 0.000, 0.316, 0.718])
g = np.array([0.000, 0.057, 0.527, 0.592, 0.559, 0.316, 0.000])
b = np.array([0.718, 0.057, 0.000, 0.000, 0.559, 0.991, 0.718])
rgb = np.stack([r, g, b], axis=1)

# colors - maybe name all equiluminant colors and provide (or use abvailable)
# color converters (for example 0 - 1 normalized to -1 - 1 psychopy norm)
# or rgb255 to psychopy -1 - 1 normalized)
colors_norm = {'pink': [0.718, 0, 0.718], 'blue': [0.316, 0.316, 0.991]}
colors_255 = {'pink': [183, 0, 183], 'blue': [81, 81, 253]}
colors_psychopy = {'pink': [0.436, -1., 0.436],
                   'blue': [-0.368, -0.368, 0.982]}
import numpy as np
import pandas as pd


def repeat_dataframe(df, n_reps):
    '''
    Repeat a dataframe ``n_reps`` times.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to repeat.
    n_reps : int
        Number of times to repeat the dataframe.

    Return
    ------
    df_rep : pandas.DataFrame
        Repeated dataframe (copy of the original dataframe).
    '''

    dfs = list()
    for rep in range(n_reps):
        dfs.append(df)
    df_rep = pd.concat(dfs).reset_index(drop=True)
    return df_rep


def shuffle(vec, block_size=None):
    '''
    Return indices to shuffle an array or dataframe in blocks.

    Parameters
    ----------
    vec : numpy array | pandas DataFrame
        Object to return shuffling indices for.
    block_size : int
        Size of each block that the object shuffling is done within.

    Returns
    -------
    indices : numpy array
        Array of shuffling indices.
    '''
    from numpy import random

    if isinstance(vec, pd.DataFrame):
        indices = np.array(vec.index.copy())
    else:
        indices = np.arange(len(vec))

    if block_size is None:
        block_size = len(indices)

    n_ind = len(indices)
    n_blocks = n_ind // block_size

    # shuffle each pack
    for start_idx in range(0, n_blocks * block_size, block_size):
        slc = slice(start_idx, start_idx + block_size)
        random.shuffle(indices[slc])

    # shuffle remaining unequal pack if present
    if n_ind > (n_blocks * block_size):
        slc = slice(n_blocks * block_size, n_ind)
        random.shuffle(indices[slc])

    return indices


def shuffle_dataframe(df, block_size=None):
    '''
    Shuffle dataframe in blocks.

    Parameters
    ----------
    df : pandas DataFrame
        The dataframe to shuffle.
    block_size : int
        Size of each block that the shuffling is done within.

    Returns
    -------
    df : pandas DataFrame
        The shuffled dataframe.
    '''
    ind = shuffle(df, block_size=block_size)
    df = df.loc[ind, :].reset_index(drop=True)
    return df


def balance_draw(shown, load=4, each_appears=None):
    '''Draw indices balancing their presentation frequency.

    Parameters
    ----------
    shown : list
        List of integers, where each integer informs how many times given index
        has been presented. For example ``[1, 3]`` means that the first index
        has been presented one time and the second index - three times.
        Beware that ``show`` will be modified in-place.
    load : int
        How many indices are shown in one trial. Defaults to 4.
    each_appears : list | None
        If one of the selected indices will be presented more than once you
        can pass this information in this argument. For example setting
        ``each_appears=[1, 2]`` means that the first selected index will be
        presented one time, and the second one - two times.

    Returns
    -------
    selected_idx : list
        List of selected indices.
        ...
    '''
    n_images = len(shown)
    if each_appears is None:
        each_appears = np.ones(load, dtype='int')

    selected_idx = list()
    used_img = np.zeros(n_images, dtype='bool')

    for add in each_appears:
        # select eligible indices
        n_shown = np.asarray(shown.copy())
        n_shown[used_img] = 10_000

        min_shown = n_shown.min()
        indices = np.where(n_shown == min_shown)[0]
        np.random.shuffle(indices)
        sel_idx = indices[0]
        shown[sel_idx] += add
        used_img[sel_idx] = True
        selected_idx.append(sel_idx)
    return selected_idx


def balance_image_position(pos_per_img, max_n=1000):
    '''Draw positions for all images balancing each position per image.

    Parameters
    ----------
    pos_per_img : list
        List of lists, where each of these sub-lists indicates how many times
        given image was shown on n-th position. So ``pos_per_img[1][2]``
        informs how many times second image (index 1) was present on third
        position (index 2) in the sequence.

    Returns
    -------
    pos_to_img : numpy.ndarray
        1d array of image indices. Subsequent elements correspond
        to subsequent positions.
    '''
    n_img = len(pos_per_img)
    load = len(pos_per_img[0])
    pos_to_img = list()

    for pos_idx in range(load):
        # find images least shown on this position
        img_n_shown = [pos_per_img[ix][pos_idx] for ix in range(n_img)]
        for img_idx in pos_to_img:
            img_n_shown[img_idx] = max_n

        # pick least frequent image
        img_idx = balance_draw(img_n_shown, load=1)[0]

        pos_per_img[img_idx][pos_idx] += 1
        pos_to_img.append(img_idx)

    return pos_to_img


def generate_orientations(num, min_ori_diff=15, ignore_cardinal=False,
                          full_circle=True, to_radians=False):
    '''Generate a sequence of orientationswith
    minimum orientation difference higher than specified value.

    Parameters
    ----------
    num : int
        Number of orientations.
    min_ori_diff : int
        Minimal orientation difference.
    ignore_cardinal : bool
        Whether to ignore orientations -/+ 5 degrees from cardinal
        orientations.
    full_circle : bool
        If ``False`` generate orientations between 0 and 179 (half-circle).
    to_radians : bool
        If ``True`` - return orientations in radians, not angular degrees.

    Returns
    -------
    oris : numpy.ndarray
        Array of orientations.
    if_success : bool
        Whether it was possible to generate all orientations while fulfilling
        the minimum orientation difference constraint.
    '''
    if isinstance(ignore_cardinal, bool):
        ignore_cardinal = 5 if ignore_cardinal else 0

    oris = list()
    max_orientation = 360 if full_circle else 180
    if full_circle:
        ori_use = np.ones(360, dtype='bool')
        ori_val = np.arange(360) - 180
    else:
        ori_use = np.ones(180, dtype='bool')
        ori_val = np.arange(180) - 90

    if ignore_cardinal > 0:
        ori_use[:ignore_cardinal] = False

        angles = [90] if not full_circle else [90, 180, 270]
        for angle in angles:
            ori_use[angle - ignore_cardinal:angle + ignore_cardinal + 1] = False
        ori_use[-ignore_cardinal:] = False

    # first one anyway
    while (len(oris) < num):
        good_ori = ori_val[ori_use]
        if len(good_ori) == 0:
            break

        # pick one and add to oris
        chosen_ori = np.random.choice(good_ori)
        oris.append(chosen_ori)

        # remove orientations surrounding the chosen one
        good_distance = np.abs(ori_val - chosen_ori) > min_ori_diff
        good_distance_inv = (np.abs(ori_val - full_circle - chosen_ori)
                             > min_ori_diff)
        ori_use = ori_use & good_distance & good_distance_inv

    if_success = len(oris) == num
    return np.array(oris), if_success
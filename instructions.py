import types
from psychopy import visual
from .io_utils import waitKeys, clear_buffer


class Instructions:
    def __init__(self, window, pages, response_device=None,
                 navigation=None, substitute_text=None,
                 finish_key=None):
        '''Object that allows for sequential instructions presentation.

        Parameters
        ----------
        window : psychopy.visual.Window
            Psychopy window.
        pages : str | list of str
            Name of the text file with instructions or list of instruction
            images (list of filenames). If text file is used, instruction pages
            should be separated with ``'[page]'`` lines (this can include
            page numbering, for example ``'[page02]'``).
        response_device : Cedrus response box device | None
            ``None`` (default) uses keyboard for instructions navigation.
        navigation : dict | None
            Dictionary mapping from keys to actions (``'prev'`` and
            ``'next'``). Defaults to:
            ``{'left': 'prev', 'right': 'next', 'space': 'next'}``.
        substitute_text : dict | None
            Used only when text instructions are used.
        finish_key : str | int | None
            A key that has to be pressed to finish instructions.
        '''
        self.window = window
        self.nextpage = 0
        self.response_device = response_device

        default_navig = {'left': 'prev', 'right': 'next', 'space': 'next'}
        self.navigation = default_navig if navigation is None else navigation
        self.has_finish_key = finish_key is not None
        if self.has_finish_key:
            self.navigation[finish_key] = 'finish'

        # get instructions from file:
        if isinstance(pages, list):
            self.file_type = 'images'
        elif isinstance(pages, str) and pages.endswith('.txt'):
            self.file_type = 'text'
            self.substitute = substitute_text
            if self.substitute is None:
                self.substitute = dict()
                operations = ['prev', 'next']
                for key, val in self.navigation.items():
                    if val in operations and val not in self.substitute:
                        self.substitute[val] = key

        self.files = pages
        self.pages = []

    def generate(self, **args):
        if self.file_type == 'images':
            generate_images(self, **args)
        elif self.file_type == 'text':
            text_pages = read_txt_instructions(self.files, self.substitute)
            generate_texts(self, text_pages, **args)
        self.stop_at_page = len(self.pages)

    def present(self, start=None, stop=None):
        if len(self.pages) == 0:
            self.generate()

        '''Present instructions.'''
        if not isinstance(start, int):
            start = self.nextpage
        if not isinstance(stop, int):
            stop = len(self.pages)

        # show pages:
        self.nextpage = start
        while self.nextpage < stop:
            allow_finish = (self.nextpage == stop - 1) and self.has_finish_key
            action = self.show_page(allow_finish=allow_finish)

            # go next/prev according to the response
            if action in ['next', 'finish']:
                self.nextpage += 1
            elif action == 'prev':
                self.nextpage = max(0, self.nextpage - 1)

    def show_page(self, page_num=None, allow_finish=False):
        if not isinstance(page_num, int):
            page_num = self.nextpage

        img = self.pages[page_num]
        if not isinstance(img, types.FunctionType):
            img.draw()
            self.window.flip()

            # select keys
            allow_keys = list()
            for key, move in self.navigation.items():
                if move in ['next', 'finish']:
                    if allow_finish and move == 'finish':
                        allow_keys.append(key)
                    elif not allow_finish and move == 'next':
                        allow_keys.append(key)
                else:
                    allow_keys.append(key)

            # wait for response
            clear_buffer(self.response_device)
            k = waitKeys(self.response_device,
                         keyList=allow_keys)
            return self.navigation[k]
        else:
            img()
            return 'next'


def read_txt_instructions(file, substitute):

    # read file contents
    with open(file) as f:
        lines = f.readlines()

    # parse the data into pages
    instr_idx = -1
    instructions = list()

    for line in lines:
        if line.startswith('[page'):
            instr_idx += 1
            instructions.append('')
        else:
            instructions[instr_idx] += line

    for idx, instr in enumerate(instructions):
        if '{' in instr and '}' in instr:
            instructions[idx] = instr.format(**substitute)

    return instructions


def generate_texts(instr, texts, **args):
    args['units'] = args.get('units', 'deg')
    args['height'] = args.get('height', 1)
    args['wrapWidth'] = args.get('wrapWidth', 30)

    for text in texts:
        instr.pages.append(visual.TextStim(instr.window, text, **args))


def generate_images(instr, **args):
    '''Generate images used in the experiment.'''
    args['size'] = args.get('size', [1280, 720])
    args['units'] = args.get('units', 'pix')
    args['interpolate'] = args.get('interpolate', True)

    for imfl in instr.files:
        if not isinstance(imfl, types.FunctionType):
            instr.pages.append(
                visual.ImageStim(instr.window, image=imfl, **args))
        else:
            instr.pages.append(imfl)

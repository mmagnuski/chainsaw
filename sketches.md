:construction:

Experiment class
----------------

## displaying stimuli
`show` method of the Experiment class allows for convenient display of relevant stimuli along with controlling their duration and sending relevant triggers.

### Examples
```python
from psychopy import visual
from chainsaw import Experiment

class MyExp(Experiment):
  def create_stimuli(self):
    self.stim['c'] = visual.Circle(self.window)
    
exp = MyExp()
exp.setup()
exp.show(['fix', 'c'])
```


## sending LPT triggers
The Experiment class automatically sends LPT triggers at the stimuli onset, provided `settings.yaml` defines trigger code for particular stimulus.

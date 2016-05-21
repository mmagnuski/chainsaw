:construction:

Experiment class
----------------

## displaying stimuli
`show` method of the Experiment class allows for convenient display of relevant stimuli along with controlling their duration and sending relevant triggers.

### Examples
`settings.yaml`:
```yaml
times:
  fix: 0.1       # 0.1 second
  c:  [0.5, 0.75] # random time from 0.5 to 0.75 seconds interval

triggers:
  fix: 10
  c:   4

port_adress: '0xCC00'
```

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

# chainsaw
*Cause every psycho(py) needs a chainsaw*  
  
Set of tools for PsychoPy. Contains an experiment class that easies things up and a bunch of useful functions.

Some of the things that `chainsaw` helps with:
* reading settings from `settings.yaml` file
* showing instructions built from images or text files, where some of the pages are python functions (allows to show actual trial examples as part of the instructions) 
* showing breaks every n trials
* presenting stimuli with simple commands. For example `exp.show_element('fix', trigger=100)` (where `exp` is an instance of the `Experiment` class) automatically checks stimuli dictionary for `'fix'` key (exp.stim dictionary created by the user at the experiment start), draws time for `'fix'` defined in the `settings.yaml` (converting the time to number of frames) and fires a trigger synced with screen refresh using the device defined in `settings.yaml` (LPT port or CPOD Cedrus device). 
* training that continues conditional on participant correctness
* fitting stimuli intensity with a staircase or the quest plus method
* sending triggers through LPT or C-pod device
* simple interface to gather responses from Cedrus response box (`getKeys` and `waitKeys` just like when using keyboard in psychopy)
* saving triggers to a `.log` file (helps testing triggers without LPT port, Cedrus C-POD or in general without the recording device)

The two core elements of experiment built with `chainsaw` are the experiment object (subclassed from `chainsaw.exp_utils.Experiment`) and the `settings.yaml` file.  
🚧 more description and examples will arrive later 🚧

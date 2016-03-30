# managing responses:

		resp = self.wait_and_ask(probe, wait_time=wait_time,
			get_resp=get_resp)
		self.check_quit(key=resp)

		# check response
		if get_resp:
			if len(resp) > 0:
				key, rt = resp
				corr = self.resp_mapping[key] == corr_resp
			else:
				corr = False
				rt = np.nan
			if feedback:
				self.show_feedback(corr)
			return corr, rt
		else:
			return False, np.nan



# Experiment methods

	# def set_trigger(self, event):
	# 	if self.send_triggers:
	# 		if isinstance(event, int):
	# 			self.window.callOnFlip(self.send_trigger, event)
	# 		else:
	# 			if 'digit' in event:
	# 				trig = self.triggers['digit'][int(event[-1])]
	# 				self.window.callOnFlip(self.send_trigger, trig)
	# 			if 'probe' in event:
	# 				trig = self.triggers['probe'][int(event[-1])]
	# 				self.window.callOnFlip(self.send_trigger, trig)
	# def set_trigger(self, event):
	# 	if self.send_triggers:
	# 		if isinstance(event, int):
	# 			self.window.callOnFlip(self.send_trigger, event)
	# 		else:
	# 			if event in self.letters:
	# 				trig = self.triggers['letter']
	# 				self.window.callOnFlip(self.send_trigger, trig)
	# 			elif event in self.relations:
	# 				trig = self.triggers['relation']
	# 				self.window.callOnFlip(self.send_trigger, trig)
	# 			elif event in self.triggers:
	# 				trig = self.triggers[event]
	# 				self.window.callOnFlip(self.send_trigger, trig)
	# 			elif event == '?':
	# 				trig = self.triggers[question_mark]
	# 				self.window.callOnFlip(self.send_trigger, trig)

	# def create_trials(self):
	# 	pass

	# def create_stimuli(self):
	# 	# create some stimuli
	# 	self.fix = fix(self.window, **self.settings['fixation'])
	# 	self.digits = [visual.TextStim(self.window, text=str(x),
	# 		height=self.settings['digits']['height']) for x in range(10)]
	# 	self.stim = dict()
	# 	feedback_colors = (np.array([[0,147,68], [190, 30, 45]],
	# 		dtype='float') / 255 - 0.5) * 2
	# 	self.stim['feedback_correct'] = fix(self.window, height=self.settings[
	# 		'feedback_circle_radius'], color=feedback_colors[0,:])
	# 	self.stim['feedback_incorrect'] = fix(self.window, height=self.\
	# 		settings['feedback_circle_radius'], color=feedback_colors[1,:])

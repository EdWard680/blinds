from controller import Controller

import logging

logger = logging.getLogger(__name__)

# Abstracts all functions of the Controller in an event scheduler
# All calls are non-blocking/sleeping.
class SyncController(Controller):
	def __init__(self, conf, scheduler):
		self.scheduler = scheduler
		self.recurring = {}
		Controller.__init__(self, conf)
	
	# Attempts to run the command immediately
	def enqueue(self, f, args=(), priority=10):
		return self.scheduler.enter(0, priority, f, (self,) + args)
	
	def reconfigure(self, new_conf):
		self.enqueue(Controller.reconfigure, (new_conf,))
	
	def reset_position(self, pos=0):
		self.enqueue(Controller.reset_position, (pos,))
	
	def set_blinds(self, pos):
		logger.debug("SyncController.set_blinds(%i)", pos)
		# clean this shit up
		for ev in reversed(self.scheduler.queue):
			if ev.action is Controller.set_blinds:
				logger.debug("  Cancelling: %s", str(ev))
				self.scheduler.cancel(ev)
		
		# increased priority
		self.enqueue(Controller.set_blinds, (pos,), 0)
	
	# Instead of immediately queueing a command, schedules one for time t
	def schedule_command(self, t, cmd_str, args=()):
		logger.debug("SyncController.schedule_command(%f, %s, %s)", t, cmd_str, str(args))
		func = getattr(self, cmd_str)
		if func is None:
			raise InputError("Invalid cmd_str: " + cmd_str)
		return self.scheduler.enterabs(t, 5, func, args)
	
	# Will run the command specified by cmd_str, and then reschedule itself to
	# execute again period time-units later. It will save the recurring event
	# by name
	def recur_command(self, name, period, cmd_str, args=()):
		logger.debug("SyncController.recur_command(%s, %f, %s, %s)", name, period, cmd_str, str(args))
		func = getattr(self, cmd_str)
		if func is None:
			raise InputError("Invalid cmd_str: " + cmd_str)
		func(*args)
		
		ev = self.scheduler.enter(period, 5, SyncController.recur_command, (self, name), kwargs={'period': period, 'cmd_str': cmd_str, 'args': args})
		
		self.save_recurring(name, ev)
	
	def schedule_recurring(self, name, first, period, cmd_str, args=()):
		logger.debug("SyncController.schedule_recurring(%s, %f, %f, %s, %s)", name, first, period, cmd_str, str(args))
		
		ev = self.scheduler.enterabs(first, 5, SyncController.recur_command, (self, name), kwargs={'period': period, 'cmd_str': cmd_str, 'args': args})
		
		self.save_recurring(name, ev)
	
	def save_recurring(self, name, ev):
		logger.debug("SyncController.save_recurring(%s, %s)", name, str(ev))
		if name in self.recurring and self.recurring[name] != ev and self.recurring[name] in self.scheduler.queue:
			self.scheduler.cancel(self.recurring[name])
		
		self.recurring[name] = ev
		logger.info("Recurring commands updated: %s", str(self.recurring))
	
	# Will cancel a command saved as name
	def cancel_recurring(self, name):
		logger.debug("SyncController.cancel_recurring(%s)", name)
		if self.recurring[name] in self.scheduler.queue:
			logger.debug("  Cancelling previous command: %s", self.recurring[name])
			self.scheduler.cancel(self.recurring[name])
			del self.recurring[name]
	
	def get_recurring(self):
		return [{'name': k, 'time': v.time, 'command': v.kwargs['cmd_str'], 'args': v.kwargs['args']} for k, v in self.recurring.items()]

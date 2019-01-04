from controller import Controller
import threading

import logging

logger = logging.getLogger(__name__)

# Abstracts all functions of the Controller in an event scheduler
# All calls are non-blocking/sleeping.
class SyncController(Controller):
	def __init__(self, conf, scheduler):
		logger.debug("SyncController(%s, ...)", str(conf))
		self.scheduler = scheduler
		self.recurring = {}
		self.server_config = conf['server_config']
		Controller.__init__(self, conf['hardware_config'])
		logger.debug("  Initial queue: %s", str(self.scheduler.queue))
	
	# Attempts to run the command immediately
	def enqueue(self, f, args=(), priority=10):
		return self.scheduler.enter(0, priority, f, (self,) + args)
	
	# The only thing that matters is the blinds final state.
	# Many commands such as set_blinds should never really be scheduled ahead
	# of time, so this will clear all other currently queued calls to f.
	# This behavior is especially useful when it starts up, and several
	# recurring commands are caught up on. Once it gets to real time, only
	# the final state will be queued to actually run.
	def clean_enqueue(self, f, args=(), priority=10):
		for ev in self.scheduler.queue:
			if ev.action is f:
				logger.debug("  Cancelling: %s", str(ev))
				self.scheduler.cancel(ev)
		
		self.enqueue(f, args, priority)
	
	def update_server_config(self, new_conf):
		logger.debug("SyncController.update_server_config(%s)", str(new_conf))
		self.server_config.update(new_conf)
	
	def reconfigure(self, new_conf):
		logger.debug("SyncController.reconfigure(%s)", str(new_conf))
		if 'server_config' in new_conf:
			self.enqueue(SyncController.update_server_config, (new_conf['server_config'],))
		
		if 'hardware_config' in new_conf:
			self.enqueue(Controller.reconfigure, (new_conf['hardware_config'],))
	
	def get_config(self):
		return {'hardware_config': Controller.get_config(self), 'server_config': self.server_config}
	
	def reset_position(self, pos=0):
		self.enqueue(Controller.reset_position, (pos,))
	
	def set_blinds(self, pos):
		logger.debug("SyncController.set_blinds(%i)", pos)
		
		# increased priority
		self.clean_enqueue(Controller.set_blinds, (pos,), 0)
	
	def poll_button(self):
		butt = self.button_pressed()
		if butt == Controller.SHORT_PRESS:
			if self.closed():
				self.open_blinds()
			else:
				self.close_blinds()
		elif butt == Controller.LONG_PRESS:
			self.reset_position()

	# Instead of immediately queueing a command, schedules one for time t
	def schedule_command(self, t, cmd_str, args=()):
		logger.debug("SyncController.schedule_command(%f, %s, %s)", t, cmd_str, str(args))
		func = getattr(self, cmd_str)
		if func is None:
			raise InputError("Invalid cmd_str: " + cmd_str)
		ret = self.scheduler.enterabs(t, 5, func, args)
		
		self.save()
		
		return ret
	
	# Will run the command specified by cmd_str, and then reschedule itself to
	# execute again period time-units later. It will save the recurring event
	# by name
	def recur_command(self, name, period, cmd_str, args=()):
		logger.debug("SyncController.recur_command(%s, %f, %s, %s)", name, period, cmd_str, str(args))
		func = getattr(self, cmd_str)
		if func is None:
			raise InputError("Invalid cmd_str: " + cmd_str)
		func(*args)
		
		next_time = self.recurring[name].time + period
		ev = self.scheduler.enterabs(next_time, 5, SyncController.recur_command, (self, name), kwargs={'period': period, 'cmd_str': cmd_str, 'args': args})
		
		self.save()
		
		self.save_recurring(name, ev)
	
	def schedule_recurring(self, name, first, period, cmd_str, args=()):
		logger.debug("SyncController.schedule_recurring(%s, %f, %f, %s, %s)", name, first, period, cmd_str, str(args))
		
		ev = self.scheduler.enterabs(first, 5, SyncController.recur_command, (self, name), kwargs={'period': period, 'cmd_str': cmd_str, 'args': args})
		
		self.save()
		self.save_recurring(name, ev)
	
	def save_recurring(self, name, ev):
		logger.debug("SyncController.save_recurring(%s, %s)", name, str(ev))
		if name in self.recurring and self.recurring[name] != ev and self.recurring[name] in self.scheduler.queue:
			self.scheduler.cancel(self.recurring[name])
		
		self.recurring[name] = ev
		self.save()
		logger.info("Recurring commands updated: %s", str(self.recurring))
	
	# Will cancel a command saved as name
	def cancel_recurring(self, name):
		logger.debug("SyncController.cancel_recurring(%s)", name)
		if name in self.recurring and self.recurring[name] in self.scheduler.queue:
			logger.debug("  Cancelling previous command: %s", self.recurring[name])
			self.scheduler.cancel(self.recurring[name])
			del self.recurring[name]
			self.save()
	
	def get_recurring(self):
		return [{'name': k, 'time': v.time, 'command': v.kwargs['cmd_str'], 'args': v.kwargs['args']} for k, v in self.recurring.items()]
	
	def save(self):
		logger.debug("SyncController.save()")
		self.clean_enqueue(Controller.save)

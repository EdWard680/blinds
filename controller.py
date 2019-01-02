import wiringpi
import logging
from wiringpi import INPUT, OUTPUT, PUD_OFF, PUD_UP, PUD_DOWN

logger = logging.getLogger(__name__)

def run_motor_for(pin, dur):
	wiringpi.digitalWrite(pin, 1)
	wiringpi.delay(dur)
	wiringpi.digitalWrite(pin, 0)

# Maintains the state of the blinds.
# Ensures that configuration changes don't break the current state of the blinds
# Guarantees that changes in pin-number, open-duration, etc. don't put the blinds
# in an invalid state.
class Controller:
	
	REST, CLOSING, OPENING = tuple(range(3))
	
	def __init__(self, config):
		logger.debug("Controller(%s)", config)
		wiringpi.wiringPiSetup()
		self.reset_position()
		self.config = {}
		self.state = Controller.REST
		self.reconfigure(config)
	
	def reconfigure(self, config):
		logger.debug("Controller.reconfigure(%s)", config)
		
		# only overwrites what is present
		for k, v in config.items():
			self.config[k] = v
		
		wiringpi.pinMode(self.config['motor_pin'], OUTPUT)
		wiringpi.pinMode(self.config['direction_pin'], OUTPUT)
		wiringpi.pinMode(self.config['button_pin'], INPUT)
		wiringpi.pullUpDnControl(self.config['button_pin'], PUD_UP)
	
	def reset_position(self, pos=0):
		logger.debug("Controller.reset_position(%i)", pos)
		self.amount_opened = pos
	
	def get_position(self):
		return self.amount_opened
	
	def get_state(self):
		return self.state
	
	def get_config(self):
		return self.config
	
	def closed(self):
		logger.debug("Controller.closed() -> %i", 1 if self.amount_opened == 0 else 0)
		return self.amount_opened == 0
	
	NO_PRESS, SHORT_PRESS, LONG_PRESS = tuple(range(3))
	def button_pressed(self):
		# logger.debug("Controller.button_pressed()")
		pin = self.config['button_pin']
		short_dur = self.config['short_debounce_millis']
		long_dur = short_dur + self.config['long_additional_debounce_millis']
		start = wiringpi.millis()
		while wiringpi.millis() - start < short_dur:
			if wiringpi.digitalRead(pin):
				# logger.debug("Controller.button_pressed() -> NO_PRESS")
				return Controller.NO_PRESS
		
		while wiringpi.millis() - start < long_dur:
			if wiringpi.digitalRead(pin):
				logger.debug("Controller.button_pressed() -> SHORT_PRESS")
				return Controller.SHORT_PRESS
		
		while not wiringpi.digitalRead(pin):
			wiringpi.delay(1)
		
		logger.debug("Controller.button_pressed() -> LONG_PRESS")
		return Controller.LONG_PRESS
	
	def set_blinds(self, amount):
		logger.debug("Controller.set_blinds(%i)", amount)
		diff = amount - self.amount_opened
		if diff > 0:
			logger.info("Opening blinds for %i milliseconds", diff)
			self.state = Controller.OPENING
			start = wiringpi.millis()
			run_motor_for(self.config['motor_pin'], diff)
			self.amount_opened += wiringpi.millis() - start
		elif diff < 0:
			logger.info("Closing blinds for %i milliseconds", -diff)
			self.state = Controller.CLOSING
			dir_pin = self.config['direction_pin']
			wiringpi.digitalWrite(dir_pin, 1)
			wiringpi.delay(100)
			start = wiringpi.millis()
			run_motor_for(self.config['motor_pin'], -diff)
			self.amount_opened -= wiringpi.millis() - start
			wiringpi.delay(100)
			wiringpi.digitalWrite(dir_pin, 0)
		self.state = Controller.REST
		logger.debug("Blinds set. amount_opened = %i", self.amount_opened)
	
	def open_blinds(self):
		logger.debug("Controller.open_blinds()")
		self.set_blinds(self.config['open_millis'])
	
	def close_blinds(self):
		logger.debug("Controller.close_blinds()")
		
		self.set_blinds(-self.config['close_offset_millis'])
		self.reset_position()

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
	def __init__(self, config):
		logger.debug("Controller(%s)", config)
		wiringpi.wiringPiSetup()
		self.config = config
		self.reset_position()
		self.reconfigure()
	
	def reconfigure(self):
		logger.debug("Controller.reconfigure()")
		wiringpi.pinMode(self.config['motor_pin'], OUTPUT)
		wiringpi.pinMode(self.config['direction_pin'], OUTPUT)
		wiringpi.pinMode(self.config['button_pin'], INPUT)
		wiringpi.pullUpDnControl(self.config['button_pin'], PUD_UP)
	
	def reset_position(self, pos=0):
		logger.debug("Controller.reset_position(%i)", pos)
		self.amount_opened = pos
	
	def get_position(self):
		logger.debug("Controller.get_position() -> %i", self.amount_opened)
		return self.amount_opened
	
	def closed(self):
		logger.debug("Controller.closed() -> %i", 1 if self.amount_opened == 0 else 0)
		return self.amount_opened == 0
	
	def button_pressed(self):
		# logger.debug("Controller.button_pressed()")
		pin = self.config['button_pin']
		dur = self.config['debounce_millis']
		start = wiringpi.millis()
		while wiringpi.millis() - start < dur:
			if wiringpi.digitalRead(pin):
				# logger.debug("Controller.button_pressed() -> False")
				return False
		
		logger.debug("Controller.button_pressed() -> True")
		return True
	
	def open_blinds(self, amount=-1):
		logger.debug("Controller.open_blinds(%i)", amount)
		if amount == -1:
			amount = self.config['open_millis']
		
		# I hope it hasn't been the exact amount of time that wraps here
		start = wiringpi.millis()
		logger.info("Opening blinds for %i milliseconds", amount)
		run_motor_for(self.config['motor_pin'], amount)
		
		self.amount_opened = wiringpi.millis() - start
		logger.debug("Blinds opened. amount_opened = %i", self.amount_opened)
	
	def close_blinds(self):
		logger.debug("Controller.close_blinds()")
		c = self.config
		dir_pin = c['direction_pin']
		
		wiringpi.digitalWrite(dir_pin, 1)
		wiringpi.delay(100)
		
		close_millis = self.amount_opened + c['close_offset_millis']
		logger.info("Closing blinds for %i milliseconds", close_millis)
		run_motor_for(c['motor_pin'], close_millis)
		
		wiringpi.delay(100)
		wiringpi.digitalWrite(dir_pin, 0)
		
		self.amount_opened = 0
		logger.debug("Blinds closed.")

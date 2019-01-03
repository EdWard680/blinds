from controller import Controller
from sync_controller import SyncController
from server import start_public_server, start_local_server

import sched
import logging
import os
import time

def default_hardware_config():
	return {
		'motor_pin': int(os.getenv('BLINDS_MOTOR_PIN', "0")),
		'direction_pin': int(os.getenv('BLINDS_DIRECTION_PIN', "2")),
		'button_pin': int(os.getenv('BLINDS_BUTTON_PIN', "28")),
		'open_millis': int(os.getenv('BLINDS_DEFAULT_OPEN_MILLIS', "6000")),
		'close_offset_millis': int(os.getenv('BLINDS_DEFAULT_CLOSE_MILLIS', "0")),
		'short_debounce_millis': int(os.getenv('BLINDS_SHORT_DEBOUNCE_MILLIS', "50")),
		'long_additional_debounce_millis': int(os.getenv('BLINDS_LONG_ADDITIONAL_DEBOUNCE_MILLIS', "700"))
	}

def default_server_config():
	return {
		'username': os.getenv('BLINDS_SERVER_USERNAME', "ward"),
		'password': os.getenv('BLINDS_SERVER_PASSWORD', "opensource")
	}

def default_config():
	return {
		'hardware_config': default_hardware_config(),
		'server_config': default_server_config()
	}

def test_controller(conf):
	logging.info("Running test_controller")
	controller = Controller(conf)
	while True:
		time.sleep(10)
		controller.open_blinds()
		time.sleep(10)
		controller.close_blinds()

def button_controller(conf):
	logging.info("Running button_controller")
	controller = Controller(conf)
	while True:
		while controller.button_pressed() != Controller.SHORT_PRESS:
			time.sleep(0.01)
		controller.open_blinds()
		
		while controller.button_pressed() != Controller.SHORT_PRESS:
			time.sleep(0.01)
		controller.close_blinds()

def server_controller(conf):
	logging.info("Running server")
	
	s = sched.scheduler(time.time, time.sleep)
	controller = SyncController(conf, s)
	
	def check_button():
		butt = controller.button_pressed()
		if butt == Controller.SHORT_PRESS:
			if controller.closed():
				controller.open_blinds()
			else:
				controller.close_blinds()
		elif butt == Controller.LONG_PRESS:
			controller.reset_position()
		
		s.enter(0.01, 0, check_button)
	
	s.enter(0.01, 0, check_button)
	
	local_port = int(os.getenv('BLINDS_LOCAL_PORT', "8080"))
	local_server_thread = start_local_server(controller, local_port)
	public_server_thread = start_public_server(controller)
	
	while True:
		s.run()
	

def main():
	print("Starting blinds controller")
	
	loglevel = getattr(logging, os.getenv('BLINDS_LOG_LEVEL', "DEBUG"), 5)
	logging.basicConfig(level=loglevel)
	
	mode = os.getenv('BLINDS_MODE', "LED_TEST")
	if mode == "LED_TEST":
		test_controller(default_hardware_config())
	elif mode == "BUTTON_TEST":
		button_controller(default_hardware_config())
	elif mode == "SERVER":
		server_controller(default_config())
	
	

if __name__ == "__main__":
	main()

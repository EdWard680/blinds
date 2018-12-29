from controller import Controller
import logging

import os
import time

def default_config():
	return {
		'motor_pin': int(os.getenv('BLINDS_MOTOR_PIN', "0")),
		'direction_pin': int(os.getenv('BLINDS_DIRECTION_PIN', "2")),
		'open_millis': int(os.getenv('BLINDS_DEFAULT_OPEN_MILLIS', "6000")),
		'close_offset_millis': int(os.getenv('BLINDS_DEFAULT_CLOSE_MILLIS', "0"))
	}


def test_controller(controller):
	logging.info("Running test_controller")
	while True:
		time.sleep(10)
		controller.open_blinds()
		time.sleep(10)
		controller.close_blinds()

def main():
	print("Starting blinds controller")
	
	loglevel = getattr(logging, os.getenv('BLINDS_LOG_LEVEL', "DEBUG"), 5)
	logging.basicConfig(level=loglevel)
	
	controller = Controller(default_config())
	
	if os.getenv('BLINDS_RUN_TEST', "1") == "1":
		test_controller(controller)
	
	

if __name__ == "__main__":
	main()

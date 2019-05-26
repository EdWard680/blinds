import logging
import board
import busio
import adafruit_veml7700

class LightSensor(adafruit_veml7700.VEML7700):
	def __init__(self):
		i2c = busio.I2C(board.SCL, board.SDA)
		adafruit_veml7700.VEML7700.__init__(self, i2c)

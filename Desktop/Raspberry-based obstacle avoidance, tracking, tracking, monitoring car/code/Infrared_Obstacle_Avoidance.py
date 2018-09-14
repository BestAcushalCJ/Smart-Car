import RPi.GPIO as GPIO
import time
from MotionBase import MotionBase

motion = MotionBase()

DR = 16
DL = 19

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(DR,GPIO.IN,GPIO.PUD_UP)
GPIO.setup(DL,GPIO.IN,GPIO.PUD_UP)

try:
	while True:
		DR_status = GPIO.input(DR)
		DL_status = GPIO.input(DL)
		if((DL_status == 1) and (DR_status == 1)):
			motion.forward()
			print("forward")
		elif((DL_status == 1) and (DR_status == 0)):
			motion.left()
			print("left")
		elif((DL_status == 0) and (DR_status == 1)):
			motion.right()
			print("right")
		else:
			motion.backward()
			time.sleep(0.3)
			motion.left()
			time.sleep(0.3)
			motion.stop()
			print("backward")

except KeyboardInterrupt:
	GPIO.cleanup();


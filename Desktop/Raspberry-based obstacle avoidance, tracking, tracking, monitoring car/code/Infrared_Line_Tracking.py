import RPi.GPIO as GPIO
import time

CS = 5
Clock = 25
Address = 24
DataOut = 23

class TRSensor(object):
        #初始化相应的管脚，已经申请内存用作存储各个传感器的Max,Min值
	def __init__(self,numSensors = 5):
		self.numSensors = numSensors
		self.calibratedMin = [0] * self.numSensors
		self.calibratedMax = [1023] * self.numSensors
		self.last_value = 0
		
        #读取五路探测器的模拟值
	def AnalogRead(self):
		value = [0,0,0,0,0,0]
		for j in range(0,6):
			GPIO.output(CS, GPIO.LOW)
			for i in range(0,4):
				if(((j) >> (3 - i)) & 0x01):
					GPIO.output(Address,GPIO.HIGH)
				else:
					GPIO.output(Address,GPIO.LOW)
				value[j] <<= 1
				if(GPIO.input(DataOut)):
					value[j] |= 0x01
				GPIO.output(Clock,GPIO.HIGH)
				GPIO.output(Clock,GPIO.LOW)
			for i in range(0,6):
				value[j] <<= 1
				if(GPIO.input(DataOut)):
					value[j] |= 0x01
				GPIO.output(Clock,GPIO.HIGH)
				GPIO.output(Clock,GPIO.LOW)
			for i in range(0,6):
				GPIO.output(Clock,GPIO.HIGH)
				GPIO.output(Clock,GPIO.LOW)
#			time.sleep(0.0001)
			GPIO.output(CS,GPIO.HIGH)
		return value[1:]
		
	#校准函数，通过多次采集数据，确定Max，Min值
	#校准阶段时，小车需在黑线中紧贴地面左右摇晃
	def calibrate(self):
		max_sensor_values = [0]*self.numSensors
		min_sensor_values = [0]*self.numSensors
		for j in range(0,10):
		
			sensor_values = self.AnalogRead();
			
			for i in range(0,self.numSensors):
				if((j == 0) or max_sensor_values[i] < sensor_values[i]):
					max_sensor_values[i] = sensor_values[i]

				if((j == 0) or min_sensor_values[i] > sensor_values[i]):
					min_sensor_values[i] = sensor_values[i]

				for i in range(0,self.numSensors):
			if(min_sensor_values[i] > self.calibratedMin[i]):
				self.calibratedMin[i] = min_sensor_values[i]
			if(max_sensor_values[i] < self.calibratedMax[i]):
				self.calibratedMax[i] = max_sensor_values[i]
	#归一化线性转换，将数据转为0~1000范围内
	#1000表示探测器远离黑线，0表示探测器在黑线正中
	def	readCalibrated(self):
		value = 0
		sensor_values = self.AnalogRead();

		for i in range (0,self.numSensors):

			denominator = self.calibratedMax[i] - self.calibratedMin[i]

			if(denominator != 0):
				value = (sensor_values[i] - self.calibratedMin[i])* 1000 / denominator
				
			if(value < 0):
				value = 0
			elif(value > 1000):
				value = 1000
				
			sensor_values[i] = value
		
		print("readCalibrated",sensor_values)
		return sensor_values
			
	"""

	   0*value0 + 1000*value1 + 2000*value2 + ...
	   --------------------------------------------
			 value0  +  value1  +  value2 + ...

	"""
	#加权平均算出寻迹线的位置,数值范围为0~4000
	#0表示在黑线在模块的最左侧，4000表示黑线在最右侧
	def readLine(self, white_line = 0):

		sensor_values = self.readCalibrated()
		avg = 0
		sum = 0
		on_line = 0
		for i in range(0,self.numSensors):
			value = sensor_values[i]
			if(white_line):
				value = 1000-value
			if(value > 200):
				on_line = 1
				
			if(value > 50):
				avg += value * (i * 1000);
				sum += value;

		if(on_line != 1):
			if(self.last_value < (self.numSensors - 1)*1000/2):
				#print("left")
				return 0;
			else:
				#print("right")
				return (self.numSensors - 1)*1000

		self.last_value = avg/sum
		
		return self.last_value
	
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Clock,GPIO.OUT)
GPIO.setup(Address,GPIO.OUT)
GPIO.setup(CS,GPIO.OUT)
GPIO.setup(DataOut,GPIO.IN,GPIO.PUD_UP)

if __name__ == '__main__':

	from MotionBase import MotionBase
	
	maximum = 35;
	integral = 0;
	last_proportional = 0
	
	TR = TRSensor()
	motion = MotionBase()
	motion.stop()
	print("Line follow Example")
	time.sleep(0.5)
	for i in range(0,400):
		TR.calibrate()
		print i
	print(TR.calibratedMin)
	print(TR.calibratedMax)
	time.sleep(0.5)	
	motion.backward()
	while True:
		position = TR.readLine()

		proportional = position - 2000
		
		derivative = proportional - last_proportional
		integral += proportional
		
		last_proportional = proportional
		#PD算法
  
		power_difference = proportional/25 + derivative/100 #+ integral/1000;  

		if (power_difference > maximum):
			power_difference = maximum
		if (power_difference < - maximum):
			power_difference = - maximum
		print(position,power_difference)
		if (power_difference < 0):
			motion.setPWMB(maximum + power_difference)
			motion.setPWMA(maximum);
		else:
			motion.setPWMB(maximum); 
			motion.setPWMA(maximum - power_difference)
			 


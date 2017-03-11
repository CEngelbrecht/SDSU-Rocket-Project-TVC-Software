import roboclaw
from ABE_ADCPi import ADCPi
from ABE_helpers import ABEHelpers
import time
import PID
import socket
import numpy as np 
import time

class TVCServer():

	def __init__(self):

		#Get the ADC fired up. 
		i2c_helper = ABEHelpers()
		bus = i2c_helper.get_smbus()
		self.adc = ADCPi(bus, 0x68, 0x69, 12)

		#Open the serial port for use. 
		roboclaw.Open("/dev/ttyAMA0",38400)
		print("Serial port open!")
		self.address = 0x80

		#Networking vars. Currently set to Christian's IP and Laptop
		client_IP = "10.42.0.87"
		port = 6969
		self.server_address = (client_IP,port)

		#Set the max speed of the motors. Max/min is +32767/-32767
		self.max_speed = 20000
		self.min_speed = -20000

		#Scaling params. Experimentally obtained. 
		self.adc_min = 0.600453
		self.adc_max = 4.6000

		self.mapped_max = 0 #Yes, max is zero and min is 100.
		self.mapped_min = 100 #This is due to backward wiring in TVCBey and on my part.

		#Vars needed for mapping method.
		self.adc_span = self.adc_max - self.adc_min
		self.mapped_span = self.mapped_max - self.mapped_min
	
		#Initializing feedbacks
		self.x_feedback = 0
		self.y_feedback = 0

		#PID Params. They're currently same for x and y
		kp = 2500
		ki = 50
		kd = 0
		sample_time = 0.001 

		#Objects from the PID.py import. See documentation there.
		self.x_PID = PID.PID(kp,ki,kd)
		self.y_PID = PID.PID(kp,ki,kd)

		self.x_PID.setSampleTime(sample_time)
		self.y_PID.setSampleTime(sample_time)

		#Zero point for actuators to balance motor
		self.x_zero = 57 #Experimentally defined
		self.y_zero = 56 

		self.output_error_range = 1000

	def feedback_map(self,raw_feedback):
		'''Scales raw ADC feedback between 0 and 100'''

		scale_factor = float(raw_feedback - self.adc_min)/float(self.adc_span)

		return self.mapped_min + (scale_factor*self.mapped_span)

	def connect(self):
		'''Creates connection between TVC Client and Server'''
		self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.s.bind(self.server_address)
		self.s.listen(1)

		self.conn,addr = self.s.accept()
		self.conn.setblocking(0) #Makes a nonblocking socket


	def get_data(self):
		'''Get data from client's socket'''

		try: 
			data = self.conn.recv(1024)
			if len(data) > 1:
				return data
		except socket.error as e:
			pass

	def send_data(self):
		'''Send position data back to client'''

		x_feedback,y_feedback = self.read_adc()
		send_packet = str(x_feedback)+","+str(y_feedback)
		self.conn.send(send_packet)

	def read_adc(self):
		'''Read the ADC feedbacks'''

		x_feedback = self.adc.read_voltage(1)
		y_feedback = self.adc.read_voltage(2)

		x_feedback = self.feedback_map(x_feedback)
		y_feedback = self.feedback_map(y_feedback)

		return x_feedback,y_feedback

	def run_PID(self,setpoint,feedback,motor):
		'''Update the x_PID and y_PID objects'''

		motor.SetPoint = setpoint 
		motor.update(feedback)
		output = motor.output

		if output > self.max_speed:
			output = self.max_speed
		if output < self.min_speed: 
			output = self.min_speed

		return int(output)

	def move_motors(self,speed,motor):
		'''Move one motor at speed'''

		if motor == 'X':
			roboclaw.DutyM1M2(self.address,-speed,0) #Need this minus sign, for mixed wiring 
		elif motor == 'Y':
			roboclaw.DutyM1M2(self.address,0,speed)

	def stop_moving(self):
		'''Stops both motors'''

		roboclaw.DutyM1M2(self.address,0,0)

	def zero_motors(self):
		'''Move motors to zero point'''

		feedbacks = self.read_adc()
		x_SP = self.x_zero
		y_SP = self.y_zero
		x_output = self.run_PID(x_SP,feedbacks[0],self.x_PID)
		y_output = self.run_PID(y_SP,feedbacks[1],self.y_PID)

		while (abs(x_output) > self.output_error_range or abs(y_output) > self.output_error_range):

			print x_output,y_output
			feedbacks = self.read_adc()
			x_output = self.run_PID(x_SP,feedbacks[0],self.x_PID)
			y_output = self.run_PID(y_SP,feedbacks[1],self.y_PID)
			roboclaw.DutyM1M2(self.address,-x_output,y_output)
			self.send_data()
			self.get_data()

		self.stop_moving()


	def OneSetpoint(self,setpoint,motor):

		if motor == 'X':

			feedback = self.read_adc()[0] #grab the X feedback
			output = self.run_PID(setpoint,feedback,self.x_PID)
					
			while abs(output) > self.output_error_range:

				feedback = self.read_adc()[0]
				output = self.run_PID(setpoint,feedback,self.x_PID)
				self.move_motors(output,'X')
				self.send_data()
				self.get_data()

			self.stop_moving()

		if motor == 'Y':

			feedback = self.read_adc()[1] #grab the Y feedback
			output = server.run_PID(setpoint,feedback,self.y_PID)
					
			while abs(output) > self.output_error_range:

				feedback = server.read_adc()[1]
				output = server.run_PID(setpoint,feedback,self.y_PID)
				self.move_motors(output,'Y')
				self.send_data()
				self.get_data()

			self.stop_moving()

	def do_circle(self):
		#Ymin and max for 7 degree radius: 28,79
		#Xmin and max for 7 degree radius: 30,82

		t = np.linspace(2*np.pi,0.0,130)

		x_SPs = [25*np.cos(i) + 57 for i in t]
		y_SPs = [23*np.sin(i) + 56 for i in t]

		self.OneSetpoint(82,'X')

		print "Waiting"

		time.sleep(1)

		for i in range(len(t)):

			feedbacks = self.read_adc()
			x_output = self.run_PID(x_SPs[i],feedbacks[0],self.x_PID)
			y_output = self.run_PID(y_SPs[i],feedbacks[1],self.y_PID)
			roboclaw.DutyM1M2(self.address,-x_output,y_output)
			#self.send_data()
			#print "xsp = {}, xout = {},yout = {} i = {}".format(x_SPs[i],x_output,y_SPs[i],i)
			#print feedbacks
		#if feedbacks[0] 
		self.stop_moving()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':

	#Some initializations

	
	server = TVCServer()

	print "Attempting Connection"
	server.connect()
	print "Connection Established"

	while 1:

		server.send_data()
		data = server.get_data()

		if not data:
			pass

		elif data[0] == 'X':

			setpoint = float(data[1:]) #Strip Header, convert to float
			server.OneSetpoint(setpoint,"X")

		elif data[0] == 'Y':

			setpoint = float(data[1:]) #Strip Header, Convert to float
			server.OneSetpoint(setpoint,"Y")

		elif data[0] == 'Z':

			server.zero_motors()

		elif data[0] == 'P':
			'''Do plus sign routine'''

			server.zero_motors()

			for point in [30,82,server.x_zero]:
				server.OneSetpoint(point,'X')

			for point in [28,79,server.y_zero]:
				server.OneSetpoint(point,'Y')

		elif data[0] == 'C':

			server.do_circle()
			time.sleep(0.2)
			server.zero_motors()

		elif data[0] == 'G':

			server.x_PID.setKp() #Gainz boyz








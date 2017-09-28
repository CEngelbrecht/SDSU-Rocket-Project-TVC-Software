import roboclaw
from ABE_ADCPi import ADCPi
from ABE_helpers import ABEHelpers
import time
import PID
import socket
import numpy as np 
import time
import logging 
import threading

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
		self.x_zero = 54 #Experimentally defined
		self.y_zero = 51 

		self.x_output_error_range = 1500
		self.y_output_error_range = 1000

	def feedback_map(self,raw_feedback):
		'''Scales raw ADC feedback between 0 and 100'''

		scale_factor = float(raw_feedback - self.adc_min)/float(self.adc_span)

		return self.mapped_min + (scale_factor*self.mapped_span)

	def send_gains(self):
		'''Sends current gain info to client'''
		x_kp = self.x_PID.Kp
		x_ki = self.x_PID.Ki
		x_kd = self.x_PID.Kd 

		y_kp = self.y_PID.Kp
		y_ki = self.y_PID.Ki
		y_kd = self.y_PID.Kd

		msg = str(x_kp)+','+str(x_ki)+','+str(x_kd)+','+str(y_kp)+','+str(y_ki)+','+str(y_kd)

		msg = 'G'+str(msg)+'GEnd' #Attach header and footer to message

		try:
			self.conn.send(msg)

		except socket.error as e:
			print e

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

		while (abs(x_output) > self.x_output_error_range or abs(y_output) > self.y_output_error_range):

			feedbacks = self.read_adc()
			x_output = self.run_PID(x_SP,feedbacks[0],self.x_PID)
			y_output = self.run_PID(y_SP,feedbacks[1],self.y_PID)
			roboclaw.DutyM1M2(self.address,-x_output,y_output) #Minus sign is there to compensate for wiring 
			self.send_data()  
			self.get_data()
			self.log_to_file(feedbacks,x_SP,y_SP)
		self.stop_moving()


	def OneSetpoint(self,setpoint,motor):

		if motor == 'X':

			feedback = self.read_adc()[0] #grab the X feedback
			output = self.run_PID(setpoint,feedback,self.x_PID) #Update the PID, receive an output 
					
			while abs(output) > self.x_output_error_range: #Move until error is acceptable.

				feedbacks = self.read_adc()
				output = self.run_PID(setpoint,feedbacks[0],self.x_PID)
				self.move_motors(output,'X')
				self.send_data()
				response = self.get_data()
				if response == 'Z':
					break
				self.log_to_file(feedbacks,setpoint,0) #Y SP is zero since the motors are zeroed and X is called first. 
	
			self.stop_moving()

		if motor == 'Y':

			feedback = self.read_adc()[1] #grab the Y feedback
			output = server.run_PID(setpoint,feedback,self.y_PID)
					
			while abs(output) > self.y_output_error_range:

				feedbacks = self.read_adc()
				output = server.run_PID(setpoint,feedbacks[1],self.y_PID)
				print output,setpoint
				self.move_motors(output,'Y')
				self.send_data()
				response = self.get_data()
				if response == 'Z':
					break
				self.log_to_file(feedbacks,0,setpoint) #Y is done seccond, and X is zeroed, so send 0 setpoint for log for X 

			self.stop_moving()

	def do_circle(self):
		'''Make the actuators move in a circle'''


		#YMax: 74 ,23, 51 is zero: #Use these calibrations
		#XMax: 54 is zero, 79,27

		t = np.linspace(2*np.pi,0.0,110)

		x_SPs = [25*np.cos(i) + 54 for i in t]
		y_SPs = [23*np.sin(i) + 51 for i in t]

		self.OneSetpoint(82,'X')

		print "Waiting"

		time.sleep(1)

		for i in range(len(t)):

			feedbacks = self.read_adc()
			x_output = self.run_PID(x_SPs[i],feedbacks[0],self.x_PID)
			y_output = self.run_PID(y_SPs[i],feedbacks[1],self.y_PID)
			roboclaw.DutyM1M2(self.address,-x_output,y_output)
			self.log_to_file(feedbacks,x_SPs[i],y_SPs[i])
			self.send_data() 
			#print "xFB = {},yFB ={},xSP = {},ySP = {},".format(feedbacks[0],feedbacks[1],x_SPs[i],y_SPs[i])
		#self.stop_moving()

	def move_both(self,setpoints):
		 #setpoints is a tuple
		feedbacks = self.read_adc()
		x_SP = setpoints[0]
		y_SP = setpoints[1]

		x_output = self.run_PID(x_SP,feedbacks[0],self.x_PID)
		y_output = self.run_PID(y_SP,feedbacks[1],self.y_PID)

		while (abs(x_output) > self.x_output_error_range or abs(y_output) > self.y_output_error_range):

			feedbacks = self.read_adc()
			x_output = self.run_PID(x_SP,feedbacks[0],self.x_PID)
			y_output = self.run_PID(y_SP,feedbacks[1],self.y_PID)
			roboclaw.DutyM1M2(self.address,-x_output,y_output)
			self.log_to_file(feedbacks,setpoints[0],setpoints[1])
			self.send_data()
			print "{},{},{},{}".format(x_output,y_output,feedbacks[0],feedbacks[1])

	def log_to_file(self,feedbacks,x_setpoint,y_setpoint):
		'''Log positions and setpoints to a file'''
		
		logging.debug("{},{},{},{},{}".format(time.time(),feedbacks[0],feedbacks[1],x_setpoint,y_setpoint))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':

	file_name = 'positions_and_setpoints'+time.strftime("%Y%m%d%H%M%S",time.localtime())+'.log'
	logging.basicConfig(filename=file_name,level=logging.DEBUG,filemode = 'wr+') #wb overwrites
	#Time,x_FB,y_FB,x_SP,y_SP

	server = TVCServer()	#This instance off the class will be what runs the setpoints and routines 	

	while 1:

		try: 
			'''Always Zero The Motors after every routine. The logging is dependent on it'''

			print "Attempting Connection"
			server.connect() #This blocks unitl connection is successful 
			print "Connection Established"
			#gain_thread.start()

			while 1:
				server.zero_motors() #Start off in the zero poisition
				feedbacks = server.read_adc()
				server.log_to_file(feedbacks,server.x_zero,server.y_zero)
				server.send_data()
				data = server.get_data() # Listen for commands from client

				if not data:
					pass

				elif data[0] == 'X':

					setpoint = float(data[1:]) #Strip Header, convert to float
					server.OneSetpoint(setpoint,"X")

				elif data[0] == 'Y':

					setpoint = float(data[1:]) #Strip Header, Convert to float
					server.OneSetpoint(setpoint,"Y")

				elif data[0] == 'Z':
					'''Zero the positions'''

					server.zero_motors()

				elif data[0] == 'P':
					'''Do plus sign routine'''

					server.zero_motors()
					#Do the X motor first, then do Y. 
					for point in [30,82,server.x_zero]:
						server.OneSetpoint(point,'X')

					for point in [28,79,server.y_zero]:
						server.OneSetpoint(point,'Y')


				elif data[0] == 'C':

					server.do_circle()
					time.sleep(0.15)
					server.zero_motors()
					print "Done Circle"

				elif data[0] == 'G':
					'''Set new gains'''
					
					gains = []
					msg = data[1:-1]#Strip Header 
					
					for i in msg.split(','):
						gains.append(float(i)) #Extract info
					print 'New gains from client are {}'.format(gains)
					print 'Message is {}'.format(msg)
					print 'Data is {}'.format(data)

					if data[-1] == 'X':
						print 'Setting new X Gains'+str(gains)
						server.x_PID.setKp(gains[0])
						server.x_PID.setKi(gains[1])
						server.x_PID.setKd(gains[2])

					elif data[-1] == 'Y':
						server.y_PID.setKp(gains[0])
						server.y_PID.setKi(gains[1])
						server.y_PID.setKd(gains[2])

				elif data[0] == 'L':

					server.send_gains()

				elif data[0] == 'Q':
					#Do cross sign, then zero out
		
					points_list = [(26,74),(26,23),(79,73),(79,23),(server.x_zero,server.y_zero)]

					for points in points_list:
						print points
						server.move_both(points)

					print "Done Cross"



		except socket.error as e:
				#Catches a connection error 
				print "Connection Error. Attempting reset..." 
from DualPosCtrl import sendToMotorX,sendToMotorY
#import the roboclaw and ADC and all those other things in a different file.
#This code is just for the control logic. 

xSetPoint = 0
ySetPoint = 0

xFeedback = 0
yFeedback = 0 
address = address

outMax = 127
outmin = -127
#Need these and others for roboclaw

zeropoint = 0.1
errorRange = 0.01
#experimentally define some zeropoints and errors based on ADC feedback. Need more testing...
dataSendSock
dataSendPort = 12345

dataGetSock
dataGetSock = 6969 
BUFF_SIZE = 8

def checkADC()

	try: 
		xFeedback = adc.readvoltage(1)
		yFeedback = adc.readvoltage(2)

	except adcError:
		#I have no idea what kind of error would be raised, but hey just being safe
		break

	volts = (xFeedback,yFeedback)
	
	return volts


def MotorMove(setpoint,feedback,motor): 

	#computes proportional error based on current feedback 
	#the motor argument will define if it's X or Y to be moved. 

	error = setpoint - feedback 
	outPut = Kp*error

	#if the proportional error, known here as outPut, is less than some error range, break out of this function
	#this should prevent little oscillations around a setpoint 
	#errorRange should be pretty close to zero. 

	if abs(outPut) < errorRange
		return 2

	#if the proposed amount to move is larger than what the motors can handle
	#then just do the maximum/minumum
	if propError > outMax:
		outPut = outMax
	elif loopOutput < outMin:
		outPut = outMin

	#Check whether to send forward or backwards based the sign of outPut
	if outPut > 0:
		if motor == 'X'
			roboclaw.ForwardM1(address,outPut)
		elif motor == 'Y'
			roboclaw.ForwardM2(address,outPut)

	elif outPut < 0:
		outPut = abs(outPut)
		#go backwards the same magnitude as forwards
		if motor == 'X'
			roboclaw.BackwardM1(address,outPut)
		elif motor == 'Y'
			roboclaw.BackwardM2(address,outPut)

	return 1

def routineA():
	
	#calls MotorMove as much as needed

def routineB():
	#calls MotorMove as much as needed
def Zeroing():

	#Individually checks X and Y setpoints and brings them to zero.
	#We need to see if the calls to roboclaw are blocking or not. VERY IMPORTANT
	try:

		xCheck = MotorMove(zeropoint xFeedback, 'X')
		yCheck = MotorMove(zeropoint,yFeedback, 'Y')

		while xCheck !=2  and yCheck != 2:

			#This loop will only be broken out of if the difference between the zeropoint 
			#and the feedbacks are less than the specified error range.
			#even if X is at zero, commands will still be sent until both are 
			#at zero, and vice versa.
			xFeedback = checkADC[0]
			yFeedback = checkADC[1]
			xCheck = MotorMove(zeropoint xFeedback, 'X')
			yCheck = MotorMove(zeropoint,yFeedback, 'Y')
			
	except error: 
		#I don't expect this path to be taken, but we need to test what errors can be raised
		#if we attempt to send the actuators to zero. This path will handle that. 
		break

main():
	
	#initalize the actuators to zero. 
	Zeroing() 

	try:
		
		msg = dataGetSock.recvfrom(BUFF_SIZE)
		#Check for input from datasocket
		if msg[0] = 'A':

			try: 
				routineA() 
				#Calls the predefined routine

			except error: 

				break
				#This will be a catch all path, where any sort of error resulting from an attempted
				#routine execution will break the routine call
				#'break' will take us out of this current if loop, and on to the "B" check

		elif msg[0] = 'B':
			
			try: 
				routineB() 
				#Calls the predefined routine

			except error: 

				break 
				#same logic as in routineA(). 
				#Not sure what sort of errors might be raised. Need to test!

		elif msg[0] = 'X': 

			#Checks if there's a header in msg that will define this to be an Xsetpoint update
			#This header will be defined in the GUI send command. 

			xSetpoint = msg[1]
			xFeedback = checkADC()[0]

			try:

				xCheck = MotorMove(xSetpoint,xFeedback,'X')
				while xCheck != 2:
					#This loop will run continously until MotorMove returns a 2, which indicats that
					#the error between the setpoint and feedback is less than the errorRange, which is 
					#close to zero.
					xCheck = MotorMove(xSetpoint,xFeedback,'X')
									
			except error:
				#This path is taken if MotorMove can't be called for some reason. 'error' will be replaced 
				#by the type of errors that could be raised.
				break
			
		elif msg[0] = 'Y'

			
			ySetpoint = msg[1]
			yFeedback = checkADC()[1]

			try:

				yCheck = MotorMove(ySetpoint,yFeedback,'Y')
				while yCheck != 2:
					#This loop will run continisouly until MotorMove returns a 2, which indicated that
					#the error between the setpoint and feedback is less than the errorRange, which is 
					#close to zero.
					yCheck = MotorMove(ySetpoint,yFeedback,'X')
									
			except error:
				#same logic as in the X if statement
				break
			
	except socketError:

		#This path is taken if msg can't be defined, which will happen if no setpoint or routine call is sent from GUI
		break
		#This break, if called, brings us to the next try/except block. 

	try: 

		# If the feedbacks match the setpoints +- errors, then this loop will run forever
	    # and send the feedBacks are sent to the client. 
	    #IMPORTANT: This loop's validity is contingent on XFeedBack and YFeedback being accurate. This needs testing too.

		while (xFeedback - errorRange) < xSetPoint < (xFeedback + errorRange) and \
			  (yFeedback - errorRange) < ySetPoint < (yFeedback + errorRange)

			try:
				dataSendSock.sendto(str(xFeedback,yFeedback),(clientIP,dataSendPort))
			except socketError:
				continue

			xFeedback = checkADC()[0]
			yFeedback = checkADC()[1]

			if dataGetSock.recvfrom(BUFF_SIZE)[0]:
				#This break breaks us out of the while loop, and ends main(). 
				#BUT!!
				#main() is itself in a while loop, so we start back at the top with Zeroing().
				break
			elif: 
				continue
			 
	except error:
			#Same story as before, just a safety catch.			
if name = "__main__":
	#just in case this script ever needs to be imported, use this format 
	while 1:
	#main is always going to be run. 
		main()
		

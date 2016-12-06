from DualPosCtrl import sendToMotorX,sendToMotorY
#import the roboclaw and ADC and all those other things in a different file.
#This code is just for the control logic. 

xSetPoint = 0
ySetPoint = 0

xFeedback = 0
yFeedback = 0 
address = address
#Need these and others for roboclaw

zeropoint = 0.1
errorRange = 0.01
#experimentally define some zeropoints and errors based on ADC feedback. Need more testing...

def routineA():

	#Does a specific routine that updates global setpoint variables
	#calls sendToMotorX and sendToMotorY as needed

def routineB():

	#Does a specific routine that updates global setpoint variables
	#calls sendToMotorX and sendToMotorY as needed
def Zeroing():

	#Individually checks X and Y setpoints and brings them to zero.
	#We need to see if the calls to roboclaw are blocking or not. VERY IMPORTANT

	try:
		if xFeedback and yFeedback > zeropoint:
			xSetPoint = zeropoint
			ySetPoint = zeropoint
			sendToMotorX(address,xSetPoint)
			sendToMotorY(address,ySetPoint)
			#sends commands to get X and Y actuators to zero. These commands will obviously
			#be more sophisticated, based on MC functions. This is just a rough sketch of the logic

		elif xFeedback > zeropoint and yFeedback <= zeropoint

			xSetPoint = zeropoint 
			sendToMotorX(address,xSetPoint)

		elif yFeedback > zerpoint and xFeedback <= zeropoint

			ySetPoint = zeropoint 
			sendToMotorY(address,ySetPoint)
			
	except error: 
			break
			#I don't expect this path to be taken, but we need to test what errors can be raised
			#if we attempt to send the actuators to zero. This path will handle that. 

main():

	while 1: 
	 # This loop will contrinuously run. 
	 # If nothing is coming through the datasocket, then this loop will continuously call Zeroing()
	 # PS Apparently while 1: is faster than while True: ...


		try:
			
			msg = inputFromSocket 
			#Check for input from datasocket

			if msg = 'A':

				try: 
					routineA() 
					#Calls the predefined routine

				except error: 

					break
					#This will be a catch all path, where any sort of error resulting from an attempted
					#routine execution will break the routine call
					#'break' will take us out of this current if loop, and on to the "B" check

			elif msg = 'B':
				
				try: 
					routineB() 
					#Calls the predefined routine

				except error: 

					break 
					#same logic as in routineA(). 
					#Not sure what sort of errors might be raised. Need to test!

			elif msg[0] = 'X': 

				try:
					xSetpoint = msg
					sendToMotorX(address,xSetpoint)
					#Checks if there's a header in msg that will define this to be an Xsetpoint update
					#This header will be defined in the GUI send command. 
				except error:

					break
				
			elif msg[0] = 'Y'

				try:
					ySetPoint = msg
					sendToMotorY(address,ySetPoint)
					#Checks if there's a header in msg that will define this to be an Ysetpoint update

				except error:

					break
				
		except socketError:

			#This path is taken if msg can't be defined, which will happen if no setpoint or routine call is sent from GUI
			break 
			#This break, if called, brings us to the next try/except block. 

		try: 
			
			while xFeedback = ( xSetPoint - errorRange < xSetPoint < xSetPoint + errorRange) and \
			      yFeedback = ( ySetPoint - errorRange < ySetPoint < ySetPoint + errorRange):

		      dataSendSock.sendto("All is going well",(clientIP,dataSendPort))

		      # If the feedbacks match the setpoints +- errors, then this loop will run forever
		      # and send a happy message to the client. 

		      #IMPORTANT: This loop's validity is contingent on XFeedBack and YFeedback being accurate. This needs testing too.

		except error:
			#Same story as before, just a safety catch.
			#This path however will only be taken if the feedbacks don't match the setpoints.
			#Thus, we zero both actuators out.

			Zeroing() 

	
if name = __main__:
	#just in case this script ever needs to be imported, use this format 
	main()

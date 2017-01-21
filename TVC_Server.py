#!/usr/bin/python
#
# This file is part of IvPID.
# Copyright (C) 2015 Ivmech Mechatronics Ltd. <bilgi@ivmech.com>
#
# IvPID is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IvPID is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#title           :test_pid.py
#description     :python pid controller test
#author          :Caner Durmusoglu
#date            :20151218
#version         :0.1
#notes           :
#python_version  :2.7
#dependencies    : matplotlib, numpy, scipy
#==============================================================================

import PID
from time import time,sleep
from datetime import datetime
import logging 
import random
import multiprocessing
import socket
import numpy as np
import roboclaw
from ABE_ADCPi import ADCPi
from ABE_helpers import ABEHelpers

# Get the ADC fired up
i2c_helper = ABEHelpers()
bus = i2c_helper.get_smbus()
adc = ADCPi(bus, 0x68, 0x69, 12)

# Open serial port for Motor Controller
roboclaw.Open("/dev/ttyAMA0",38400)
print("Serial port open!")
address = 0x80

#Maximum values that can be sent to the MC.
outMax = 127
outMin = -127

'''
Logging format is:
TIMESTAMP,XSETPOINT,XFEEDBACK,YSETPOINT,YFEEDBACK

The timestamp will be Unix timestamp. 
'''

#Change this to level = DEBUG to log everything. Filemode = 'w' makes the log overwrite
logging.basicConfig(filename='positions.log',level=logging.DEBUG,filemode = 'w') 

#Networking Setup
data_get_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
data_get_port = 12345
data_get_sock.bind(('',data_get_port))

data_send_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
data_send_port = 6969
client_IP = "10.42.0.1" #This is Christian's Laptop Ubuntu IP
BUFF_SIZE = 128
data_send_sock.connect((client_IP,data_send_port))

#Make the connections non blocking.
data_send_sock.setblocking(0)
data_get_sock.setblocking(0)

print "Socket Bound: Awaiting Input"

kp = 500
ki = 1.5
kd = 0.001

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def test_pid(P,I,D,L,send_end):

    pid = PID.PID(P, I, D)

    pid.SetPoint=0.0
    pid.setSampleTime(0.01)

    END = L
    feedback = 0

    feedback_list = []
    time_list = []
    setpoint_list = []

    for i in range(1, END):
        pid.update(feedback)
        output = pid.output
        if pid.SetPoint > 0:
            # feedback += (output - (1/i))
            feedback += output + 0.1*random.random()
        if i>9:
            pid.SetPoint = 1
        if i > 50:
            pid.SetPoint = 3.5
        if i > 150:
            pid.SetPoint = 2.0
        time.sleep(0.02)
        logging.debug("Position is {}".format(feedback))

        feedback_list.append(feedback)
        setpoint_list.append(pid.SetPoint)
        time_list.append(i)
     
    send_list = (feedback_list,setpoint_list) 

    send_end.send(send_list)

def run_routine(setpoints,P,I,D,motor):

    pid = PID.PID(P,I,D)

    #Don't think I need this line, but keeping it in case. 
    #pid.SetPoint=0.0
    pid.setSampleTime(sample_time)   

    #Get initial feedbacks
    if motor == 'X':
        adc_num = 1
        feedback = adc.read_voltage(adc_num)
        print feedback    
    elif motor == 'Y':
        adc_num = 2
        feedback = adc.read_voltage(adc_num)

    #Loop through all setpoints passed to the function, update PID, call the MC
    for point in setpoints: 

        pid.SetPoint = point
        pid.update(feedback)
        output = pid.output 
        
        if output > outMax:
            output = outMax
        elif output < outMin:
            output = outMin

        #Check whether to send forward or backwards based the sign of outPut

        if output >= 0:
            if motor == 'X':
                roboclaw.ForwardM1(address,int(output))
            elif motor == 'Y':
                roboclaw.ForwardM2(address,int(output))

        elif output < 0:
            output = abs(output)
            #go backwards the same magnitude as forwards
            if motor == 'X':
                roboclaw.BackwardM1(address,int(output))
            elif motor == 'Y':
                roboclaw.BackwardM2(address,int(output))

        #Get feedback, log what's going on, keep looping until all setpoints have been depleted. 
        feedback = adc.read_voltage(adc_num)
        logging.debug("{},{},{}".format(time.time(),pid.SetPoint,output))

def one_setpoint(setpoint,feedback,P,I,D,motor):

    #Maybe put this in main loop??
    pid = PID.PID(P,I,D)

    if setpoint > 4.75: 
        setpoint = 4.75
    elif setpoint < 0.12:
        setpoint = 0.12

    pid.SetPoint=setpoint
    pid.setSampleTime(sample_time)

    pid.update(feedback)

    output = pid.output

    
    if output > outMax:
        output = outMax
    elif output < outMin:
        output = outMin

    #Check whether to send forward or backwards based the sign of outPut

    if output >= 0:
        if motor == 'X':
            roboclaw.ForwardM1(address,int(output))
        elif motor == 'Y':
            roboclaw.ForwardM2(address,int(output))

    elif output < 0:
        output = abs(output)
        #go backwards the same magnitude as forwards
        if motor == 'X':
            roboclaw.BackwardM1(address,int(output))
        elif motor == 'Y':
            roboclaw.BackwardM2(address,int(output))

    #logging happens in main loop.

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":

    #The PID controlling sampling time, gains, and allowed error between setpoint and feedback 
    sample_time = 0.000001
    kp = 1000
    ki = 1
    kd = 0.001
    #allowed_error = 0.005
    #Initital Starting out point for the actuators
    x_setpoint = 0.0
    y_setpoint = 0.0 
    
    logging.info("Starting TVC Control. Time is {}".format(datetime.now()))

    while 1:

        #Initializing message to be false after each loop. 
        msg = False

        #Get feedbac
        x_feedback = adc.read_voltage(1)
        y_feedback = adc.read_voltage(2)
        print "x_feedback is {}, x_setpoint is {},y_feedback is {}, y_setpoint is {}".format(x_feedback,x_setpoint,y_feedback,y_setpoint)

        try:
            msg = data_get_sock.recvfrom(BUFF_SIZE)[0]
            print "msg received: {}".format(msg)

        except socket.error:
            #This means nothing was sent. Since the socket is non-blocking, trying to receive anything 
            #will raise a socket.error exception instead of causing the program to hang. 
            pass

        one_setpoint(x_setpoint,x_feedback,kp,ki,kd,'X')
        one_setpoint(y_setpoint,y_feedback,kp,ki,kd,'Y')

        logging.debug("{},X{},{},Y{},{}".format(time(),x_setpoint,x_feedback,y_setpoint,y_feedback))
        send_packet = "{},{}".format(x_feedback,y_feedback)
        
        try:
            data_send_sock.send(send_packet)
            #print "Data Sent"
        except socket.error as e:
            print e     


        if msg:

            logging.info("Order received. Message is {}".format(msg))

            if msg[0] == "X":

                try: 
                    x_setpoint = float(msg[1:]) #Strip header from messag, and cast to float
                except ValueError as e: 
                    logging.info("Couldn't read setpoint. Probably sent a blank message through the client")

            if msg[0] == "Y":

                try: 
                    y_setpoint = float(msg[1:])#Strip header from message, and cast to float
                except ValueError as e: 
                    logging.info("Couldn't read setpoint. Probably sent a blank message through the client") 

            if msg[0] == 'Z':

                x_setpoint = 0.0
                y_setpoint = 0.0

            if msg[0] == "P":

                logging.info("Plus Routine Started")



                    
            if msg[0] == "C": #XMax Ymax

                logging.info("XMax YMax Routine Started") 

                #First zeroing both: 

                x_setpoint = 0.0
                y_setpoint = 0.0

                one_setpoint(x_setpoint,x_feedback,kp,ki,kd,'X')
                one_setpoint(y_setpoint,y_feedback,kp,ki,kd,'Y')

                sleep(3) #Wait for actuators to zero out. 

                #First do the X actuator

                step_length = 50 # The tweakable parameter for distance in setpoints 

                t = np.linspace(0,4.72,50)
                for point in t:

                    x_feedback = adc.read_voltage(1) 
                    one_setpoint(point,x_feedback,kp,ki,kd,'X')
                    logging.debug("{},X{},{},Y{},{}".format(time(),point,x_feedback,y_setpoint,y_feedback))
                    print "x_feedback is {}, x_setpoint is {},y_feedback is {}, y_setpoint is {}".format(x_feedback,point,y_feedback,y_setpoint)

                t = np.linspace(4.72,0,50)
                for point in t:
                    x_feedback = adc.read_voltage(1) 
                    one_setpoint(point,x_feedback,kp,ki,kd,'X')
                    logging.debug("{},X{},{},Y{},{}".format(time(),point,x_feedback,y_setpoint,y_feedback))
                    print "x_feedback is {}, x_setpoint is {},y_feedback is {}, y_setpoint is {}".format(x_feedback,point,y_feedback,y_setpoint)


                #Then do the Y actuator

                t = np.linspace(0,4.72,50)
                for point in t:

                    y_feedback = adc.read_voltage(2) 
                    one_setpoint(point,y_feedback,kp,ki,kd,'Y')
                    logging.debug("{},X{},{},Y{},{}".format(time(),x_setpoint,x_feedback,point,y_feedback))
                    print "x_feedback is {}, x_setpoint is {},y_feedback is {}, y_setpoint is {}".format(x_feedback,point,y_feedback,y_setpoint)

                t = np.linspace(4.72,0,50)

                for point in t:
                    y_feedback = adc.read_voltage(2) 
                    one_setpoint(point,y_feedback,kp,ki,kd,'Y')
                    logging.debug("{},X{},{},Y{},{}".format(time(),x_setpoint,x_feedback,point,y_feedback))
                    print "x_feedback is {}, x_setpoint is {},y_feedback is {}, y_setpoint is {}".format(x_feedback,point,y_feedback,y_setpoint)












                


'''
Comment Graveyard

Create Pipes for messaging back and forth. False argument means one-way communication.
x_recv_end, x_send_end = multiprocessing.Pipe(False)
y_recv_end, y_send_end = multiprocessing.Pipe(False)

x_temp = x_recv_end.recv()
y_temp = y_recv_end.recv()

x_results = x_temp[0]
y_results = y_temp[0]

x_setpoints = x_temp[1]
y_setpoints = y_temp[1]
'''

            
    

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np 
import Tkinter as Tk
import random
import socket
import tkMessageBox
import threading 
import sys
import Queue

#Initial figure. This figure will be updated with matplotlib.animatinon.FuncAnimation
f = plt.figure()
ax = plt.axes(xlim=(-5,105), ylim=(-5,105))
line, = ax.plot(0,0, 'r+',markersize = 10)
ax.axhline(y = 56,xmin = 0, xmax = 100,color = 'black')
ax.axvline(x = 57,ymin = 0 , ymax = 100,color = 'black')
ax.axvline(x= 0,ymin = 0,ymax = 100,color = 'black')
ax.axvline(x= 100,ymin = 0,ymax = 100,color = 'black')
ax.axhline(y = 100,xmin = 0, xmax = 100,color = 'black')	
ax.axhline(y = 0,xmin = 0, xmax = 100,color = 'black')

#Networking params
server_address = ("10.42.0.87",6969)
BUFF = 64

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
This class has the thread to get info from the TVC server. Once the connection is made in the 
GUI, the get_thread is started in the 
'''
class GetInfo():

	def __init__(self):

		self.x_data = 0
		self.y_data = 0
		self.get_thread = threading.Thread(target = self.get_data)
		self.get_thread.daemon = True

		self.graph_queue = Queue.LifoQueue()

	def create_connection(self):

		try:
			self.s = socket.create_connection(server_address,timeout = 0.1)
			return "success"
		except socket.error as e:
			return e


	def get_random_data(self):
		'''Used for testing'''

		self.x_data = 4*random.random()
		self.y_data = 5*random.random()


	def get_data(self):

		try:
			data = self.s.recv(BUFF).split(',')
			if len(data) == 2:
				self.x_data = float(data[0]) #Strip parens off and convert to float
				self.y_data = float(data[1])
		except (socket.error,NameError,AttributeError) as e:
			return e

	def send_data(self,msg):

		print "I'm sending {}".format(msg)
		self.s.send(msg)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GUI:

	def __init__(self,master):
		'''All the inital parameters for the GUI'''

		self.master = master
		self.get_info = GetInfo() #Have an instance of the GetInfo class in this class, to use the networking

		quit_button = Tk.Button(master,text = "Quit",command = self.quit)
		quit_button.grid(row = 0, column = 0)
	
		connect_button = Tk.Button(master,text = "Connect",command = self.connect)
		connect_button.grid(row = 0, column = 1)

		xEntryVar = Tk.StringVar()  # Need to initialize a StringVar
		xEntry = Tk.Entry(master, textvariable=xEntryVar)
		xEntry.grid(row = 2, column = 1)

		x_SendButton = Tk.Button(master, text = 'Set X Set Point',command = lambda:self.send_msg(xEntry.get(),'X'))
		x_SendButton.grid(row = 2, column = 0)

		self.x_label = Tk.Label(master, text = "Current X Position")
		self.x_label.grid(row = 5, column = 0)

		y_Entry = Tk.Entry(master)
		y_Entry.grid(row = 3, column = 1)

		y_SendButton = Tk.Button(master, text = 'Set Y Set Point',command = lambda:self.send_msg(yEntry.get(),'Y'))
		y_SendButton.grid(row = 3, column = 0)

		currentXLabel = Tk.Label(master, text = "Current X Location")

		zero_Button = Tk.Button(master, text = 'Zero Actuators', command = lambda:self.send_msg('0','Z'))
		zero_Button.grid(row = 1, column = 1)

		plus_Button = Tk.Button(master, text = 'Plus Sign', command = lambda:self.send_msg('0','P'))
		plus_Button.grid(row = 4, column = 0)

		circle_Button = Tk.Button(master, text = 'Circle',command = lambda:self.send_msg('0','C'))
		circle_Button.grid(row = 4, column = 1)

		canvas = FigureCanvasTkAgg(f, self.master)
		canvas.show()
		canvas.get_tk_widget().grid(row = 6, column = 0, columnspan = 2)

		self.connection_status = False

	def connect(self):
		'''Creates connection between server and client'''
		if self.connection_status == False: #This prevents connection reset. 
			response = self.get_info.create_connection()
			if response == "success":
				self.connection_status = True
				msg = tkMessageBox.showinfo('','Connection to Server Successful')
			else:
				msg = tkMessageBox.showerror("Connection Error","Couldn't connect to server. Error is: \n{}".format(response))

		elif self.connection_status == True:
			msg = tkMessageBox.showerror("","You should be connected already!")

	def send_msg(self,msg,motor):
		'''Sends the message from the client to the server'''

		if self.connection_status == True: 
			msg = motor+msg #This adds the header to the message, so the server knows which one to move
			self.get_info.send_data(msg)
		else:
			msg = tkMessageBox.showerror('Connection Error','Please connect first')

	def animate(self):
		'''Starts the FuncAnimation'''

		anim = animation.FuncAnimation(f,self.animate_function,interval = 20,frames = 200,blit = True,init_func= self.init_ani)
		f.canvas.show()

	def init_ani(self):
		'''Initial params for plot that'll be updated below'''

		line.set_data([],[])
		return line,

	
	def animate_function(self,i):
		'''Retrieves values from other class, updates plot'''

		try:
			self.get_info.get_data()
		except ValueError as e: 
			print e 	

		x = self.get_info.x_data
		y = self.get_info.y_data

		print "x = {}, y = {}".format(x,y)

		if (x < 105 and x > 0) and (y < 105 and y > 0): 
			line.set_data(x,y)
			return line,
		return line,

	def quit(self):
		'''Kills application'''

		if self.get_info.get_thread.isAlive():
			self.get_info.get_thread.join() #Joining means putting the threads together
		self.master.destroy()
		self.master.quit()
		sys.exit(1)


root = Tk.Tk()
GUIPart = GUI(root)
root.mainloop()

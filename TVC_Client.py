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
import re

#Initial figure. This figure will be updated with matplotlib.animatinon.FuncAnimation
f = plt.figure()
ax = plt.axes(xlim=(-5,105), ylim=(-5,105))
line, = ax.plot(0,0, 'r+',markersize = 10)
#Zero lines
ax.axhline(y = 51,xmin = 0, xmax = 100,color = 'black')
ax.axvline(x = 54,ymin = 0 , ymax = 100,color = 'black')
#Borders
ax.axvline(x= 0,ymin = 0,ymax = 50,color = 'black')
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

		#self.graph_queue = Queue.LifoQueue() Useless

	def create_connection(self):

		try:
			self.s = socket.create_connection(server_address,timeout = 0.1)
			return "success"
		except socket.error as e:
			return e

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
		self.connection_status = False #Initialize this to false, make true when connection is success

		self.ani_thread = threading.Thread(target = self.animate())

		quit_button = Tk.Button(master,text = "Quit",command = self.quit)
		quit_button.grid(row = 0, column = 0)
	
		connect_button = Tk.Button(master,text = "Connect to Server",command = self.connect)
		connect_button.grid(row = 0, column = 1)

		xEntryVar = Tk.StringVar()  # Need to initialize a StringVar
		xEntry = Tk.Entry(master, textvariable=xEntryVar)
		xEntry.grid(row = 1, column = 1)

		x_SendButton = Tk.Button(master, text = 'Set X Set Point',command = lambda:self.send_msg(xEntry.get(),'X'))
		x_SendButton.grid(row = 1, column = 0)

		self.y_Entry = Tk.Entry(master)
		self.y_Entry.grid(row = 2, column = 1)

		y_SendButton = Tk.Button(master, text = 'Set Y Set Point',command = lambda:self.send_msg(self.y_Entry.get(),'Y'))
		y_SendButton.grid(row = 2, column = 0)

		zero_Button = Tk.Button(master, text = 'Zero Actuators', command = lambda:self.send_msg('0','Z'))
		zero_Button.grid(row = 4, column = 1)

		plus_Button = Tk.Button(master, text = 'Plus Sign', command = lambda:self.send_msg('0','P'))
		plus_Button.grid(row = 3, column = 0)

		circle_Button = Tk.Button(master, text = 'Circle',command = lambda:self.send_msg('0','C'))
		circle_Button.grid(row = 3, column = 1)

		#~~~~~~~~~~~~~~
		#X Gain Tuning 

		x_Kp_entry_label = Tk.Label(master, text = "Current X Kp")
		x_Ki_entry_label = Tk.Label(master, text = "Current X Ki")
		x_Kd_entry_label = Tk.Label(master, text = "Current X Kd")
		self.x_Kp_entry_box = Tk.Entry(master)
		self.x_Ki_entry_box = Tk.Entry(master)
		self.x_Kd_entry_box = Tk.Entry(master)

		x_gain_set_button = Tk.Button(master, text = "Set X Gains", command = lambda:self.set_gains('X'))
		x_gain_set_button.grid(row = 6, column = 3)

		x_gain_listen_button = Tk.Button(master,text = 'Retrieve X Gains\n From Server',command = lambda:self.listen_for_gains())
		x_gain_listen_button.grid(row = 6, column = 2)

		x_kp_label = Tk.Label(master,text = "Set New X Kp")
		x_ki_label = Tk.Label(master,text = "Set New X Ki")
		x_kd_label = Tk.Label(master,text = "Set New X Kd")

		self.x_current_kp_value_var = Tk.StringVar()
		self.x_current_kp_value_var.set('0')
		self.x_current_kp_value_label = Tk.Label(master,text = self.x_current_kp_value_var.get())
		self.x_current_ki_value_var = Tk.StringVar()
		self.x_current_ki_value_var.set('0')
		self.x_current_ki_value_label = Tk.Label(master, text = self.x_current_ki_value_var.get())
		self.x_current_kd_value_var = Tk.StringVar()
		self.x_current_kd_value_var.set('0')
		self.x_current_kd_value_label = Tk.Label(master, text = self.x_current_kd_value_var.get())

		self.x_current_kp_value_label.grid(row = 0,column = 3)
		self.x_current_ki_value_label.grid(row = 1,column = 3)
		self.x_current_kd_value_label.grid(row = 2,column = 3)
		self.x_Kp_entry_box.grid(row = 3, column = 3)
		self.x_Ki_entry_box.grid(row = 4, column = 3)
		self.x_Kd_entry_box.grid(row = 5, column = 3)
		
		x_Kp_entry_label.grid(row = 0, column = 2)
		x_Ki_entry_label.grid(row = 1, column = 2)
		x_Kd_entry_label.grid(row = 2, column = 2)
		x_kp_label.grid(row = 3, column = 2)
		x_ki_label.grid(row = 4, column = 2)
		x_kd_label.grid(row = 5, column = 2)

		#~~~~~~~~~~~~~~
		#Y Gain Tuning 
		y_Kp_entry_label = Tk.Label(master, text = "Current Y Kp")
		y_Ki_entry_label = Tk.Label(master, text = "Current Y Ki")
		y_Kd_entry_label = Tk.Label(master, text = "Current Y Kd")
		self.y_Kp_entry_box = Tk.Entry(master)
		self.y_Ki_entry_box = Tk.Entry(master)
		self.y_Kd_entry_box = Tk.Entry(master)

		y_kp_label = Tk.Label(master,text = "Set Y New Kp")
		y_ki_label = Tk.Label(master,text = "Set Y New Ki")
		y_kd_label = Tk.Label(master,text = "Set Y New Kd")

		self.y_current_kp_value_var = Tk.StringVar()
		self.y_current_kp_value_var.set('0')
		self.y_current_kp_value_label = Tk.Label(master,text = self.y_current_kp_value_var.get())
		self.y_current_ki_value_var = Tk.StringVar()
		self.y_current_ki_value_var.set('0')
		self.y_current_ki_value_label = Tk.Label(master, text = self.y_current_ki_value_var.get())
		self.y_current_kd_value_var = Tk.StringVar()
		self.y_current_kd_value_var.set('0')
		self.y_current_kd_value_label = Tk.Label(master, text = self.y_current_kd_value_var.get())

		self.y_current_kp_value_label.grid(row = 0,column = 5)
		self.y_current_ki_value_label.grid(row = 1,column = 5)
		self.y_current_kd_value_label.grid(row = 2,column = 5)
		self.y_Kp_entry_box.grid(row = 3, column = 5)
		self.y_Ki_entry_box.grid(row = 4, column = 5)
		self.y_Kd_entry_box.grid(row = 5, column = 5)
		
		y_Kp_entry_label.grid(row = 0, column = 4)
		y_Ki_entry_label.grid(row = 1, column = 4)
		y_Kd_entry_label.grid(row = 2, column = 4)
		y_kp_label.grid(row = 3, column = 4)
		y_ki_label.grid(row = 4, column = 4)
		y_kd_label.grid(row = 5, column = 4)

		y_gain_set_button = Tk.Button(master, text = "Set YGains", command = lambda:self.set_gains('Y'))
		y_gain_set_button.grid(row = 6, column = 5)

		y_gain_listen_button = Tk.Button(master,text = 'Retrieve Y Gains\n From Server',command = lambda:self.listen_for_gains())
		y_gain_listen_button.grid(row = 6, column = 4)

		#~~~~~~~~~~~~~~

		canvas = FigureCanvasTkAgg(f, self.master)
		canvas.show()
		canvas.get_tk_widget().grid(row = 7, column = 0, columnspan = 6)

	def connect(self):
		'''Creates connection between server and client'''
		if self.connection_status == False: #This prevents connection reset. 
			response = self.get_info.create_connection()
			if response == "success":
				self.connection_status = True
				msg = tkMessageBox.showinfo('','Connection to Server Successful')
				self.ani_thread.start()
				#self.animate()
			else:
				msg = tkMessageBox.showerror("Connection Error","Couldn't connect to server. Error is: \n{}".format(response))

		elif self.connection_status == True:
			msg = tkMessageBox.showerror("","You should be connected already!")
			
	def set_gains(self,motor):
		'''Function to extract gains from boxes and set those values as the new gains on the server'''

		if motor == 'X':

			x_kp = self.x_Kp_entry_box.get()
			x_ki = self.x_Ki_entry_box.get()
			x_kd = self.x_Kd_entry_box.get()

			msg = str(x_kp)+','+str(x_ki)+','+str(x_kd)+'X'

		elif motor == 'Y':

			y_kp = self.y_Kp_entry_box.get()
			y_ki = self.y_Ki_entry_box.get()
			y_kd = self.y_Kd_entry_box.get()

			msg = str(y_kp)+','+str(y_ki)+','+str(y_kd)+'Y' #Concatenate new gains into a message, and send off		

		print msg
		self.send_msg(msg,'G') #Sends new gains to the TVC 

	def listen_for_gains(self):

		if self.connection_status == True:
			self.ani_thread.join() #T
			print "Animation Stopped"
			self.get_info.s.send('L0')
			for i in range(5): #Try a couple of times to listen for the gains
				response = self.get_info.s.recv(BUFF)
				if response[0] == 'G': #Header for gain message
					print "GOT GAINZ BOYZZZ"+response
					new_gains = []
					try:
						gains = re.findall('G.+(?=GEnd)',response)[0]#Match the gain message syntax from the server
						for i in gains[1:].split(','):
							new_gains.append(float(i))
					except IndexError as e:
						print e
			self.x_current_kp_value_label.config(text = new_gains[0])
			self.x_current_ki_value_label.config(text = new_gains[1])
			self.x_current_kd_value_label.config(text = new_gains[2])
			self.y_current_kp_value_label.config(text = new_gains[3])
			self.y_current_ki_value_label.config(text = new_gains[4])
			self.y_current_kd_value_label.config(text = new_gains[5])
		else: 
			msg = tkMessageBox.showerror('','Please connect to the server first')
		
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

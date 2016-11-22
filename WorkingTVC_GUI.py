import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")
from matplotlib import style
import Tkinter as Tk	
import random 
import threading
import Queue
import time
import socket
import numpy as np
import random

style.use("ggplot") 		
FONT = ("Helvetica", 12)

class GuiPart(Tk.Tk):

	def __init__(self,master,queue,endCommand):
		
		self.queue = queue
		
		#Extensive __init__ to set up buttons, grid locations, subplots, etc. Considering putting this in a seperate file.
		
		gridDict = {	'byeButton':		[0,0],		#[row,column]
				'GreetButton':		[0,1],
				'CurrentXLabel':	[1,0],
				'CurrentXDisplay':	[1,1],
				'CurrentYLabel':	[2,0],
				'CurrentYDisplay':	[2,1],
				'XSetPointLabel':	[3,0],
				'XEntry':		[3,1],
				'YSetPointLabel':	[4,0],
				'YEntry':		[4,1]
			   }
		
		bye_button = Tk.Button(master,text = 'Goodbye', command = endCommand, font = FONT)
		bye_button.grid(row = gridDict['byeButton'][0], column = gridDict['byeButton'][1])
		
		greet_button = Tk.Button(master, text="Greet", command=self.printstuff,font = FONT)
		greet_button.grid(row = gridDict["GreetButton"][0], column = gridDict["GreetButton"][1])
		
		xEntryVar = Tk.StringVar()  # Need to initialize a StringVar
        	xEntry = Tk.Entry(master, textvariable=xEntryVar)
        	xEntry.grid(row = gridDict['XEntry'][0], column = gridDict['XEntry'][1])
        	
        	xSendButton = Tk.Button(master, text = 'Set X Set Point',command = lambda:self.dataSend(xEntryVar.get()),font = FONT)
        	xSendButton.grid(row = gridDict['XSetPointLabel'][0], column = gridDict['XSetPointLabel'][1])   
        	
        	self.currentXVar = Tk.StringVar()
        	currentXDisplay = Tk.Label(master,textvariable = self.currentXVar,font = FONT)
        	currentXDisplay.grid(row = gridDict['CurrentXDisplay'][0], column = gridDict['CurrentXDisplay'][1])
        	
        	currentXLabel = Tk.Label(master, text = "Current X Location",font = FONT)
        	currentXLabel.grid(row = gridDict["CurrentXLabel"][0], column = gridDict["CurrentXLabel"][1])
        	
        	yEntryVar = Tk.StringVar()  # Need to initialize a StringVar
        	yEntry = Tk.Entry(master, textvariable=yEntryVar)
        	yEntry.grid(row = gridDict['YEntry'][0], column = gridDict['YEntry'][1])
               	
               	ySendButton = Tk.Button(master, text = 'Set Y Set Point',command = lambda:self.dataSend(yEntryVar.get()),font = FONT)
        	ySendButton.grid(row = gridDict['YSetPointLabel'][0], column = gridDict['YSetPointLabel'][1])
        	
        	self.currentYVar = Tk.StringVar()
        	currentYLabel = Tk.Label(master,textvariable = self.currentYVar,font = FONT)
        	currentYLabel.grid(row = gridDict["CurrentYDisplay"][0], column = gridDict["CurrentYDisplay"][1]) 
        	
        	currentYDisplay = Tk.Label(master, text = "Current Y Location",font = FONT)
        	currentYDisplay.grid(row = gridDict["CurrentYLabel"][0], column = gridDict["CurrentYLabel"][1])
        	
        	
        	optionList = ["Routine 1","Routine 2"]
        	self.dropVar= Tk.StringVar()
        	self.dropVar.set("Yes") # default choice
        	self.dropMenu1 = Tk.OptionMenu(master, self.dropVar, *optionList)
        	self.dropMenu1.grid(row = 5, column = 0)
      	
      		#Below is the setup for all the subplots. 
		
		self.canvasFig = plt.figure(1)
        	fig = Figure(figsize=(5, 5), dpi=100)
        	self.figSubPlot1 = fig.add_subplot(211)
        	self.figSubPlot2 = fig.add_subplot(212)
        	x = [0] #initialize plots to zero. 
        	y = [0]
        	fig.subplots_adjust(hspace = 0.5)
        	self.line1, = self.figSubPlot1.plot(x,y)
        	self.line2, = self.figSubPlot2.plot(x,y)
        	self.canvas = FigureCanvasTkAgg(fig, master=master)
		#Subplot Initialization 
        	ax1 = self.canvas.figure.axes[0]
		ax1.set_title("Polar Plot of current Angle",fontsize = 12)
		ax1.set_xlim(-6.5,6.5)
		ax1.set_ylim(-6.5,6.5)
		ax2 = self.canvas.figure.axes[1]
		ax2.set_xlim(-6.5,6.5)
		ax2.set_ylim(-6.5,6.5)
		ax2.set_title('Negative Polar Plot of Current Angle',fontsize = 12)
        	self.canvas.show()
        	self.canvas.get_tk_widget().grid(row = 6 ,column = 0, columnspan = 2, sticky = 'S')
        	
	def processIncoming(self):
	
	
    		while self.queue.qsize():
			try:
		        	msg = self.queue.get(0) 	   #Gets first object from queue
		    		self.currentXVar.set(round(msg,5))
		    		self.currentYVar.set(round(msg,5)) #Updates the X and Y Current Position Labels
				self.getData(msg)		   #Calls the getData function, which extracts data and updates plot
		     		#print msg
			except Queue.Empty:
		        # just on general principles, although we don't
		        # expect this branch to be taken in this case
		        	pass
	
	def getData(self,textdata):
		
		angle = float(textdata)
		self.updatePlot(angle)
	
	def updatePlot(self,angle):
		
		r = 5
		
		x = r * np.cos(angle)
		y = r * np.sin(angle)
		
		self.line1.set_data([0,x],[0,y])
		self.line2.set_data([0,-x],[0,-y])
		 
		self.canvas.draw()
	
	def dataSend(self,message):
		#Send information to Pi. This should probably be happening in ThreadedClient
		datasendsock.sendto(message,(piIP,sendport))
		
class ThreadedClient:
	def __init__(self, master):
		self.master = master
	        # Create the queue
        	self.queue = Queue.Queue()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication)

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    def periodicCall(self):
  
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            #datasendsock.close()
            #datagetsock.close()
            import sys
            sys.exit(1)
            
        self.master.after(50, self.periodicCall)

    def workerThread1(self):
  
        while self.running:

            #msg = datagetsock.recvfrom(8)[0] #8 because that's the number of bytes the server sends about angle info
            msg = random.random()
            time.sleep(0.2)
            self.queue.put(msg)
            pass
    
    def endApplication(self):
        self.running = 0
		

piIP = "10.42.0.208"
datagetsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
getport = 6969
datagetsock.bind(('',getport)) #Client needs to bind to socket, server doesn't 

datasendsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sendport = 12345

#datasock.recvfrom(10)

		
root = Tk.Tk()
GUI = ThreadedClient(root)
root.mainloop()

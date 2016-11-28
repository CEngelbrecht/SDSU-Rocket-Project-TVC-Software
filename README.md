# TVC-GUI
A working repo for the SDSU Rocket Project Galactic Aztec Heavy nascent TVC subsystem.

There will shortly be both the scripts for the motor controller/actuator and ADC/Pi units, as well as the client GUI software. 

Current GUI Issues:

Not sure what the best plotting routine for the X and Y positions are. Scatter plots seem to create lots of lag.


Graphs are not sticky - expanding the GUI doesn't keep the plots on the borders.


Future plans: 

Have predefined routine function calls in ThreadedClient Class, called by a button press in the GUI. 

Clean up script by having init and routines in seperate scripts, to be imported in the main script. 
  
  

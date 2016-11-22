# TVC-GUI
A working repo for the SDSU Rocket Project Galactic Aztec Heavy nascent TVC subsystem.

There will shortly be both the scripts for the motor controller/actuator and ADC/Pi units, as well as the client GUI software. 


Current GUI Issues:

Not sure what the best plotting routine for the X and Y positions are. Scatter plots seem to create lots of lag.
Graphs are not sticky - expanding the GUI doesn't keep the plots on the borders.
The threading doesn't work as planned. The .after call in the Threaded Client Class doesn’t choke the data stream coming  in.
It simply stalls for the specified time instead of calling the queue in the required intervals 
  
  
  

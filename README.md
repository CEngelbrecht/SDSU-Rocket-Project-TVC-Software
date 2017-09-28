# TVC-GUI
A repo for the SDSU Rocket Project Galactic Aztec Heavy nascent TVC subsystem. This 

This contains the scripts for the motor controller/actuator and ADC/Pi units, as well as the client GUI software. 

Dependencies: 
Roboclaw.py, the library from IonMotion that controls the Motor Controller
ABElectronics libraries: specifically the ABE_Helpers.py and ABE_ADCPi. These interface with the ADC currently mounted on the ADC in the TVCBey

Gimbaling the motor was achieved by placing two linear actuators at 90 degrees to each other, and using a PID based feedback control loop to perform a series of predefined routines during the burn. 

The GUI seen below was the interface by which the operator could monitor the position of the actuators, using a TKinter based application, with a graph being updated using Matplotlib's funcanimation function. 



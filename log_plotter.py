import csv
import matplotlib.pyplot as plt
import re
import sys

log_file = sys.argv[1]
print log_file
with open(log_file,'rb') as file:

	reader = csv.reader(file)
	data = []
	for line in reader:
		data.append(line)

time_stamps = [i[0] for i in data]
times = []
for time in time_stamps:
	x, = re.findall(':[\d]+.[\d]+',time)
	times.append(float(x[1:]))
#print times
x_positions = [float(i[1]) for i in data]
y_positions = [float(i[2]) for i in data]
print data[0][0]
plt.plot(times,x_positions,label = 'X')
plt.plot(times,y_positions,label = 'Y')
plt.legend()
plt.show()
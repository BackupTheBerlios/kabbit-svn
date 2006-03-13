#
#
#sysinfo.py
#
# Version 0.1 by Sebastian Moors 23.02.2006
#

import os
import string
import re

def uptime():
	ShellObj = os.popen('/bin/cat /proc/uptime')
	my_buffer=((ShellObj.read()).strip()).split(" ")
	hours=int(my_buffer[0].split('.')[0])/60/60%24
	minutes=int(my_buffer[0].split('.')[0])/60%60
	days=int(my_buffer[0].split('.')[0])/60/60/24
	return str(days) + " days , " + str(hours) + " hours, " + str(minutes) + " minutes";

def hostname():
	ShellObj = os.popen('/bin/hostname')
	hostname= (ShellObj.read()).strip();
	return hostname;

def df(mode):
	#
	#if mode = quit display only mountpoints and free space
	#
	if mode == "quiet":
		ShellObj = os.popen('/bin/df -h')
		free_space = (ShellObj.read()).strip()
		table=free_space.split("\n")

		#delete the info-line
		del table[0]
		my_buffer=[]
		for line in table:
			parts=line.split(" ")
			counter=1
			mountpoint=""
			space=0
			percentage=0

			while space==0 and counter < len(parts):

				if (parts[-(counter)]).strip() != "" and mountpoint=="":
					mountpoint=parts[-(counter)]

				elif (parts[-(counter)]).strip() != "" and percentage==0:
					percentage=parts[-(counter)]

				elif (parts[-(counter)]).strip() != "" and space==0:
					space=parts[-(counter)]
				counter = counter + 1;

			#print counter
			#line=str(mountpoint) + "\t"  + str(space) + "\t" + str(percentage)

			#line='%-20s  %10s   %10s' % (mountpoint, space,percentage)

			line = string.ljust(mountpoint,20)
			line += string.ljust(space,5)
			line += string.ljust(percentage,3)

			my_buffer.append(line)

		free_space=""
		for line in my_buffer:
			free_space += line + "\n"

	else:
		ShellObj = os.popen('/bin/df -h')
		free_space = (ShellObj.read()).strip();




	#print free_space
	return free_space;

def ps():
	services=""
	p=re.compile('\[.+\]')
	ps=os.popen('ps aux', 'r')

	l=[]
	for i in ps:
		if i.split()[10] == 'COMMAND':
			continue
		append_string=i.split()[10]
		try:
			for ii in range (11,len(i.split())):
				append_string+=" "+i.split()[ii]
		except Exception:
			pass

		if not p.match(append_string):
			services+="\n" + append_string
	return services;

def date():
	ShellObj = os.popen('/bin/date')
	date = (ShellObj.read()).strip();
	small_date = date.split(' ');
	return small_date[1]+" "+small_date[2] + " " + small_date[3];

def version():
	ShellObj = os.popen('/bin/cat /proc/version ')
	return (ShellObj.read()).strip();



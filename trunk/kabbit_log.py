#!/usr/bin/python
#kabbit_log.py
import time

class kabbit_logger:
	def __init__(self,path):
		self.access_log_path=path

	def access_log(self,direction,command,jid):
		file=open(self.access_log_path,"a+")
		file.write("[" + str(time.strftime("%d/%B/%Y:%H:%M:%S") + "]") + " [" + direction +"] " +  jid + " " + command + "\n")
		file.close()


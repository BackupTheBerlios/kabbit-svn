
import os
import string
import re
import sys
import time
import fileinput


sys.path.append("/usr/lib/kabbit")
from plugin import plugin

class kabbit_plugin(plugin):
	def __init__(self,config,roster):
		self.descr="simple todolist plugin"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["addtodo"]="adds a todolist entry"
		self.commands["deltodo"]="deletes a todolist entry"
		self.commands["todolist"]="print the todolist"

		self.help = "a tiny todolist"
		self.auth = "private"
		self.roster = roster
		self.todoFile = "/tmp/todo"

	def process_message(self,user,cmd,args):
		
		if cmd == "addtodo":
			return self.addTodo(user,args)
		
		if cmd == "deltodo":
			return self.deleteTodo(user,args)

		if cmd == "todolist" or cmd == "todo":
			return self.listTodo(user)

		

	def addTodo(self,user,args):
		#the command looks like this:
		#addtodo get food : need to get some food tomorrow
		
		user = (str(user).split("/"))[0]

		if args.count(":") <> 1: 
			return "Please use not more or less then one \":\" in your command.It seperates the todo-topic from the description"
		
		topic,descr = args.split(":")
		f = open(self.todoFile,"a")
		f.write(user + ":" +  str(time.time()) + ":" + topic + ":" + descr +"\n") 
		f.close()

		return "a todo with topic '%s' has been added to your list." % topic 

		
	def deleteTodo(self,user,args):
		print "indelete"
		delete = False

		if not os.path.isfile(self.todoFile): return "Your list is empty."


		for line in fileinput.input(self.todoFile,inplace =1):
		 	line = line.strip()
			if (line.split(":"))[0] == (str(user).split("/"))[0] and (line.split(":"))[2]!=args: 
				print line
			else:
				delete=True

		if delete:
			return "The todo entry with the topic '%s' has been deleted." % args 
		else:
			return "No todo entry '%s' found " % args
	
	def listTodo(self,user):
		user = (str(user).split("/"))[0]

		result = ""
		
		if not os.path.isfile(self.todoFile): return "Your todolist is empty." 
		
		file = open(self.todoFile,"r")
		
		for f in file.readlines():
			fUser,time,topic,descr = f.split(":")
			if str(user) == fUser: 
				result = result + topic + "\n"
		file.close()
		if result.strip()=="":
			return "Your todolist is emtpy."
		return result


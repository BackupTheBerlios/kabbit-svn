#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# kabbit.py by Sebastian Moors

# Copyright (C) 2006 Sebastian Moors <sebastian.moors@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
####################################################################
import re
import sys
import xmpp
import os
import signal
import logging
import time
import threading

from Queue import Queue
from string import strip
from os import stat

#the config module is stored here
sys.path.append("/usr/lib/kabbit")

from plugin import plugin
from config import config
from kabbit_log import kabbit_logger

conf=config()

access_logger = kabbit_logger("/var/log/kabbit/access.log")


DEBUG = conf.debug

stopped_by_sig=0

pluginlist = {}

send_queue = Queue()


# command_list['status'] = "core"
# command_list['cmd'] = "pluginname"
command_list={}

#register builtin commands
command_list['plugins'] = "builtin"
command_list['help'] = "builtin"
command_list['load'] = "builtin"
command_list['unload'] = "builtin"

r=re.compile(".*\.py$")

#maximal accounts in our roster
MAX_ROSTER_LENGTH=100

##########################################################
#  setup the logger.					 #
#     - set path (from config)				 #
#     - set level (from config)				 #
#  level could  be "error" or "warning"			 #
#  if error is chosen, only errors will be logged..	 #
##########################################################


logger = logging.getLogger('kabbit')
hdlr = logging.FileHandler(conf.log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

if conf.log_level == "warning":
	logger.setLevel(logging.WARNING)
else:
	logger.setLevel(logging.ERROR)



#data structure used in message queing
class kabbit_message:
	def __init__(self,user,msg):
		self.user=user
		self.msg=msg

##########################################################
# 			Plugin manager			 #
# A plugin has to be a class named plugin implementing   #
#the process_message(mess,args) method and the following #
# properties:						 #
#							 #
# -descr	A short plugin description               #
# -author	The Authors Name and / or email adress   #
# -version	Version of the plugin                    #
# -commands     commands which are implemented by plugin #
# -auth		authentication method                    #
# -help		help on commands and plugin              #
##########################################################



#load available plugins
def get_plugins(nothing,path,files):
	global pluginlist
	for f in files:
		if r.match(f):
			fname = f.split('.')[0]
			loadPlugin(fname)


def loadPlugin(name):
	'''load plugin'''

	if isPluginLoaded(name):
		#reload it
		unloadPlugin(name)

	try:
		tmp=(__import__(name,globals(),locals(),[]))
		tmp_object=tmp.kabbit_plugin(conf)
		if isinstance(tmp_object,plugin):
			if DEBUG:	print name + " is a valid plugin"
			#be sure that no command is already in the commandlist
			for command in tmp_object.commands:
				if command in command_list:
					raise Exception
				else:
					command_list[command] = name
			# construct an instance

			pluginlist[name] = tmp_object
	except Exception,e:
		if DEBUG:	print e


def unloadPlugin(name):
	''' remove plugin'''
	if name in pluginlist:
		#delete all commands from pluginlist
		for command in pluginlist[name].commands:
			del(command_list[command])
		del(pluginlist[name])
		return 1
	else:
		return 0


def getPluginList():
	''' return the loaded plugins '''
	global pluginlist
	ret_string = "\n Loaded Plugins: \n"
	for plugin in pluginlist:
		ret_string += plugin.strip() + "\t\t" + pluginlist[plugin].descr + "\n"
	return ret_string

def isPluginLoaded(name):
	''' check if a plugin is loaded '''
	if name in pluginlist:
		return 1
	else:
		return 0

def help():
	#print help
	help_text = "\nHi, this is kabbit 0.0.7, your server-monitoring Killer Rabbit.";
	help_text += "\nCopyright by Sebastian Moors <sebastian.moors@gmail.com> 23.02.2006";
	help_text += "\nLicensed under GPLv2";
	help_text += "\n\nAvailable commands: \n\nstatus\t\t\tPrint status informations"
	help_text += "\nservices\t\t\t Show running processes"
	help_text += "\nplugins\t\t\t Show loaded plugins"
	help_text += "\nload pluginname\t\t Load plugin"
	help_text += "\nunload pluginname\t\t Unload plugin"
	help_text += "\nhelp\t\t\t\t This text"
	return help_text





def send_msg(conn,user,msg):
	#conn.send(xmpp.protocol.Message(user,msg,"chat"))
	msg=str(msg).strip()
	if msg.strip() != "None" and len(msg) > 0:
		send_queue.put(kabbit_message(user,msg))






def presenceCB(conn,prs):
	'''callback handler for presence actions'''
	msg_type = prs.getType()

	status=str(prs.getStatus())
	show=str(prs.getShow())

	who = prs.getFrom().getStripped()

	if(strip(status)=="" or strip(status)=="Logged out"):
		print who + " seems to be offline now"
	else:
		print who + " seems to be online now"
		print status

	#print "status:" + status
	#print "Show: " + show
	#print "type:" + str(msg_type) + "\n"




	allowed_jids = conf.admin_users

	if msg_type == 'subscribe' :
		if conf.visibiliy == "public" or ((str(user)).split("/"))[0] in allowed_jids:
			roster = conn.getRoster()
			# for security reasons there's a maximal roster length
			if len(roster) < MAX_ROSTER_LENGTH:
				conn.send(xmpp.Presence(to=who, typ = 'subscribed'))
				conn.send(xmpp.Presence(to=who, typ = 'subscribe'))
			else:
				logger.error("Maximum roster length reached,dropped subscribtion from " + str(user))



def messageCB(conn,mess):
	global pluginlist
	global command_list
	text = mess.getBody()
	user = mess.getFrom()


	allowed_jids = conf.admin_users

	auth=0

	if ((str(user)).split("/"))[0] not in allowed_jids:
		#exit if user is not allowed to use our bot
		#logger.warning("Failed login from " + ((str(user)).split("/"))[0])
		#return
		pass
	else:
		auth=1



	if text.find(' ')+1:
		command,args = text.split(' ', 1)
	else:
		command,args = text, ''

	#convert incoming commands to lowercase letters
	cmd = command.lower()

	#log the command
	access_logger.access_log("in",str(user),str(command))

	if not cmd in command_list:
		access_logger.access_log("out",str(user),str("unknown command:" + cmd))
		return

	if auth == 1:


		if cmd == "load":
			loadPlugin(args)

		if cmd == "unload":
			unloadPlugin(args)

		if cmd == "help" and len(args)==0:
			#conn.send(xmpp.protocol.Message(user, help()))
			send_msg(conn,user,help())


		if cmd == "help" and len(args)>0:
			'''print help on plugin or command '''
			if isPluginLoaded(str(args)):
				help_string=pluginlist[args].help
				help_string+="\n\nThe " + args + " plugins provides the following commands: \n"
				for command in pluginlist[args].commands:
					help_string+= command + "\t\t" + pluginlist[args].commands[command] + "\n"
				send_msg(conn,user,help_string)
			elif command_list.has_key(str(args)):
				help_string= command + "\t\t" + pluginlist[command_list[str(args)]].commands[str(args)] + "\n"
				send_msg(conn,user,help_string)

		if cmd == "plugins":
			send_msg(conn,user,getPluginList())



	for plugin in pluginlist:
		if pluginlist[plugin].auth == "public":
			send_msg(conn,user,pluginlist[plugin].process_message(cmd,args))

		if pluginlist[plugin].auth == "self":
			if pluginlist[plugin].authenticate(user):
				send_msg(user, pluginlist[plugin].process_message(cmd,args))

		if pluginlist[plugin].auth == "private" and auth == 1:
			send_msg(conn,user, pluginlist[plugin].process_message(cmd,args))


def StepOn(conn):
    try:
        conn.Process(1)
    except KeyboardInterrupt:
	    return 0
    return 1

def GoOn(conn):
	while StepOn(conn):



		if int(time.time())%60 == 0:
			conn.send(' ')

			for plugin in pluginlist:
				(pluginlist[plugin]).poll(conn)

def sighandler(arg1, arg2):
	global stopped_by_sig

	file_handle = open("/var/run/kabbit.pid", "w")
	file_handle.write(" ")
	file_handle.close

	stopped_by_sig = 1


class queue_daemon(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.con=""
	def setCon(self,con):
		# set actual connection
		self.con = con

	def run(self):
		global stopped_by_sig
		while(stopped_by_sig==0):
			time.sleep(1)
		        if send_queue.qsize() > 0 and self.con != "":
				k_msg=send_queue.get()
				self.con.send(xmpp.protocol.Message(k_msg.user,k_msg.msg,"chat"))
				access_logger.access_log("out",str(k_msg.user),"*")



class roster_watcher(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.con=""


	def setCon(self,con):
		self.con = con

	def run(self):
		roster = self.con.getRoster()


	def setStatus(jid,status):
		#set the current status for contact jid

		#while(stopped_by_sig==0):
		#	if self.con != "":
		#		time.sleep(1)
				#roster_it = roster.getItems()
				#pint roster_it[2]
				#print roster.getStatus(roster_it[2])
				#print roster.getSubscription(roster_it[2])




def main():
	print "k"
	pid = os.fork()
	if pid == 0:

		os.setsid()
		file_handle = open("/var/run/kabbit.pid", "w")
		file_handle.write(repr(os.getpid()))
		file_handle.close
		del file_handle
	else:
		sys.exit(0)

	rw=roster_watcher()

	q=queue_daemon()
	q.start()


	#initalize our plugins
	sys.path.append(os.path.abspath('/usr/lib/kabbit/plugins/'))
	os.path.walk('/usr/lib/kabbit/plugins/',get_plugins,None)


	jid=xmpp.JID(conf.jid)

	user, server, password = jid.getNode(), jid.getDomain(), conf.pwd

	signal.signal(signal.SIGTERM, sighandler)
	global stopped_by_sig

	while stopped_by_sig == 0:

		try:
			#authres=1
			conn = xmpp.Client(server,debug=[""])
			conres = conn.connect()
			if DEBUG: print "Conres:",conres


			if not conres:
				if DEBUG: print "Unable to connect to server %s!"%server
				logger.error("Unable to connect to server %s!"%server)
				sys.exit(1)

			if conres <> 'tls':
				if DEBUG: print 'Warning: unable to estabilish secure connection - TLS failed!'
				logger.warning('Warning: unable to estabilish secure connection - TLS failed!')
			authres = conn.auth(user,password)


			if not authres:
				if DEBUG: print "Unable to authorize on %s - check login/password."%server
				logger.error("Unable to authorize on %s - check login/password."%server)
				sys.exit(1)



			if authres <> 'sasl':
				if DEBUG: print "Warning: unable to perform SASL auth os " + server + ". Old authentication method used!"
				logger.warning("Warning: unable to perform SASL auth os " + server + ". Old authentication method used!")

			#register our handlers
			conn.RegisterHandler('message', messageCB)
			conn.RegisterHandler('presence', presenceCB)


			conn.sendInitPresence()


			q.setCon(conn)
			rw.setCon(conn)
			#rw.run()
			GoOn(conn)


		except Exception,e:
			if DEBUG:	print "Exception:" + str(e)
			q.setCon("")
			time.sleep(8)

main()

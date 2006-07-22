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





##############################################
#data structure used in message queing       #
##############################################
class kabbit_message:
	def __init__(self,user,msg):
		self.user=user
		self.msg=msg





##############################################
#data structure used for roster managment    #
##############################################
class roster_element:
	def __init__(self,jid,status,show):
		self._jid=jid
		self._status=status
		self._show=show

	def setStatus(self,status):
		self.status=status

	def setShow(self,show):
		self.show=show

	def getStatus(self):
		return self.status


	def getShow(self):
		return self.show



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


class plugin_manager:

	pluginlist = {}




	# command_list['status'] = "core"
	# command_list['cmd'] = "pluginname"
	command_list={}

	#register builtin commands
	command_list['plugins'] = "builtin"
	command_list['help'] = "builtin"
	command_list['load'] = "builtin"
	command_list['unload'] = "builtin"

	def __init__(self):
		self.r=re.compile(".*\.py$")


	def get_plugins(self,nothing,path,files):

		for f in files:
			if self.r.match(f):
				fname = f.split('.')[0]
				self.loadPlugin(fname)


	def loadPlugin(self,name):
		'''load plugin'''

		if self.isPluginLoaded(name):
			#reload it
			self.unloadPlugin(name)

		try:
			tmp=(__import__(name,globals(),locals(),[]))
			tmp_object=tmp.kabbit_plugin(conf)
			if isinstance(tmp_object,plugin):
				if DEBUG:	print name + " is a valid plugin"
				#be sure that no command is already in the commandlist
				for command in tmp_object.commands:
					if command in self.command_list:
						raise Exception
					else:
						self.command_list[command] = name

				# construct an instance
				self.pluginlist[name] = tmp_object

		except Exception,e:
			if DEBUG:	print e


	def unloadPlugin(self,name):
		''' remove plugin'''
		if name in self.pluginlist:
			#delete all commands from pluginlist
			for command in self.pluginlist[name].commands:
				del(self.command_list[command])
			del(self.pluginlist[name])
			return 1
		else:
			return 0


	def getPluginList(self):
		''' return the loaded plugins '''

		ret_string = "\n Loaded Plugins: \n"
		for plugin in self.pluginlist:
			ret_string += plugin.strip() + "\t\t" + self.pluginlist[plugin].descr + "\n"
		return ret_string


	def isPluginLoaded(self,name):
		''' check if a plugin is loaded '''
		if name in self.pluginlist:
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











class queue_daemon(threading.Thread):
	def __init__(self,queue):
		threading.Thread.__init__(self)
		self.con=""
		self.send_queue=queue

	def setCon(self,con):
		# set actual connection
		self.con = con

	def run(self):
		global stopped_by_sig
		while(stopped_by_sig==0):
			time.sleep(1)
		        if self.send_queue.qsize() > 0 and self.con != "":
				k_msg=self.send_queue.get()
				self.con.send(xmpp.protocol.Message(k_msg.user,k_msg.msg,"chat"))
				access_logger.access_log("out",str(k_msg.user),"*")



class roster_watcher(threading.Thread):

	valid_states=["online,offline,away"]

	def __init__(self):
		threading.Thread.__init__(self)
		self.con=""
		self.roster={}


	def setCon(self,con):
		self.con = con

	def run(self):
		roster = self.con.getRoster()
		for item in roster.getItems():
			self.roster[item]=roster_element(item,"offline","")
			self.setStatus(item,"offline")

	def setStatus(self,jid,status):
		#if not self.roster

		if status in self.valid_states:
			self.roster[jid].setStatus(status)

	def getStatus(self,jid):
		return self.roster[jid].getStatus()

	def setShow(self,jid,show):
		if self.roster.has_key(jid):
			self.roster[jid].setShow(show)



class kabbit_bot:




	def __init__(self,queue_daemon,roster_watcher,plugin_manager):

		self.q=queue_daemon
		self.rw=roster_watcher
		self.p=plugin_manager



	def StepOn(self,conn):
		try:
			conn.Process(1)
		except KeyboardInterrupt:
			return 0
		return 1



	def GoOn(self,conn):
		while self.StepOn(conn):
			if int(time.time())%60 == 0:
				conn.send(' ')

				for plugin in self.p.pluginlist:
					(self.p.pluginlist[plugin]).poll(conn)



	def send_msg(self,conn,user,msg):
		#conn.send(xmpp.protocol.Message(user,msg,"chat"))
		msg=str(msg).strip()
		if msg.strip() != "None" and len(msg) > 0:
			self.q.send_queue.put(kabbit_message(user,msg))




	def sighandler(self,arg1, arg2):
		global stopped_by_sig

		file_handle = open("/var/run/kabbit.pid", "w")
		file_handle.write(" ")
		file_handle.close

		stopped_by_sig = 1



	def presenceCB(self,conn,prs):
		'''callback handler for presence actions'''
		msg_type = prs.getType()
		status=str(prs.getStatus())
		show=str(prs.getShow())
		who = prs.getFrom().getStripped()



		if(strip(status)=="Logged out"):
			if DEBUG: print who + " seems to be offline now"
			self.rw.setStatus(who,"offline")
		else:
			if DEBUG: print who + " seems to be online now"
			self.rw.setStatus(who,"online")


		self.rw.setShow(who,str(show))



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



	def messageCB(self,conn,mess):


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

		if not cmd in self.p.command_list:
			access_logger.access_log("out",str(user),str("unknown command:" + cmd))
			return


		if auth == 1:


			if cmd == "load":
				self.p.loadPlugin(args)

			if cmd == "unload":
				self.p.unloadPlugin(args)

			if cmd == "help" and len(args)==0:
				self.send_msg(conn,user,help())


			if cmd == "help" and len(args)>0:
				'''print help on plugin or command '''
				if self.p.isPluginLoaded(str(args)):
					help_string=self.p.pluginlist[args].help
					help_string+="\n\nThe " + args + " plugins provides the following commands: \n"
					for command in self.p.pluginlist[args].commands:
						help_string+= command + "\t\t" + self.p.pluginlist[args].commands[command] + "\n"
					self.send_msg(conn,user,help_string)
				elif self.p.command_list.has_key(str(args)):
					help_string= command + "\t\t" + self.p.pluginlist[self.p.command_list[str(args)]].commands[str(args)] + "\n"
					self.send_msg(conn,user,help_string)

			if cmd == "plugins":
				self.send_msg(conn,user,self.p.getPluginList())



		for plugin in self.p.pluginlist:
			if self.p.pluginlist[plugin].auth == "public":
				self.send_msg(conn,user,self.p.pluginlist[plugin].process_message(cmd,args))

			if self.p.pluginlist[plugin].auth == "self":
				if pluginlist[plugin].authenticate(user):
					self.send_msg(user, self.p.pluginlist[plugin].process_message(cmd,args))

			if self.p.pluginlist[plugin].auth == "private" and auth == 1:
				self.send_msg(conn,user, self.p.pluginlist[plugin].process_message(cmd,args))


	def run(self):
		jid=xmpp.JID(conf.jid)

		user, server, password = jid.getNode(), jid.getDomain(), conf.pwd

		signal.signal(signal.SIGTERM, self.sighandler)
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
				conn.RegisterHandler('message', self.messageCB)
				conn.RegisterHandler('presence', self.presenceCB)


				conn.sendInitPresence()


				#setting up queue_daemon
				self.q.setCon(conn)

				#setting up roster manager
				self.rw.setCon(conn)
				self.rw.run()

				self.GoOn(conn)


			except Exception,e:
				if DEBUG:	print "Exception:" + str(e)
				self.q.setCon("")
				time.sleep(8)





def main():
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

	q=queue_daemon(Queue())
	q.start()

	p=plugin_manager()

	#initalize our plugins
	sys.path.append(os.path.abspath('/usr/lib/kabbit/plugins/'))
	os.path.walk('/usr/lib/kabbit/plugins/',p.get_plugins,None)

	kabbit = kabbit_bot(q,rw,p)
	kabbit.run()


main()

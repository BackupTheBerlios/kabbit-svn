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
#



import re
import sys
import xmpp
import os
import signal
import logging
import time


#the config module is stored here
sys.path.append("/usr/lib/kabbit")

from config import config



conf=config()

stopped_by_sig=0

pluginlist = {}

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


##########################################################
# 			Plugin manager			 #
# A plugin has to be a class named plugin implenting the #
# process_message(mess,args) method and the following    #
# properties:						 #
#							 #
# -descr	A short plugin description               #
# -author	The Authors Name and / or email adress   #
# -version	Version of the plugin                    #
# -commands     commands which are implemented by plugin #
# -auth		authentication method                    #
# -help		help on commands and plugin              #
##########################################################



def get_plugins(nothing,path,files):
	global pluginlist
	for f in files:
		if r.match(f):
			fname = f.split('.')[0]
            		pluginlist[fname] = (__import__(fname,globals(),locals(),[]))
			# construct an instance
			pluginlist[fname] = pluginlist[fname].plugin()
def loadPlugin(name):
	'''load plugin'''
	if isPluginLoaded(name):
		#reload it
		unloadPlugin(name)

	try:
		pluginlist[name] = (__import__(name,globals(),locals(),[]))
		# construct an instance
		pluginlist[name] = pluginlist[name].plugin()
	except Exception:
		pass

def unloadPlugin(name):
	''' remove plugin'''
	if name in pluginlist:
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
	if name in pluginlist:
		return 1
	else:
		return 0

def help():
	#print help
	help_text = "\nHi, this is kabbit 0.0.4, your server-monitoring Killer Rabbit.";
	help_text += "\nCopyright by Sebastian Moors <sebastian.moors@gmail.com> 23.02.2006";
	help_text += "\nLicensed under GPLv2";
	help_text += "\n\nAvailable commands: \n\nstatus\t\t\tPrint status informations"
	help_text += "\nservices\t\t\t Show running processes"
	help_text += "\nplugins\t\t\t Show loaded plugins"
	help_text += "\nload pluginname\t\t Load plugin"
	help_text += "\nunload pluginname\t\t Unload plugin"
	help_text += "\nhelp\t\t\t\t This text"
	return help_text

def presenceCB(conn,prs):
	'''callback handler for presence actions'''
	msg_type = prs.getType()
	who = prs.getFrom().getStripped()
	allowed_jids = conf.allowed_users

	if msg_type == 'subscribe' :
		roster = conn.getRoster()
		# for security reasons there's a maximal roster length
		if len(roster) < MAX_ROSTER_LENGTH:
			conn.send(xmpp.Presence(to=who, typ = 'subscribed'))
			conn.send(xmpp.Presence(to=who, typ = 'subscribe'))

def messageCB(conn,mess):
	global pluginlist
	text = mess.getBody()
	user = mess.getFrom()


	allowed_jids = conf.allowed_users

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

	cmd = command.lower()

	if auth == 1:


		if cmd == "load":
			loadPlugin(args)

		if cmd == "unload":
			unloadPlugin(args)

		if cmd == "help" and len(args)==0:
			conn.send(xmpp.Message(user, help()))


		if cmd == "help" and len(args)>0:
			if isPluginLoaded(str(args)):
				conn.send(xmpp.Message(user, pluginlist[args].help))


		if cmd == "plugins":
			conn.send(xmpp.Message(user, getPluginList()))

	for plugin in pluginlist:
		if pluginlist[plugin].auth == "public":
			conn.send(xmpp.Message(user, pluginlist[plugin].process_message(cmd,args)))

		if pluginlist[plugin].auth == "self":
			if pluginlist[plugin].authenticate(user):
				conn.send(xmpp.Message(user, pluginlist[plugin].process_message(cmd,args)))

		if pluginlist[plugin].auth == "private" and auth == 1:
			conn.send(xmpp.Message(user, pluginlist[plugin].process_message(cmd,args)))



def StepOn(conn):
    try:
        conn.Process(1)
    except KeyboardInterrupt:
	    return 0
    return 1

def GoOn(conn):

    while StepOn(conn):
	    pass

def sighandler(arg1, arg2):
	""" handler for signals. is used to shutdown pyras """
	global stopped_by_sig

	file_handle = open("/var/run/kabbit.pid", "w")
	file_handle.write(" ")
	file_handle.close

	stopped_by_sig = 1


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

	#initalize our plugins
	sys.path.append(os.path.abspath('/usr/lib/kabbit/plugins/'))
	os.path.walk('/usr/lib/kabbit/plugins/',get_plugins,None)


	jid=xmpp.JID(conf.jid)

	user, server, password = jid.getNode(), jid.getDomain(), conf.pwd

	signal.signal(signal.SIGTERM, sighandler)
	global stopped_by_sig

	while stopped_by_sig == 0:

		try:
			conn = xmpp.Client(server, debug=[])
			conres = conn.connect()
			if not conres:
				logger.error("Unable to connect to server %s!"%server)
				sys.exit(1)
			if conres <> 'tls':
				logger.warning('Warning: unable to estabilish secure connection - TLS failed!')
				authres = conn.auth(user,password)
			if not authres:
				logger.error("Unable to authorize on %s - check login/password."%server)
				sys.exit(1)
			if authres <> 'sasl':
				logger.warning("Warning: unable to perform SASL auth os " + server + ". Old authentication method used!")
			conn.RegisterHandler('message', messageCB)
			conn.RegisterHandler('presence', presenceCB)

			roster = conn.getRoster()
			#print roster.getItems()
			conn.sendInitPresence()
			GoOn(conn)
		except Exception,e:
			print e
			time.sleep(30)

main()

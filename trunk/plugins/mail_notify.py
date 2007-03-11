#!/usr/bin/python
import sys

sys.path.append("/usr/lib/kabbit")
from plugin import plugin
from config import config
import xmpp
import poplib
import time
from string import strip
from os import stat

#################################################################
#	TODO:
#		- register/unregister
#		- check if user is online
#		- authentication
#################################################################

class email_account:
	def __init__(self,jid,acc_type,server,username,pwd):
		self.jid=jid
		self.acc_type=acc_type
		self.server=server
		self.username=username
		self.pwd=pwd
		self.msg_count=0
		self.timeout=0


class kabbit_plugin(plugin):
	def __init__(self,config,roster):
		self.descr="pop/imap Mail Notifier"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["unregister"]="turn off notification"

		self.help="This Plugin sends an notification if new mail arrives"
		self.auth="private"


		self.conf = config
		self.roster = roster
		
		#seconds between 2 logins
		self.delta = 30 

		self.user_container = []

		self.pop_ssl_warn=False;


		#check if configuration is just readeable for user "kabbit"
		filename="/etc/kabbit_mail.conf"
		mode= int(oct(stat(filename).st_mode)[4:])
		if mode > 700:
			print "WARNING: insecure filepermissions for " + filename

		#read our configuration file
		file = open("/etc/kabbit_mail.conf","r")

		#
		# config file syntax: jid:accout_type:server:username:password:active
		#
		#

		f=file.readline()
		while(f):
			jid=strip(f.split(":")[0])
			acc_type=strip(f.split(":")[1])
			server=strip(f.split(":")[2])
			username=strip(f.split(":")[3])
			pwd=strip(f.split(":")[4])
			self.user_container.append(email_account(jid,acc_type,server,username,pwd))
			f=file.readline()





	def poll(self,con):
		for e in self.user_container:
			if self.roster.getStatus(e.jid) == "online":
				newMails=self.check_mail(e)
				s=""
				if newMails > 0:
					if newMails > 1: s="s"
					msgString="You have " + str(newMails) + " new Mail" + s + " at "+  e.username + "@" + e.server
					con.send(xmpp.protocol.Message(e.jid,msgString,"chat"))
				 


	def check_mail(self,e):
		if e.acc_type == "pop":

			try:
				if e.timeout == 0 or (time.time() - e.timeout) > self.delta:
					M = poplib.POP3(strip(e.server))
					M.user(e.username)
					M.pass_(e.pwd)
					numMessages = len(M.list()[1])


					e.timeout = time.time()

					#oops, someone has deleted mails. set the msg_count back
					if e.msg_count !=0 and e.msg_count > numMessages:
						e.msg_count=numMessages
						return 0 

					#seems that we have new mail
					if e.msg_count != 0 and e.msg_count < numMessages:
						e.msg_count=numMessages
						return numMessages - e.msg_count
					else:

						if e.msg_count==0:
							e.msg_count=numMessages

						return 0

			except Exception,ex:
				print "some error occured" + str(ex)
				return False


		#check once if ssl is available and log it
		if e.acc_type == "pops" and float(sys.version[0:3]) < 2.4 and self.pop_ssl_warn==False:
			self.pop_ssl_warn=True;
			print "pops requested, but python version < 2.4 found. Please upgrade to a version >= 2.4 "



		if e.acc_type == "pops" and float(sys.version[0:3]) >= 2.4:

			#
			# poplib ssl support must be enabled
			# you have to use a python version >= 2.4
			#

			try:
				if e.timeout == 0 or (time.time() - e.timeout) > self.delta:
					M = poplib.POP3_SSL(strip(e.server))
					M.user(e.username)
					M.pass_(e.pwd)
					numMessages = len(M.list()[1])
					e.timeout = time.time()

					#oops, someone has deleted mails. set the msg_count back
					if e.msg_count !=0 and e.msg_count > numMessages:
						e.msg_count=numMessages
						return 0 


					if e.msg_count != 0 and e.msg_count <> numMessages:
						old_msg_count=e.msg_count
						e.msg_count=numMessages
						return (numMessages - old_msg_count)
					else:

						if e.msg_count==0:
							e.msg_count=numMessages

						return 0

			except Exception,e:
				print "some error occured" + str(e)
				return False




	def process_message(self,user,cmd,args):
		pass

if __name__=="__main__":
   plugin2=kabbit_plugin(None,None)
   plugin2.poll("a")

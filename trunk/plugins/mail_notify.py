#!/usr/bin/python
import sys

sys.path.append("/usr/lib/kabbit")
from plugin import plugin
from config import config
import xmpp
import poplib
import time
from string import strip

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
	def __init__(self,config):
		self.descr="Mail Notifier"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["unregister"]="turn off notification"

		self.help="mensa plugins"
		self.auth="private"


		self.conf = config

		#seconds between 2 logins
		self.delta = 200

		#number of messages in our mailbox
		#self.msg_count[jid]=number
		self.msg_count={}
		self.timeouts={}


		user =  "mauser@jabber.ccc.de"
		self.timeouts[user]=0
		self.msg_count[user]=0

		self.user_container = []

		#read our configuration file
		file = open("/etc/kabbit_mail.conf","r")
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
			if self.check_mail(e) == True:
				con.send(xmpp.Message(e.jid,"You have new Mail @ " + e.server))

		'''
		user =  "mauser@jabber.ccc.de"
		if self.timeouts[user] == 0 or (time.time() - self.timeouts[user]) > 300:
			try:
				M = poplib.POP3('pop.gmx.de')
				M.user("sebastian.moors@gmx.de")
				M.pass_("rotten")
				numMessages = len(M.list()[1])
				print numMessages

				self.timeouts[user] = time.time()
				if self.msg_count[user] != 0 and self.msg_count[user] <> numMessages:
					#con.send(xmpp.Message(user,"You have new Mail"))
					print "you have new mail"
				self.msg_count[user]=numMessages
				#for i in range(numMessages):
				#	for j in M.retr(i+1)[1]:
				#		print j
			except Exception,e:
				print "some error occured"
		'''

	def check_mail(self,e):
		print "checking mail"
		print e.timeout
		#try:
		if e.timeout == 0 or (time.time() - e.timeout) > self.delta:
			print "in if"
			print e.server
			print e.username
			print e.pwd
			M = poplib.POP3(strip(e.server))
			M.user(e.username)
			M.pass_(e.pwd)
			numMessages = len(M.list()[1])
			print e.username + ":" + str(numMessages)

			e.timeout = time.time()
			if e.msg_count != 0 and e.msg_count <> numMessages:
				e.msg_count=numMessages
				return True
			else:
				return False

		#except Exception,e:
		#	print "some error occured" + str(e)
		#	return False

	def process_message(self,cmd,args):
		if cmd == "test":
			return self.conf.allowed_users

if __name__=="__main__":
   plugin2=kabbit_plugin(config())
   plugin2.poll("a")
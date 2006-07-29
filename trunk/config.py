import ConfigParser
import getopt

import os
import sys

class kabbit_config:
	def __init__(self):
		self.__jid=""
		self.__pwd=""
		self.__visibility=""
		self.__log_file=""
		self.__log_level=""
		self.__debug=0
		self.__admin_users=[]
		self.__accountName=""
		self.__PluginDir=""
		self.__AdminMail=""

	def setAdminMail(self,mail):
		self.__AdminMail=mail

	def setPluginDir(self,pl_dir):
		self.__PluginDir=pl_dir

	def getPluginDir(self):
		return self.__PluginDir

	def setAccountName(self,name):
		self.__accountName=name


	def getAccountName(self):
		return self.__accountName

	def setJid(self,jid):
		self.__jid=jid

	def setPwd(self,pwd):
		self.__pwd=pwd

	def setVisibility(self,visibility):
		self.__visibility=visibility

	def setLogfile(self,file):
		self.__log_file=file

	def setLoglevel(self,level):
		self.__Loglevel=level

	def setDebug(self,debug):
		self.__debug=debug


	def setAdminusers(self,user):
		self.__admin_users=user


	def getJid(self):
		return self.__jid

	def getPwd(self):
		return self.__pwd

	def getVisibility(self):
		return self.__visibility

	def getLogfile(self):
		return self.__log_file

	def getLoglevel(self):
		return self.__log_level

	def getDebug(self):
		return self.__debug

	def getAdminusers(self):
		return self.__admin_users

	def getAdminMail(self):
		return self.__AdminMail



class config:

	__configHash={}

	def __init__(self):
		"""Class for Configuration Managment"""
		config = ConfigParser.ConfigParser()

		config.readfp(open('/etc/kabbit.conf'))

		accounts = config.sections()

		self.configHash={}

		for account in accounts:
			admin_users=[]
			c=kabbit_config()
			c.setJid(config.get(account,"bot_jid"))
			c.setPwd(config.get(account,"bot_password"))
			c.setVisibility(config.get(account,"bot_password"))
			c.setLogfile(config.get(account,"log_file"))
			c.setLoglevel(config.get(account,"log_level"))
			c.setPluginDir(config.get(account,"plugin_dir"))


			if config.get(account,"admin_users").find(",") >= 0:
				admin_users=config.get(account,"admin_users").split(",")
			else:
				admin_users.append(config.get(account,"admin_users"))

			c.setAdminusers(admin_users)

			try:
				long_opts=["debug"]
				opts, args = getopt.getopt(sys.argv[1:], "d",long_opts )
			except getopt.GetoptError:
				sys.exit(2)

			for option, argument in opts:
				if option in ("-d", "--debug"):
					c.setDebug(1)

			self.configHash[account]=c;

	def getConfig(self):
		return self.configHash



if __name__ == "__main__":
		p = config()
		print p.getConfig()


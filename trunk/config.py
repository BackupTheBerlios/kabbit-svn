import ConfigParser
import getopt

import os
import sys

class config:

	def __init__(self):
		"""Class for Configuration Managment"""
		config = ConfigParser.ConfigParser()
		self.allowed_users=[]
		config.readfp(open('/etc/kabbit.conf'))

		self.jid=config.get("jabber","bot_jid")
		self.pwd=config.get("jabber","bot_password")

		self.visibility=config.get("jabber","visibility")

		self.log_file=config.get("main","log_file")
		self.log_level=config.get("main","log_level")

		self.debug = 0

		if config.get("jabber","allowed_users").find(",") >= 0:
			self.allowed_users=config.get("jabber","allowed_users").split(",")
		else:
			self.allowed_users.append(config.get("jabber","allowed_users"))


		try:
			long_opts=["debug"]
			opts, args = getopt.getopt(sys.argv[1:], "d",long_opts )
		except getopt.GetoptError:
			sys.exit(2)

		for option, argument in opts:
			if option in ("-d", "--debug"):
				self.debug=1


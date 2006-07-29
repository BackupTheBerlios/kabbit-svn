class plugin:
	def __init__(self,config,roster):
		self.conf = config
		self.roster=roster

	def poll(self,connection):
		pass

	def process_message(self,cmd,args):
		pass
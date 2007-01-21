
import os
import string
import re
import sys
import sqlite

sys.path.append("/usr/lib/kabbit")
from plugin import plugin

class watcher:
	def __init__(self):
		dbfile="/usr/lib/kabbit/plugins/fileinfo.db"

		new=0
		#check if database exists
		if not os.path.isfile(dbfile):
			new=1
			
		self.db = sqlite.connect(dbfile)
		self.cursor = self.db.cursor()
			
		if new==1:
			self.createDB()
			
	def createDB(self):	
                sql="CREATE TABLE 'files' (fileID INTEGER PRIMARY KEY, name TEXT,hash TEXT)"
		self.cursor.execute(sql)
       		sql="CREATE TABLE 'watchlist' (user TEXT,dir TEXT)"
		self.cursor.execute(sql)
	        self.db.commit()

	def watch(self,user,args):
		print args
		self.getWatchList(user)
		

	def getWatchList(self,user):
		sql="SELECT dir FROM watchlist where user like '%s'" % user
		print sql
		self.cursor.execute(sql)
		row=self.cursor.fetchall()

		

class kabbit_plugin(plugin):
	def __init__(self,config,roster):
		self.descr="directory notify"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["watch"]="notify if someting changes in a certain directory"
		self.commands["unwatch"]="cancel notification"
		self.commands["watchlist"]="list all watched directorys"

		self.help="notification service for directory changes"
		self.auth="private"
		self.roster=roster
		self.eye=watcher()


	def process_message(self,user,cmd,args):
		if cmd == "watch":
			return self.eye.watch(user,args)

		if cmd == "unwatch":
			return self.unwatch(args)

		if cmd == "watchlist":
			return self.watchlist(args)

if __name__ == "__main__":
	p=kabbit_plugin(None,None)
	p.process_message("mauser@jabber.ccc.de","watch","/tmp")



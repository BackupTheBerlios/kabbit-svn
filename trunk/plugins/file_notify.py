#!/usr/bin/python
import os
import string
import re
import sys
import sqlite
import xmpp

sys.path.append("/usr/lib/kabbit")
from plugin import plugin
from os import walk
import os.path
import stat

class watcher:
	def __init__(self):
		dbfile="/usr/lib/kabbit/plugins/fileinfo.db"

		
		stats=os.stat(dbfile)
		#TODO: what happens when the file belongs to the wrong user ? 
		if stats[stat.ST_UID] != os.getuid():
			print dbfile + " belongs to the wrong user. Be sure that it belongs to the same user which runs kabbit"
			return

		new=0
		#check if database exists
		if not os.path.isfile(dbfile):
			new=1
			
		self.db = sqlite.connect(dbfile)
		self.cursor = self.db.cursor()
			
		if new==1:
			self.createDB()
			
	def createDB(self):	
                sql="CREATE TABLE 'files' (fileID INTEGER PRIMARY KEY,listID INTEGER,name TEXT,mtime TEXT)"
		self.cursor.execute(sql)
       		sql="CREATE TABLE 'watchlist' (listID INTEGER PRIMARY KEY,user TEXT,dir TEXT,mtime TEXT)"
		self.cursor.execute(sql)
	        self.db.commit()

	def watch(self,user,args):
		#TODO: check if dir exists, readable etc.
		if not os.path.isdir(args):
			return args + " is not a valid directory"

		
		if not args in self.getWatchList(user):
			mtime=os.path.getmtime(args)
			self.cursor.execute("INSERT INTO 'watchlist' VALUES (NULL,%s,%s,%s)",(user,args,mtime))
			self.db.commit()

			self.cursor.execute("SELECT listID FROM watchlist WHERE dir=%s AND user=%s",(args,user))
	                listID = str(self.cursor.fetchone())
			listID = str(listID[1])

			
			for root, dirs, files in walk(args):
				for name in files:
					filename=os.path.join (root,name)
					mtime=os.path.getmtime(filename)
					self.cursor.execute("INSERT INTO 'files' VALUES (NULL,%s,%s,'%s')",(listID,filename,mtime))
			self.db.commit()
					




			
		
		#self.printAllFiles()
		return args + " added to watchlist"

	def printAllFiles(self):
		self.cursor.execute("SELECT * FROM files")
		self.db.commit()
		print self.cursor.fetchall()

	def unwatch(self,user,args):
		''' delete dir from watchlist '''
		if args in self.getWatchList(user):
			self.cursor.execute("SELECT listID FROM watchlist WHERE dir=%s AND user=%s",(args,user))
                        listID = str(self.cursor.fetchone())
			listID = str(listID[1])
				

		
			self.cursor.execute("DELETE FROM files WHERE listID=%s",(listID))
			self.cursor.execute("DELETE FROM 'watchlist' WHERE user=%s and dir=%s",(user,args))
			self.db.commit()

		
			#print self.getWatchList(user)
			#self.printAllFiles()
			return "%s deleted from watchlist" % args	    
		else:
			#self.printAllFiles()
			return "%s not fount in watchlist" % args

		

	def getWatchList(self,user):
		sql="SELECT dir FROM watchlist WHERE user LIKE '%s'" % user
		self.cursor.execute(sql)
		rows = self.cursor.fetchall()
		watchlist=[]
		for row in rows:
			watchlist.append(row[0])
		return watchlist

	def update(self,con):
		self.cursor.execute("SELECT * FROM watchlist")
		self.db.commit()
		for line in self.cursor.fetchall():
			listID=line[0]
			user=line[1]
			dir=line[2]
			mtime=str(line[3])
			act_mtime=str(os.path.getmtime(dir))
			if act_mtime != mtime:
				msgString= "Directory %s has changed " % dir 
				con.send(xmpp.protocol.Message(user,msgString + mtime,"chat"))
				#set mtime in database to current mtime
				self.cursor.execute("UPDATE watchlist SET mtime=%s WHERE listID=%s",(act_mtime,listID))
				self.db.commit()
				
		

class kabbit_plugin(plugin):
	def __init__(self,config,roster):
		self.descr="directory notify"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["watch"]="notify if something changes in a certain directory"
		self.commands["unwatch"]="cancel notification"
		self.commands["watchlist"]="list all watched directorys"

		self.help="notification service for directory changes"
		self.auth="private"
		self.roster=roster
		self.eye=watcher()

	def poll(self,con):
		self.eye.update(con)
		


	def process_message(self,user,cmd,args):
		user=str(user).split("/")[0]
		if cmd == "watch":
			if len(args) > 0:
				return self.eye.watch(user,args)
			else:
				return "watch: no argument"
			

		if cmd == "unwatch":
			if len(args) > 0:
				return self.eye.unwatch(user,args)
			else:
				return "unwatch: no argument"

		if cmd == "watchlist":
			wl=self.eye.getWatchList(user)
			if len(wl) == 0:
				return "No directories watched"
			else:
				return wl
				

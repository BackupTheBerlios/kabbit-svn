#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import httplib, urllib, re, sys, string, time


class plugin:

	debug=0

	def __init__(self):
		self.descr="Lyrics Plugin"
		self.author="Sebastian Moors"
		self.version="0.1"
		self.commands={}
		self.commands["lyr"]="Usage: lyr artist - song"
		self.auth="public"
		self.help="\n You can search the lyrics database for a song with the command 'lyr artist - song'"
		'''auth could be public,self or private
		   private means only the users defined by the allowed_jid's list are allowed_jid
		   to use the service
		'''
		self.auth="public"



	def get_lyrics(self,ARTIST,TITLE):
		'''
		 this method is taken from the open source project of http://lyrc.com.ar and was slightly changed
		 (found some bugs in their code ;-) )

		If lyrics are found, return a string

		If listing (songlisting) is found, return a list
		 '''

		found=1
		my_buffer=""
		ARTIST=urllib.quote(ARTIST)
		TITLE=urllib.quote(TITLE)
		global nbimage
		if (self.debug>0):
			print "[Lyrc] Searching on lyrc.com.ar ("+ARTIST+"-"+TITLE+")"
		URL="http://lyrc.com.ar/tema1en.php?artist="+string.replace(ARTIST," ","%20")+"&songname="+string.replace(TITLE," ","%20")



		conn = urllib.urlopen(URL)
		data = conn.read()
		conn.close()
		s = re.search("<message>nothing found</message>", data)
		if (s):
			#Search the links
			if self.debug>0:
				print "[Lyrc] --> lyrics not found :( ("+ARTIST+"-"+TITLE+")"
			sys.exit(0)
		else:
			#NO, get lyrics
			URL="http://lyrc.com.ar/tema1en.php?artist="+string.replace(ARTIST," ","%20")+"&songname="+string.replace(TITLE," ","%20")+"&act=1"

			conn = urllib.urlopen(URL)
			data = conn.read()
			#print data
			conn.close()

			data=string.replace(data,"\n<","<") #You shouldn't go do linefeed like that in XML!!!
			data=string.replace(data,"&","&amp;")
			my_buffer+=data
			if self.debug>0:
				print "[Lyrc] --> lyrics found :) ("+ARTIST+"-"+TITLE+")"
		return my_buffer

	def process_message(self,mess,args):

		if mess != "lyr":
			return ""
		if args.find("-") > 0:
			artist,title = args.split("-")
		else:
			artist = args
			title = ""


		artist=artist.strip()
		title=title.strip()
		data=self.get_lyrics(artist,title)

		if data.find("Suggestions :") > 0:
			lines=data.split("\n")

			buffer_on=0
			my_buffer=""

			import re

			r=re.compile(".*<p>.*")
			r2=re.compile("(.*)<br><br>(.*)")
			start=re.compile("^Suggestions")
			line=0
			while line < len(lines):


				if start.match(lines[line]):
					my_buffer = lines[line]
					break
				line=line+1

			r=re.compile("<br><br>.*")
			my_buffer=r.sub("",my_buffer)
			#my_buffer=(my_buffer.split("<form .*>"))[0]


			r=re.compile("</font>")
			my_buffer=r.sub("\n",my_buffer)

			delete_tags=re.compile("<.*?>")
			my_buffer=delete_tags.sub("",my_buffer)


			return my_buffer.decode("iso-8859-1")

		else:
			lines=data.split("\n")

			buffer_on=0
			my_buffer=""

			import re

			r=re.compile(".*<p>.*")
			r2=re.compile("(.*)<br><br>(.*)")
			r3=re.compile("<font.*>.*</font>")
			line=0
			while line < len(lines):


				if r3.match(lines[line]):
					if buffer_on==1:
						buffer_on=0
					else:
						buffer_on=1


				elif r2.match(lines[line]):
					if buffer_on==1:
						buffer_on=0


				if r.match(lines[line]):
					buffer_on=0

				if buffer_on==1:
					my_buffer = my_buffer + lines[line] + "\n"

				line=line+1

			r=re.compile("<font .*>.*</font>")
			my_buffer=r.sub("",my_buffer)

			r=re.compile(".*<p>.*")
			my_buffer=r.sub("",my_buffer)

			delete_tags=re.compile("<.*?>")
			my_buffer=delete_tags.sub("",my_buffer)

			if my_buffer.strip()=="":
				return "No song found."
			return "\n" + my_buffer.decode("iso-8859-1")

if __name__=="__main__":
   plugin2=plugin()
   print plugin2.process_message("lyr","Die Ärzte - ")

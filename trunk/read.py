#!/usr/bin/python
import httplib, urllib, re, sys, string, time

RARTIST=""
RTITLE=""
FILENAME="/home/sebastian/"
FORCE_RETRIEVE=0
ARTIST="Metallica"
TITLE="The Unforgiven"
debug=0

def get_lyrics(ARTIST,TITLE):
	found=1
	my_buffer=""
	global nbimage
	if (debug>0):
		print "[Lyrc] Searching on lyrc.com.ar ("+ARTIST+"-"+TITLE+")"
	URL="http://lyrc.com.ar/xsearch.php?artist="+string.replace(ARTIST," ","%20")+"&songname="+string.replace(TITLE," ","%20")
	conn = urllib.urlopen(URL)
	data = conn.read()
	conn.close()
	s = re.search("<message>nothing found</message>", data)
	if (s):
		found=0
	if (found==0):
		#Search the links
		f = open (FILENAME+".lyrics.xml", 'w')
		f.close ()
		if (debug>0):
			print "[Lyrc] --> lyrics not found :( ("+ARTIST+"-"+TITLE+")"
		sys.exit(0)
	else:
		# Are there multiple results?
		s = re.findall("<song>", data)
		if (len(s)>1 and FORCE_RETRIEVE==0):
			#YES!
			f = open (FILENAME+".lyrics.xml", 'w')
			data=string.replace(data,"\n<","<") #You shouldn't go do linefeed like that in XML!!!
			data=string.replace(data,"&","&amp;")
			f.write (data)
			my_buffer+=data
			f.close ()
			if (debug>0):
				print "[Lyrc] --> multiple lyrics found :S ("+ARTIST+"-"+TITLE+")"
		else:
			#NO, get lyrics
			URL="http://lyrc.com.ar/tema1en.php?artist="+string.replace(ARTIST," ","%20")+"&songname="+string.replace(TITLE," ","%20")+"&act=1"

			conn = urllib.urlopen(URL)
			data = conn.read()
			conn.close()
			f = open (FILENAME+".lyrics.xml", 'w')
			data=string.replace(data,"\n<","<") #You shouldn't go do linefeed like that in XML!!!
			data=string.replace(data,"&","&amp;")
			my_buffer+=data
			f.write (data)
			f.close ()
			if (debug>0):
				print "[Lyrc] --> lyrics found :) ("+ARTIST+"-"+TITLE+")"
	return my_buffer

def process_message(mess,args):

	if mess != "lyr":
		return ""
	artist, title = args.split("|")
	artist=artist.strip()
	title=title.strip()
	data=get_lyrics(artist,title)
	file=open("/home/sebastian/.lyrics.xml")
	line=file.readline()
	buffer_on=0
	my_buffer=""

	import re

	r=re.compile(".*<p>.*")
	r2=re.compile("(.*)<br><br>(.*)")
	r3=re.compile("<font.*>.*</font>")
	while line != "":
	#print line

		if r3.match(line):
			if buffer_on==1:
				buffer_on=0
			else:
				buffer_on=1
			#line=file.readline()
		elif r2.match(line):
			if buffer_on==1:
				buffer_on=0


		if r.match(line):
			buffer_on=0

		if buffer_on==1:
			my_buffer+=line
		line=file.readline()
	file.close()

	r=re.compile("<font .*>.*</font>")
	my_buffer=r.sub("",my_buffer)

	r=re.compile(".*<p>.*")
	my_buffer=r.sub("",my_buffer)

	delete_tags=re.compile("<.*?>")
	my_buffer=delete_tags.sub("",my_buffer)


	return my_buffer


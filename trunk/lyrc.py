#!/usr/bin/python

import httplib, urllib, re, sys, string, time



ARTIST="Nick Cave"
TITLE="15 ft of pure white snow"
RARTIST=""
RTITLE=""
FILENAME=""
FORCE_RETRIEVE=0
debug = 1
def lyrc():
	found=1
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
			f.close ()
			if (debug>0):
				print "[Lyrc] --> multiple lyrics found :S ("+ARTIST+"-"+TITLE+")"
		else:
			#NO, get lyrics
			URL="http://lyrc.com.ar/tema1en.php?artist="+string.replace(ARTIST," ","%20")+"&songname="+string.replace(TITLE," ","%20")+"&act=1"
			print URL
			conn = urllib.urlopen(URL)
			data = conn.read()
			conn.close()
			f = open (FILENAME+".lyrics.xml", 'w')
			data=string.replace(data,"\n<","<") #You shouldn't go do linefeed like that in XML!!!
			data=string.replace(data,"&","&amp;")
			print data
			f.write (data)
			f.close ()
			if (debug>0):
				print "[Lyrc] --> lyrics found :) ("+ARTIST+"-"+TITLE+")"

lyrc()

ShellObj = os.popen('/usr/bin/lynx')
hostname= (ShellObj.read()).strip();
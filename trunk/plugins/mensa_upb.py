#!/usr/bin/python
import sys
from BeautifulSoup import BeautifulSoup
import urllib
import re

sys.path.append("/usr/lib/kabbit")
from plugin import plugin

class kabbit_plugin(plugin):
	def __init__(self):
		self.descr="Shows mensa-informations for the University Paderborn "
		self.author="Sebastian Moors"
		self.version="0.2"
		self.commands={}
		self.commands["menu"]="Shows today's menu"

		self.help="mensa plugins"
		self.auth="private"

	def poll(self):
		pass

	def process_message(self,cmd,args):
		if cmd == "mensa":



			import datetime
			t = datetime.datetime.now()
			day=int(t.strftime("%w"))
			day=day-1

			if day > 6:
				return "The mensa is closed  today"

			delete_tags=re.compile("<.*?>")
			delete_entity=re.compile("&.*;")
			delete_newline=re.compile("\n")
			delete_tab=re.compile("\t")

			conn = urllib.urlopen('http://www.stwpb.de/essen/speiseplan/mensa.html')
			data = conn.read()
			conn.close()


			soup = BeautifulSoup(data)
			week_buffer=[]

			counter=0
			day_buffer=[]
			for incident in soup('div', {'class' : 'menuName'}):
				counter=counter+1
				incident=delete_tab.sub("",str(incident))
				incident=delete_entity.sub("",incident)
				incident=delete_newline.sub("",str(incident))
				day_buffer.append(delete_tags.sub("",str(incident)))
				if counter%3==0:
					counter=0
					week_buffer.append(day_buffer)
					day_buffer=[]

			return_string="\n Today's menu:\n\n"


			for item in week_buffer[day]:
				return_string += (str(item)).decode("iso-8859-1") + "\n"

			return return_string

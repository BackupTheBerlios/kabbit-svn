#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# The kabbit Installer by Sebastian Moors, 23.02.2006
#
# - create user 'kabbit'
# - copy modules to /usr/lib/kabbit
# - copy executable to /usr/sbin
# - copy config template to /etc
# - copy start/stop script to /etc/init.d
#

import sys
import os
import shutil
from time import sleep

import fileinput
import string
from os.path import join
from pwd import getpwnam

import os

LIB_DIR="/usr/lib/kabbit"

LOG_DIR="/var/log/kabbit"

print "Welcome to the kabbit Installer.This is free software,you can (re)distribute it under the terms of the GPL\n";

if os.geteuid() <> 0:
	print "Please be sure to run this installer as root."
	sys.exit(0)

#look for the xmpppy module
try:
	import xmpp
except Exception:
	print "[ERROR] The Python xmpppy module was not found. Please install it before you install kabbit.\nSee http://xmpppy.sourceforge.net/ for further informations.\n"
	sys.exit(0)

kabbit_uid=0
kabbit_gid=0

#check if user "kabbit" exists
try:
	pwd_entry=getpwnam("kabbit")
	kabbit_uid=pwd_entry[2]
	kabbit_gid=pwd_entry[3]

	if pwd_entry[6] != "":
		print "WARNING: There is an shell entry for user kabbit in /etc/passwd. This may be a security problem."


except KeyError:

	ShellObj = os.popen('/usr/sbin/useradd kabbit')
	ShellObj.close()

	try:
		pwd_entry=getpwnam("kabbit")
		kabbit_uid=pwd_entry[2]
		kabbit_gid=pwd_entry[3]

	except KeyError:
		print "Failed to create user 'kabbit'.Aborting."
		sys.exit(1)



#copy our own modules to /usr/lib/kabbit
#delete complete folder to prevent problems with old versions
if not os.path.isdir(LIB_DIR):
	os.mkdir(LIB_DIR)
	os.chown(LIB_DIR,kabbit_uid,kabbit_gid)

if not os.path.isdir("/usr/lib/kabbit/plugins"):
	os.mkdir("/usr/lib/kabbit/plugins")
	os.chown(LIB_DIR,kabbit_uid,kabbit_gid)

#copy plugins
shutil.copyfile("plugins/song.py","/usr/lib/kabbit/plugins/song.py")
shutil.copyfile("plugins/core.py","/usr/lib/kabbit/plugins/core.py")
shutil.copyfile("plugins/mail_notify.py","/usr/lib/kabbit/plugins/mail_notify.py")

#copy modules
shutil.copyfile("./config.py","/usr/lib/kabbit/config.py")
shutil.copyfile("./plugin.py","/usr/lib/kabbit/plugin.py")
shutil.copyfile("./kabbit_log.py","/usr/lib/kabbit/kabbit_log.py")

#init.d skript
shutil.copyfile("./kabbit.sh","/etc/init.d/kabbit")
os.chmod("/etc/init.d/kabbit",0711)

#our main executable
shutil.copyfile("./kabbit.py","/usr/sbin/kabbit")
os.chmod("/usr/sbin/kabbit",0711)
os.chown("/usr/sbin/kabbit",kabbit_uid,kabbit_gid)

#copy the configuration example
#Check for /etc/kabbit.conf
if os.path.isfile("/etc/kabbit.conf"):
	print "Configfile /etc/kabbit.conf already exists. Do you want to overwrite it? y/n  (Your old configuration gets lost)"
	if raw_input() != "y":
		print "Not overwriting\n"
	else:
		print "New configfile generated"
		shutil.copyfile("./kabbit.conf.tmpl","/etc/kabbit.conf")
else:
	shutil.copyfile("./kabbit.conf.tmpl","/etc/kabbit.conf")

#create pid file (used for clean startup)
if not os.path.isfile("/var/run/kabbit.pid"):
	file_handle = open("/var/run/kabbit.pid", "w")
	file_handle.write(" ")
	file_handle.close
	os.chown("/var/run/kabbit.pid",kabbit_uid,kabbit_gid)

#create logging directory
if not os.path.isdir(LOG_DIR):
	os.mkdir(LOG_DIR)
	os.chown(LOG_DIR,kabbit_uid,kabbit_gid)

if not os.path.isfile("/etc/rc2.d/S90kabbit"):
	print "Do you want kabbit to start automatically at boottime ? This will create bootup skripts in /etc/rc2.d/ "
	if raw_input() == "y":
		os.link("/etc/init.d/kabbit","/etc/rc2.d/S90kabbit")

		if not os.path.isfile("/etc/rc2.d/K20kabbit"):
			os.link("/etc/init.d/kabbit","/etc/rc2.d/K20kabbit")




print "Configuration successful !"

sys.exit(0)



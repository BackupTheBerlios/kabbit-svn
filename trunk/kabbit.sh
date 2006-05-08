#!/bin/bash
# start/stop Skript for kabbit
# Sebastian Moors 23.02.2006
# sebastian.moors@gmail.com

if [ $# -lt 1 ]; then
	echo "Usage: /etc/init.d/kabbit start | stop"
	exit 1
fi

binfile=/usr/sbin/kabbit
pidfile=/var/run/kabbit.pid

if [ ! -x $binfile ]; then
	echo "kabbit binary not found"
	exit 1
fi

if [ ! -f $pidfile ]; then
	touch $pidfile
fi

if [ ! -w $pidfile ]; then
	exit 1
fi

chown kabbit $pidfile

if [  $1 == "start" ]; then
	start-stop-daemon -x $binfile  --start --pidfile $pidfile -c kabbit
fi

if [ $1 == "stop" ]; then
	start-stop-daemon  --stop --pidfile $pidfile
fi

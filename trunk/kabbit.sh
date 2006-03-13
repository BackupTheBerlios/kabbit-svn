#!/bin/bash
# start/stop Skript for kabbit
# Sebastian Moors 23.02.2006
# sebastian.moors@gmail.com


if [ $1 == "start" ]; then
	pid=$(cat "/var/run/kabbit.pid" 2> /dev/null)

	if [ $(ps aux | grep $pid 2> /dev/null | wc -l) -gt 1 ]; then
		echo "kabbit is already running with pid $pid"
	else
		/usr/sbin/kabbit
	fi

fi

if [ $1 == "stop" ]; then
	pid=$(cat "/var/run/kabbit.pid")
	if [ $pid > 1 ]; then
		kill $pid
	fi

fi
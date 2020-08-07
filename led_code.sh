#!/bin/bash

for i in {1..10}
do
	echo "1" > /sys/class/leds/led0/brightness
	sleep 0.5
	echo "0" > /sys/class/leds/led0/brightness
	sleep 0.5
done

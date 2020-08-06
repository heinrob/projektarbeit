#!/bin/bash

systemctl stop sniff.service

echo "0" > /sys/class/leds/led0/brightness

rm /home/pi/projektarbeit/data*.json
rm /home/pi/projektarbeit/sniff.log
echo "0" > /home/pi/projektarbeit/restart_counter.txt

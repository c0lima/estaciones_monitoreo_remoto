#!/usr/bin/python

from gpiozero import Button
from signal import pause
from subprocess import check_call
import os

def shutdown():
	os.system("sudo shutdown -h now")

def reset():
	os.system("sudo shutdown -r now")


button_poweroff = Button(6, hold_time=3)
button_reset = Button(13, hold_time=3)

button_poweroff.when_held=shutdown
button_reset.when_held=reset

pause()

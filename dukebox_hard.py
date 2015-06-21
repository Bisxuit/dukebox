#! /usr/bin/env python

import RPi.GPIO as g
import time
import os,sys
import dukebox


# TODO - lock callback state
# TODO - incorporate network monitor
# TODO - startup MPD properly
# TODO - start this script
# TODO - use PIGPIO instead
# TODO - logging and robustness

def red_button(channel,p):
	detect_state(p)
	p.advance(p.mode,p.genre)
	

def green_button(channel,p):
	detect_state(p)
	p.c.pause()


def dial_change(channel,p):
	# Wait for a random time?
	if not p.speak_lock:
		p.speak_lock = True
		temp_mode = p.mode
		temp_genre = p.genre
		detect_state(p)
		if temp_mode<>p.mode:
			p.speak(p.mode+' mode')
		if temp_genre<>p.genre:
			p.speak(p.genre)
		p.speak_lock = False


def detect_state(p):
	#output_pin_state()
	
	# Nots because buttons will ground pins
	#mode_pins = [10,12,8,0]
	if not g.input(10):
		p.mode = "album"
		p.speak_option="none"
	elif not g.input(12):
		p.mode = "track"
		p.speak_option="none"
	elif not g.input(8):
		p.mode = "radio"
		p.speak_option="none"
	else:
		# Special mode
		p.mode = "album"
		p.speak_option="artist"
		
	#genre_pins = [7,0,5,3,19,11,13,15,21,26,23,24]
	if not g.input(7):
		p.genre = "All"
	elif not g.input(5):
		p.genre = "Heavy Rock"
	elif not g.input(3):
		p.genre = "Classic Rock"
	elif not g.input(19):
		p.genre = "Mellow"
	elif not g.input(11):
		p.genre = "Soft Rock"
	elif not g.input(13):
		p.genre = "Pop"
	elif not g.input(15):
		p.genre = "Folk"
	elif not g.input(21):
		p.genre = "Dance"
	elif not g.input(26):
		p.genre = "Classical"
	elif not g.input(23):
		p.genre = "Musical"
	elif not g.input(24):
		p.genre = "Opera"
	else:
		# Artefact of poorly chosen soldering (this pin not actually connected) - should be second position
		# TODO - resolder so first or last pin is zero
		p.genre = "Rock"
		#pass	
	

def output_pin_state():
	genre_pins = [7,5,3,19,11,13,15,21,26,23,24]
	x = ""
	for n in genre_pins:
		if not(g.input(n)):
			x = x+"#"
		else:
			x = x+"_"

	x = x+"  "
	mode_pins = [10,12,8]
	for n in mode_pins:
		if not(g.input(n)):
			x = x+"#"
		else:
			x = x+"_"
	
	print x
	

def main(server):
	# Use P1 header pin numbering convention
	g.setmode(g.BOARD)

	# Set which pins are inputs
	input_pins = [3,5,7,11,13,15,19,21,23,8,10,12,16,22,24,26]
		
	#try:
	# Set all the input pins to be pulled up (grounded when activated)
	for n in input_pins:
		g.setup(n, g.IN, pull_up_down=g.PUD_UP)
	print "+ Pi pins set up"
		
	# Create an instance of the player class	
	p = dukebox.player(server)
	
	# Detect current settings
	detect_state(p)

	# Define callbacks for the two buttons and dial movement
	for n in input_pins:
		if n == 16:
			g.add_event_detect(n, g.FALLING, callback=lambda x: red_button(n,p), bouncetime=500)
		elif n == 22:
			g.add_event_detect(n, g.FALLING, callback=lambda x: green_button(n,p), bouncetime=500)
		else:
			#TODO - stop this being called twice at the same time
			# Dial change event (doesn't pick up zero position)
			g.add_event_detect(n, g.RISING, callback=lambda x: dial_change(n,p), bouncetime=500)


	# Main loop - basically just waiting for interupts
	running = True
	while running:
		time.sleep(2)
	#except:
	#	print "Crashed for some reason"

	#finally:
	g.cleanup()


if __name__ == '__main__':
	if len(sys.argv)>1:
		main(sys.argv[1])
	else:
		main('localhost')

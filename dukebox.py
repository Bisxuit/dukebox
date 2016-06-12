#!/usr/bin/env python
# Dukebox 2016-06-12
# This file is the main desktop interface that launches a pygame window to interact with an MPD server.


import dukebox_player
import dukebox_graphics
import pygame as pyg
import sys
	
	
# TODO - disconnection behaviour (won't exit)
# BUG - sometimes only musical albums are queued on startup


def main(server):
	# Create an instance of the player class	
	p = dukebox_player.player(server)
	pyg.init()
	# Create an instance of the display class
	d = dukebox_graphics.display(p.size,p.server,p)
	#print "+ Display loaded"
			
	d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)

	# Main loop - basically just waiting for key events
	last_t = 0
	running = True
	while running:
		for this_event in pyg.event.get():
			last_event = pyg.time.get_ticks()
			if not(event_handler(p,d,this_event)):
				running = False
				return 1
				
		# Do regular updates (frequency alterable in config)
		t = pyg.time.get_ticks()
		if t-last_t>p.update_time:
			last_t = t
			if t-last_event>p.screensaver_time and p.screensaver_time<>0:
				d.update_screensaver(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)
				# Reduce processor load
				pyg.time.wait(1000)
			else:
				d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)


			
def event_handler(p,d,this_event):
	if this_event.type==pyg.QUIT:
		print "+ Quitting from event"
		return 0
	elif this_event.type==pyg.VIDEORESIZE:
		# Screen resize event
		d.size = this_event.dict['size']
		screen = pyg.display.set_mode(d.size,pyg.RESIZABLE)
		d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)
	elif this_event.type==pyg.KEYUP:
		pass
	elif this_event.type==pyg.KEYDOWN:
		if this_event.key==pyg.K_q:
			print "+ Quitting from key press"
			return 0
		elif this_event.key==pyg.K_u:
			# Update MPD and Dukebox album list
			p.generate_album_list()
		elif this_event.key==pyg.K_e:
			p.mode = "album"
			d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)
		elif this_event.key==pyg.K_t:
			p.mode = "track"
			d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)
		elif this_event.key==pyg.K_r:
			# Play radio
			p.mode = "radio"
			p.advance(p.mode,p.genre)
		elif this_event.key==pyg.K_f:
			d.toggle_fullscreen()
		elif this_event.key==pyg.K_g:
			# Toggle simple graphics
			p.set_graphics_mode()
		elif this_event.key==pyg.K_m:
			# Move to different player
			move_player(p,d)
		elif this_event.key==pyg.K_p:
			# Edit track info in external program
			p.open_picard()
		elif this_event.key==pyg.K_LCTRL:
			p.speak_track_info(True)
		elif this_event.key==pyg.K_SPACE:
			p.c.pause()
		elif this_event.key==pyg.K_x:
			# Print a load of stats to terminal
			p.output_stats()
		elif this_event.key==pyg.K_s:
			# Switch to album search screen and allow for quitting from this screen
			if not(p.text_search(d)):
				return 0
		elif this_event.key==pyg.K_a:
			# Change speech option
			if p.speak_option=="all":
				p.speak_option="artist"
			elif p.speak_option=="artist":
				p.speak_option="none"
			elif p.speak_option=="none":
				p.speak_option="all"
			else:
				p.speak_option="none"
			p.speak("Speak set to "+p.speak_option)
		elif this_event.key==pyg.K_RIGHT:
			# Next track
			p.c.next()
		elif this_event.key==pyg.K_LEFT:
			# Previous track
			p.c.previous()
		elif this_event.key==pyg.K_DOWN:
			# Go back an album
			p.retreat()
		elif this_event.key==pyg.K_UP:
			# Skip to next album or track depending on mode
			p.advance(p.mode,p.genre)
		elif this_event.key==pyg.K_ESCAPE:
			# Play an album of any genre and switch to album mode
			p.advance("album","All")
		elif this_event.key==pyg.K_BACKSPACE:
			# Undo last action (only one deep)
			p.undo()
		elif this_event.key==pyg.K_EQUALS:
			p.set_volume(+5)
		elif this_event.key==pyg.K_MINUS:
			p.set_volume(-5)
		elif this_event.key==pyg.K_DELETE:
			# Switch to track mode
			p.advance("track","All")
		# Function and number keys have been assigned to a genre already
		# Use their numerical enums to find the relevant genre
		elif this_event.key>=pyg.K_F1 and this_event.key<=pyg.K_F12:
			i = this_event.key-pyg.K_F1
			p.advance(p.mode,p.k[0+i][1])
		elif this_event.key>=pyg.K_1 and this_event.key<=pyg.K_9:
			i = this_event.key-pyg.K_1
			p.advance(p.mode,p.k[12+i][1])
		elif this_event.key==pyg.K_0:
			print p.k
			# TODO - fix crash when there aren't this many genres
			p.advance(p.mode,p.k[21][1])
		
		# Display update
		d.update(p.c.currentsong(),p.c.status(),p.get_battery_level(),p)
		
		# TODO - play the rest of this album (when in track mode)
		# Add/replace mode switch
		# Choose radio station
		# Enqueue mode
		# Longplayer
	return 1


def move_player(p,d):
	# Take or give local player to remote player (assumed to be raspberrypi)
	# Assumes that music libraries are the same
	# TODO - make fuzzier, define servers in config file
	p.save_state()
	p.c.pause()
	p.disconnect()
	
	old_server = p.server
	if old_server=="192.168.1.76":
		p.server = "localhost"
	elif old_server=="localhost":
		p.server = "192.168.1.76"
	else:
		print "# Don't know how to switch from server <",p.server,">"

	if p.connect():
		p.undo()
		d.set_caption(p.server)
		p.read_server_config()
	else:
		p.server = old_server
		p.connect()
		p.c.play()


if __name__ == '__main__':
	if len(sys.argv)>1:
		main(sys.argv[1])
	else:
		main('localhost')

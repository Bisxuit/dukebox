#!/usr/bin/env python
# Dukebox v2.7.4 2015-05-08

import dukebox_graphics

import pygame as pyg
from mpd import MPDClient

import sys
import os
import time
import subprocess
from random import seed
from random import shuffle
	
import urllib
import pprint
	
class player:
	def __init__(self,server):
		# Parameters
		self.config_dir = os.path.expanduser("~")+"/.dukebox/"
		self.server = server
		self.create_time = time.time()
		self.read_config()

		# Connect to MPD
		self.c = MPDClient()              
		self.c.timeout = 10
		self.c.idletimeout = None
		self.connect()
		
		status = self.c.status()
		if status.get("state")!="stop":
			temp = self.c.currentsong()
			self.genre = "All"
			self.last_genre = ""
			if status.get("random")=="1":
				print "+ Appear to be in track mode"
				self.mode = "track"
			else:
				self.mode = "album"
			# TODO - radio mode
			self.last_mode = ""
			self.last_song = temp.get("id")
			self.last_pos  = status.get("elapsed")
		else:		
			self.genre = "All"
			self.last_genre = ""
			self.mode = "album"
			self.last_mode = ""

		self.i=dict()
		self.n=dict()
		self.read_album_list()
		# List that changes depending on the genre selected
		self.some_albums = list(self.albums)
		# List of all albums that remains static for text search
		self.sort_albums = list(self.albums)
		self.album_art_stub = ""
		self.track_lengths = []

		seed()
		shuffle(self.albums)
		
		print "+ Album list read: "+str(len(self.albums))


	def __del__(self):
		# Close the socket
		if self.connected:
			self.disconnect()
		
		
	def connect(self):
		print "+ Connecting to <"+self.server+">"
		try:
			self.c.connect(self.server, 6600)
			#print "+              ...connected"
			self.connected = True
			self.connected = True
			return True
		except:
			print "# Could not connect"
			self.connected = False
			return False
	
	
	def disconnect(self):
		print "+ Disconnecting from <"+self.server+">"
		self.c.close()
		self.c.disconnect()
			
		
	def read_config(self):
		# Defaults
		width = 1024
		height = 550
		self.fullscreen = False
		self.graphics = "simple"
		self.speak_option = "none"
		self.try_reading_battery = True
		self.screensaver_time = 30000
		
		# Read the Dukebox config file
		config_file = self.config_dir+"dukebox.conf"
		if os.path.isfile(config_file):
			for line in open(config_file):
				if line[0]!="#":
					try:
						if "width" in line:
							width = int(line.split("=")[-1].strip())
						elif "height" in line:
							height = int(line.split("=")[-1].strip())
						elif "fullscreen" in line:
							self.fullscreen = bool(line.split("=")[-1].strip())
						elif "speak_option" in line:
							self.speak_option = (line.split("=")[-1].strip()).lower()
						elif "graphics" in line:
							self.graphics = line.split("=")[-1].strip().lower()
						elif "screensaver_time" in line:
							self.screensaver_time = int(line.split("=")[-1].strip())
					except:
						print "# Error reading config file: "+config_file
						print "# Line: "+line
		self.size = (width,height)
		self.read_server_config()
		

	def read_server_config(self):
		# Defaults
		self.folder = os.path.expanduser("~")+"/Music/"
		self.update_time = 500
		
		# Read specific config file for this server
		server_config = self.config_dir+self.server
		print server_config
		if os.path.isfile(server_config):
			for line in open(server_config):
				if line[0]!="#":
					try:
						if "update_time" in line:
							self.update_time = int(line.split("=")[-1].strip())
						elif "folder" in line:
							self.folder = line.split("=")[-1].strip()
					except:
						print "# Error reading server config file: "+server_config
						print "# Line: "+line
		self.music_list = self.folder+".music_list"
		print "+ Using music list: "+self.music_list
		
		
	def advance(self,mode,genre):
		test_speak_mode = not mode==self.mode
		test_speak_genre = not genre==self.genre
		test_speak_track = False	
		
		if genre=="": genre=="All"

		if mode=="track":
			self.c.stop()
			self.c.clear()
			#TODO - sub
			if genre=="All":
				self.c.add("/")			
			else:
				self.c.findadd("genre",genre)
			self.c.random(1)
			self.c.play()
			self.genre = genre
			self.mode = mode
			
		elif mode=="album" or mode=="radio":
			if genre=="All":
				self.some_albums = list(self.albums)
				# Increment counter down through list
				if not "All" in self.i:
					self.i["All"]=len(self.some_albums)-1
				else:
					self.i["All"] = self.i["All"]-1

				if self.i["All"]<0:
					self.i["All"]=len(self.some_albums)-1
			else:
				# Build album list if genre has changed
				if not self.last_genre==genre:
					self.some_albums = []
					for a in self.albums:
						if a[0]==genre:
							self.some_albums.append(a)

				# Increment counter up through sub list
				if not genre in self.i:
					self.i[genre]=0
				else:
					self.i[genre]=self.i[genre]+1
				
				if self.i[genre]>len(self.some_albums)-1:
					self.i[genre]=0
				
			if len(self.some_albums)>0:
				self.play_album(self.some_albums[self.i[genre]][2],self.some_albums[self.i[genre]][1])
				test_speak_track=True
				self.genre = genre
				self.mode = mode
			else:
				print "# No albums in genre "+genre

		# Speaking done like this to allow display update first - TODO threads
		#self.display.update(self.c.currentsong(),self.c.status(),self.get_battery_level(),self)
		if test_speak_mode:
			self.speak(mode+' mode')
		if test_speak_genre:
			self.speak(genre)
		if test_speak_track:
			self.speak_track_info(False)


	def retreat(self):
		if self.mode=="album":
			if self.genre=="" or self.genre=="All":
				# Increment counter up through list
				if not "All" in self.i:
					self.i["All"]=0
				else:
					self.i["All"] = self.i["All"]+1
				
				if self.i["All"]>len(self.albums)-1:
					self.i["All"]=0
			else:
				# Increment counter down through sub list
				if not self.genre in self.i:
					self.i[self.genre]=0
				else:
					self.i[self.genre]=self.i[self.genre]-1
				
				if self.i[self.genre]<0:
					self.i[self.genre]=len(self.some_albums)-1

			if len(self.some_albums)>0:
				self.play_album(self.some_albums[self.i[self.genre]][2],self.some_albums[self.i[self.genre]][1])
	
	
	def text_search(self,d):
		# Interface for searching albums
		search_string = ""
		running = True
	
		while running:
			# Downselect albums and list those that will fit on screen
			if search_string=="":
				matching_albums = ""
			else:
				matching_albums = [s for s in self.sort_albums if search_string.lower() in s[2].lower()]

			# Loop waiting for events
			for this_event in pyg.event.get():
				if this_event.type==pyg.QUIT:
					print "+ Quitting from text search"
					return False
				elif this_event.type==pyg.VIDEORESIZE:
					self.size = this_event.dict['size']
					screen=pyg.display.set_mode(self.size,pyg.RESIZABLE)
				elif this_event.type==pyg.KEYDOWN:
					if this_event.key==pyg.K_ESCAPE:
						running = False
					elif this_event.key==pyg.K_BACKSPACE:
						search_string=search_string[0:-1]
					elif (this_event.key>=pyg.K_a and this_event.key<=pyg.K_z) or this_event.key==pyg.K_SPACE:
						# Letters to search on
						search_string=search_string+chr(this_event.key)
					elif this_event.key>=pyg.K_F1 and this_event.key<=pyg.K_F12:
						# Function keys to select albums
						i = this_event.key-pyg.K_F1
						if len(matching_albums)>=i:
							self.play_album(matching_albums[i][2],matching_albums[i][1])
							running = False
					elif this_event.key==pyg.K_RETURN:
						# Special case if only one match
						if len(matching_albums)==1:
							self.play_album(matching_albums[0][2],matching_albums[0][1])
							running = False
					else:
						# Unknown key
						#print this_event.key
						pass
			d.update_search(search_string,matching_albums,self)
			
		self.mode = "album"
		return True


	def play_radio(self):
		self.save_state()
		self.speak("Attempting to play radio")
		# TODO - options for different stations
		f=urllib.urlopen("http://www.radiofeeds.co.uk/bbc6music.pls")
		s=f.read()
		f.close()
		url=""
		# Grep File1
		for l in s.split("\n"):
			if "File1=" in l:
				url=l.split("?")[0].replace("File1=","")
				
		if url!="":
			print "+ Playing: "+url
			self.c.stop()
			self.c.clear()
			self.c.add(url)
			self.c.play()
			self.mode="radio"
		
		else:
			self.speak("Could not find radio feed")


	def play_album(self,album,artist):
		self.save_state()
					
		# TODO - check album is ok before adding
		self.c.stop()
		self.c.clear()
		self.c.random(0)
		self.c.findadd('album',album,'artist',artist)
		self.c.play()
		
		self.generate_track_lengths()
		
		
	def save_state(self):
		# TODO - write to config file	
		temp = self.c.currentsong()
		status = self.c.status()

		# Save current state
		self.last_mode   = self.mode
		self.last_genre  = self.genre
		self.last_album  = temp.get("album")
		self.last_artist = temp.get("artist")
		self.last_song   = temp.get("pos")
		self.last_time 	 = status.get("elapsed")
	
	
	def undo(self):
		# Reverse the last action (i.e. back to the last time save_state() was called)
		self.c.stop()
		self.c.clear()
		this_song = self.last_song
		this_time = self.last_time

		if self.last_mode=="track":
			if self.genre=="" or self.genre=="All":
				self.c.add("/")			
			else:
				self.c.findadd("genre",self.genre)
			self.c.random(1)
			self.c.play()
		elif self.last_mode=="album":
			self.mode = "album"
			self.c.random(0)
			self.play_album(self.last_album,self.last_artist)
		
		# Attempt to seek to the previous track and album
		try:
			if this_song and this_time:
				self.c.seek(this_song,int(round(float(this_time))))
			elif this_song:
				self.c.play(this_song)
		except:
			print "# Could not seek to song and track"
		
		
	def generate_track_lengths(self):
		# Build list of track lengths (used for display)
		self.track_lengths = []
		self.track_names = []
		for track in self.c.playlistid():
			self.track_lengths.append(float(track.get("time","")))
			self.track_names.append(track.get("title",""))


	def generate_album_list(self):
		print "+ Updating MPD database"
		self.c.update() #need to wait for this somehow

		# TODO - check for file
		fid = open(self.music_list,'wt')
		all_genres = list(self.c.list('genre'))
		self.albums=[]
		print "+ Generating database..."
		t_songs = 0
		t_albums = 0		
		
		for g in all_genres:
			if not (g=="" or g=="Video"):
				songs = self.c.find('genre',g)
				self.n[g] = len(songs)
				t_songs+=len(songs)
				print "  - "+g+": "+str(len(songs))
				for s in songs:
					# Get the artist and album for this song, with defaults if blank or absent
					temp = [g,s.get('artist','Various'),s.get('album','Other')]
					if not temp in self.albums:
						fid.write(temp[0]+'/'+temp[1]+'/'+temp[2]+'\n')
						t_albums+=1
						self.albums.append(temp)

		print "+ "+str(len(self.n))+" genres found"
		print "+ "+str(t_albums)+" albums found"
		print "+ "+str(t_songs)+" songs found"
		self.genre="All"

		fid.close
	

	def read_album_list(self):
		# Update available album list
		if os.path.isfile(self.music_list):
			fid = open(self.music_list,'rt')
			self.albums=[]
			for	a in fid.readlines():
				a=a.replace('\n','')
				self.albums.append(a.split("/"))
			fid.close()
		else:
			print "# Database not found. Generating now."
			self.generate_album_list()
		self.set_buttons()


	def set_buttons(self):
		# Which function keys control which genres
		g = []
		c = []
		for a in self.albums:
			g.append(a[0])
			
		# Count number of albums in each genre and sort with magic
		g1=set(g)
		for g2 in g1:
			c.append(g.count(g2))
		t = sorted(zip(c,g1))

		n_genre = 22
		self.k=[None]*n_genre
		if len(t)!=0:
			for n in range(0,n_genre):
				self.k[n]=t.pop()
				if len(t)==0:
					break
			

	def speak_track_info(self,test_all):
		if self.speak_option=="none":
			return
		temp = self.c.currentsong()
		alb = temp.get("album","")
		art = temp.get("artist","")
		song = temp.get("title","")

		# Choose a language heuristically - TODO, use language tag
		if art == "Richard Wagner" or art == "Rammstein":
			# German
			v1="de+f4"
			v2="de+m4"
		elif art == "Sigur ros":
			# Icelandic
			v1="is+f2"
			v2="is+f3"
		elif art == "Ensemble Orchestra Synaxis":
			# French
			v1="en+f2"
			v2="fr+f3"
		elif art == "Puccini":
			# Italian
			v1="it+f2"
			v2="it+f3"
		else:
			# English
			v1="en+f2"
			v2="en+f3"
	
		# Swap the position of "the"
		if art[-5:] == ", the" or art[-5:] == ", The":
			art="The " + art[0:-5]

		# TODO - use python plugin (on remote server?)
		if test_all:
			subprocess.call('espeak '+'"'+song+'" -s 150 -v '+ v1 + '>/dev/null 2>&1',shell=True)
		if self.speak_option == "artist" or self.speak_option == "all" or test_all:
			subprocess.call('espeak '+'"'+art+'" -s 130 -v '+ v1 + '>/dev/null 2>&1',shell=True)
		if self.speak_option == "all" or test_all:
			subprocess.call('espeak '+'"'+alb+'" -s 150 -v '+ v2 + '>/dev/null 2>&1',shell=True)


	def speak(self,this_text):
		print "+ "+this_text
		#text = self.font2.render(this_text,True,self.colour['white'],self.colour['black']) #a surf
		#self.surf.blit(text,(10,150))
		#pyg.display.update()
		if self.speak_option!="none":
			devnull = open(os.devnull, 'white')
			subprocess.call('espeak "'+this_text+'" -s 150 -v en+f2',shell=True, stdout=devnull, stderr=devnull)
	

	def set_volume(self,delta_vol):
		status = self.c.status()
		if status.get('state')!="stop":
			volume = int(status.get("volume"))
			volume+=delta_vol
			if volume>100:
				volume = 100
			elif volume<0:
				volume=0
			self.c.setvol(volume)
		
		
	def output_stats(self):
		#print(self.genre,self.last_genre,self.mode,self.last_mode,self.speak_option)
		print "+ Status:"
		pp = pprint.PrettyPrinter(indent=3)
		#pp.pprint(self)
		#pp.pprint(self.sort_albums)
		pp.pprint(self.c.stats())
		pp.pprint(self.c.status())
		pp.pprint(self.c.currentsong())
		

	def toggle_fullscreen(self):
		pyg.display.toggle_fullscreen()


	def set_graphics_mode(self):
		if self.graphics == "simple":
			self.graphics = "full"
		else:
			self.graphics = "simple"
			
			
	def open_picard(self):
		# Edit metadata for this album (in Picard)
		temp = self.c.currentsong()
		uri=temp.get("file","")
		temp = uri.split("/")
		uri=""
		for n in range(0,len(temp)-2):
			uri = uri+temp[n]+"/"
		# Special case for various - select album as well
		if temp[n]=="Various":
			uri = uri+temp[n+1]
		arg = "picard "+'"'+self.folder+uri+'"'
		print "+ Opening Picard ("+arg+")"
		subprocess.call(arg,shell=True)
		
		
	def get_battery_level(self):
		if self.try_reading_battery:
			# System dependent options (Crunch bang vs Ubuntu 14.04)
			if os.path.isdir("/sys/class/power_supply/"):
				if os.path.isfile("/sys/class/power_supply/BAT0/charge_now"):
					battery = "BAT0"
				elif os.path.isfile("/sys/class/power_supply/BAT1/charge_now"):
					battery = "BAT1"
				else:
					print "# Could not find battery in /sys/class/power_supply/"
					self.try_reading_battery = False
					return 0
					
				c = float(open('/sys/class/power_supply/'+battery+'/charge_now','r').read())
				ct = float(open('/sys/class/power_supply/'+battery+'/charge_full','r').read())
				cs = open('/sys/class/power_supply/'+battery+'/status','r').read().lower().strip()
				if cs=="charging" or cs=="charged" or cs=="full":
					return c/ct
				elif cs=="discharging":
					return -1*c/ct
				else:
					print "# Unknown battery state: ",cs
					return 0

			elif os.path.isdir("/proc/acpi/battery/"):
				if os.path.isfile("/proc/acpi/battery/BAT0/state"):
					battery = "BAT0"
				elif os.path.isfile("/proc/acpi/battery/BAT1/state"):
					battery = "BAT1"
				else:
					print "# Could not find battery in /proc/acpi/battery/"
					self.try_reading_battery = False
					return 0
					
				battery_status_file = "/proc/acpi/battery/"+battery+"/state"
				battery_info_file = "/proc/acpi/battery/"+battery+"/info"
				for line in open(battery_status_file):
					if "remaining capacity" in line:
						c = float(line.split(":")[-1].replace("mAh",""))
					elif "charging state" in line:
						cs = line.split(":")[-1].strip()
				for line in open(battery_info_file):
					if "last full capacity" in line:
						ct = float(line.split(":")[-1].replace("mAh",""))
			else:
				print "# Could not find battery in /sys/class/power_supply/"
				self.try_reading_battery = False
				return 0
				
		else:
			return 0
			
			
def event_handler(p,d,this_event):
	if this_event.type==pyg.QUIT:
		print "+ Quitting from event"
		return 0
	elif this_event.type==pyg.VIDEORESIZE:
		# Screen resize event
		p.size = this_event.dict['size']
		screen = pyg.display.set_mode(p.size,pyg.RESIZABLE)
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
			# Queue radio - TODO - new screen with options?
			p.play_radio()
		elif this_event.key==pyg.K_f:
			p.toggle_fullscreen()
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
			p.advance(p.mode,p.k[12][1])
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
	# Assumes that music libraries are the same - TODO - make fuzzier
	p.save_state()
	p.c.pause()
	p.disconnect()
	
	old_server = p.server
	if old_server=="raspberrypi":
		p.server = "localhost"
	elif old_server=="localhost":
		p.server = "raspberrypi"
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
	

def main(server):
	# Create an instance of the player class	
	p = player(server)
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



if __name__ == '__main__':
	if len(sys.argv)>1:
		main(sys.argv[1])
	else:
		main('localhost')

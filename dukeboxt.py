#!/usr/bin/env python

# Dukebox 2016-06-12
# Provides the display class for Dukebox.py for running a Pygame based MPD client

import pygame as pyg
import datetime
import time
import os
import math
from random import randrange
import dukebox_scanner
import dukebox_player

class touchme:
	def __init__(self):
		# Create a pygame window
		self.size = (320,240)
		pyg.init()
				
		self.set_colours()
		self.set_fonts()
		
		
		screen = pyg.display.set_mode(self.size,pyg.RESIZABLE)
		pyg.mouse.set_visible(False)
		pyg.time.Clock()
		self.surf = pyg.display.get_surface()
		self.surf.fill(self.colour['black'])
		
		self.music = dukebox_player.player("192.168.1.76")

		# Network scanner client
		# Just read the text file output by cron job (possibly on another device), as sudo is needed		
		self.scanner = 	dukebox_scanner.scanner()
		self.scanner.read_name_lookup()
		
		# Nest client
		self.nest = heatme()
		
		
	def __del__(self):	
		# Quit pygame
		pyg.quit()
	
		
	def set_fonts(self):
		self.font60 = pyg.font.Font(pyg.font.match_font('arial'),60)
		self.font40 = pyg.font.Font(pyg.font.match_font('arial'),40)
		self.font20 = pyg.font.Font(pyg.font.match_font('arial'),20)
		self.font16 = pyg.font.Font(pyg.font.match_font('arial'),16)
		self.font12 = pyg.font.Font(pyg.font.match_font('arial'),12)
				
		
	def set_colours(self):
		self.colour = {}
		self.colour['black'] =(pyg.Color(0,0,0,128)) 		# black (BK)
		self.colour['white'] =(pyg.Color(255,255,255,128))	# white (Most text, controls)
		self.colour['dark red']=(pyg.Color(120,0,0,128))	# dark green (Highlights)
		self.colour['red'] =(pyg.Color(255,0,0,128))		# red (Messages)
		self.colour['dark green']=(pyg.Color(0,120,0,128))	# dark green (Highlights)
		self.colour['green'] =(pyg.Color(0,255,0,128))		# green (Selected)
		self.colour['grey']=(pyg.Color(64,64,64,128))		# grey (Button backgrounds)
		self.colour['blue']=(pyg.Color(90,110,150,128))		# blue (system state)
		
		
	def update(self): 
		tx = int(self.size[0])
		ty = int(self.size[1])

		# Clear screen
		s = pyg.Surface(self.size)
		s.fill(self.colour['grey'])
		self.surf.blit(s, (0,0))
		
		# Top left - time
		self.surf.blit(self.display_time(tx/2,ty/2),(0,0))
		
		# Top right - Nest status
		self.surf.blit(self.display_nest(tx/2,ty/2),(tx/2,0))
		
		# Bottom left - network scanner
		self.surf.blit(self.display_scanner(tx/2,ty/2),(0,ty/2))
		
		# Bottom right - MPD status
		self.surf.blit(self.display_music(tx/2,ty/2),(tx/2,ty/2))
		
		pyg.display.update()
	
	
	def display_time(self,tx,ty):
		st = pyg.Surface((tx,ty))
		st.fill(self.colour['grey'])
		
		text = self.font60.render(str(datetime.datetime.now().strftime("%H:%M")),True,self.colour['white'])
		textpos = text.get_rect()
		textpos.centerx = st.get_rect().centerx
		st.blit(text, textpos)
		dy = text.get_height()
		
		text = self.font20.render(str(datetime.datetime.now().strftime("%Y-%m-%d")),True,self.colour['white'])
		textpos = text.get_rect()
		textpos.centerx = st.get_rect().centerx
		textpos.y = dy
		st.blit(text, textpos)
		return st
		
	
	def display_scanner(self,tx,ty):
		st = pyg.Surface((tx,ty))
		st.fill(self.colour['blue']) #set colour on status
		y = 5
		
		t = time.time()
		# Blit picture in colour or grayscale with time away
		for mac in self.scanner.machines:
			time_away  = self.scanner.last_seen[mac]-t+3600 # Nasty hack to sort out timezones (Pi doesn't seem to do it correctly)
			if self.scanner.names[mac][0]<>"." and time_away<24*60*10:
				
				stub = self.scanner.names[mac]+".jpg"
				#if player.album_art_stub!=stub:
				#try:
				if os.path.isfile(stub):
					img_art = pyg.image.load(stub).convert()
				else:
					img_art=pyg.Surface((1,1))
				#except:
				#	print "# Could not load",stub
				#	player.img_art=pyg.Surface((1,1))
				#player.album_art_stub = stub
				
				img_art = pyg.transform.scale(img_art, (30, 40))
				
				# Output to display	
				st.blit(img_art,(5,y))
								
				text = self.font12.render(self.scanner.names[mac],True,self.colour['white'])
				st.blit(text,(45,y))
				y = y+text.get_height()
				
				if time_away<60*10:
					text = self.font12.render('Here',True,self.colour['white'])
				else:
					text = self.font12.render('{:0.0f}'.format(time_away),True,self.colour['white'])
					
				st.blit(text,(45,y))
				y = y+45
		return st		
	
	
	def display_nest(self,tx,ty):
		y = 20
		st = pyg.Surface((tx,ty))
		st.fill(self.colour['dark red']) #set colour from heat on/off
		text = self.font40.render(self.nest.temp,True,self.colour['white'])
		textpos = text.get_rect()
		textpos.centerx = st.get_rect().centerx
		textpos.y = y
		st.blit(text,textpos)
		dy = text.get_height()
		text = self.font20.render("Target: "+"18"+u'\N{DEGREE SIGN}'+"C",True,self.colour['white'])
		textpos = text.get_rect()
		textpos.centerx = st.get_rect().centerx
		textpos.y = y+dy
		st.blit(text, textpos)
		return st
		
	
	def display_music(self,tx,ty):
		song = self.music.c.currentsong()
		status = self.music.c.status()
		st = pyg.Surface((tx,ty))
		st.fill(self.colour['black'])
		if status.get("state")!="stop":
			title = song.get("title",song.get("name","NO TITLE")).decode("utf-8")
			if song.get("artist","").decode("utf-8")!="Various":
				artist = song.get("artist","").decode("utf-8")
			else:
				artist = ""
			album = song.get("album","").decode("utf-8")
			
			# Artist
			text = self.font20.render(artist,True,self.colour['white'])
			st.blit(text,(5,0))
			y = text.get_height()
			
			# Track
			text = self.font12.render(title,True,self.colour['white'])
			st.blit(text,(5,y))
			y = y+text.get_height()
			
			dy = 0
			# Track bar
			if status.get("elapsed","") and song.get("time",""):
				dx = int((tx)*float(status.get("elapsed"))/float(song.get("time")))
				dy = 10
				s = pyg.Surface((tx,dy))
				s.fill(self.colour['grey'])
				st.blit(s, (0,y))
				# Track time elapsed
				s = pyg.Surface((dx,dy))
				if status.get("state")=="play":
					s.fill(self.colour['green'])
				else:
					s.fill(self.colour['dark green'])
				st.blit(s, (0,y))
			y = y+dy
				
			# Album			
			text = self.font12.render(album,True,self.colour['white'])
			st.blit(text,(5,y))
			y=y+text.get_height()

			# Album bar
			t = self.music.track_lengths
			total_t = sum(t)
			if total_t==0:
				self.music.generate_track_lengths()

				total_t = sum(t)
			i = int(status.get("song",""))
			n = int(status.get("playlistlength",""))
							
			if status.get("song","")!="":
				dx = [0]*n
				if len(t)==n:
					# Track lengths probably match current playlist
					for i_x in range(0,n):
						dx[i_x] = float(tx)*t[i_x]/total_t
				else:
					# Track lengths don't match current playlist
					dx = [float(tx)/n]*n
					
				if self.music.mode=="album":# and min(dx)>gap1:
					# Album mode
					gap1=1
					for i_x in range(0,n):
						# Box for each track
						s = pyg.Surface((max(dx[i_x]-gap1,1),dy))
						if i_x==i:
							s.fill(self.colour['green'])
						elif i_x<i:
							s.fill(self.colour['dark green'])
						else:
							s.fill(self.colour['grey'])
						st.blit(s, (int(sum(dx[:i_x])+gap1/2),y))
			
		if status.get("state")=="pause":
			# Pause icon
			dy = int(ty/2)
			dx = int(dy/4)
			s = pyg.Surface((dx,dy))
			s.fill(self.colour['white'])
			st.blit(s, (int(tx/2-1.5*dx),int(dy/2)))
			st.blit(s, (int(tx/2+0.5*dx),int(dy/2)))
		
		return st


class heatme:
	def __init__(self):
		self.temp = "20"+u'\N{DEGREE SIGN}'+"C"
	def update(self):
		self.temp = "20"+u'\N{DEGREE SIGN}'+"C"


def event_handler(d,this_event):
	if this_event.type==pyg.QUIT:
		print "+ Quitting from event"
		return 0
	elif this_event.type==pyg.KEYUP:
		pass
	elif this_event.type==pyg.KEYDOWN:
		if this_event.key==pyg.K_q:
			print "+ Quitting from key press"
			return 0

		# Display update
		d.update()
	return 1


def main():
	# Display client
	d = touchme()
	d.update()
						
	# Main loop - basically just waiting for key events
	last_t = 0
	update_time = 1000
	running = True
	while running:
		for this_event in pyg.event.get():
			last_event = pyg.time.get_ticks()
			if not(event_handler(d,this_event)):
				running = False
				return 1
				
		# Do regular updates (frequency alterable in config)
		t = pyg.time.get_ticks()
		if t-last_t>update_time:
			last_t = t
			d.scanner.read_log()
			d.update()


if __name__ == '__main__':
	main()

#!/usr/bin/env python
# Dukebox v2.7.4 2015-05-08
import pygame as pyg
import datetime
import os
import math
from random import randrange

class display:
	def __init__(self,size,server,player):
		# Create a pygame window
		self.size = size
		self.set_colours()
		self.set_fonts()
		
		screen = pyg.display.set_mode(self.size,pyg.RESIZABLE)
		self.set_caption(server)
		pyg.mouse.set_visible(False)
		pyg.time.Clock()
		self.surf = pyg.display.get_surface()
		self.surf.fill(self.colour['black'])
		
	
	def __del__(self):	
		# Quit pygame
		pyg.quit()
	
	
	def set_caption(self,server):
		pyg.display.set_caption('Dukebox ('+server+')')
	
	
	def set_fonts(self):
		self.font1 = pyg.font.Font(pyg.font.match_font('arial'),48)
		self.font2 = pyg.font.Font(pyg.font.match_font('arial'),24)
		self.font3 = pyg.font.Font(pyg.font.match_font('arial'),13)
		
		
	def set_colours(self):
		self.colour = {}
		self.colour['black'] =(pyg.Color(0,0,0,128)) 		# black (BK)
		self.colour['white'] =(pyg.Color(255,255,255,128))	# white (Most text, controls)
		self.colour['red'] =(pyg.Color(255,0,0,128))		# red (Messages)
		self.colour['dark green']=(pyg.Color(0,120,0,128))	# dark green (Highlights)
		self.colour['green'] =(pyg.Color(0,255,0,128))		# green (Selected)
		self.colour['grey']=(pyg.Color(64,64,64,128))		# grey (Button backgrounds)
		self.colour['blue']=(pyg.Color(90,110,150,128))		# blue (system state)
		
		
	def update(self,song,status,battery_level,player):
		tx = int(self.size[0])
		ty = int(self.size[1])
		y = 0
		gap1 = 6 # Between buttons and other elements
		gap2 = 12 # Between groups of buttons 
		gap3 = 2 # Between genre buttons
			
		# Clear screen
		s = pyg.Surface(self.size)
		s.fill(self.colour['black'])
		self.surf.blit(s, (0,0))
		
		# Start by working down
		if status.get("state")!="stop":
			if player.mode=="radio":
				# Just display station name
				text = self.font1.render(player.radio_stations[player.i["radio"]][0].decode("utf-8"),True,self.colour['white'])
				self.surf.blit(text,(gap2,y))
				dy = text.get_height()
			else:
				# Track details
				text = self.font1.render(song.get("title",song.get("name","NO TITLE")).decode("utf-8"),True,self.colour['white'])
				self.surf.blit(text,(gap2,y))
				dy = text.get_height()

				# Artist details
				if song.get("artist","").decode("utf-8")!="Various":
					text = self.font2.render(song.get("artist","").decode("utf-8"),True,self.colour['white'],self.colour['black'])
					self.surf.blit(text,(tx-text.get_width()-gap2,y))
					py = text.get_height()
				else:
					py = 0
				
				# Album details
				text = self.font2.render(song.get("album","").decode("utf-8"),True,self.colour['white'],self.colour['black'])
				self.surf.blit(text,((tx-text.get_width()-gap2,y+py)))
			
				# Track position
				t = player.track_lengths
				total_t = sum(t)
				if total_t==0:
					player.generate_track_lengths()
					total_t = sum(t)
				
				y = y+dy+gap1
				dy = 20
				if status.get("elapsed","") and song.get("time",""):
					# Background for track time elapsed
					dx = int(tx*float(status.get("elapsed"))/float(song.get("time")))
					s = pyg.Surface((tx,dy))
					s.fill(self.colour['grey'])
					self.surf.blit(s, (0,y))
					# Track time elapsed
					s = pyg.Surface((dx,dy))
					if status.get("state")=="play":
						s.fill(self.colour['green'])
					else:
						s.fill(self.colour['dark green'])
					self.surf.blit(s, (0,y))
					if player.graphics!="simple":
						text = self.font3.render(convert_seconds(song.get("time"))+" / "+convert_seconds(total_t),True,self.colour['black'])
						self.surf.blit(text, (gap1,y+dy/2-text.get_height()/2))

				# Boxes for track number
				y = y+dy+gap1
				i = int(status.get("song",""))
				n = int(status.get("playlistlength",""))
							
				if status.get("song","")!="":
					dx = [0]*n
					dy = 20
					if len(t)==n:
						# Track lengths probably match current playlist
						for i_x in range(0,n):
							dx[i_x] = float(tx)*t[i_x]/total_t
					else:
						# Track lengths don't match current playlist
						dx = [float(tx)/n]*n
					
					if player.mode=="album":# and min(dx)>gap1:
						# Album mode
						for i_x in range(0,n):
							# Box for each track
							s = pyg.Surface((max(dx[i_x]-gap1,1),dy))
							if i_x==i:
								s.fill(self.colour['green'])
							elif i_x<i:
								s.fill(self.colour['dark green'])
							else:
								s.fill(self.colour['grey'])
							if player.graphics!="simple" and i_x!=i:
								text = self.font3.render(player.track_names[i_x],True,self.colour['white'])
								s.blit(text,(gap1,0))
							self.surf.blit(s, (int(sum(dx[:i_x])+gap1/2),y))
					else:
						# Track mode - continuous bar
						s = pyg.Surface((tx,dy))
						s.fill(self.colour['grey'])
						self.surf.blit(s, (0,y))
						if player.mode=="radio":					
							text = self.font2.render('Live radio',True,self.colour['white'])
						else:
							if player.genre=="All":
								text = self.font3.render('All tracks queued ('+str(n)+")",True,self.colour['white'])
							else:
								text = self.font3.render('All '+player.genre+' tracks queued ('+str(n)+')',True,self.colour['white'])
						self.surf.blit(text, (tx/2-text.get_width()/2,y+dy/2-text.get_height()/2))					

			y = y+dy+gap2
			# Display album art
			# TODO - log if missing (or try and fetch)
			stub = player.folder+".covers/"+song.get("artist","")+"-"+song.get("album","")
			if player.album_art_stub!=stub:
				try:
					if os.path.isfile(stub+".png"):
						player.img_art = pyg.image.load(stub+".png").convert()
					elif os.path.isfile(stub+".jpg"):
						player.img_art = pyg.image.load(stub+".jpg").convert()
					else:
						player.img_art=pyg.Surface((1,1))
				except:
					print "# Could not load",stub
					player.img_art=pyg.Surface((1,1))
				player.album_art_stub = stub
			# Output to display	
			self.surf.blit(player.img_art,(gap2,y))
			#if player.graphics=="simple":
			text = self.font2.render(song.get("genre",""),True,self.colour['white'])
			self.surf.blit(text, (gap2,y+player.img_art.get_height()))

		# Display current time
		text = self.font1.render(str(datetime.datetime.now().strftime("%H:%M")),True,self.colour['white'])
		self.surf.blit(text,(tx-text.get_width(),y))
		
		# Battery indicator
		dx = text.get_width()
		dy = 30
		y = y+text.get_height()
		s = self.battery_indicator(dx,dy,battery_level)
		self.surf.blit(s,(tx-text.get_width(),y))

		# Now work up from bottom (as it's less of an issue if the art gets covered up)
		# Volume indicator
		dy = 30
		y = ty-dy
		v = int(status.get("volume"))
		# TODO - make triangular under battery indicator
		if v>=0:
			# Background bar
			s = pyg.Surface((tx,dy))
			s.fill(self.colour['grey'])
			self.surf.blit(s, (0,y))
			# Current volume level
			dx = int(tx*v/100)
			s = pyg.Surface((dx,dy))
			s.fill(self.colour['dark green'])
			self.surf.blit(s, (0,y))
			if player.graphics!="simple":
				# +/- buttons
				text = self.font2.render("-",True,self.colour['white'])
				self.surf.blit(text,(0,ty-dy+(dy-text.get_height())/2))
				text = self.font2.render("+",True,self.colour['white'])
				self.surf.blit(text,(tx-text.get_width(),ty-dy+(dy-text.get_height())/2))

		# If not in clean/simple/car mode
		dy = 60
		y = y-dy-gap2
		
		if player.graphics!="simple":
			if player.mode!="radio":
				# Genre buttons - row 4
				dx = float(tx)/10
				for i_x in range(12,22):
					if player.k[i_x]:
						self.surf.blit(self.option_button(dx,dy,str((i_x-11)%10),str(player.k[i_x][1]),player.genre=="All" or player.genre==player.k[i_x][1]),(int(dx*(i_x-12)),y))

				# Genre buttons - row 3
				dx = float(tx)/12
				y = y-dy-gap3
				for i_x in range(0,12):
					self.surf.blit(self.option_button(dx,dy,"F"+str(i_x+1),str(player.k[i_x][1]),player.genre=="All" or player.genre==player.k[i_x][1]),(int(dx*(i_x)),y))
				
			# Command buttons - row 2
			dx = float(tx)/9
			y = y-dy-gap2
			self.surf.blit(self.option_button(dx,dy,"A","Audio mode",(player.speak_option!="none")),(dx*3,y))
			self.surf.blit(self.option_button(dx,dy,"U","Update",False),(dx*4,y))
			self.surf.blit(self.option_button(dx,dy,"S","Search",False),(dx*5,y))
			self.surf.blit(self.option_button(dx,dy,"F","Full screen",False),(dx*6,y))
			self.surf.blit(self.option_button(dx,dy,"Q","Quit",False),(dx*8,y))
		
			# Mode buttons - row 1
			dx = float(tx)/9
			y = y-dy-gap2

			#self.option_button(dx*2,y,dx,dy,"G","Graphics mode",False)
			self.surf.blit(self.option_button(dx,dy,"Esc","Play an album",False),(dx*3,y))
			self.surf.blit(self.option_button(dx,dy,"E","Album mode",(player.mode=="album")),(dx*4,y))
			self.surf.blit(self.option_button(dx,dy,"R","Radio",(player.mode=="Radio")),(dx*5,y))
			self.surf.blit(self.option_button(dx,dy,"T","Track mode",(player.mode=="track")),(dx*6,y))
			self.surf.blit(self.option_button(dx,dy,"Del","Shuffle tracks",False),(dx*7,y))
			
		if status.get("state")=="pause":
			# Pause icon
			dy = int(ty/2)
			dx = int(dy/4)
			s = pyg.Surface((dx,dy))
			s.fill(self.colour['white'])
			self.surf.blit(s, (int(tx/2-1.5*dx),int(dy/2)))
			self.surf.blit(s, (int(tx/2+0.5*dx),int(dy/2)))
			
		pyg.display.update()


	def update_screensaver(self,song,status,battery_level,player):
		tx = int(self.size[0])
		ty = int(self.size[1])
		
		# Clear screen
		s = pyg.Surface(self.size)
		s.fill(self.colour['black'])
		self.surf.blit(s, (0,0))
		
		dx=500
		dy=100
		
		st = pyg.Surface((dx,dy))
		y = 0
		
		# Display current time
		text = self.font1.render(str(datetime.datetime.now().strftime("%H:%M")),True,self.colour['white'])
		st.blit(text,(0,y))
		x=text.get_width() + 4
		y+=text.get_height()
		
		# Battery
		s = self.battery_indicator(text.get_width(),30,battery_level)
		st.blit(s,(0,y))
		
		if status.get("state")=="play":
			y=0
			# Track details
			text = self.font2.render(song.get("title",song.get("name","NO TITLE")).decode("utf-8"),True,self.colour['white'])
			st.blit(text,(x,y))
			y+=text.get_height()

			# Artist details
			if song.get("artist","").decode("utf-8")!="Various":
				text = self.font3.render(song.get("artist","").decode("utf-8"),True,self.colour['white'],self.colour['black'])
				st.blit(text,(x,y))
				y+=text.get_height()
			else:
				py = 0
			
			# Album details
			if player.mode=="album":
				text = self.font3.render(song.get("album","").decode("utf-8"),True,self.colour['white'],self.colour['black'])
				st.blit(text,(x,y))
				
		
		# TODO - bounce the clock, battery monitor, track info and album art around
		self.surf.blit(st,(randrange(tx-dx),randrange(ty-dy)))
		pyg.display.update()


	def update_search(self,search_string,matching_albums,player):
			tx = int(self.size[0])
			ty = int(self.size[1])
			x = 0
			y = 0

			# Clear screen
			s = pyg.Surface((tx,ty))
			s.fill(self.colour['black'])
			self.surf.blit(s, (0,0))
			
			# Search title
			text = self.font2.render("Search albums: ",True,self.colour['dark green'])
			self.surf.blit(text,(x,y))
			dx = text.get_width()
			dy = text.get_height()
			# Search text
			text = self.font2.render(search_string,True,self.colour['green'])
			self.surf.blit(text,(dx,y))
			
			text = self.font2.render(" ",True,self.colour['white'])
			x = 0
			y = y+dy
			dx = text.get_width()
			dy = text.get_height()
			n = int((ty-y)/dy)
			for i in range(0,min(12,min(n,len(matching_albums)))):
				t = "F"+(str(i+1)+": "+matching_albums[i][2]+" - "+matching_albums[i][1]).decode("utf-8")
				text = self.font2.render(t,True,self.colour['white'],self.colour['black'])
				dx = text.get_width()
				dy = text.get_height()
				self.surf.blit(text,(x,y))
				y = y+dy
			if len(matching_albums)>12:
				t = "..."
				text = self.font2.render(t,True,self.colour['white'],self.colour['black'])
				self.surf.blit(text,(x,y))
				
			# Back button
			if player.graphics!="simple":
				dx = 70
				dy = 50
				self.option_button(tx-dx,0,dx,dy,"Esc","Back",True)
					
			pyg.display.update()
		
	
	def option_button(self,dx,dy,text1,text2,selected):
		col_bk = self.colour['grey']
		col_fore = self.colour['white']
		if selected:
			col_edge = self.colour['green']
		else:
			col_edge = self.colour['grey']
		gap = 2
		
		# Outer border
		st = pyg.Surface((dx-2,dy))
		st.fill(col_edge)
				
		# Inner button
		s = pyg.Surface((dx-2-2*gap,dy-2*gap))
		s.fill(col_bk)
		st.blit(s,(gap,gap))
		
		text = self.font3.render(text2,True,col_fore,col_bk)
		dy = text.get_height()
		st.blit(text,(-text.get_width()/2+dx/2,gap))
		text = self.font3.render(text1,True,col_fore,col_bk)
		st.blit(text,(-text.get_width()/2+dx/2,gap+dy))
		return st
		
	
	def battery_indicator(self,dx,dy,c):
		# Battery level indicator
		# Background bar		
		st = pyg.Surface((dx,dy))
		st.fill(self.colour['grey'])
		if c:
			s = pyg.Surface((dx*abs(c),dy))
			if abs(c)>0.4:
				s.fill(self.colour['dark green'])
			else:
				s.fill(self.colour['red'])
			st.blit(s, (0,0))
			# Showing a line if charging
			if c>0:
				s = pyg.Surface((4,dy))
				s.fill(self.colour['green'])
				st.blit(s, (dx*abs(c)-4,0))
		# Make it battery shaped
		s = pyg.Surface((dy/4,dy/4))
		st.blit(s, (dx-dy/4,0))
		st.blit(s, (dx-dy/4,dy-dy/4))
		return st


def convert_seconds(t):
	t = float(t)
	if t>=3600:
		#print math.floor(t/3600),math.floor((t % 3600)/60),int(t % 60)
		return str(int(math.floor(t/3600)))+":"+str(int(math.floor((t % 3600)/60)))+":"+str(int(t % 60))
	else:
		#print t,math.floor(t/3600),math.floor((t % 3600)/60),int(t % 60)
		return str(int(math.floor(t/60)))+":"+str(int(t % 60))

#! /usr/bin/env python
import os,sys,time

pid_file = "/home/pi/.dukebox/pid"

# For logging, run with:
# sudo python /netfs/Code/dukeboxd.py > /netfs/dukebox_log 2>&1 &

# TODO - dukebox viewer with scanner outputs

class controls:
	def __init__(self):
		import RPi.GPIO as g
		
		# Use P1 header pin numbering convention
		g.setmode(g.BOARD)

		# Set which pins are inputs
		self.input_pins = [3,5,7,11,13,15,19,21,23,8,10,12,16,22,24,26]
		self.genre_dial_options = ["All","Rock","Heavy Rock","Classic Rock","Mellow","Soft Rock","Pop","Folk","Dance","Classical","Musical","Opera"]

		# Set up dummy states
		self.dial = [0,0]
		
		# Set all the input pins to be pulled up (grounded when activated)
		for n in self.input_pins:
			g.setup(n, g.IN, pull_up_down=g.PUD_UP)

		g.add_event_detect(16, g.FALLING, callback=lambda x: self.button_down("green"), bouncetime=500)
		g.add_event_detect(22, g.FALLING, callback=lambda x: self.button_down("red"), bouncetime=500)

		# Detect current settings
		self.detect_state()


	def __del__(self):
		g.cleanup()	
		
			
	def detect_state(self):
		import RPi.GPIO as g
		# Looking for low state because button down/dial select will ground pins
		#mode_pins = [10,12,8,0]
		if not g.input(10):
			self.dial[0] = 0
		elif not g.input(12):
			self.dial[0] = 1
		elif not g.input(8):
			self.dial[0] = 2
		else:
			self.dial[0] = 3
			
		#genre_pins = [7,0,5,3,19,11,13,15,21,26,23,24]
		if not g.input(7):
			self.dial[1] = 0
		elif not g.input(5):
			self.dial[1] = 2
		elif not g.input(3):
			self.dial[1] = 3
		elif not g.input(19):
			self.dial[1] = 4
		elif not g.input(11):
			self.dial[1] = 5
		elif not g.input(13):
			self.dial[1] = 6
		elif not g.input(15):
			self.dial[1] = 7
		elif not g.input(21):
			self.dial[1] = 8
		elif not g.input(26):
			self.dial[1] = 9
		elif not g.input(23):
			self.dial[1] = 10
		elif not g.input(24):
			self.dial[1] = 11
		else:
			# Artefact of poorly chosen soldering (this pin not actually connected) - should be second position
			# TODO - resolder so first or last pin is zero
			self.dial[1] = 1
			#pass	


	def button_down(self,action):
		global p
		self.detect_state()
		if action=="red":
			# This bit crashes sometimes after having been running for a while
			p.c.pause()
		elif action=="green":
			if self.dial[0]==0:
				p.mode = "album"
			elif self.dial[0]==1:
				p.mode = "track"
			elif self.dial[0]==2:
				p.mode = "radio"
			elif self.dial[0]==3:
				# Special mode
				#use dial[1] setting to choose switch behaviour and read out
				# Special mode - egg timer/uncle fucker/sex music/welcome home mode etc
				pass
			else:
				print "Bad mode:",self.dial[0]
				
			p.genre = self.genre_dial_options[self.dial[1]] 
			p.advance(p.mode,p.genre)
		else:
			print "Bad action:",action
		

def write_pid(pid):
	try:
		fid = open(pid_file, 'w')
		fid.write(pid)
		fid.close()
	except:
		print "Could not write PID to file"


def read_pid():
	if os.path.exists(pid_file):
		fid = open(pid_file,'rt')
		pid = int(fid.read())
		fid.close()
		return pid
	else:
		#print "PID file not found"
		return 0
	

def pid_is_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return
    else:
        return pid

        
def main(command):
	global p
	
	if command<>"":
		if command=="kill":
			pid = read_pid()
			if pid<>0:
				print "Killing",pid
				# This won't clean up
				os.kill(pid,9)
				os.remove(pid_file)
			else:
				print "No instances found running"
		else:
			print "Command",command,"not defined"
		raise SystemExit
		
	
	# See if an instance is already running
	pid = read_pid()
	if pid_is_running(pid):
		print "Already running as process",format(pid)
		raise SystemExit
	elif pid<>0:
		# Crashed at some point in the past
		os.remove(pid_file)

	# Save this instance
	pid = str(os.getpid())
	print "Running as",pid
	write_pid(pid)

	import dukebox_player
	import dukebox_scanner
	
	# Start up controls (via PIGPIO?)
	c = controls()
	#c.set_control("red",)
	#c.set_control("green",)

	# Start MPD connection via Dukebox (locally for now)
	p = dukebox_player.player("localhost")

	# Start network scanner
	s = dukebox_scanner.scanner()
	s.timeout = 600
	
	# Set frequencies of jobs
	f = {}
	f['log'] = 60*60
	f['scan'] = 60
	
	t_last = {}
	t_last['log'] = 0
	t_last['connected'] = 0
	t_last['scan'] = 0

	# Wait for stuff to happen
	while 1:
		t = time.time()
		# Do network monitoring - ping Elterwater, less frequent full survey
		# If Elterwater appears in sociable house unpause music or start new album
		
		# Check MPD connection is still good
		try:
			p.c.status()['state']
			# TODO - find out if paused or stopped for >30 mins and depower speakers via Pimote
			t_last['connected'] = t
		except:
			# Try reconnecting
			print "Disconnected for",t-t_last['connected']
			try:
				p.connect()
			except:
				print "Connecting didn't work"
			
		# Do hourly log - uptime etc
		if t-t_last['log']>f['log']:
			pass

		if t-t_last['scan']>f['scan']:
			try:
				s.update()
				t_last['scan'] = t
				#TODO - look up specific machine
			except Exception as e:
				print e
			
		# Email interesting events - power cut
		# Espeak interesting events
		# Update light on box to show state (flashing?)
		# Pimote update - unpower unused devices
		# Temperature monitoring
		# Household security
		time.sleep(6)
		
	# Clean up
	os.remove(pid_file)

	
if __name__ == '__main__':
	if len(sys.argv)>1:
		main(sys.argv[1])
	else:
		main("")

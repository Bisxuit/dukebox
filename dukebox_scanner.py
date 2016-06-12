#! /usr/bin/env python
import os
import time
import socket
from scapy.all import srp,Ether,ARP,conf
timepoll = 60


class scanner():
	def __init__(self):
		self.addr = "192.168.1.0/24"
		self.mac_name_lookup = "/netfs/Network/mac_name_lookup.txt"
		self.mac_manufacturer_lookup = "/netfs/Network/mac_manufacturer_lookup.txt"
		self.log = "/netfs/device_log"
		self.read_name_lookup()
		self.timeout = 120
		
		self.machines = []
		self.addresses = {}
		self.names = {}
		self.last_seen = {}
		self.state = {}
		self.manufacturer = {}
		
		# Read existing log
		self.read_log()


	def read_log(self):
		if os.path.isfile(self.log):
			fid = open(self.log,'rt')
		
			for	a in fid.readlines():
				if a[0]<>"#":
					a = a.replace('\n','')
					b = a.split(",")
					#time, mac, desc, IP, manufacturer, last seen
					mac = b[1].strip()
					self.machines.append(mac)
					self.addresses[mac] = b[3].strip()
					#self.names[mac] = b[2].strip()
					self.names[mac] = self.get_name(mac,self.addresses[mac])
					# TODO - use absolute time
					t_seen_s = time.strptime(b[0].strip(),"%Y-%m-%d %H:%M:%S")
					self.last_seen[mac] = time.mktime(t_seen_s)
					#self.last_seen[mac] = float(b[5].strip())
					self.state[mac] = "New"
					self.manufacturer[mac] = b[4].strip()
									
			fid.close()
		else:
			print "# Log not available."


	def get_name(self,mac,ip):
		if mac in self.machine_names:
			return self.machine_names[mac]
		else:
			# Reverse DNS on network name
			return socket.gethostbyaddr(ip)[0]
		

	def update(self):
		# Do an ARP scan of the local network
		conf.verb = 0
		ans, unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=self.addr),timeout=2)

		# TODO - sort out timezones/summer time
		t = time.time()

		# Update list of friendly device names
		self.read_name_lookup()
		
		# Extract a list of machines and their IP addresses
		for snd,rcv in ans:
			mac = rcv.sprintf(r"%Ether.src%")
			ip = rcv.sprintf(r"%ARP.psrc%")
			if not mac in self.machines:
				self.state[mac] = "New"
				self.machines.append(mac)
				self.addresses[mac] = ip
				self.manufacturer[mac] = self.read_manufacturer_lookup(mac)
				self.names[mac] = self.get_name(mac,ip)
			elif mac in self.machines and mac in self.state and self.state[mac]=="Gone":
				self.state[mac] = "Appeared"
			else:
				self.state[mac] = "Here"
			
			self.last_seen[mac] = t

			fid = open(self.log,'wt')
			fid.write("# "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t))+'\n')
			for mac in self.machines:
				#spaces = (13-len(addresses[mac]))*" "
				
				#fid.write(addresses[mac]+spaces+" -"+str(last_seen[mac]-t)+"  "+names[mac]+'\n')
				#fid.write(str('%s' % float('%.1g' % (last_seen[mac]-t)))+"  "+names[mac]+'\n')
				# TODO - sort by last seen time
				fid.write(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.last_seen[mac]))+" , "+mac+" , "+self.names[mac]+" , "+self.addresses[mac]+" , "+self.manufacturer[mac]+" , "+str('%s' % float('%.1g' % (self.last_seen[mac]-t)))+'\n')

				if self.state[mac] == "Here" and t-self.last_seen[mac]>self.timeout:
					self.state[mac] = "Disappeared"
	 
				if self.state[mac] == "New":
					print "# ",time.strftime("%H:%M:%S",time.localtime(self.last_seen[mac])),self.addresses[mac],self.names[mac],mac,self.manufacturer[mac]
					self.state[mac] = "Here"
				elif self.state[mac] == "Appeared":
					print "+ ",time.strftime("%H:%M:%S",time.localtime(self.last_seen[mac])),self.addresses[mac],self.names[mac]
					self.state[mac] = "Here"
				elif self.state[mac]== "Disappeared":
					print "- ",time.strftime("%H:%M:%S",time.localtime(self.last_seen[mac])),self.addresses[mac],self.names[mac]
					self.state[mac] = "Gone"
					
			fid.close()
	

	def read_name_lookup(self):
		# Read in saved file of pretty names for machines
		if os.path.isfile(self.mac_name_lookup):
			fid = open(self.mac_name_lookup,'rt')
			self.machine_names = {}
			for	a in fid.readlines():
				if a[0]!="#":
					a = a.replace('\n','')
					if len(a)>0:
						try:
							self.machine_names[a.split(",")[0]] = a.split(",")[1]
						except:
							print "Crap line in "+self.mac_name_lookup+": "+a
			fid.close()
					

	def read_manufacturer_lookup(self,mac):
		# Look up manufacturers name
		fid = open(self.mac_manufacturer_lookup,'rt')
		manufacturer_code = mac.strip()[:8].replace(":","").upper()
		found = False
		for line in fid:
			if manufacturer_code in line:
				manufacturer = line[7:].replace("\n","")
				found = True
				break
		fid.close()

		if not found:
			return('Dunno')
		else:
			return manufacturer


def main():
	s = scanner()
	while 1:
		s.read_name_lookup()
		s.update()
		time.sleep(timepoll)
		

if __name__ == '__main__':
	main()

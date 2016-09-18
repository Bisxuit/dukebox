#! /usr/bin/env python

# Dukebox 2016-06-12
# Monitor network devices and maintain a log. RUn as a cron job or import to read log

import os
import time
import socket

class scanner():
	def __init__(self):
		self.addr = "192.168.1.0/24"
		self.log = "/netfs/log/device.log"
		self.mac_name_lookup = "/netfs/Network/mac_name_lookup.txt"
		
		# Read existing log
		self.read_log()


	def read_log(self):
		self.machines = []
		self.addresses = {}
		self.names = {}
		self.last_seen = {}

		if os.path.isfile(self.log):
			fid = open(self.log,'rt')
		
			for	a in fid.readlines():
				if a[0]<>"#":
					a = a.replace('\n','')
					b = a.split(",")
					#time run, time seen, mac, IP
					mac = b[2].strip()
					self.machines.append(mac)
					self.addresses[mac] = b[3].strip()
					self.names[mac] = b[5].strip()
					
					# TODO - use absolute time
					t_seen_s = time.strptime(b[1].strip(),"%Y-%m-%d %H:%M:%S")
					self.last_seen[mac] = time.mktime(t_seen_s)
									
			fid.close()
		else:
			print "# Net scanner log not available."


	def get_name(self,mac,ip):
		if mac in self.machine_names:
			return self.machine_names[mac]
		else:
			# Reverse DNS on network name
			try:
				return socket.gethostbyaddr(ip)[0]
			except:
				return "Unknown"


	def read_name_lookup(self):
		# Read in saved file of pretty names for machines
		if os.path.isfile(self.mac_name_lookup):
			fid = open(self.mac_name_lookup,'rt')
			self.machine_names = {}
			for a in fid.readlines():
				if a[0]!="#":
					a = a.replace('\n','')
					if len(a)>0:
						try:
							self.machine_names[a.split(",")[0]] = a.split(",")[1]
						except:
							print "Crap line in "+self.mac_name_lookup+": "+a
			fid.close()


	def update(self):
		from scapy.all import srp,Ether,ARP,conf
		
		# Do an ARP scan of the local network
		conf.verb = 0
		ans, unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=self.addr),timeout=2)

		# TODO - sort out timezones/summer time
		t = time.time()

		# Extract a list of machines and their IP addresses
		for snd,rcv in ans:
			mac = rcv.sprintf(r"%Ether.src%")
			ip = rcv.sprintf(r"%ARP.psrc%")
			if not mac in self.machines:
				self.machines.append(mac)
				self.addresses[mac] = ip
			self.names[mac] = self.get_name(mac,ip)
			self.last_seen[mac] = t

		fid = open(self.log,'wt')
		#fid.write("# "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t))+'\n')
		# current scan time, last seen time, mac, ip
		for mac in sorted(self.last_seen,key=self.last_seen.get):
			# TODO - sort by last seen time
			fid.write(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t))+" , "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.last_seen[mac]))+" , "+mac+" , "+self.addresses[mac]+" , "+str('%s' % float('%.1g' % (self.last_seen[mac]-t)))+" , "+self.names[mac]+'\n')
		fid.close()

	
def main():
	s = scanner()
	s.read_name_lookup()
	s.update()

	# Open a socket to dukebox to highlight recent arrivals
		

if __name__ == '__main__':
	main()

#!/usr/bin/python3

import time
import schedule
import subprocess
import telnetlib
import json
import os

import RPi.GPIO as GPIO
    
# ------------------------------------------------------
class WifiWatchdog:
    
    def __init__(self):
        print("init watchdog")
        with open('config.json', 'r') as f:
            self.cfg = json.load(f)
        self.tests = 0
    
    def check(self):
    
        FNULL = open(os.devnull, 'w')
                
        error = subprocess.call(["ping", "-c4", self.cfg['localhost']], stdout=FNULL)
        
        if error == 0:
            # success
            self.tests += 1
        elif error == 1:
            print("local host unreachable")
            self.wlan_restart()
        elif error == 2:
            print("local network unreachable")
            self.wlan_restart()
        else:
            print("unknown local error: {}".format(error))

        error = subprocess.call(["ping", "-c4", self.cfg['globalhost']], stdout=FNULL)
 
    def ctc_reboot(self):
        try:
            print("Connecting to router...")
        except:
            print("Unexpected telnet error")
        
               
        
# ------------------------------------------------------
wd = WifiWatchdog()

# Schedule every..
schedule.every(1).hours.do(wd.check)


# ------------------------------------------------------
# Run forever
print(" Ctc watchdog initiated")

try:
    schedule.run_all()
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    print(" Logger failed")
    

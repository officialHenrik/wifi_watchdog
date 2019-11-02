#!/usr/bin/python3

import time
import schedule
import subprocess
import telnetlib
import json
import os

    
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
        
        if error == 0:
            # success
            self.tests += 1
        elif error == 1:
            print("host unreachable")
            self.router_reboot()
        elif error == 2:
            print("network unreachable")
        else:
            print("unknown error: {}".format(error))
                  
        print(str(time.strftime("%d/%m/%Y")) + " " + str(time.strftime("%H:%M:%S")) + ": " + str(self.tests))
                  
    def router_reboot(self):
        try:
            print("Connecting to router...")
            tn = telnetlib.Telnet(host=self.cfg['localhost'], port=23, timeout=5)
            print("Logging in")
            tn.read_until("username:", timeout=5)
            tn.write(self.cfg['telnet_usr'] + "\n")
            tn.read_until("password:", timeout=5)
            tn.write(self.cfg['telnet_pwr'] + "\n")
            tn.read_until("TP-LINK(conf)#", timeout=5)
            print("Rebooting router")
            tn.write("dev reboot" + "\n")
            print("Reboot delay")
            time.sleep(10)
            tn.close()
        except:
            print("Unexpected telnet error")
        
        
    def wlan_restart(self):
        print("restarting wlan")
            
        try:
            nmcli_path = subprocess.call(["which", "nmcli"])
            if nmcli_path != "":
                # Works on ubuntu
                subprocess.call(["nmcli", "radio", "wifi", "off"])
                time.sleep(5)
                subprocess.call(["nmcli", "radio", "wifi", "on"])
            else:
                # Should work on the raspberry pi
                subprocess.call(["/sbin/ifdown", "wlan0"])
                time.sleep(5)
                subprocess.call(["/sbin/ifup", "--force", "wlan0"])
        except:
            print("Unexpected wlan restart error")
        time.sleep(60)            
        
# ------------------------------------------------------
wd = WifiWatchdog()

# Schedule every..
schedule.every(1).hours.do(wd.check)


# ------------------------------------------------------
# Run forever
print(" Wifi watchdog initiated")

try:
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    print(" Logger failed")
    

#!/usr/bin/python3

import time
import schedule
import subprocess
import telnetlib

# ------------------------------------------------------
class WifiWatchdog:
    
    def __init__(self):
        print("init watchdog")
    
    def check(self):
    
        print("")
        print("Checking internet connetion...")
        print(str(time.strftime("%d/%m/%Y")) + " " + str(time.strftime("%H:%M:%S")))
        
        print("Checking local...")
        error = subprocess.call(["ping", "-c4", "192.168.0.1"])
        
        if error == 0:
            print("local ping success")
        elif error == 1:
            print("local host unreachable")
            self.wlan_restart()
        elif error == 2:
            print("local network unreachable")
            self.wlan_restart()
        else:
            print("unknown local error: {}".format(error))


        print("Checking global...")
        error = subprocess.call(["ping", "-c4", "www.google.com"])
        
        if error == 0:
            print("ping success")
        elif error == 1:
            print("host unreachable")
            self.router_reboot()
        elif error == 2:
            print("network unreachable")
        else:
            print("unknown error: {}".format(error))
        print("------------------------------------------------------")
                  
                  
    def router_reboot(self):
        
        print("Connecting to router...")
        tn = telnetlib.Telnet(host="192.168.0.1", port=23, timeout=5)
        print("Logging in")
        tn.read_until("username:")
        tn.write("henrni" + "\n")
        tn.read_until("password:")
        tn.write("ebbeebbe" + "\n")
        tn.read_until("TP-LINK(conf)#")
        print("Rebooting router")
        tn.write("dev reboot" + "\n")
        print("Reboot delay")
        time.sleep(10)
        tn.close()
        
        
    def wlan_restart(self):
        print("restarting wlan")
            
        if subprocess.call(["which" "nmcli"]):
            # Works on ubuntu
            subprocess.call(["nmcli", "radio", "wifi", "off"])
            time.sleep(5)
            subprocess.call(["nmcli", "radio", "wifi", "on"])
        else:
            # Should work on the raspberry pi
            subprocess.call(["/sbin/ifdown", "wlan0"])
            time.sleep(5)
            subprocess.call(["/sbin/ifup", "--force", "wlan0"])
        time.sleep(20)            
        
# ------------------------------------------------------
wd = WifiWatchdog()

# Schedule every..
schedule.every(1).hours.do(wd.check)

wd.router_reboot()

# ------------------------------------------------------
# Run forever
print(" Wifi watchdog initiated")

try:
    schedule.run_all()
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    print(" Logger failed")
    

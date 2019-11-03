#!/usr/bin/python3

import time
import schedule
import subprocess
import telnetlib
import json
import os

import RPi.GPIO as GPIO
from sheetLog.SheetItf import SheetItf
import config

# ------------------------------------------------------
class Watchdog:

    def __init__(self):
        print("init watchdog")
        with open('config.json', 'r') as f:
            self.cfg = json.load(f)

        # Setup
        GPIO.setmode(GPIO.BCM) # set up BCM GPIO numbering
        GPIO.setwarnings(True)

        GPIO.setup(self.cfg['RELAY_ENABLE'], GPIO.OUT)
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.LOW)

        # logger
        self.sheet = SheetItf(config.GOOGLE)

        self.log("Watchdog initiated")
        self.tests = 1

    def check(self):
        FNULL = open(os.devnull, 'w')
        error = subprocess.call(["ping", "-c1", self.cfg['localhost']], stdout=FNULL)

        if error == 0:
            # success
            print("ping success!")
            if self.tests == 0:
                self.log("Ping ok")
                self.tests += 1
        elif error == 1:
            print("local host unreachable")
            if self.tests > 0:
                self.tests = 0
                self.log("Ping failed")
            self.ctc_reboot()
        elif error == 2:
            print("local network unreachable")
        else:
            print("unknown local error: {}".format(error))

    def ctc_reboot(self):
        print("Rebooting CTC internet module...")
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.HIGH)
        time.sleep(5)
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.LOW)
        print("Done")

    def log(self, txt):
        self.sheet.addToRow([str(time.strftime("%d/%m/%Y")), str(time.strftime("%H:%M:%S"))])
        self.sheet.addToRow([txt])
        print("pushing:", self.sheet.nextRow)
        self.sheet.pushRow()

# ------------------------------------------------------
wd = Watchdog()

# Schedule every..
schedule.every(0.5).minutes.do(wd.check)


# ------------------------------------------------------
# Run forever
print(" Ctc watchdog initiated")

try:
    schedule.run_all()
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    print(" Watchdog failed")
    GPIO.cleanup() # clean up 
GPIO.cleanup() # clean up, default

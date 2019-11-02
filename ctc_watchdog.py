#!/usr/bin/python3

import time
import schedule
import subprocess
import telnetlib
import json
import os

import RPi.GPIO as GPIO

# ------------------------------------------------------
class Watchdog:

    def __init__(self):
        print("init watchdog")
        with open('config.json', 'r') as f:
            self.cfg = json.load(f)
        self.tests = 0

        # Setup
        GPIO.setmode(GPIO.BCM) # set up BCM GPIO numbering
        GPIO.setwarnings(True)

        GPIO.setup(self.cfg['RELAY_ENABLE'], GPIO.OUT)
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.LOW)


    def check(self):
        FNULL = open(os.devnull, 'w')
        error = subprocess.call(["ping", "-c1", self.cfg['localhost']], stdout=FNULL)

        if error == 0:
            # success
            print("ping success!")
            self.tests += 1
        elif error == 1:
            print("local host unreachable")
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
    print(" Logger failed")


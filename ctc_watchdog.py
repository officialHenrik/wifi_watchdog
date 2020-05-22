#!/usr/bin/python3

import time
import schedule
import json
import os
import subprocess

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
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.HIGH)

        # logger
        self.sheet = SheetItf(config.GOOGLE)

        self.log(["Watchdog initiated"])
        self.tests = 0
        self.fails = 0
        self.failCnt = 0
        self.noConn = 0
        self.reboots = 0
        self.enabled = 1

    def check(self):

        FNULL = open(os.devnull, 'w')

        self.enabledCheck()

        if self.enabled > 0:

            # Check internet connection
            error = subprocess.call(["ping", "-c1", self.cfg['globalhost']], stdout=FNULL)
            if error > 0:
                self.noConn += 1
                print("No internet connection")
                return 1

            # Check connection with ctc pump
            error = subprocess.call(["ping", "-c4", self.cfg['localhost']], stdout=FNULL)
            self.tests += 1
            if error == 0:
                # success
                print("ping success!")
                if self.failCnt > 0:
                    # fist success, print
                    self.log(["Ping ok"])
                self.failCnt = 0
            elif error == 1:
                print("host unreachable")
                self.fails +=1
                if self.failCnt == 0:
                    # first fail, print
                    self.log(["Ping failed"])
                self.failCnt +=1
                if self.failCnt >= 6:
                    self.ctc_reboot()
                    self.failCnt = 0
            elif error == 2:
                print("local network unreachable")
            else:
                print("unknown local error: {}".format(error))

    def enabledCheck(self):
        enabled = int(self.sheet.getCell("setup","B1"))
        if self.enabled != enabled:
            self.log(["Watchdog enabled: %d" % enabled])
        self.enabled = enabled

    def ctc_reboot(self):
        print("Rebooting CTC internet module...")
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.LOW)
        time.sleep(5)
        GPIO.output(self.cfg['RELAY_ENABLE'], GPIO.HIGH)
        print("Reboot done")

        self.reboots += 1
        self.log(["Reboot"])

    def log(self, txt):
        self.sheet.addToRow([str(time.strftime("%d/%m/%Y")), str(time.strftime("%H:%M:%S"))])
        self.sheet.addToRow(txt)
        print("pushing:", self.sheet.nextRow)
        self.sheet.pushRow()

    def logStat(self):
        self.log([self.tests, self.reboots, self.fails, self.noConn])

# ------------------------------------------------------
wd = Watchdog()

# Schedule every..
schedule.every(10).minutes.do(wd.check)
schedule.every().hour.at(":00").do(wd.logStat)


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

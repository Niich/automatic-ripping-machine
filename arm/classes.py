import pyudev
import os
import logging
import dcMachine as machine
import time

from enums import Position
from enums import Gripper

class Disc(object):
    """A disc class


    Attributes:
        devpath
        mountpoint
        videotitle
        videoyear
        videotype
        hasnicetitle
        label
        disctype
        ejected
        errors
    """

    def __init__(self, devpath):
        """Return a disc object"""
        self.devpath = devpath
        self.mountpoint = "/mnt" + devpath
        self.videotitle = ""
        self.videoyear = ""
        self.videotype = ""
        self.hasnicetitle = False
        self.label = ""
        self.disctype = ""
        self.ejected = False
        self.errors = []

        self.parse_udev()

    def parse_udev(self):
        """Parse udev for properties of current disc"""

        # print("Entering disc")
        context = pyudev.Context()
        device = pyudev.Devices.from_device_file(context, self.devpath)
        self.disctype = "unknown"
        for key, value in device.items():
            if key == "ID_FS_LABEL":
                self.label = value
                if value == "iso9660":
                    self.disctype = "data"
            elif key == "ID_CDROM_MEDIA_BD":
                self.disctype = "bluray"
            elif key == "ID_CDROM_MEDIA_DVD":
                self.disctype = "dvd"
            elif key == "ID_CDROM_MEDIA_TRACK_COUNT_AUDIO":
                self.disctype = "music"
            else:
                pass

    def __str__(self):
        """Returns a string of the object"""

        s = self.__class__.__name__ + ": "
        for attr, value in self.__dict__.items():
            s = s + "(" + str(attr) + "=" + str(value) + ") "

        return s

    def eject(self):
        """Eject disc if it hasn't previously been ejected"""

        # print("Value is " + str(self.ejected))
        if not self.ejected:
            logging.info("ejecting: " + self.devpath)
            os.system("eject " + self.devpath)
            self.ejected = True
        else:
            logging.info(self.devpath + " is already ejected")
        
    def inject(self):
        """Close tray if its open"""

        if self.ejected:
            logging.info("Closeing: " + self.devpath)
            os.system("eject -t" + self.devpath)
            self.ejected = False
        else:
            logging.info(self.devpath + " is already closed")

class Machine(object):
    def __init__(self):
        #set the propertied to unknown by default
        self.gripper = Gripper.UNKNOWN
        self.position = Position.UNKNOWN

        # run the machine start command and update the 
        # properties based on the result. 
        self.gripper, self.position = machine.start()

    def __del__(self):
        #machine.shutdown()
        print("Shutting down GPIO")
        machine.shutdownGPIO()

    def home(self):
        # run home rutine
        logging.info("homing")
        self.position = machine.home()

    def moveNext(self):
        # move to next position and update position var
        logging.info("moveing next")

    def manualMove(self,direction,steps):
        for i in range(steps):
            machine.stepMove(direction)

    def changeDisk(self,disk):
        self.position = machine.changeDisk(self.position)

    def moveToPosition(self,requestedPosition):
        self.position = machine.moveToPosition(self.position,requestedPosition)


    def gripperAction(self,requestedGripperAction):
        if requestedGripperAction == Gripper.STOP_GRIPPING:
            # already gripping. make it let go.
            # then turn off servo
            machine.gripper(Gripper.STOP_GRIPPING)
            time.sleep(1)
            machine.gripper(Gripper.OFF)
            logging.info("stop gripping")
        else:
            # not gripping. make it grab
            logging.info("start gripping")
            machine.gripper(Gripper.GRIP)

         


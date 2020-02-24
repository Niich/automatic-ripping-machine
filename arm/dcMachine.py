import RPi.GPIO as GPIO
import time
import logging

from enum import Enum

from enums import Position
from enums import Gripper
from config import cfgM

def start():
    """Fucntion to init all the GPIO configs.
    
    Needs to be ran before any other functions or the GPIO commands will fail.
    """
    # setup pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(cfgM["MM_SPEED"], GPIO.OUT)
    GPIO.setup(cfgM["MM_FORWARD"], GPIO.OUT)
    GPIO.setup(cfgM["MM_REVERSE"], GPIO.OUT)
    GPIO.setup(cfgM["GRIPPER"], GPIO.OUT)
    GPIO.setup(cfgM["DVD_SWITCH"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(cfgM["CENTER_SWITCH"], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    setupMotorPwm()
    setupGripperPwm()
    # I could add the home routine here so that the machine gets homes when its 
    # first started up.
    return Gripper.UNKNOWN, Position.UNKNOWN

def shutdownGPIO():
    GPIO.cleanup()

def setupMotorPwm():
    global pwmMotor
    pwmMotor = GPIO.PWM(cfgM["MM_SPEED"],100)

def setupGripperPwm():
    global pwmGripper
    pwmGripper = GPIO.PWM(cfgM["GRIPPER"],100)

# globals are used in the callbacks and need to also be used in any function
# that relies on the callback since they execute in a seperate thread.
def homeDVDCallback(channel):
    """ Callback for DVD switch that also forces movement to stop.
    
    Sets the DVD status changed to true and forces all movemnt to stop.
    Also includes a false detect check.

    Movemnt is stopped and then the pin status is checked. 
    This allows for bounce to settle before reading the pin, to reduce false detects caused by vibration.
    """
    global dvdPinStatusChanged, dvdSwitchStatus
    #print("dvd change detected")
    GPIO.output(cfgM["MM_FORWARD"], GPIO.LOW)
    GPIO.output(cfgM["MM_REVERSE"], GPIO.LOW)
    #debounce logic
    time.sleep(.05)
    if (GPIO.input(cfgM["DVD_SWITCH"]) != dvdSwitchStatus):
        dvdPinStatusChanged = True
        print("Status updated")
          

def homeCenterCallback(channel):
    """ Callback for center switch that also forces the movement to stop.

    Sets the global center status to true when the switch is pressed.
    Also sents all the movement pins to LOW so that all movement stops.
    """
    global centerStatusChanged
    centerStatusChanged = True
    GPIO.output(cfgM["MM_FORWARD"], GPIO.LOW)
    GPIO.output(cfgM["MM_REVERSE"], GPIO.LOW)
    

def detectCenterCallback(channel):
    """Callback for the center switch.
    
    Sets the global center status to true when the switch is pressed.
    """
    global centerStatusChanged
    centerStatusChanged = True
    

def monitorDVDswitch():
    """ Funtion for monitoring the switch in the DVD arm.

    Monitors the status of the DVD switch and listens for changes
    """
    global dvdPinStatusChanged
    dvdPinStatusChanged = False
    global dvdSwitchStatus
    dvdSwitchStatus = GPIO.input(cfgM["DVD_SWITCH"])

    if GPIO.input(cfgM["DVD_SWITCH"]):
        GPIO.add_event_detect(cfgM["DVD_SWITCH"], GPIO.FALLING, bouncetime=500)
    else:
        GPIO.add_event_detect(cfgM["DVD_SWITCH"], GPIO.RISING, bouncetime=500)
    
    GPIO.add_event_callback(cfgM["DVD_SWITCH"], callback=homeDVDCallback)

def home():
    """ Homing funtion

    funtion that should be ran anytime the position is unknown.
    
    Uses a series of moves and sensor detects to find a known position, either the tray or the stack.
    """
    global dvdPinStatusChanged
    dvdPinStatusChanged = False
    global currentLocation
    motorSpeed = cfgM["MM_MAX_SPEED"]
    steps = 1
    global DVDstatus
    DVDstatus = GPIO.input(cfgM["DVD_SWITCH"])
    homed = False
    forward = False
    CenterStatus = GPIO.input(cfgM["CENTER_SWITCH"])
    print(DVDstatus)
    
    monitorDVDswitch()
    
    if CenterStatus:
        GPIO.add_event_detect(cfgM["CENTER_SWITCH"], GPIO.FALLING, callback=homeCenterCallback, bouncetime=500)
    else:
        GPIO.add_event_detect(cfgM["CENTER_SWITCH"], GPIO.RISING, callback=homeCenterCallback, bouncetime=500)
    
    if DVDstatus:
        # start a a high power
        pwmMotor.start(cfgM["MM_MAX_SPEED"])
        GPIO.output(cfgM["MM_FORWARD"], GPIO.HIGH)
        time.sleep(.5)
        GPIO.output(cfgM["MM_FORWARD"], GPIO.LOW)
        if DVDstatus != GPIO.input(cfgM["DVD_SWITCH"]):
            homed = True
            currentLocation = Position.STACK
        else:
            homed = True
            currentLocation = Position.TRAY

    while not homed:
        #move one direction then check sensor
        pwmMotor.start(cfgM["MM_STEP_SPEED"])
        if not dvdPinStatusChanged:
            GPIO.output(cfgM["MM_REVERSE"], GPIO.HIGH)
            time.sleep(cfgM["MM_STEP_DURATION"])
            GPIO.output(cfgM["MM_REVERSE"], GPIO.LOW)
            time.sleep(cfgM["MM_STEP_DELAY"])

        print(dvdPinStatusChanged)
        if dvdPinStatusChanged:
            homed = True
            currentLocation = Position.STACK

    # if (forward and GPIO.input(cfgM["DVD_SWITCH"])) or (not forward and not GPIO.input(cfgM["DVD_SWITCH"])):
    #     currentLocation = Position.TRAY
    # else:
    

    GPIO.output(cfgM["MM_REVERSE"], GPIO.LOW)
    GPIO.output(cfgM["MM_FORWARD"], GPIO.LOW)
    GPIO.remove_event_detect(cfgM["CENTER_SWITCH"])
    GPIO.remove_event_detect(cfgM["DVD_SWITCH"])
    print(currentLocation.name)
    return currentLocation

def moveToPosition(currentPosition,requestedPosition):
    """ This fucntion accepts two Position(ENUM) arguments and performs a series of moves.

    First arg is the current position.
    Second arg is the desired position.

    Based on these arguments a series of actions are performed to move form the curent
    postion to the desired position.
    """

    print("Current: " + currentPosition.name + " Requested: " + requestedPosition.name)
    if currentPosition == Position.UNKNOWN:
           currentPosition = home()
        
    if currentPosition == Position.TRAY:
        if requestedPosition == Position.STACK:
            # move to stack
            direction = cfgM["MM_REVERSE"] # set the direction for this move
            logging.info("move to stack")
            #cycleMove(cfgM["MM_REVERSE"])
            currentSpeed = accelerateToCenter(direction)
            for i in range(cfgM["POS_STEPS_FROM_CENTER"]):
                stepMove(direction)
            stepTillDetect(direction,cfgM["MM_MIN_SPEED"])
            newPosition = requestedPosition
        elif requestedPosition == Position.ABOVE_TRAY:
            # move to above the tray
            direction = cfgM["MM_REVERSE"] # set the direction for this move
            logging.info("move to above tray")
            timedMove(direction,cfgM["POS_TIME_FROM_TRAY"],cfgM["MM_STEP_SPEED"])

            newPosition = requestedPosition
        else:
            logging.info("Invalid move requested")
            newPosition = currentPosition
    elif currentPosition == Position.STACK:
        if requestedPosition == Position.TRAY:
            # move to tray
            direction = cfgM["MM_FORWARD"] # set the direction for this move
            logging.info("move to tray")
            currentSpeed = accelerateToCenter(direction)
            print("current speed is: " + str(currentSpeed))
            for i in range(cfgM["POS_STEPS_FROM_CENTER"]):
                stepMove(direction)
            #stepTillDetect(direction)
            # verifiy that the arm is on the tray and if not keep moving till it is
            while not GPIO.input(cfgM["DVD_SWITCH"]):
                stepTillDetect(direction)
                time.sleep(.5)

            newPosition = requestedPosition
        elif requestedPosition == Position.ABOVE_TRAY:
            # move to above the tray
            direction = cfgM["MM_FORWARD"] # set the direction for this move
            logging.info("move to above tray")
            currentSpeed = accelerateToCenter(direction)
            for i in range(cfgM["POS_STEPS_FROM_CENTER"]):
                stepMove(direction)

            newPosition = requestedPosition
        else:
            logging.info("Invalid move requested")
            newPosition = currentPosition
    elif currentPosition == Position.ABOVE_TRAY:
        if requestedPosition == Position.TRAY:
            # move to tray
            direction = cfgM["MM_FORWARD"] # set the direction for this move
            logging.info("move to tray")
            while not GPIO.input(cfgM["DVD_SWITCH"]):
                stepTillDetect(direction)
                time.sleep(.5)

            newPosition = requestedPosition
        elif requestedPosition == Position.STACK:
            # move to the stack            
            direction = cfgM["MM_REVERSE"] # set the direction for this move
            logging.info("move to stack")
            currentSpeed = accelerateToCenter(direction)
            print("current speed is: " + str(currentSpeed))
            for i in range(cfgM["POS_STEPS_FROM_CENTER"]):
                stepMove(direction)
            stepTillDetect(direction)

            newPosition = requestedPosition
        else:
            logging.info("Invalid move requested")
            newPosition = currentPosition
    else:
        logging.info("Invalid starting postion")
        print("Invalid starting postion")
        newPosition = currentPosition

    return newPosition

def changeDisk(currentPosition,disk):
    # set the return value to unknown incase something fails, 
    # that way it will try to home before next action and 
    # hopefully not break anything.
    finalPosition = Position.UNKNOWN
    

    # move to safe location above tray before opening disk drive
    if currentPosition == Position.TRAY:
        currentPosition = moveToPosition(currentPosition,Position.ABOVE_TRAY)
    
    # open tray and try to remove a disk if there is any
    disk.eject()                                                            # open tray
    gripper(Gripper.STOP_GRIPPING)                                          # close gripper so it fits in a disk
    currentPosition = moveToPosition(currentPosition,Position.TRAY)         # move to the tray
    gripper(Gripper.GRIP)                                                   # grab a disk
    time.sleep(1)                                                 
    currentPosition = moveToPosition(currentPosition,Position.ABOVE_TRAY)   # move the disk out of the tray
    disk.inject()                                                           # close the tray so its out of the way
    time.sleep(1)
    gripper(Gripper.STOP_GRIPPING)                                          # drop the disk

    # try to collect a new disk from the stack and place it in the tray
    currentPosition = moveToPosition(currentPosition,Position.STACK)
    gripper(Gripper.GRIP)
    disk.eject()
    currentPosition = moveToPosition(currentPosition,Position.TRAY)
    gripper(Gripper.STOP_GRIPPING)
    currentPosition = moveToPosition(currentPosition,Position.STACK)
    disk.inject()
    time.sleep(2)
    # move to safe location so tray can be closed

def cycleMove(dir_pin):
    """Function to move to the TRAY or STACK in a quick and reliable way"""
    #start slow
    motorSpeed = cfgM["MM_MIN_SPEED"]
    global pwmMotor
    
    GPIO.output(dir_pin, GPIO.HIGH)
    STOP = False
    count = 0
    first_half = True
    while not STOP:
        if count < 2:
            status = GPIO.input(cfgM["DVD_SWITCH"])
            if status and not first_half: #if the pin is high
                count = count + 1
            else: #if the pin is low
                count = 0

            if first_half:
            #increase speed
                    
                while  motorSpeed < cfgM["MM_MAX_SPEED"]:
                    motorSpeed = motorSpeed + 1
                    time.sleep(.02)
                    pwmMotor.start(motorSpeed)

                GPIO.wait_for_edge(cfgM["CENTER_SWITCH"], GPIO.FALLING, bouncetime=500)
                first_half = False
                print('center detected')
            else:
            #decrease speed
                if motorSpeed > MM_MIN_SPEED:
                    motorSpeed = motorSpeed - 1
                    time.sleep(.025)
                    pwmMotor.start(motorSpeed)

        if motorSpeed == cfgM["MM_MIN_SPEED"]:
            stepMove(dir_pin, cfgM["MM_MIN_SPEED"])
            # GPIO.output(dir_pin, GPIO.HIGH) 
            # time.sleep(.02)
            # GPIO.output(dir_pin, GPIO.LOW)
            # time.sleep(.03)
        else:
            STOP = True

    print('Disk detected')
    GPIO.output(dir_pin, GPIO.LOW)

def stepMove(direction, speed = cfgM["MM_STEP_SPEED"]):
    """Step emulation function
    
    Tries to emulate steps like a stepper motor. This process it FAR from exact and
    the distance traved in a 'step' will not be uniform.
    
    The basic idea of this is to move at a high speed for a short time and then 
    stop before moving again, giving the illution of a step.
    """

    timedMove(direction, cfgM["MM_STEP_DURATION"], speed)
    time.sleep(cfgM["MM_STEP_DELAY"])

def timedMove(direction, duration, speed):
    """Basic move fucntion
    
    Sets the specified direction pin HIGH for the duration requested then sets it LOW.
    Also creates a PWM object using the MM_SPEED pin and sets its duty cycle to 
    the value of speed.
    """
    global pwmMotor

    pwmMotor.start(speed)
    GPIO.output(direction, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(direction, GPIO.LOW)

def accelerateToCenter(direction, stopAtCenter = True):
    """Accelerate to max speed and continues till the center switch is reached.
    
    If stopAtCenter is true (default) than movement will stop when center is reached and the
    current speed will be set to 0. If its False than movement will continue until a 
    GPIO.output(direction, GPIO.LOW) command is issued, directly or through another function.

    Returns the current speed when the center is detected.    
    """
    print("accelerateToCenter")
    global centerStatusChanged
    centerStatusChanged = False
    CenterStatus = GPIO.input(cfgM["CENTER_SWITCH"])
    # start at min speed
    motorSpeed = cfgM["MM_MIN_SPEED"]
    global pwmMotor
    

    if CenterStatus:
        GPIO.add_event_detect(cfgM["CENTER_SWITCH"], GPIO.FALLING, callback=detectCenterCallback, bouncetime=500)
    else:
        GPIO.add_event_detect(cfgM["CENTER_SWITCH"], GPIO.RISING, callback=detectCenterCallback, bouncetime=500)

    # start moving
    pwmMotor.start(motorSpeed)
    GPIO.output(direction, GPIO.HIGH)
    while not centerStatusChanged:
        if motorSpeed < cfgM["MM_MAX_SPEED"]:
            motorSpeed = motorSpeed + 1
            pwmMotor.ChangeDutyCycle(motorSpeed)
            time.sleep(cfgM["MM_ACCEL_DELAY"])
    
    if stopAtCenter:
        GPIO.output(direction, GPIO.LOW)
        motorSpeed = 0
    # else:
    #     time.sleep(cfgM["MM_DECEL_DELAY"])
    #     GPIO.output(direction, GPIO.LOW)

    GPIO.remove_event_detect(cfgM["CENTER_SWITCH"])
    return motorSpeed

def decelerate(direction, currentSpeed = cfgM["MM_MAX_SPEED"], minSpeed = cfgM["MM_MIN_SPEED"], stopAtMinSpeed = True):
    print("decelerate")
    global dvdPinStatusChanged
    dvdPinStatusChanged = False
    global pwmMotor

    monitorDVDswitch()

    pwmMotor.start(currentSpeed)
    #GPIO.output(direction, GPIO.HIGH)
    while not dvdPinStatusChanged:
        if currentSpeed > minSpeed:
            print("decelerate more: " + str(currentSpeed))
            currentSpeed = currentSpeed - 1
            pwmMotor.ChangeDutyCycle(currentSpeed)
            time.sleep(cfgM["MM_DECEL_DELAY"])
        else:
            break

    if stopAtMinSpeed:
        GPIO.output(direction, GPIO.LOW)
        currentSpeed = 0

    GPIO.remove_event_detect(cfgM["DVD_SWITCH"])
    return currentSpeed

def stepTillDetect(direction,speed = (cfgM["MM_STEP_SPEED"] * .66)):
    print("stepTillDetect")
    global dvdPinStatusChanged
    global DVDstatus
    count = 0
    DVDstatus = GPIO.input(cfgM["DVD_SWITCH"])

    monitorDVDswitch()

    while not dvdPinStatusChanged:
        if not GPIO.input(cfgM["DVD_SWITCH"]) :
            stepMove(direction,speed)
            count = 0
        elif GPIO.input(cfgM["DVD_SWITCH"]) and count < 5:
            count = count + 1
        else:
            break

    GPIO.remove_event_detect(cfgM["DVD_SWITCH"])

def gripper(requestedGripAction):
    global pwmGripper
    if requestedGripAction == Gripper.GRIP:
        pwmGripper.start(cfgM["GRIPPER_OPEN"])
        time.sleep(1)
    elif requestedGripAction == Gripper.STOP_GRIPPING:
        pwmGripper.start(cfgM["GRIPPER_CLOSED"])
    else:
        pwmGripper.start(0)


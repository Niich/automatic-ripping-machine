from classes import Machine
from enums import Position
from enums import Gripper

import time

def main():
    print("createing machine Obj")
    machine = Machine()

    # print("trying to home")
    # machine.home()

    # machine.manualMove(13,5)
    machine.moveToPosition(Position.TRAY)
    time.sleep(1)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    # #input("Press Enter to continue...")
    # machine.gripperAction(Gripper.GRIP)
    # time.sleep(1)
    machine.moveToPosition(Position.STACK)
    #input("Press Enter to continue...")
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    # time.sleep(1)
    machine.moveToPosition(Position.ABOVE_TRAY)
    #input("Press Enter to continue...")
    machine.moveToPosition(Position.STACK)
    time.sleep(1)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    #input("Press Enter to continue...")
    # machine.gripperAction(Gripper.GRIP)
    time.sleep(1)
    machine.moveToPosition(Position.TRAY)
    time.sleep(1)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    #input("Press Enter to continue...")
    time.sleep(1)
    machine.moveToPosition(Position.ABOVE_TRAY)
    time.sleep(1)
    machine.moveToPosition(Position.STACK)


    # time.sleep(1)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    # machine.moveToPosition(Position.ABOVE_TRAY)
    # time.sleep(1)
    # machine.moveToPosition(Position.STACK)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    # time.sleep(10)
    # machine.gripperAction(Gripper.GRIP)
    # time.sleep(1)
    # machine.moveToPosition(Position.TRAY)
    # time.sleep(1)
    # machine.gripperAction(Gripper.STOP_GRIPPING)
    # time.sleep(1)
    # machine.moveToPosition(Position.ABOVE_TRAY)



if __name__ == "__main__":
    main()
    pass
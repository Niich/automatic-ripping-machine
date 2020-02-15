from enum import Enum

class Position(Enum):
	UNKNOWN = 0
	TRAY = 1
	STACK = 2
	ABOVE_TRAY = 3

class Gripper(Enum):
    UNKNOWN = 0
    GRIP = 1
    STOP_GRIPPING = 2
    OFF = 3
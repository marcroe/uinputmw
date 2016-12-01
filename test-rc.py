#!/usr/bin/env python

from pyMultiwii import MultiWii
from sys import stdout
import uinput
import time

smallest = 0
largest = 1000
mid = 500
	
def clamp(n):
    return max(smallest, min(n-1000, largest)) # we subtract 1000 to make minimum equal to zero

if __name__ == "__main__":

    board = MultiWii("/dev/ttyACM0")
    #board = MultiWii("/dev/tty.SLAB_USBtoUART")
    #if not board:
	#print "Error opening port"
	
    events = (
        uinput.BTN_JOYSTICK,
        uinput.ABS_X + (smallest, largest, 0, 0),
        uinput.ABS_Y + (smallest, largest, 0, 0),
        uinput.ABS_Z + (smallest, largest, 0, 0),
        uinput.ABS_RX + (smallest, largest, 0, 0)
        )

    with uinput.Device(events) as device:
	print "Uinput device created"

	device.emit(uinput.ABS_X, mid, syn=False)
	device.emit(uinput.ABS_Y, mid, syn=False)
	device.emit(uinput.ABS_Z, smallest, syn=False)
	device.emit(uinput.ABS_RX, mid)

	old_roll = mid
	old_pitch = mid
	old_throttle = smallest
	old_yaw = mid

    	while True: #getData is blocking
        	board.getData(MultiWii.RC)
		
		throttle = clamp(board.rcChannels['throttle'])
		roll =  largest - clamp(board.rcChannels['roll']) #invert
		pitch = clamp(board.rcChannels['pitch'])
		yaw =  largest - clamp(board.rcChannels['yaw']) #invert

		if throttle == old_throttle and roll == old_roll and pitch == old_pitch and yaw == old_yaw:
			continue
		else:
			old_throttle = throttle
			old_roll = roll
			old_pitch = pitch
			old_yaw = yaw

		if int(board.rcChannels['throttle']) > 900: # remote is turned on. BF sends 850 when no signal)
			device.emit(uinput.ABS_X, roll, syn=False)
			device.emit(uinput.ABS_Y, pitch, syn=False)
			device.emit(uinput.ABS_Z, throttle, syn=False)
			device.emit(uinput.ABS_RX, yaw)

			message = "throttle = {:+.1f} \t yaw = {:+.1f} \t pitch = {:+.1f} \t roll = {:+.1f} \t".format(float(board.rcChannels['throttle']),float(board.rcChannels['yaw']),float(board.rcChannels['pitch']),float(board.rcChannels['roll']))
			stdout.write("\r%s" % message )
			stdout.flush()
		else:
			device.emit(uinput.ABS_X, mid, syn=False)
			device.emit(uinput.ABS_Y, mid, syn=False)
			device.emit(uinput.ABS_Z, smallest, syn=False)
			device.emit(uinput.ABS_RX, mid)

			stdout.write("\n remote turned off.\n")
			stdout.flush()
			break


    board.disconnect()




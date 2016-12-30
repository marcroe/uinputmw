#!/usr/bin/env python

from pyMultiwii import MultiWii
from sys import stdout
import uinput
import time
import sys
import glob
import serial
import signal

def find_board():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    for port in ports:
	board = None
        try:
            s = serial.Serial(port)
            s.close()
	    board = MultiWii(port)
	    board.getData(MultiWii.RC)
	    return board
        except (OSError, serial.SerialException):
	    if board:
		board.disconnect()
            pass
    return None


smallest = 0
largest = 1000
mid = 500
	
def clamp(n): # map rc values (1000 - 2000) to 0 - 1000
    return max(smallest, min(n-1000, largest)) # we subtract 1000 to make minimum equal to zero

if __name__ == "__main__":
    events = (
        uinput.BTN_JOYSTICK,
        uinput.ABS_X + (smallest, largest, 0, 0),
        uinput.ABS_Y + (smallest, largest, 0, 0),
        uinput.ABS_Z + (smallest, largest, 0, 0),
        uinput.ABS_RX + (smallest, largest, 0, 0)
        )
    with uinput.Device(events) as device:
	print "Uinput device created"

	loop = {'activated':True}
	def signal_handler(signal, frame):
        	print('\nYou pressed Ctrl+C! Exiting.')
		loop['activated'] = False
	signal.signal(signal.SIGINT, signal_handler)

	board = None
	while loop['activated']:
		time.sleep(1)
		board = find_board()
		if not board:
			print("No flight controller found. Retrying..")
		else:
			print("Flight controller found.")
			responding = True
		    	while loop['activated'] and responding:
				try:
					board.getData(MultiWii.RC)
					throttle = clamp(board.rcChannels['throttle'])
					roll =  largest - clamp(board.rcChannels['roll']) #invert
					pitch = clamp(board.rcChannels['pitch'])
					yaw =  largest - clamp(board.rcChannels['yaw']) #invert
					elapsed =  board.rcChannels['elapsed']

					message = "throttle={:5}\tyaw={:5}\tpitch={:5}\troll={:5}\tt_delta={:5}".format(throttle,yaw,pitch,roll,"") #,elapsed)
					stdout.write("\r\r%s" % message )
					stdout.flush()

					device.emit(uinput.ABS_X, roll) #, syn=False)
					device.emit(uinput.ABS_Y, pitch) #, syn=False)
					device.emit(uinput.ABS_Z, throttle) #, syn=False)
					device.emit(uinput.ABS_RX, yaw)

					#time.sleep(0.025)

				except Exception as inst:
					responding = False
					print "\nboard stoppped responding"
					if board:
						board.disconnect()
					print type(inst)     # the exception instance
					print inst.args      # arguments stored in .args

	# disconnect upon exit
	if board:
		board.disconnect()






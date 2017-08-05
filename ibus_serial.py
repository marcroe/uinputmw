#!/usr/bin/env python

from sys import stdout
import uinput
import time
import sys
import glob
import serial
import signal
import struct 
def find_receiver():
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
        ports = glob.glob('/dev/tty[A-Z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    for port in ports:
        try:
	    print "checking " + port
            s = serial.Serial(port)
	    if s.is_open:
	    	s.close()
	    s.baudrate=115200
	    s.timeout=2 # 1 sec read timeout
	    s.open()
	    getData(s)
	    return s
        except (OSError, serial.SerialException) as excpt:
	    if s.is_open:
		s.close()
            pass
    return None


smallest = 0
largest = 1000
mid = 500

def getData(recv): # we have 14 channels. channels start after 2 byte offset.
	ibusBuffer=bytearray(32)
	bytesRead = 0
	ibusBufferPos = 0
	while True:
		data = recv.read(size=1)
		if not data or len(data) < 1:
			print "receiver does not send data"
		ibusBuffer[ibusBufferPos] = data
		bytesRead = bytesRead + 1
		ibusBufferPos = (ibusBufferPos+1) % 32
		if bytesRead >= 32:
			#print [i for i in ibusBuffer]
			checksum = 0xFFFF - sum( [ibusBuffer[i%32] for i in range(ibusBufferPos,ibusBufferPos+30,1)] )
			if (checksum >> 8) == ibusBuffer[(ibusBufferPos-1) % 32] and (checksum & 0xFF) == ibusBuffer[(ibusBufferPos-2) % 32]:
				channelFbit = [ibusBuffer[i%32] for i in range(ibusBufferPos+2,ibusBufferPos+28+2,2)]
				channelLbit = [ibusBuffer[i%32] for i in range(ibusBufferPos+3,ibusBufferPos+28+3,2)]
				channels = [i+(j<<8) for i,j in zip(channelFbit, channelLbit)]
				return channels

		


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
    with uinput.Device(events, name="ibus") as device:
	print "Uinput device created"

	loop = {'activated':True}
	def signal_handler(signal, frame):
        	print('\nYou pressed Ctrl+C! Exiting.')
		loop['activated'] = False
	signal.signal(signal.SIGINT, signal_handler)

	receiver = None
	while loop['activated']:
		time.sleep(1)
		receiver = find_receiver()
		if not receiver:
			print("No ibus receiver found. Retrying..")
		else:
			print("ibus receiver found.")
			responding = True
		    	while loop['activated'] and responding:
				try:
					rcChannels = getData(receiver)
					throttle = largest - clamp(rcChannels[2]) #invert
					roll =  clamp(rcChannels[0]) 
					pitch = largest - clamp(rcChannels[1]) #invert
					yaw =  clamp(rcChannels[3])


					message = "throttle={:5}\tyaw={:5}\tpitch={:5}\troll={:5}".format(throttle,yaw,pitch,roll)
					stdout.write("\r\r%s" % message )
					stdout.flush()

					device.emit(uinput.ABS_X, roll) #, syn=False)
					device.emit(uinput.ABS_Y, pitch) #, syn=False)
					device.emit(uinput.ABS_Z, throttle) #, syn=False)
					device.emit(uinput.ABS_RX, yaw)

				except Exception as inst:
					responding = False
					print "\nreceiver stoppped responding"
					if receiver and receiver.is_open:
						receiver.close()
					print type(inst)     # the exception instance
					print inst.args      # arguments stored in .args

	# disconnect upon exit
	if receiver and receiver.is_open:
		receiver.close()






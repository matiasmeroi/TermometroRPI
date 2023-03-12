import RPi.GPIO as GPIO
import time
import signal
import sys, time
import subprocess

RASP = 0
BATOCERA = 1

OS = BATOCERA


LATCH_CLOCK = 2
SHIFT_CLOCK = 3
SHIFT_INPUT = 4



def readTempRasp():
	res = subprocess.check_output(["vcgencmd", "measure_temp"])
	res = res.strip("temp=")
	res = res[0:2]
	return int(res)



def readTempBatocera():
	res = subprocess.check_output(["batocera-info"])
	res = res.strip("Temperature: ")
	res = res[0:2]
	return int(res)


def readTemp():
	if OS == RASP:
		return readTempRasp()
	elif OS == BATOCERA:
		return readTempBatocera()
	return 0

# cierra io cuando se interrumpe el programa
def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# enumera las salidas de acuerdo al numero de gpio
# no del header
GPIO.setmode(GPIO.BCM)


GPIO.setup(LATCH_CLOCK, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(SHIFT_CLOCK, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(SHIFT_INPUT, GPIO.OUT, initial=GPIO.LOW)


def shiftBit(bit):
	sh = None
	if bit != "0":
		GPIO.output(SHIFT_INPUT, GPIO.HIGH)
		sh = 1
	else:
		GPIO.output(SHIFT_INPUT, GPIO.LOW)
		sh = 0

	GPIO.output(SHIFT_CLOCK, GPIO.LOW)
	GPIO.output(SHIFT_CLOCK, GPIO.HIGH)
	GPIO.output(SHIFT_CLOCK, GPIO.LOW)



# agrega 0's
def fixLength(byte, des):
	l = len(byte)
	if l < 8:
		byte = ("0" * (des - l)) + byte
	return byte




def toByte(num, heartbeat = False, length = -1):
	byte = bin(num)
	lenByte = len(byte)
	byte = byte[2:lenByte]

	if length > 0:
		byte = fixLength(byte, length)


	if heartbeat and length == 8:
		byte = '1' + byte[1:8]

	return byte



# arg no invertido
def shiftByte(byte):
	byte = byte[::-1]
	for ch in byte:
		shiftBit(ch)
	latch()




def shiftTemp(temp, heartbeat = False):
	unidad = temp % 10
	decena = temp / 10

	unidad = toByte(unidad, length = 4)
	decena = toByte(decena, length = 3)
	
	bits = ("1" if heartbeat else "0") + decena + unidad

	shiftByte(bits)



def latch():
	GPIO.output(LATCH_CLOCK, GPIO.LOW)
	GPIO.output(LATCH_CLOCK, GPIO.HIGH)
	GPIO.output(LATCH_CLOCK, GPIO.LOW)



def introSequence():
	for i in range(0, 2):
		for j in range(0, 13):

			bits = None
			if j < 6:
				bits = 1 << j
			else:
				bits = 1 << (12 - j)
			bits = toByte(bits, length = 8)

			shiftByte(bits)

			time.sleep(0.06)

	d = 0.1
	for i in range(0, 5):
		shiftByte(toByte(255))
		time.sleep(d)
		shiftByte(toByte(0, length = 8))
		time.sleep(d)

time.sleep(0.5)


introSequence()


while True:
	temp = readTemp()
	shiftTemp(temp = temp, heartbeat = True)
	time.sleep(0.2)
	shiftTemp(temp = temp, heartbeat = False)
	time.sleep(2)



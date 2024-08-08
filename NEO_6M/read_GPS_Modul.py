import io
import serial
import sys
import logging


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

ser = serial.Serial(
        port = '/dev/ttyAMA0',
        baudrate = 9600,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize = serial.EIGHTBITS,
        timeout = 1
)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

while True:
        try:
                line = sio.readline()
                
                new_line = line.split(sep =",")
                
                logger.debug (new_line)
                
                if(new_line[0] == '$GPRMC'):
                    speed_knots = float(new_line[7])
                    print("Speed in knots: ", speed_knots)
                    speed_km_h = speed_knots * 1.852
                    print("Speed in km/h: {:5.1f}".format(speed_km_h))
        except KeyboardInterrupt:
                print("\nProgram terminated by user.")
                break
        except serial.SerialException as e:
                logger.error('SerialException: {}'.format(e))
                break
        except UnicodeDecodeError as e:
                logger.error('UnicodeDecodeError: {}'.format(e))
                continue

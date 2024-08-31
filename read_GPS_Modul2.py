# Programm liest vom Neo 6M GPS Modul und extrahiert die Geschwindigkeit
# Quelle: https://www.haraldkreuzer.net/aktuelles/mit-gps-modul-die-uhrzeit-fuer-raspberry-pi-3-a-plus-setzen-ganz-ohne-netzwerk
# Erweiterung: Die Geschwindigkeit wird für die Inter-Prozess-Kommunikation bereitgestellt

import io
import serial
import sys
import logging
import filelock

# Logger für die serielle Schnittstelle initialisieren 
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für Inter-Prozess-Kommunikation definieren
file_path = "SolarCar_speed.txt"
lock_path = "SolarCar_speed.txt.lock"

# serielle Schnittstelle initialisieren
ser = serial.Serial(
        port = '/dev/ttyAMA0',
        baudrate = 9600,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize = serial.EIGHTBITS,
        timeout =  0.9
)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

# Begrüßung drucken
print("Hello from read_GPS_Modul2.py")

while True:
    try:
        # Read and return a line from the stream
        line = sio.readline()
        # aufspalten in einzelne Elemente
        new_line = line.split(sep =",")
        # wenn der GPRMC Frame gelesen wurde
        if new_line[0] == '$GPRMC':
            # wenn die Daten gültig sind
            if new_line[2] == 'A':
                # speed_km_h berechnen
                speed_knots = float(new_line[7])/ 100.
                speed_km_h = 1.852 * (float(new_line[7]))
                # speed_km_h auf Konsole schreiben
                logger.debug (str(speed_km_h))
                try:
                    # speed_km_h in Datei für Inter-Prozess-Kommunikation schreiben
                    lock = filelock.FileLock(lock_path, timeout=1) # lock
                    with lock:
                        with open(file_path, mode="w", encoding="utf-8") as datei:
                            datei.write(str(speed_km_h))
                except filelock._error.Timeout:
                    print("Aktuell wird der Speed Lock von einem anderen Programm gehalten!")    
    except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            break
    except serial.SerialException as e:
            logger.error('SerialException: {}'.format(e))
            break
    except UnicodeDecodeError as e:
            logger.error('UnicodeDecodeError: {}'.format(e))
            continue

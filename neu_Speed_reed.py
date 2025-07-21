#Auslesen eines Reed-Schalters mit gpiozero um die Radgeschwindigkeit auszulesen. Diese wird dann in eine Datei geschrieben

from gpiozero import Button
from time import time, sleep
import sys
import logging
import filelock

# GPIO-Pin, an dem der Reed-Kontakt angeschlossen ist
reed_pin = 4

# Umfang des Rades in Metern (z.B. 2 Meter) ; /5, da 5 Impulse pro umdrehung
wheel_circumference_m = 2.2/5

# Button-Objekt fuer den Reed-Kontakt (nimmt an, dass der Reed Kontakt den Pin auf LOW zieht)
reed_switch = Button(reed_pin, pull_up=False, bounce_time=0.1)

# Zeit des letzten Impulses
last_time = None
# gemessene Geschwindigkeit (km/h)
speed_kmh = 0

# Logger für die serielle Schnittstelle initialisieren 
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für Inter-Prozess-Kommunikation definieren
file_path = "SolarCar_speed.txt"
lock_path = "SolarCar_speed.txt.lock" 

def calculate_speed():
    global last_time, speed_kmh
    current_time = time()
    if last_time is not None:
        delta_time = current_time - last_time
        if delta_time > 0:
            # Geschwindigkeit in m/s: Umfang / Zeit furr eine Umdrehung
            speed_m_per_s = wheel_circumference_m / delta_time
            # Umrechnung m/s in km/h
            speed_kmh = speed_m_per_s * 3.6
            print(f"Geschwindigkeit: {speed_kmh:.2f} km/h")
            
            try:
                lock = filelock.FileLock(lock_path, timeout=1)
                with lock:
                    with open(file_path, mode="w", encoding="utf-8") as datei:
                        datei.write(f"{speed_kmh:.1f}")
            except filelock._error.Timeout:
                print("aktuell wird der Speed Lock von einem anderen Programm gehalten!")
            
    last_time = current_time

# Callback, wenn der Reed-Kontakt schliesst (Taster gedrueckt)
reed_switch.when_pressed = calculate_speed

try:
    print("Geschwindigkeitsmessung gestartet. Drurcke STRG+C zum Beenden.")
    while True:
        sleep(1)  # Hauptloop schlaeft, alles passiert ueber Callback

except KeyboardInterrupt:
    print("\nProgramm beendet.")


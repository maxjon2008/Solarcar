# Inhalt des Moduls
# - Funktion liest speed_km von einer Datei für Inter-Prozess-Kommunikation
# - Funktion schreibt bms_data in eine andere Datei für Inter-Prozess-Kommunikation

# Bibliotheken importieren
import filelock
import logging

# Initialisierung der Variable der Inter-Prozess-Kommunikation
speed_km_h = 0.0

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für Inter-Prozess-Kommunikation definieren
speed_file_path = "SolarCar_speed.txt"
speed_lock_path = "SolarCar_speed.txt.lock"

# speed_km lesen
def read_speed_km_h():
    global speed_km_h
    
    try:
        # lock
        speed_lock = filelock.FileLock(speed_lock_path, timeout=1)
        # Input-Datei öffnen, lesen und schließen
        with speed_lock:
            with open(speed_file_path, mode="r", encoding="utf-8") as datei:
                speed_km_h = datei.read()
    except filelock._error.Timeout:
        print("Aktuell wird der Lock von einem anderen Programm gehalten!")    
    return speed_km_h

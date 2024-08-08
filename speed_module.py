# Inhalt des Moduls
# - Funktion zum Lesen von der Datei für Inter-Prozess-Kommunikation

# Bibliotheken importieren
from filelock import FileLock
import logging

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für Inter-Prozess-Kommunikation definieren
file_path = "SolarCar_speed.txt"
lock_path = "SolarCar_speed.txt.lock"

# lesen und anzeigen 
def read_speed_km_h():
    # lock
    lock = FileLock(lock_path, timeout=1)
    # Input-Datei öffnen, lesen und schließen
    with lock:
        with open(file_path, mode="r", encoding="utf-8") as datei:
            speed_km_h = datei.read()
    return speed_km_h

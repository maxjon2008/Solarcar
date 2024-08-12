# Inhalt des Moduls
# - Funktion zum Lesen von der Datei für Inter-Prozess-Kommunikation

# Bibliotheken importieren
import filelock
import logging

# Initialisierung der Variable der Inter-Prozess-Kommunikation
speed_km_h = 0.0

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für Inter-Prozess-Kommunikation definieren
file_path = "SolarCar_speed.txt"
lock_path = "SolarCar_speed.txt.lock"

# lesen und anzeigen 
def read_speed_km_h():
    global speed_km_h
    
    try:
        # lock
        lock = filelock.FileLock(lock_path, timeout=1)
        # Input-Datei öffnen, lesen und schließen
        with lock:
            with open(file_path, mode="r", encoding="utf-8") as datei:
                speed_km_h = datei.read()
    except filelock._error.Timeout:
        print("Aktuell wird der Lock von einem anderen Programm gehalten!")    
    return speed_km_h

# Inhalt des Moduls
# - das Dictionary mit dem BMS GUI-Daten
# - die Funktion zum Setzen der BMS GUI-Daten
# - Funktion zum Lesen von speed_km von einer Datei für Inter-Prozess-Kommunikation
# - Funktion zum Schreiben des bms_data_string in eine Datei für Inter-Prozess-Kommunikation

# Bibliotheken importieren
import filelock
import logging

# Initialisierung der gelesenen Variable der Inter-Prozess-Kommunikation
speed_km_h = 0.0

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Dateien für speed Inter-Prozess-Kommunikation definieren
speed_file_path = "SolarCar_speed.txt"
speed_lock_path = "SolarCar_speed.txt.lock"

# Dateien bms_data Inter-Prozess-Kommunikation definieren
bms_data_file_path = "SolarCar_bms_data.txt"
bms_data_lock_path = "SolarCar_bms_data.txt.lock"

bms_gui_data = {
    "cell_max_volt": 0,
    "cell_min_volt": 0,
    "cell_max_temp": 0,
    "cell_min_temp": 0,
    "p_pack": 0,
    "soc": 0,
    "warning_string": "",
}

# Funktion zum Setzen der BMS GUI-Daten
def set_bms_gui_data(key, value):
    bms_gui_data[key] = value
    return bms_gui_data

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
        print("Aktuell wird der Speed Lock von einem anderen Programm gehalten!")    
    return speed_km_h

# bms_data schreiben
def write_bms_data():
    try:
        # lock
        bms_data_lock = filelock.FileLock(bms_data_lock_path, timeout=1)
        # Output-Datei öffnen, schreiben und schließen
        with bms_data_lock:
            with open(bms_data_file_path, mode="w", encoding="utf-8") as datei:
                datei.write(str(bms_gui_data["cell_max_volt"]) + ','
                          + str(bms_gui_data["cell_min_volt"]) + ','
                          + str(bms_gui_data["cell_max_temp"]) + ','
                          + str(bms_gui_data["cell_min_temp"]) + ','
                          + str(bms_gui_data["p_pack"]) + ','
                          + str(bms_gui_data["soc"]) + ','
                          + str(bms_gui_data["warning_string"]))
    except filelock._error.Timeout:
        print("Aktuell wird der BMS Data Lock von einem anderen Programm gehalten!")    
    return 0
              
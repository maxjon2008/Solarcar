# Instrumentation GUI für SolarCar
# Initialisierung:
# - Konstruktor für das Fenster aufrufen
# - Gitter mit Zeilen und Spalten konfigurieren
# - Steuervariable und speed erzeugen
# - Dateien für Inter-Prozess-Kommunikation definieren

# Loop:
# - Geschwindigkeit aus Datei für Inter-Prozess-Kommunikation lesen
# - Geschwindigkeit auf GUI anzeigen

# Schaltfläche "Exit" oder Fenster schließen (x) gedrückt:
# - Loop beenden
# - Fenster schließen

# Bibliotheken importieren
import tkinter as tk
import filelock
import logging

# ID zum Beenden des .after Jobs
ID = "0"

# Initialisierung der Variable der Inter-Prozess-Kommunikation
speed_km_h = 0.0

# filelock logging level setzen
logging.getLogger("filelock").setLevel(logging.INFO)

# Konstruktor für das Fenster aufrufen
root = tk.Tk()
root.title("SolarCar Instrumentation")

# Gitter konfigurieren
# Zeilen
for i in range(3):
    root.rowconfigure(i, minsize=180)
# Spalten
for i in range(3):
    root.columnconfigure(i, minsize=320)

# Steuervariable für speed erzeugen und initialisieren
speed_wert = tk.StringVar()
speed_wert.set("       ")
# Ausgabefeld speed erzeugen und in GUI Elemente einbetten
speed = tk.Label(root, textvariable=speed_wert, bg = "yellow", font = ("arial", 50))
speed.grid(row=2, column=1)

# Dateien für speed Inter-Prozess-Kommunikation definieren
speed_file_path = "SolarCar_speed.txt"
speed_lock_path = "SolarCar_speed.txt.lock"

# Steuervariable für warning_string erzeugen und initialisieren
warning_string_wert = tk.StringVar()
warning_string_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
warning_string = tk.Label(root, textvariable=warning_string_wert, fg = "red", font = ("arial", 50))
warning_string.grid(row=1, column=1)

# Steuervariable für BMS data erzeugen und initialisieren
bms_data_00_wert = tk.StringVar()
bms_data_00_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_00 = tk.Label(root, textvariable=bms_data_00_wert, font = ("arial", 50))
bms_data_00.grid(row=0, column=0)
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_10_wert = tk.StringVar()
bms_data_10_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_10 = tk.Label(root, textvariable=bms_data_10_wert, font = ("arial", 50))
bms_data_10.grid(row=1, column=0)
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_20_wert = tk.StringVar()
bms_data_20_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_20 = tk.Label(root, textvariable=bms_data_20_wert, font = ("arial", 50))
bms_data_20.grid(row=2, column=0)
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_01_wert = tk.StringVar()
bms_data_01_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_01 = tk.Label(root, textvariable=bms_data_01_wert, font = ("arial", 50))
bms_data_01.grid(row=0, column=1)
#
# warning_string steht in row 1, column 1
#
# speed_km_h steht in row 1, column 2
#
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_02_wert = tk.StringVar()
bms_data_02_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_02 = tk.Label(root, textvariable=bms_data_02_wert, font = ("arial", 50))
bms_data_02.grid(row=0, column=2)
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_12_wert = tk.StringVar()
bms_data_12_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_12 = tk.Label(root, textvariable=bms_data_12_wert, font = ("arial", 50))
bms_data_12.grid(row=1, column=2)
# Steuervariable für BMS data erzeugen und initialisieren
bms_data_22_wert = tk.StringVar()
bms_data_22_wert.set("       ")
# Ausgabefeld BMS data erzeugen und in GUI Elemente einbetten
bms_data_22 = tk.Label(root, textvariable=bms_data_22_wert, font = ("arial", 50))
bms_data_22.grid(row=2, column=2)

# Dateien bms_data Inter-Prozess-Kommunikation definieren
bms_data_file_path = "SolarCar_bms_data.txt"
bms_data_lock_path = "SolarCar_bms_data.txt.lock"

# lesen und anzeigen 
def lesen_und_anzeigen():
    global ID, speed_km_h
    # speed_km_h lesen und anzeigen
    try:
        # lock
        speed_lock = filelock.FileLock(speed_lock_path, timeout=1)
        # Input-Datei öffnen, lesen und schließen
        with speed_lock:
            with open(speed_file_path, mode="r", encoding="utf-8") as datei:
                speed_km_h = datei.read()    
        
        speed_wert.set(speed_km_h[:8])
    except filelock._error.Timeout:
        print("Aktuell wird der speed Lock von einem anderen Programm gehalten!")
        
    # BMS data lesen und anzeigen   
    try:
        # lock
        bms_data_lock = filelock.FileLock(bms_data_lock_path, timeout=1)
        # Input-Datei öffnen, lesen und schließen
        with bms_data_lock:
            with open(bms_data_file_path, mode="r", encoding="utf-8") as datei:
                bms_data_string = datei.read()
                new_bms_data_string = bms_data_string.split(sep =",")
        # die gelesenen Werte in Ausgabefelder der GUI schreiben
        bms_data_12_wert.set(new_bms_data_string[0] + " mV")
        bms_data_22_wert.set(new_bms_data_string[1] + " mV")
        bms_data_10_wert.set(new_bms_data_string[2] + " °C")
        bms_data_20_wert.set(new_bms_data_string[3] + " °C")
        bms_data_02_wert.set(new_bms_data_string[4] + " W")
        bms_data_00_wert.set(new_bms_data_string[5] + " %")
        warning_string_wert.set(new_bms_data_string[6])
        
    except filelock._error.Timeout:
        print("Aktuell wird der BMS Data Lock von einem anderen Programm gehalten!")
        
    # in root.mainloop() wiederholt aufrufen
    ID = root.after(1000, lesen_und_anzeigen)   

# Funktion verarbeitet "Exit" oder das Schließen des Fensters
def close_window():
    # .after Job beenden
    root.after_cancel(ID)
    # Fenster schließen
    root.destroy()

# Funktion zum ersten Mal aufrufen
lesen_und_anzeigen()

# auch beim Schließen des Fensters die Funktion aufrufen
root.protocol("WM_DELETE_WINDOW", close_window)

# Hauptschleife, damit die GUI angezeigt wird
root.mainloop()

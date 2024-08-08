# Instrumentation GUI für SolarCar
# Initialisierung:
# - Konstruktor für das Fenster aufrufen
# - Gitter mit Zeilen und Spalten konfigurieren
# - Steuervariable und Ausgabefeld erzeugen
# - Dateien für Inter-Prozess-Kommunikation definieren

# Loop:
# - Geschwindigkeit aus Datei für Inter-Prozess-Kommunikation lesen
# - Geschwindigkeit auf GUI anzeigen

# Schaltfläche "Exit" oder Fenster schließen (x) gedrückt:
# - Loop beenden
# - Fenster schließen

# Bibliotheken importieren
import tkinter as tk
from filelock import FileLock
import logging

# ID zum Beenden des .after Jobs
ID = "0"

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

# Steuervariable für das Ausgabefeld erzeugen und initialisieren
ausgabefeld_wert = tk.StringVar()
ausgabefeld_wert.set("       ")

# Ausgabefeld erzeugen und in GUI Elemente einbetten
ausgabefeld = tk.Label(root, textvariable=ausgabefeld_wert, bg = "yellow", font = ("arial", 50))
ausgabefeld.grid(row=2, column=1)

# Dateien für Inter-Prozess-Kommunikation definieren
file_path = "SolarCar_speed.txt"
lock_path = "SolarCar_speed.txt.lock"

# lesen und anzeigen 
def lesen_und_anzeigen():
    global ID
    
    # lock
    lock = FileLock(lock_path, timeout=1)
    # Input-Datei öffnen, lesen und schließen
    with lock:
        with open(file_path, mode="r", encoding="utf-8") as datei:
            speed_km_h = datei.read()    
    
    ausgabefeld_wert.set(speed_km_h[:8])
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

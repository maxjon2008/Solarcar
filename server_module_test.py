# Testprogramm zum Aufruf der Funktionen des Server-Moduls
# Aktionen des Testprogramms:
# - verbindet mit dem THINGSBOARD_SERVER
# - Loop:
#   . holt Daten vom Raspberry Pi
#   . sendet Daten zum Server
#   . schläft 5 Sekunden
#   . toggelt die alive-Variable
# Quelle: https://thingsboard.io/docs/devices-library/raspberry-pi-4/
# Quelle verteilt auf server_module.py und server_main.py

# Bibliotheken importieren
import time
import server_module

# globale Variale
alive = False

def main():
    global alive
    server_module.TB_server_connect()
      
    try: 
        while not server_module.client.stopped:
            attributes = server_module.get_network_attributes()
            server_module.client.send_attributes(attributes)
            server_module.client.send_telemetry({"alive": alive})
            time.sleep(5)
            alive = not alive
    except KeyboardInterrupt:
        print("Program terminated by user")
        server_module.client.disconnect()
   
if __name__=='__main__':
    if server_module.ACCESS_TOKEN != "TEST_TOKEN":
        main()
    else:
        print("Please change the ACCESS_TOKEN variable to match your device access token and run script again.")

# Inhalt des Moduls
# - Funktion zum Verbinden mit dem Thingsboard Cloud Server 
# - Funktion zum Einlesen von Netzwerk-Attributen 
# Quelle: https://thingsboard.io/docs/devices-library/raspberry-pi-4/

import os
import logging.handlers
from tb_gateway_mqtt import TBDeviceMqttClient

ACCESS_TOKEN = "vu3FCDn3RH6VeWgHyX4n"
THINGSBOARD_SERVER = 'thingsboard.cloud'

logging.basicConfig(level=logging.DEBUG)
    
# globale Variable
client = None

# Funktion zum Verbinden mit dem TB Server
def TB_server_connect():
    global client
    client = TBDeviceMqttClient(THINGSBOARD_SERVER, username=ACCESS_TOKEN)
    client.connect()    

# Funktion zum Einlesen der Daten
def get_network_attributes():
    ip_address = os.popen('''hostname -I''').readline().replace('\n', '').replace(',', '.')[:-1]
    mac_address = os.popen('''cat /sys/class/net/*/address''').readline().replace('\n', '').replace(',', '.')
   
    attributes = {
        'ip_address': ip_address,
        'macaddress': mac_address
    }

    print(attributes)
    return attributes

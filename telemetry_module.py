# Inhalt des Moduls:
# - das Dictionary mit den BMS Telemetrie-Daten
# - die Funktion zum Setzen der BMS Telemetrie-Daten

telemetry = {
    "alive": False,
    "analog_data_packs": 0,
    "total_cells": 0,
    "cell_max_volt": 0,
    "cell_min_volt": 0,
    "total_temps": 0,
    "cell_max_temp": 0,
    "cell_min_temp": 0,
    "temp_5": 0,
    "temp_6": 0,
    "i_pack": 0,
    "v_pack": 0,
    "p_pack": 0,
    "i_remaining_capacity": 0,
    "soc": 0,
    "cycles": 0,
    "warning_info_packs": 0,
    "current_limit": 0,
    "charge_fet": 0,
    "discharge_fet": 0,
    "pack_indicate": 0,
    "reverse": 0,
    "ac_in": 0,
    "heart": 0,
    "warning_string": "",
    "balancing_1": 0,
    "balancing_2": 0
}

def set_telemetry(key, value):
    telemetry[key] = value
    return telemetry

# BMS Pace - Python data retrieval and display
* bms.py uses the BMS frontend of https://github.com/Tertiush/bmspace and sends PACE BMS telemetry to local GUI and TB Server. In addition bms.py sends speed_km_h to TB Server. 
* read_GPS_modul2.py provides speed_km_h to bms.py and instrumentation_gui.py.
* instrumentation_gui.py displays speed_km_h and a subset of PACE BMS telemetry. 

Features:
* Cell voltages
* Temperatures
* State of charge (SOC)
* State of health (SOH)
* Warnings & faults
* State indications
* Cell balancing state
* and many more.....

## 1. Important

This software comes with absolutely no guarantees whatsoever. Use at own risk.  
Feel free to fork and expand!

## 2. Confirmed working with
Many brands using the PACE BMS. This software was tested with: 
* Liontron LiFePO4 Speicher: LX48-100 - 48V 100Ah 
* BMS: PACE P16S120A-14530-2.01

## 3. Configuring
Install the pre-requisites as per requirements.txt. Then edit the config.yaml file to suit your needs and run the script bms.py
NB: Tested with Python 3.10. Should work on later version as well.

### 3.1 Notes on configuration options
Tested: 
* **debug_output**: Options are 0 for minimal, 1 for minor errors such as checksums, 2-3 for more severe debug logs.
* **debug_output2**: Options are 0 for no output2, 1 for bms_gui_data, 2 for bms_gui_data and telemetry.

Not tested: 
* **force_pack_offset**: This is currently available in the development version. This offset is used to force a defined offset between the data read from **multiple packs**. If you have more than one pack and only the first is read successfully, you can force an offset here to get subsequent packs to read in successfully. Default is 0, multiple of 2 (e.g. 2, 4, 6....) may work. As large as 20 has been used in one instance.
* **zero_pad_number_cells**: Adds leading 0's to the cell voltages, forcing then to display sequential in some dasboarding tools. E.g. setting this to 2 will display voltages as cell_01 rahter than cell_1.
* **zero_pad_number_packs**: Same as for _cells padding above.

## 4. RJ11 Interface (Typical, confirm your own model!)

When viewed into the RJ11 socket, tab to the bottom, pins are ordered:  
1:NC 2:GND 3:BMS_Tx 4:BMS_Rx 5:GND 6:NC

Either a direct serial interface from your hardware, a USB to serial, or a network connected TCP server device will work. 
Note the voltage levels are normal RS232 (and not TTL / 5V or something else).

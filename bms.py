# Program reads BMS data and sends telemetry to thingsboard.cloud
# telemetry_module.telemetry stores data from only 1 BMS device 
# Tested with 1 BMS device: 
# - Liontron LiFePO4 Speicher: LX48-100 - 48V 100Ah 
# - BMS: PACE P16S120A-14530-2.01

# import libraries
import time
import yaml
import os
import serial
import io
import sys
import constants
import telemetry_module
import server_module
import inter_process_comm_module
import datetime

# start message
print("START: " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# read config
config = {}

if os.path.exists('./config.yaml'):
    print("Loading config.yaml")
    with open(r'./config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)['options']
        
else:
    sys.exit("No config file found")  

# set global config parameters
scan_interval = config['scan_interval']
connection_type = config['connection_type']
bms_serial = config['bms_serial']
bms_connected = False
debug_output = config['debug_output']
debug_output2 = config['debug_output2']

# initialize BMS properties
bms_version = ''
bms_sn = ''
pack_sn = ''
packs = 1
cells = 13
temps = 6

# alive variable
alive = False

# connection type message
print("Connection Type: " + connection_type)

# lists for telemetry assignment
# v_cell_key = ["v_cell_1", "v_cell_2", "v_cell_3", "v_cell_4", "v_cell_5", "v_cell_6", "v_cell_7", "v_cell_8",
          # "v_cell_9", "v_cell_10", "v_cell_11", "v_cell_12", "v_cell_13", "v_cell_14", "v_cell_15", "v_cell_16"]
temp_key = ["temp_1", "temp_2", "temp_3", "temp_4", "temp_5", "temp_6"]

# function connects to BMS
def bms_connect(address, port):

    if connection_type == "Serial":

        try:
            print("trying to connect %s" % bms_serial)
            s = serial.Serial(bms_serial,timeout = 1)
            print("BMS serial connected")
            return s, True
        except IOError as msg:
            print("BMS serial error connecting: %s" % msg)
            return False, False    

    else:

        try:
            print("trying to connect " + address + ":" + str(port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((address, port))
            print("BMS socket connected")
            return s, True
        except OSError as msg:
            print("BMS socket error connecting: %s" % msg)
            return False, False

# function sends data to BMS
def bms_sendData(comms,request=''):

    if connection_type == "Serial":

        try:
            if len(request) > 0:
                comms.write(request)
                time.sleep(0.25)
                return True
        except IOError as e:
            print("BMS serial error: %s" % e)
            # global bms_connected
            return False

    else:

        try:
            if len(request) > 0:
                comms.send(request)
                time.sleep(0.25)
                return True
        except Exception as e:
            print("BMS socket error: %s" % e)
            # global bms_connected
            return False

# function receives data from BMS
def bms_get_data(comms):
    try:
        if connection_type == "Serial":
            inc_data = comms.readline()
        else:
            temp = bytes()
            
            while len(temp) == 0 or temp[-1] != 13:
                temp = temp + comms.recv(4096)

            temp2 = temp.split(b'\r')
            # Decide which one to take:
            for element in range(0,len(temp2)):
                SOI = hex(ord(temp2[element][0:1]))
                if SOI == '0x7e':
                    inc_data = temp2[element] + b'\r'
                    break

            if (len(temp2) > 2) & (debug_output > 0):
                print("Multiple EOIs detected")
                print("...for incoming data: " + str(temp) + " |Hex: " + str(temp.hex(' ')))
                
        return inc_data
    except Exception as e:
        print("BMS socket receive error: %s" % e)
        # global bms_connected
        return False

# function calculates data checksum
def chksum_calc(data):

    global debug_output
    chksum = 0

    try:

        for element in range(1, len(data)): #-5):
            chksum += (data[element])
        
        chksum = chksum % 65536
        chksum = '{0:016b}'.format(chksum)
    
        flip_bits = '' 
        for i in chksum:
            if i == '0':
                flip_bits += '1'
            else:
                flip_bits += '0'

        chksum = flip_bits
        chksum = int(chksum,2)+1

        chksum = format(chksum, 'X')

    except Exception as e:
        if debug_output > 0:
            print("Error calculating CHKSUM using data: " + data)
            print("Error details: ", str(e))
        return(False)

    return(chksum)

# function processes CID2 response information (RTN)
# CID2: Command information：control indication code
# （data or action description）
def cid2_rtn(rtn):

    # RTN Reponse codes, looking for errors
    if rtn == b'00':
        return False, False
    elif rtn == b'01':
        return True, "RTN Error 01: Undefined RTN error"
    elif rtn == b'02':
        return True, "RTN Error 02: CHKSUM error"
    elif rtn == b'03':
        return True, "RTN Error 03: LCHKSUM error"
    elif rtn == b'04':
        return True, "RTN Error 04: CID2 undefined"
    elif rtn == b'05':
        return True, "RTN Error 05: Undefined error"
    elif rtn == b'06':
        return True, "RTN Error 06: Undefined error"
    elif rtn == b'09':
        return True, "RTN Error 09: Operation or write error"
    else:
        return False, False

# function parses incoming data
def bms_parse_data(inc_data):

    global debug_output
    
    # original test string
    #inc_data = b'~25014600D0F40002100DD50DBC0DD70DD70DD40DD70DD20DD50DD30DD60DC10DD40DD50DD70DD30DD5060B760B710B700B7A0B7D0B9D0000DD2326A90226AC011126AC64100DD30DBD0DD40DC60DD50DD40DD50DD50DD60DD60DD40DD20DD30\r'

    try:
        
        SOI = hex(ord(inc_data[0:1]))
        if SOI != '0x7e':
            return(False,"Incorrect starting byte for incoming data")


        if debug_output > 1:
            print("SOI: ", SOI)
            print("VER: ", inc_data[1:3])
            print("ADR: ", inc_data[3:5])
            print("CID1 (Type): ", inc_data[5:7])
            # CID1: Device indication code (device type description）

        RTN = inc_data[7:9]
        error, info = cid2_rtn(RTN)
        if error:
            print(error)
            raise Exception(error)
        
        LCHKSUM = inc_data[9]

        if debug_output > 1:
            print("RTN: ", RTN)
            print("LENGTH: ", inc_data[9:13])
            print(" - LCHKSUM: ", LCHKSUM)
            print(" - LENID: ", inc_data[10:13])

        LENID = int(inc_data[10:13],16) #amount of bytes, i.e. 2x hex

        calc_LCHKSUM = lchksum_calc(inc_data[10:13])
        if calc_LCHKSUM == False:
            return(False,"Error calculating LCHKSUM for incoming data")

        if LCHKSUM != ord(calc_LCHKSUM):
            if debug_output > 0:
                print("LCHKSUM received: " + str(LCHKSUM) + " does not match calculated: " + str(ord(calc_LCHKSUM)))
            return(False,"LCHKSUM received: " + str(LCHKSUM) + " does not match calculated: " + str(ord(calc_LCHKSUM)))

        if debug_output > 1:
            print(" - LENID (int): ", LENID)

        INFO = inc_data[13:13+LENID]

        if debug_output > 1:
            print("INFO: ", INFO)

        CHKSUM = inc_data[13+LENID:13+LENID+4]
        
        if debug_output > 1:
            print("CHKSUM: ", CHKSUM)
            #print("EOI: ", hex(inc_data[13+LENID+4]))

        calc_CHKSUM = chksum_calc(inc_data[:len(inc_data)-5])


        if debug_output > 1:
            print("Calc CHKSUM: ", calc_CHKSUM)
    except Exception as e:
        if debug_output > 0:
            print("Error1 calculating CHKSUM using data: ", inc_data)
        return(False,"Error1 calculating CHKSUM: " + str(e))

    if calc_CHKSUM == False:
        if debug_output > 0:
            print("Error2 calculating CHKSUM using data: ", inc_data)
        return(False,"Error2 calculating CHKSUM")

    if CHKSUM.decode("ASCII") == calc_CHKSUM:
        return(True,INFO)
    else:
        if debug_output > 0:
            print("Received and calculated CHKSUM does not match: Received: " + CHKSUM.decode("ASCII") + ", Calculated: " + calc_CHKSUM)
            print("...for incoming data: " + str(inc_data) + " |Hex: " + str(inc_data.hex(' ')))
            print("Length of incoming data as measured: " + str(len(inc_data)))
            print("SOI: ", SOI)
            print("VER: ", inc_data[1:3])
            print("ADR: ", inc_data[3:5])
            print("CID1 (Type): ", inc_data[5:7])
            print("RTN (decode!): ", RTN)
            print("LENGTH: ", inc_data[9:13])
            print(" - LCHKSUM: ", inc_data[9])
            print(" - LENID: ", inc_data[10:13])
            print(" - LENID (int): ", int(inc_data[10:13],16))
            print("INFO: ", INFO)
            print("CHKSUM: ", CHKSUM)
            #print("EOI: ", hex(inc_data[13+LENID+4]))
        return(False,"Checksum error")

def lchksum_calc(lenid):

    chksum = 0

    try:

        # for element in range(1, len(lenid)): #-5):
        #     chksum += (lenid[element])
        
        for element in range(0, len(lenid)):
            chksum += int(chr(lenid[element]),16)

        chksum = chksum % 16
        chksum = '{0:04b}'.format(chksum)

        flip_bits = '' 
        for i in chksum:
            if i == '0':
                flip_bits += '1'
            else:
                flip_bits += '0'

        chksum = flip_bits
        chksum = int(chksum,2)

        chksum += 1

        if chksum > 15:
            chksum = 0

        chksum = format(chksum, 'X')

    except:

        print("Error calculating LCHKSUM using LENID: ", lenid)
        return(False)

    return(chksum)

# function requests data from BMS
def bms_request(bms, ver=b"\x32\x35",adr=b"\x30\x31",cid1=b"\x34\x36",cid2=b"\x43\x31",info=b"",LENID=False):

    global bms_connected
    global debug_output
    
    # build command
    request = b'\x7e'
    request += ver
    request += adr
    request += cid1
    request += cid2

    if not(LENID):
        LENID = len(info)
        #print("Length: ", LENID)
        LENID = bytes(format(LENID, '03X'), "ASCII")

    #print("LENID: ", LENID)

    if LENID == b'000':
        LCHKSUM = '0'
    else:
        LCHKSUM = lchksum_calc(LENID)
        if LCHKSUM == False:
            return(False,"Error calculating LCHKSUM)")
    #print("LCHKSUM: ", LCHKSUM)
    request += bytes(LCHKSUM, "ASCII")
    request += LENID
    request += info
    CHKSUM = bytes(chksum_calc(request), "ASCII")
    if CHKSUM == False:
        return(False,"Error calculating CHKSUM)")
    request += CHKSUM
    request += b'\x0d'

    if debug_output > 2:
        print("-> Outgoing Data: ", request)
    
    # send data to BMS
    if not bms_sendData(bms,request):
        bms_connected = False
        print("Error, connection to BMS lost")
        return(False,"Error, connection to BMS lost")

    # receive data from BMS
    inc_data = bms_get_data(bms)

    if inc_data == False:
        print("Error retrieving data from BMS")
        return(False,"Error retrieving data from BMS")

    if debug_output > 2:
        print("<- Incoming data: ", inc_data)

    success, INFO = bms_parse_data(inc_data)

    return(success, INFO)

# function requests "pack number" from BMS
def bms_getPackNumber(bms):

    success, INFO = bms_request(bms,cid2=constants.cid2PackNumber)

    if success == False:
        return(False,INFO)    

    try:
        packNumber = int(INFO,16)
    except:
        print("Error extracting total battery count in pack")
        return(False,"Error extracting total battery count in pack")

    return(success,packNumber)

# function requests "software version" from BMS
def bms_getVersion(comms):

    global bms_version

    success, INFO = bms_request(bms,cid2=constants.cid2SoftwareVersion)
    
    if success == False:
        return(False,INFO)

    try:

        bms_version = bytes.fromhex(INFO.decode("ascii")).decode("ASCII")
        
        # remove NUL character
        bms_version_fixed = bms_version.replace('\x00','')
        
        print("BMS Version: " + bms_version_fixed)
    except:
        return(False,"Error extracting BMS version")

    return(success,bms_version)

# function requests "product information" (serial number) from BMS
def bms_getSerial(comms):

    global bms_sn
    global pack_sn

    success, INFO = bms_request(bms,cid2=constants.cid2SerialNumber)

    if success == False:
        print("Error: " + INFO)
        return(False,INFO, False)

    try:

        bms_sn = bytes.fromhex(INFO[0:30].decode("ascii")).decode("ASCII").replace(" ", "") #Remove spaces to prevent the unique ID having spaces
        pack_sn = bytes.fromhex(INFO[40:68].decode("ascii")).decode("ASCII").replace(" ", "")
        # client.publish(config['mqtt_base_topic'] + "/bms_sn",bms_sn)
        # client.publish(config['mqtt_base_topic'] + "/pack_sn",pack_sn)
        print("BMS Serial Number: " + bms_sn)
        print("Pack Serial Number: " + pack_sn)

    except:
        return(False,"Error extracting BMS version", False)

    return(success,bms_sn,pack_sn)

# function requests "analog data" from BMS
def bms_getAnalogData(bms,batNumber):

    global cells
    global temps
    global packs
    byte_index = 2
    i_pack = []
    v_pack = []
    i_remain_cap = []
    i_design_cap = []
    cycles = []
    i_full_cap = []
    soc = []
    soh = []

    battery = bytes(format(batNumber, '02X'), 'ASCII')

    success, inc_data = bms_request(bms,cid2=constants.cid2PackAnalogData,info=battery)

    #bms_request -> bms_get_data(inc_data/INFO = bms_parse_data)

    #prefix: ~250146006118
    #To test set: inc_data = INFO
    # original test string
    #inc_data = b'000A100CF40CF40CF40CF50CF30CF40CF40CF30CF80CF30CF30CF30CF30CF50CF40CF4060B2E0B300B2D0B300B3B0B47FEFCCF406B58096D2700146D60626D606D606D606D6064D1180000100000000000000000000000000000000000000000000000000000000000000000060AAA0AAA0AAA0AAA0AAA0AAA000000000000090000000000006200000000000000006400000000100CF40CF40CF30CF40CF30CF40CF40CF40CF30CF30CF40CF40CF30CF30CF40CF2060B320B2F0B340B2C0B3D0B4AFEF6CF386B65096D2700146D60626D606D606D606D6064CF320000100CF30CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF4060B330B320B2E0B340B410B48FEF9CF3F6B72096D2700146D60626D606D606D606D6064CFCC0000100CF40CF30CF40CF30CF40CF40CF30CF40CF30CF30CF30CF40CF30CF40CF30CF1060B330B2D0B2F0B340B3D0B48FF10CF646B7A096D2700146D60626D606D606D606D6064CFF70000100CF40CF30CF20CF20CF30CF20CF30CF10CF30CF30CF30CF20CF30CF30CF30CF1060B2D0B320B300B310B3C0B49FF11CF296B7F096D2A00136D60626D606D606D606D6064D0030000100CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF50CF40CF40CF40CF3060B310B2E0B310B2E0B400B4AFF1ACF4075580976EE00146D60636D606D606D606D6064CFD20000100CF30CF10CF40CF30CF30CF40CF30CF30CF10CF30CF40CF30CF30CF30CF30CF2060B300B2E0B2F0B330B3B0B42FF07CF636B50096D2400156D60626D606D606D606D6064CFCE0000100CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF40CF3060B2B0B2D0B290B2F0B3B0B4BFF1BCF3F6B7F096D2D00126D60626D606D606D606D6064D1260000100CF40CF40CF40CF40CF40CF40CF40CF60CF30CF40CF40CF40CF40CF40CF40CF3060B2A0B2E0B2D0B2A0B390B43FF24CF406B5F096D2700146D60626D606D606D606D6064D0C70000'


    if success == False:
        return(False,inc_data)

    try:

        packs = int(inc_data[byte_index:byte_index+2],16)
        telemetry_module.set_telemetry("analog_data_packs", packs) # telemetry
        if debug_output > 0:
            print("Packs: " + str(packs))
        byte_index += 2

        v_cell = {}
        t_cell = {}

        for p in range(1,packs+1):

            if p > 1:
                cells_prev = cells

            cells = int(inc_data[byte_index:byte_index+2],16)
            telemetry_module.set_telemetry("total_cells", cells) # telemetry

            #Possible remove this next test as were now testing for the INFOFLAG at the end
            if p > 1:
                if cells != cells_prev:
                    byte_index += 2
                    cells = int(inc_data[byte_index:byte_index+2],16)
                    if cells != cells_prev:
                        print("Error parsing BMS analog data: Cannot read multiple packs")
                        return(False,"Error parsing BMS analog data: Cannot read multiple packs")
            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", Total cells: " + str(cells))
            byte_index += 2
            
            cell_min_volt = 0
            cell_max_volt = 0

            for i in range(0,cells):
                v_cell[(p-1,i)] = int(inc_data[byte_index:byte_index+4],16)

                #Adding this because otherwise weird stuff happens
                # added in fork https://github.com/jpgnz/bmspace
                if v_cell[(p-1, i)] > 5000:
                    sys.exit("Exiting script because the value is greater than 5000")

                byte_index += 4
               
                if debug_output > 0:
                    print("Pack " + str(p).zfill(config['zero_pad_number_packs']) +", V Cell" + str(i+1).zfill(config['zero_pad_number_cells']) + ": " + str(v_cell[(p-1,i)]) + " mV")

                #Calculate cell max and min volt
                if i == 0:
                    cell_min_volt = v_cell[(p-1,i)]
                    cell_max_volt = v_cell[(p-1,i)]
                else:
                    if v_cell[(p-1,i)] < cell_min_volt:
                        cell_min_volt = v_cell[(p-1,i)]
                    if v_cell[(p-1,i)] > cell_max_volt:
                        cell_max_volt = v_cell[(p-1,i)]
            
            #Calculate cells max diff volt
            cell_max_diff_volt = cell_max_volt - cell_min_volt
            telemetry_module.set_telemetry("cell_max_volt", cell_max_volt) # telemetry
            telemetry_module.set_telemetry("cell_min_volt", cell_min_volt) # telemetry
            inter_process_comm_module.set_bms_gui_data("cell_max_volt", cell_max_volt) # instrumentation gui
            inter_process_comm_module.set_bms_gui_data("cell_min_volt", cell_min_volt) # instrumentation gui

            
            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) +", Cell Max Diff Volt Calc: " + str(cell_max_diff_volt) + " mV")

            temps = int(inc_data[byte_index:byte_index + 2],16)
            telemetry_module.set_telemetry("total_temps", temps) # telemetry

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", Total temperature sensors: " + str(temps))
            byte_index += 2

            for i in range(0,temps): 
                t_cell[(p-1,i)] = (int(inc_data[byte_index:byte_index + 4],16)-2730)/10
                if i >= 4:
                    telemetry_module.set_telemetry(temp_key[i], t_cell[(p-1,i)]) # telemetry of temp_5 and temp_6 
                
                byte_index += 4
                if debug_output > 0:
                    print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", Temp" + str(i+1) + ": " + str(round(t_cell[(p-1,i)],1)) + " °C")

            #Calculate "cell_max_temp", "cell_min_temp" of temp_1 .. temp_4
            for i in range(0,4):                
                if i == 0:
                    cell_min_temp = t_cell[(p-1,i)]
                    cell_max_temp = t_cell[(p-1,i)]
                else:
                    if t_cell[(p-1,i)] < cell_min_temp:
                        cell_min_temp = t_cell[(p-1,i)]
                    if t_cell[(p-1,i)] > cell_max_temp:
                        cell_max_temp = t_cell[(p-1,i)]
            telemetry_module.set_telemetry("cell_max_temp", cell_max_temp) # telemetry
            telemetry_module.set_telemetry("cell_min_temp", cell_min_temp) # telemetry
            inter_process_comm_module.set_bms_gui_data("cell_max_temp", cell_max_temp) # instrumentation gui
            inter_process_comm_module.set_bms_gui_data("cell_min_temp", cell_min_temp) # instrumentation gui
 
            # t_mos= (int(inc_data[byte_index:byte_index+4],16))/160-273
            # # client.publish(config['mqtt_base_topic'] + "/t_mos",str(round(t_mos,1)))
            # if print_initial:
            #     print("T Mos: " + str(t_mos) + " Deg")

            # t_env= (int(inc_data[byte_index:byte_index+4],16))/160-273
            # # client.publish(config['mqtt_base_topic'] + "/t_env",str(round(t_env,1)))
            # offset += 7
            # if print_initial:
            #     print("T Env: " + str(t_env) + " Deg")

            i_pack.append(int(inc_data[byte_index:byte_index+4],16))
            byte_index += 4
            if i_pack[p-1] >= 32768:
                i_pack[p-1] = -1*(65535 - i_pack[p-1])
            i_pack[p-1] = i_pack[p-1]/100
            telemetry_module.set_telemetry("i_pack", i_pack[p-1]) # telemetry

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", I Pack: " + str(i_pack[p-1]) + " A")

            v_pack.append(int(inc_data[byte_index:byte_index+4],16)/1000)
            telemetry_module.set_telemetry("v_pack", v_pack[p-1]) # telemetry
            byte_index += 4

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", V Pack: " + str(v_pack[p-1]) + " V")

            # calculate "p_pack"
            p_pack = v_pack[p-1] * i_pack[p-1]
            telemetry_module.set_telemetry("p_pack", p_pack) # telemetry
            inter_process_comm_module.set_bms_gui_data("p_pack", p_pack) # instrumentation gui
            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", P Pack: " + str(p_pack) + " W")
            
            i_remain_cap.append(int(inc_data[byte_index:byte_index+4],16)*10)
            telemetry_module.set_telemetry("i_remaining_capacity", i_remain_cap[p-1]) # telemetry
            byte_index += 4

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", I Remaining Capacity: " + str(i_remain_cap[p-1]) + " mAh")

            byte_index += 2 # Manual: Define number P = 3

            i_full_cap.append(int(inc_data[byte_index:byte_index+4],16)*10)
            byte_index += 4

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", I Full Capacity: " + str(i_full_cap[p-1]) + " mAh")

            try:
                soc.append(round(i_remain_cap[p-1]/i_full_cap[p-1]*100,2))
                telemetry_module.set_telemetry("soc", soc[p-1]) # telemetry
                inter_process_comm_module.set_bms_gui_data("soc", soc[p-1]) # instrumentation gui
                if debug_output > 0:
                    print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", SOC: " + str(soc[p-1]) + " %")
            except Exception as e:
                print("Error parsing BMS analog data, missing pack"  + str(p).zfill(config['zero_pad_number_packs']) + " full capacity: ", str(e))

            cycles.append(int(inc_data[byte_index:byte_index+4],16))
            telemetry_module.set_telemetry("cycles", cycles[p-1]) # telemetry
            byte_index += 4

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", Cycles: " + str(cycles[p-1]))

            i_design_cap.append(int(inc_data[byte_index:byte_index+4],16)*10)
            byte_index += 4

            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", Design Capacity: " + str(i_design_cap[p-1]) + " mAh")

            try:
                soh.append(round(i_full_cap[p-1]/i_design_cap[p-1]*100,2))

                if debug_output > 0:
                    print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", SOH: " + str(soh[p-1]) + " %")
            except Exception as e:
                print("Error parsing BMS analog data, missing pack"  + str(p).zfill(config['zero_pad_number_packs']) + " design capacity: ", str(e))

            #byte_index += 2

            byte_index += int(config['force_pack_offset'])

            #Test for non signed value (matching cell count), to skip possible INFOFLAG present in data
            if p < packs: #Test - Is there more packs to read?
                while (byte_index < len(inc_data)) and (cells != int(inc_data[byte_index:byte_index+2],16)):
                    byte_index += 2
                    if byte_index > len(inc_data):
                        print("Error parsing BMS analog data: Cannot read multiple packs")
                        return(False,"Error parsing BMS analog data: Cannot read multiple packs")


    except Exception as e:
        print("Error parsing BMS analog data: ", str(e))
        return(False,"Error parsing BMS analog data: " + str(e))

    return True,True

# function requests "pack capacity" from BMS
# - pack remain capacity
# - pack full capacity
# - pack design capacity
# not included in telemetry
def bms_getPackCapacity(bms):

    byte_index = 0

    success, inc_data = bms_request(bms,cid2=constants.cid2PackCapacity) # Seem to always reply with pack 1 data, even with ADR= 0 or FF and INFO= '' or FF

    if success == False:
        return(False,inc_data)

    try:

        pack_remain_cap = int(inc_data[byte_index:byte_index+4],16)*10
        byte_index += 4
        if debug_output > 0:
            print("Pack Remaining Capacity: " + str(pack_remain_cap) + " mAh")

        pack_full_cap = int(inc_data[byte_index:byte_index+4],16)*10
        byte_index += 4
        if debug_output > 0:
            print("Pack Full Capacity: " + str(pack_full_cap) + " mAh")

        pack_design_cap = int(inc_data[byte_index:byte_index+4],16)*10
        byte_index += 4
        if debug_output > 0:
            print("Pack Design Capacity: " + str(pack_design_cap) + " mAh")

        pack_soc = round(pack_remain_cap/pack_full_cap*100,2)
        if debug_output > 0:
            print("Pack SOC: " + str(pack_soc) + " %")

        pack_soh = round(pack_full_cap/pack_design_cap*100,2)
        if debug_output > 0:
            print("Pack SOH: " + str(pack_soh) + " %")

    except Exception as e:
        print("Error parsing BMS pack capacity data: ", str(e))
        return False, "Error parsing BMS pack capacity data: " + str(e)

    return True,True

# function requests "pack warn info" from BMS
def bms_getWarnInfo(bms):

    byte_index = 2
    packsW = 1
    warnings = ""

    success, inc_data = bms_request(bms,cid2=constants.cid2WarnInfo,info=b'FF')

    if success == False:
        return(False,inc_data)

    # original test string
    #inc_data = b'000210000000000000000000000000000000000600000000000000000000000E0000000000001110000000000000000000000000000000000600000000000000000000000E00000000000000'
    
    # my test strings
    # - single warning from one topic (e. g. cell voltage)
    # - multiple warning from one topic
    # - distributed warnings over all topics
    #inc_data = b'0001100100000000000000000000000000000006000000000000000000000000000000000000' # cell 1 voltage < low limit
    #inc_data = b'0001100200000000000000000000000000000006000000000000000000000000000000000000' # cell 1 voltage > up limit
    #inc_data = b'000110F000000000000000000000000000000006000000000000000000000000000000000000' # cell 1 other fault
    #inc_data = b'0001100001000000000000000000000000000006000000000000000000000000000000000000' # cell 2 voltage < low limit
    #inc_data = b'0001100000010000000000000000000000000006000000000000000000000000000000000000' # cell 3 voltage < low limit
    #inc_data = b'0001100000000100000000000000000000000006000000000000000000000000000000000000' # cell 4 voltage < low limit
    #inc_data = b'0001100000000001000000000000000000000006000000000000000000000000000000000000' # cell 5 voltage < low limit
    #inc_data = b'0001100000000000010000000000000000000006000000000000000000000000000000000000' # cell 6 voltage < low limit
    #inc_data = b'0001100000000000000100000000000000000006000000000000000000000000000000000000' # cell 7 voltage < low limit
    #inc_data = b'0001100000000000000001000000000000000006000000000000000000000000000000000000' # cell 8 voltage < low limit
    #inc_data = b'0001100000000000000000010000000000000006000000000000000000000000000000000000' # cell 9 voltage < low limit
    #inc_data = b'0001100000000000000000000100000000000006000000000000000000000000000000000000' # cell 10 voltage < low limit
    #inc_data = b'0001100000000000000000000001000000000006000000000000000000000000000000000000' # cell 11 voltage < low limit
    #inc_data = b'0001100000000000000000000000010000000006000000000000000000000000000000000000' # cell 12 voltage < low limit
    #inc_data = b'0001100000000000000000000000000100000006000000000000000000000000000000000000' # cell 13 voltage < low limit
    #inc_data = b'0001100000000000000000000000000001000006000000000000000000000000000000000000' # cell 14 voltage < low limit
    #inc_data = b'0001100000000000000000000000000000010006000000000000000000000000000000000000' # cell 15 voltage < low limit
    #inc_data = b'0001100000000000000000000000000000000106000000000000000000000000000000000000' # cell 16 voltage < low limit
    #inc_data = b'0001100102F00102F00102F00102F00102F00106000000000000000000000000000000000000' # cell voltage multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006020000000000000000000000000000000000' # temp 1 > up limit
    #inc_data = b'0001100000000000000000000000000000000006000200000000000000000000000000000000' # temp 2 > up limit
    #inc_data = b'0001100000000000000000000000000000000006000002000000000000000000000000000000' # temp 3 > up limit
    #inc_data = b'0001100000000000000000000000000000000006000000020000000000000000000000000000' # temp 4 > up limit
    #inc_data = b'0001100000000000000000000000000000000006000000000200000000000000000000000000' # temp 5 > up limit
    #inc_data = b'0001100000000000000000000000000000000006000000000002000000000000000000000000' # temp 6 > up limit
    #inc_data = b'000110000000000000000000000000000000000602F00102F001000000000000000000000000' # temp multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000F00000000000000000000000' # charge current other fault
    #inc_data = b'0001100000000000000000000000000000000006000000000000000100000000000000000000' # total voltage < low limit
    #inc_data = b'0001100000000000000000000000000000000006000000000000000002000000000000000000' # discharge current > up limit
    #inc_data = b'00011000000000000000000000000000000000060000000000000102F0000000000000000000' # charge multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000800000000000000000' # Protection State 1: undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000400000000000000000' # Protection State 1: Short circuit
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000200000000000000000' # Protection State 1: Discharge current protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000100000000000000000' # Protection State 1: Charge current protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000080000000000000000' # Protection State 1: Lower total volt protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000040000000000000000' # Protection State 1: Above total volt protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000020000000000000000' # Protection State 1: Lower cell volt protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000010000000000000000' # Protection State 1: Above cell volt protect
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000FF0000000000000000' # Protection State 1: multiple warnings 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000008000000000000000' # Protection State 2: Fully 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000004000000000000000' # Protection State 2: Lower Env temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000002000000000000000' # Protection State 2: Above Env temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000001000000000000000' # Protection State 2: Above MOS temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000800000000000000' # Protection State 2: Lower discharge temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000400000000000000' # Protection State 2: Lower charge temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000200000000000000' # Protection State 2: Above discharge temp protect 
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000100000000000000' # Protection State 2: Above charge temperature protect 
    #inc_data = b'000110000000000000000000000000000000000600000000000000000000FF06000000000000' # Protection State 2: multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000080000000000000' # Instruction State: Heart indicate ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000040000000000000' # Instruction State: Undefined -> omitted
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000020000000000000' # Instruction State: ACin ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000010000000000000' # Instruction State: Reverse indicate ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000008000000000000' # Instruction State: Pack indicate ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000004000000000000' # Instruction State: DFET indicate ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000002000000000000' # Instruction State: CFET indicate ON
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000001000000000000' # Instruction State: Current limit indicate ON
    #inc_data = b'00011000000000000000000000000000000000060000000000000000000000FF000000000000' # Instruction State: multiple indications
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000800000000000' # Control State: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000400000000000' # Control State: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000200000000000' # Control State: LED warn function disabled
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000100000000000' # Control State: Current limit function disabled
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000080000000000' # Control State: Current limit gear => low gear
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000040000000000' # Control State: undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000020000000000' # Control State: undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000010000000000' # Control State: Buzzer warn function enabled
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000FF0000000000' # Control State: multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000008000000000' # Fault State: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000004000000000' # Fault State: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000002000000000' # Fault State: Sample fault
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000001000000000' # Fault State: Cell fault
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000800000000' # Fault State: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000400000000' # Fault State: NTC fault (NTC)
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000200000000' # Fault State: Discharge MOS fault
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000100000000' # Fault State: Charge MOS fault
    #inc_data = b'000110000000000000000000000000000000000600000000000000000000000000FF00000000' # Fault State: multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000008000' # Warning State 1: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000004000' # Warning State 1: Undefined
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000002000' # Warning State 1: Discharge current warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000001000' # Warning State 1: Charge current warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000800' # Warning State 1: Lower total voltage warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000400' # Warning State 1: Above total voltage warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000200' # Warning State 1: Lower cell voltage warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000100' # Warning State 1: Above cell voltage warn
    #inc_data = b'000110000000000000000000000000000000000600000000000000000000000000000000FF00' # Warning State 1: multiple warnings
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000080' # Warning State 2: Low power warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000040' # Warning State 2: High MOS temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000020' # Warning State 2: Low env temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000010' # Warning State 2: High env temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000008' # Warning State 2: Low discharge temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000004' # Warning State 2: Low charge temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000002' # Warning State 2: Above discharge temp warn
    #inc_data = b'0001100000000000000000000000000000000006000000000000000000000000000000000001' # Warning State 2: Above charge temp warn
    #inc_data = b'00011000000000000000000000000000000000060000000000000000000000000000000000FF' # Warning State 2: multiple warnings
    #inc_data = b'0001100000000000000000000000000000F000060000020000000000F0100820042000008040' # Warnings from 10 sources
    
    try:

        packsW = int(inc_data[byte_index:byte_index+2],16)
        telemetry_module.set_telemetry("warning_info_packs", packsW) # telemetry
        if debug_output > 0:
            print("Packs for warnings: " + str(packsW))
        byte_index += 2

        for p in range(1,packs+1):

            cellsW = int(inc_data[byte_index:byte_index+2],16)
            byte_index += 2

            for c in range(1,cellsW+1):

                if inc_data[byte_index:byte_index+2] != b'00':
                    warn = constants.warningStates[inc_data[byte_index:byte_index+2]]
                    warnings += "cell " + str(c) + " " + warn + ", "
                byte_index += 2

            tempsW = int(inc_data[byte_index:byte_index+2],16)
            byte_index += 2
        
            for t in range(1,tempsW+1):

                if inc_data[byte_index:byte_index+2] != b'00':
                    warn = constants.warningStates[inc_data[byte_index:byte_index+2]]
                    warnings += "temp " + str(t) + " " + warn + ", "
                byte_index += 2

            if inc_data[byte_index:byte_index+2] != b'00':
                warn = constants.warningStates[inc_data[byte_index:byte_index+2]]
                warnings += "charge current " + warn + ", "
            byte_index += 2

            if inc_data[byte_index:byte_index+2] != b'00':
                warn = constants.warningStates[inc_data[byte_index:byte_index+2]]
                warnings += "total voltage " + warn + ", "
            byte_index += 2

            if inc_data[byte_index:byte_index+2] != b'00':
                warn = constants.warningStates[inc_data[byte_index:byte_index+2]]
                warnings += "discharge current " + warn + ", "
            byte_index += 2

            protectState1 = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if protectState1 > 0:
                warnings += "Protection State 1: "
                for x in range(0,8):
                    if (protectState1 & (1<<x)):
                        warnings += constants.protectState1[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "
            byte_index += 2

            protectState2 = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if protectState2 > 0:
                warnings += "Protection State 2: "
                for x in range(0,8):
                    if (protectState2 & (1<<x)):
                        warnings += constants.protectState2[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "
            byte_index += 2

            
            # "instruction state" shall not be included in "warnings"
            # instructionState = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            # if instructionState > 0:
                # warnings += "Instruction State: "
                # for x in range(0,8):
                    # if (instructionState & (1<<x)):
                         # warnings += constants.instructionState[x+1] + " | "
                # warnings = warnings.rstrip("| ")
                # warnings += ", "  
            # byte_index += 2

            # "instruction state" shall be printed separately
            # added in fork https://github.com/jpgnz/bmspace
            instructionState = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            telemetry_module.set_telemetry("current_limit", instructionState>>0 & 1) # telemetry
            telemetry_module.set_telemetry("charge_fet", instructionState>>1 & 1) # telemetry
            telemetry_module.set_telemetry("discharge_fet", instructionState>>2 & 1) # telemetry
            telemetry_module.set_telemetry("pack_indicate", instructionState>>3 & 1) # telemetry
            telemetry_module.set_telemetry("reverse", instructionState>>4 & 1) # telemetry
            telemetry_module.set_telemetry("ac_in", instructionState>>5 & 1) # telemetry
            telemetry_module.set_telemetry("heart", instructionState>>7 & 1) # telemetry
            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", current_limit: " + str(instructionState>>0 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", charge_fet: " + str(instructionState>>1 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", discharge_fet: " + str(instructionState>>2 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", pack_indicate: " + str(instructionState>>3 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", reverse: " + str(instructionState>>4 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", ac_in: " + str(instructionState>>5 & 1))
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", heart: " + str(instructionState>>7 & 1))
            byte_index += 2


            controlState = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if controlState > 0:
                warnings += "Control State: "
                for x in range(0,8):
                    if (controlState & (1<<x)):
                        warnings += constants.controlState[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "  
            byte_index += 2

            faultState = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if faultState > 0:
                warnings += "Fault State: "
                for x in range(0,8):
                    if (faultState & (1<<x)):
                        warnings += constants.faultState[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "  
            byte_index += 2

            balanceState1 = '{0:08b}'.format(int(inc_data[byte_index:byte_index+2],16))
            byte_index += 2

            balanceState2 = '{0:08b}'.format(int(inc_data[byte_index:byte_index+2],16))
            byte_index += 2

            warnState1 = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if warnState1 > 0:
                warnings += "Warning State 1: "
                for x in range(0,8):
                    if (warnState1 & (1<<x)):
                        warnings += constants.warnState1[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "  
            byte_index += 2

            warnState2 = ord(bytes.fromhex(inc_data[byte_index:byte_index+2].decode('ascii')))
            if warnState2 > 0:
                warnings += "Warning State 2: "
                for x in range(0,8):
                    if (warnState2 & (1<<x)):
                        warnings += constants.warnState2[x+1] + " | "
                warnings = warnings.rstrip("| ")
                warnings += ", "  
            byte_index += 2

            warnings = warnings.rstrip(", ")

            telemetry_module.set_telemetry("warning_string", warnings) # telemetry
            if warnings == "":
                inter_process_comm_module.set_bms_gui_data("warning_string", "       ") # instrumentation gui
            else:
                inter_process_comm_module.set_bms_gui_data("warning_string", "Warning") # instrumentation gui
            telemetry_module.set_telemetry("balancing_1", balanceState1) # telemetry
            telemetry_module.set_telemetry("balancing_2", balanceState1) # telemetry
            if debug_output > 0:
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", warnings: " + warnings)
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", balancing1: " + balanceState1)
                print("Pack " + str(p).zfill(config['zero_pad_number_packs']) + ", balancing2: " + balanceState2)

            warnings = ""

            #Test for non signed value (matching cell count), to skip possible INFOFLAG present in data
            if (byte_index < len(inc_data)) and (cellsW != int(inc_data[byte_index:byte_index+2],16)):
                byte_index += 2

    except Exception as e:
        print("Error parsing BMS warning data: ", str(e))
        return False, "Error parsing BMS warning data: " + str(e)

    return True,True

# message to console
# print BMS software version and serial number only once
print("Connecting to BMS...")
bms,bms_connected = bms_connect(config['bms_ip'],config['bms_port'])

success, data = bms_getVersion(bms)
if success != True:
    print("Error retrieving BMS version number")

time.sleep(0.1)
success, bms_sn,pack_sn = bms_getSerial(bms)

if success != True:
    print("Error retrieving BMS and pack serial numbers. Exiting...")
    quit()

# message to console
# print network attributes
attributes = server_module.get_network_attributes()

# connect to TB Server
server_module.TB_server_connect()

# Loop
try:
    while True:
        if bms_connected == True:
            ###############
            # data from BMS 
            success, data = bms_getAnalogData(bms,batNumber=255)
            if success != True:
                print("Error retrieving BMS analog data: " + data)
            time.sleep(scan_interval/3)
            success, data = bms_getPackCapacity(bms)
            if success != True:
                print("Error retrieving BMS pack capacity: " + data)
            time.sleep(scan_interval/3)
            success, data = bms_getWarnInfo(bms)
            if success != True:
                print("Error retrieving BMS warning info: " + data)
            ######################
            # speed and alive data
            speed_km_h = inter_process_comm_module.read_speed_km_h() # read speed_km_h
            telemetry_module.set_telemetry("speed_km_h", speed_km_h)
            alive = not alive # toggle alive variable
            telemetry_module.set_telemetry("alive", alive)
            ############################
            # send telemetry to TB Server
            server_module.client.send_telemetry(telemetry_module.telemetry)
            if debug_output2 > 1:
                print(telemetry_module.telemetry)
            time.sleep(scan_interval/3)
            ###########################
            # BMS GUI data
            inter_process_comm_module.write_bms_data()
            if debug_output2 > 0:
                print(inter_process_comm_module.bms_gui_data)
        else: #BMS not connected
            print("BMS disconnected, trying to reconnect...")
            bms,bms_connected = bms_connect(config['bms_ip'],config['bms_port'])
            time.sleep(5)
except KeyboardInterrupt:
    print("\nProgram terminated by user.")
    server_module.client.disconnect()
 
# end of program
print("END: " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

#
# Copyright (C) 2023 - Seyit Koyuncu
#
# GUI code for CanBee CanSat 2023 Ground Control System

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QFileDialog
import time

def create_xbee_device(port):
    try:
        device = XBeeDevice(port, 9600)
        device.open()
        print("xbee.is_open():", device.is_open())
        return device

    except Exception as e:
        print("Error in creating xbee object")
        print("Exception = ",e)

def send_command_with_xbee(device, device_to_send, data_to_send):
    device.send_data_async(device_to_send, data_to_send)
    print(f"{data_to_send} sended")

def send_sim_with_xbee(device, device_to_send, data_to_send):
    device.send_data_async(device_to_send, data_to_send)
    print(f"{data_to_send} sended")
    

def read_from_xbee(device, data): #read_from_xbee(device, container_data, payload_data,mqtt):
    xbee_message = device.read_data()
    if (xbee_message is not None): 
        data_xbee = xbee_message.data.decode("utf8").strip()

        if not (len(data) > 0):
            return 
        decode_csv(data_xbee, data)

def decode_csv(csv, data):
    data_list = csv.split(",")
    if not (len(data_list) > 0):
        return

    data_conversion = [
            "TEAM_ID", "MISSION_TIME", "PACKET_COUNT", "MODE","STATE",
            "ALTITUDE",
            "HS_DEPLOYED", "PC_DEPLOYED", "MAST_RAISED",
            "TEMPERATURE", "PRESSURE", "VOLTAGE",
            "GPS_TIME", "GPS_ALTITUDE", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_SATS",
            "TILT_X", "TILT_Y", "CMD_ECHO",
    ]
    
    if (len(data_list[2]) != 0):
        index = 0
        # Container data
        for key in data.keys():
            datum = data_list[index].strip()
            if key in data_conversion:
                if len(datum) > 0:
                    #son index 19 olcak cmd nin indexi
                    if index != 3 and index != 1 and index != 4 and index != 6 and index != 7 and index != 8 and index != 12 and index != 19:
                        datum = float(datum)
                else:
                    datum = 0
            data[key].append(datum)
            index += 1     
    else:
        print("Wrong Packet Type!!!")

# Sadece thread için
def read_from_xbee_loop(xbee, data): #(xbee, container_data, payload_data, mqtt):
    while True:
        read_from_xbee(xbee, data) #read_from_xbee(xbee, container_data, payload_data,mqtt)

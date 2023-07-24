#
# Copyright (C) 2023 - Seyit Koyuncu
#
# GUI code for CanBee CanSat 2023 Ground Control System

from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QDialog, QFileDialog, QTextEdit
from pyqtgraph import PlotWidget, plot
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from random import randint
import serial.tools.list_ports
import numpy as np
import sys
import os
import time
import random
import logging
import json
import threading
import xbee_handler
import csv

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('MainUI.ui', self)

        self.showMaximized()

        logo_pix = QtGui.QPixmap('canbeelogo.png')
        self.team_logo.setPixmap(logo_pix)

        self.xbee = None

        self.SIM_ON = False
        self.done = False

        self.data2023 = {
            "TEAM_ID": [],
            "MISSION_TIME": [],
            "PACKET_COUNT": [],
            "MODE": [],
            "STATE": [],
            "ALTITUDE": [],
            "HS_DEPLOYED": [],
            "PC_DEPLOYED": [],
            "MAST_RAISED": [],
            "TEMPERATURE": [],
            "PRESSURE": [],
            "VOLTAGE": [],
            "GPS_TIME": [],
            "GPS_ALTITUDE": [],
            "GPS_LATITUDE": [],
            "GPS_LONGITUDE": [],
            "GPS_SATS": [],
            "TILT_X": [],
            "TILT_Y": [],
            "CMD_ECHO": [],
        }

        self.x = list(range(20))  # 100 time points
        self.y = [randint(0,100) for _ in range(100)]  # 100 data points

        # set pen
        self.pen = pg.mkPen(color=((255, 211, 105)), width=1)
        styles = {'color':'#4DD599', 'font-family': "Chakra Petch Medium", 'font-size': '11px'}

        self.telemetry_box_count = 0

        #variables for graphing datas
        self.DATA_ALTITUDE = [0 for _ in range(20)]
        self.DATA_PRESSURE = [0 for _ in range(20)]
        self.DATA_TEMPERATURE = [0 for _ in range(20)]
        self.DATA_GPS_ALTITUDE = [0 for _ in range(20)]
        self.DATA_GPS_LATITUDE = [0 for _ in range(20)]
        self.DATA_GPS_LONGITUDE = [0 for _ in range(20)]
        self.DATA_GPS_SATS = [0 for _ in range(20)]
        self.DATA_VOLTAGE = [0 for _ in range(20)]
        self.DATA_TILT_X = [0 for _ in range(20)]
        self.DATA_TILT_Y = [0 for _ in range(20)]


        # plot widgets
        self.widget_ALTITUDE.setTitle("Altitude", color=((255, 211, 105)))
        self.widget_PRESSURE.setTitle("Pressure", color=((255, 211, 105)))
        self.widget_TEMPERATURE.setTitle("Temperature", color=((255, 211, 105)))
        self.widget_GPS_ALTITUDE.setTitle("GPS Altitude", color=((255, 211, 105)))
        self.widget_GPS_LATITUDE.setTitle("GPS Latitude", color=((255, 211, 105)))
        self.widget_GPS_LONGITUDE.setTitle("GPS Longitude", color=((255, 211, 105)))
        # self.widget_GPS_SATS.setTitle("GPS Sats", color=((255, 211, 105)))
        self.widget_TILT_X.setTitle("Tilt X", color=((255, 211, 105)))
        self.widget_TILT_Y.setTitle("Tilt Y", color=((255, 211, 105)))
        self.widget_VOLTAGE.setTitle("VOLTAGE", color=((255, 211, 105)))
        # battery voltage comes with voltage title by default

        self.widget_ALTITUDE.setBackground(("#393E46")) #meter
        self.widget_PRESSURE.setBackground(("#393E46")) #kilopascal
        self.widget_TEMPERATURE.setBackground(("#393E46")) #celcius
        self.widget_GPS_ALTITUDE.setBackground(("#393E46")) #meter
        self.widget_GPS_LATITUDE.setBackground(("#393E46")) #
        self.widget_GPS_LONGITUDE.setBackground(("#393E46")) #
        self.widget_TILT_X.setBackground(("#393E46")) #degree
        self.widget_TILT_Y.setBackground(("#393E46")) #degree
        self.widget_VOLTAGE.setBackground(("#393E46")) #volt

        #plot objects
        self.PLOT_ALTITUDE = self.widget_ALTITUDE.plot(self.x, self.DATA_ALTITUDE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_PRESSURE = self.widget_PRESSURE.plot(self.x, self.DATA_PRESSURE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_TEMPERATURE = self.widget_TEMPERATURE.plot(self.x, self.DATA_TEMPERATURE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_GPS_ALTITUDE = self.widget_GPS_ALTITUDE.plot(self.x, self.DATA_GPS_ALTITUDE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_GPS_LATITUDE = self.widget_GPS_LATITUDE.plot(self.x, self.DATA_GPS_LATITUDE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_GPS_LONGITUDE = self.widget_GPS_LONGITUDE.plot(self.x, self.DATA_GPS_LONGITUDE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        # self.PLOT_GPS_SATS = self.widget_GPS_SATS.plot(self.x, self.DATA_GPS_SATS, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_TILT_X = self.widget_TILT_X.plot(self.x, self.DATA_TILT_X, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_TILT_Y = self.widget_TILT_Y.plot(self.x, self.DATA_TILT_Y, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)
        self.PLOT_VOLTAGE = self.widget_VOLTAGE.plot(self.x, self.DATA_VOLTAGE, pen=self.pen, symbol='o', symbolSize=7, symbolPen=((238, 238, 238)), symbolBrush=((77, 213, 153)), skipFiniteCheck = True)



        # graph tuples
        self.plot_items = [
            (self.DATA_PRESSURE,                self.PLOT_PRESSURE,                 "PRESSURE"),
             (self.DATA_ALTITUDE,               self.PLOT_ALTITUDE,                 "ALTITUDE"),
             (self.DATA_TEMPERATURE,            self.PLOT_TEMPERATURE,              "TEMPERATURE"),
             (self.DATA_GPS_LATITUDE,           self.PLOT_GPS_LATITUDE,             "GPS_LATITUDE"),
             (self.DATA_GPS_LONGITUDE,          self.PLOT_GPS_LONGITUDE,            "GPS_LONGITUDE"),
             (self.DATA_GPS_ALTITUDE,           self.PLOT_GPS_ALTITUDE,             "GPS_ALTITUDE"),
             (self.DATA_TILT_X,                 self.PLOT_TILT_X,                   "TILT_X"),
             (self.DATA_TILT_Y,                 self.PLOT_TILT_Y,                   "TILT_Y"),
             (self.DATA_VOLTAGE,                self.PLOT_VOLTAGE,                  "VOLTAGE")
        ]


        self.timer = QtCore.QTimer()
        self.timer.setInterval(1) #give change of graph speed
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start() #TODO burayi bir kapattim yemezse data receiveddeki timeri kapatip bir dene o da olmazsa hepsini ac tekrardan

        self.sim_browse_button.clicked.connect(self.BrowseClicked)
        self.command_send_button.clicked.connect(self.SendButtonClicked)
        self.sim_data_label.setText('<sim data returns here>')
        #self.Sendsim_pathButton.clicked.connect(self.Sendsim_pathToUDP) #TODO Bu tuşa artık gerek yok gibi
        self.xbee_check_button.clicked.connect(self.CheckPorts)
        self.xbee_send_button.clicked.connect(self.SelectPort)
        self.sim_send_button.clicked.connect(self.send_sim_pressure_data)

        self.command_combo_box.addItems(["CMD,1008,CX,ON", "CMD,1008,CX,OFF",
                                         "CMD,1008,CAL", "CMD,1008,ST",
                                         "CMD,1008,LOCK", "CMD,1008,UNLOCK", 
                                         "CMD,1008,PRC90", "CMD,1008,PRC0",
                                         "CMD,1008,RHS", "CMD,1008,UHS", "CMD,1008,CHS",
                                         "CMD,1008,CF", "CMD,1008,RFS",
                                         "CMD,1008,CAM,ON", "CMD,1008,CAM,OFF",
                                         "CMD,1008,BUZ,ON", "CMD,1008,BUZ,OFF",
                                         "CMD,1008,SIM,ENABLE", "CMD,1008,SIM,ACTIVATE", "CMD,1008,SIM,DISABLE"])

        self.widget_ALTITUDE.setLimits(xMin=0, xMax=8000, yMin=-50, yMax=1000)
        self.widget_PRESSURE.setLimits(xMin=0, xMax=8000, yMin=700, yMax=1000)
        self.widget_TEMPERATURE.setLimits(xMin=0, xMax=8000, yMin=0, yMax=70)
        self.widget_GPS_ALTITUDE.setLimits(xMin=0, xMax=8000, yMin=-50, yMax=1000)
        self.widget_GPS_LATITUDE.setLimits(xMin=0, xMax=8000, yMin=-180, yMax=180)
        self.widget_GPS_LONGITUDE.setLimits(xMin=0, xMax=8000, yMin=-180, yMax=180)
        self.widget_TILT_X.setLimits(xMin=0, xMax=8000, yMin=-180, yMax=180)
        self.widget_TILT_Y.setLimits(xMin=0, xMax=8000, yMin=-180, yMax=180)
        self.widget_VOLTAGE.setLimits(xMin=0, xMax=8000, yMin=0, yMax=30)


        self.widget_ALTITUDE.plotItem.setRange(yRange=[-10, 1000])
        self.widget_PRESSURE.plotItem.setRange(yRange=[700, 1000])
        self.widget_TEMPERATURE.plotItem.setRange(yRange=[-10, 200])
        self.widget_GPS_ALTITUDE.plotItem.setRange(yRange=[-10, 1000])
        self.widget_GPS_LATITUDE.plotItem.setRange(yRange=[-180, 180])
        self.widget_GPS_LONGITUDE.plotItem.setRange(yRange=[-180, 10])
        self.widget_TILT_X.plotItem.setRange(yRange=[-180, 180])
        self.widget_TILT_Y.plotItem.setRange(yRange=[-180, 180])
        self.widget_VOLTAGE.plotItem.setRange(yRange=[0, 30])
        self.sim_path = " "
        self.count = 0
        self.last_command = " "
        self.previous_packet_count = -1
        self.previous_command = ""
        self.payload = None
        self.label_sim_mode.setText("SIM MODE: OFF")

        try:
            with open("Flight_1008.csv", 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.data2023.keys())  # Write the header row
                writer.writerows(zip(*self.data2023.values()))  # Write the data rows

        except Exception as e:
            print("Error while creating csv file for telemetries")
            print(e)
            

    def ChangeSIM(self):
        self.SIM_ON = not self.SIM_ON
        print("self.SIM_ON is", self.SIM_ON)

    def send_sim_pressure_data(self):
        thread_send_sim = threading.Thread(
            target = self.send_sim_pressure_data_thread,
            args = ()
        )
        thread_send_sim.start()

    def send_sim_pressure_data_thread(self):
        if self.payload == None: self.payload = RemoteXBeeDevice(self.xbee, XBee64BitAddress.from_hex_string("0013A200418DAC91"))

        try:    
            with open (self.sim_path) as f:
                while True:
                    line = f.readline()
                    if line:
                        chunks = (line.strip()).split(',')
                        command = chunks[2]
                        sim_data = chunks[3]
                        all_sim_command = command + sim_data
                        xbee_handler.send_sim_with_xbee(self.xbee, self.payload, all_sim_command)
                        time.sleep(1)
                        
                    else: 
                        break
        except Exception as e:
            print("Error while reading data from csv")
            print(e)


    def CheckPorts(self):
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            if ("PID=0403:6001" in hwid): # Xbee PID
                self.xbee_port_box.addItem(port)

    def BrowseClicked(self):
        try:
            file = QFileDialog.getOpenFileName(self,'Open file','D:')
            self.sim_path = file[0]
            self.sim_data_label.setText(os.path.basename(file[0]))
        except:
            pass

    def SelectPort(self):
        try:
            port = self.xbee_port_box.currentText()
            self.xbee = xbee_handler.create_xbee_device(port)

            print("xbee.is_open():", self.xbee.is_open())

            self.xbee_receive_thread = threading.Thread(
                target = xbee_handler.read_from_xbee_loop,
                args   = (self.xbee, self.data2023)#(self.xbee, self.data2023, self.payload_data, self.mqtt,)
            )

            self.xbee_receive_thread.start()
            self.timer.start()
        except:
            print("Error in selecting xbee port")

    def SendButtonClicked(self):
        try:
            data = self.command_combo_box.currentText()
            self.last_command = data

            #payload = RemoteXBeeDevice(XBee64BitAddress.from_hex_string("0013A20042073BF1"), XBee64BitAddress.from_hex_string("0013A200418DAC91"))
            if self.payload == None: self.payload = RemoteXBeeDevice(self.xbee, XBee64BitAddress.from_hex_string("0013A200418DAC91"))
            self.previous_command = self.last_command

            if(self.last_command == "CMD,1008,LOCK"):
                data = "CMD,1008,RLS0"
            elif(self.last_command == "CMD,1008,UNLOCK"):
                data = "CMD,1008,RLS90"

            xbee_handler.send_command_with_xbee(self.xbee, self.payload, data)

        except Exception as e:
            print("Error while trying to send data from ground to payload")
            print("Exception = ",e)

    def append_to_csv_file(self):
        try:
            last_telemetries_list = []
            with open("Flight_1008.csv", 'a', newline='') as file:
                writer = csv.writer(file)
                for telemetri_name , telemetri_value in self.data2023.items():
                    last_telemetries_list.append(telemetri_value[-1])

                writer.writerow(last_telemetries_list)
        except Exception as e:
            print("Exception when trying to append data to the csv file")
            print("Exception = ", e) 

    def update_plot_data(self):
        try:
            if(len(self.data2023['PACKET_COUNT']) > 1 and self.previous_packet_count != self.data2023['PACKET_COUNT'][-1]):
                if(self.data2023['CMD_ECHO'][-1] == "SimulationActivated" or self.data2023['CMD_ECHO'][-1] == "SimulatedPressureData"): self.label_sim_mode.setText("SIM MODE: ON") 
                else: self.label_sim_mode.setText("SIM MODE: OFF")

                self.append_to_csv_file()

                self.x = self.x[1:]  # Remove the first y element.
                self.x.append(self.x[-1] + 1)

                for(data, graph, name) in self.plot_items:
                    data.append(float(self.data2023[name][len(self.data2023[name]) - 1]))  # Add a new random value.
                    data.pop(0)
                    graph.setData(self.x, data)
                    #graph.setXRange(self.x[0], self.x[-1])


                for telemetri_name , telemetri_value in self.data2023.items():
                    if(telemetri_name == "TEAM_ID" or telemetri_name == "PACKET_COUNT"):
                        self.telemetry_console.insertPlainText(str(int(telemetri_value[len(telemetri_value) - 1])))
                        self.telemetry_console.insertPlainText(",")

                    else:
                        self.telemetry_console.insertPlainText(f"{telemetri_value[len(telemetri_value) - 1]},")
                    if self.telemetry_box_count == 15:
                        self.telemetry_box_count = 0
                        self.telemetry_console.clear()

                self.telemetry_box_count = self.telemetry_box_count + 1 
                self.telemetry_console.insertPlainText("\n")

                #acceleration labels
                '''
                self.label_acceleration_pitch.setText("Accel Pitch: " + str(self.data2023['ACCELP'][-1]))
                self.label_acceleration_yaw.setText("Accel Yaw: " + str(self.data2023['ACCELY'][-1]))
                self.label_acceleration_roll.setText("Accel Roll: " + str(self.data2023['ACCELR'][-1]))
                '''
                
                self.label_altitude.setText("Altitude: " + str(self.data2023['ALTITUDE'][-1]))
                self.label_state.setText("State: " + str(self.data2023['STATE'][-1]))
                self.label_last_command.setText("Last Command: " + self.last_command)

                self.label_packet_count.setText('Packet Count: ' + str(int(self.data2023['PACKET_COUNT'][-1])))
                self.label_GPS_SATS.setText('GPS Sats : ' + str(int(self.data2023['GPS_SATS'][-1])))

                self.altitude_last.setText(str(self.data2023['ALTITUDE'][-1]) + str("(m)"))
                self.latitude_last.setText(str(self.data2023['GPS_LATITUDE'][-1]) + str("(°)"))
                self.longitude_last.setText(str(self.data2023['GPS_LONGITUDE'][-1]) + str("(°)"))
                self.pressure_last.setText(str(self.data2023['PRESSURE'][-1]) + str("(kPa)"))
                self.GPS_altitude_last.setText(str(self.data2023['GPS_ALTITUDE'][-1]) + str("(m)"))
                self.temperature_last.setText(str(self.data2023['TEMPERATURE'][-1]) + str("(°C)"))
                self.tilt_x_last.setText(str(self.data2023['TILT_X'][-1]) + str("(°)"))
                self.tilt_y_last.setText(str(self.data2023['TILT_Y'][-1]) + str("(°)"))
                self.voltage_last.setText(str(self.data2023['VOLTAGE'][-1]) + str("(V)"))

                self.previous_packet_count = self.data2023['PACKET_COUNT'][-1]


        except Exception as e:
            print("Error while updating plots")
            print("Exception = ", e)




#def main():
app = QtWidgets.QApplication(sys.argv)
main = MainWindow()

main.show()
sys.exit(app.exec_())

#if __name__ == '__main__':
    #main()


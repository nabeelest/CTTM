import os, sys, csv, random
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QMessageBox,QGraphicsDropShadowEffect, QLineEdit
from PyQt5.QtGui import QPixmap, QImage, QIntValidator, QDoubleValidator, QIcon,QFont
from PyQt5.QtCore import Qt, QTimer, QSize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import serial.tools.list_ports
import serial 
from main3 import VirtualKeyboard
from PIL import Image, ImageOps
import cv2
import numpy as np
base_path = "."


# To run this app in PC environment without building exe, comment the lines below  
#base_path = sys._MEIPASS
# To build this code make sure all paths have "/" to change directory.



#==============COMMUNICATION PROTOCOLS==============
#--------------------AUTO PAGE----------------------
ON_PROCESS_PAGE="*3:5#"
RX_MODE="*PRS:"
TX_START="*1:1:{}:{}:{}:{}#"        #sent from pc
RX_START="*PRS:STR#"                #expected from machine
TX_PAUSE="*1:2:{}:{}:{}:{}#"        #send from pc
RX_PAUSE="*PRS:PUS#"                #expected from machine
TX_RESET="*1:3 :{}:{}:{}:{}#"       #sent from pc
RX_RESET="*PRS:HOM#"                #expected from machine
RX_READY="*PRS:RED#"                #expected from machine when ready
#----------------------VALUES----------------------
RX_TEMPERATURE="*TEP:xxx#"
RX_FORCE="*FRC:xxxxxx#"
#--------------------MANUAL PAGE-------------------
TX_MOTOR_FORWARD_START="*2:4:1:1#"
TX_MOTOR_FORWARD_STOP="*2:4:2:1#"
TX_MOTOR_BACKWARD_START="*2:4:1:2#"
TX_MOTOR_BACKWARD_STOP="*2:4:2:2#"
TX_VALVE1_OPEN="*2:5:2#"
TX_VALVE1_CLOSE="*2:5:1#"
TX_VALVE2_OPEN="*2:6:1#"
TX_VALVE2_CLOSE="*2:6:2#"
TX_HEATER_START="*2:7:1#"
TX_HEATER_STOP="*2:7:2#"
#=======================================================

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{base_path}/ui_cttm.ui', self)
 
 
        self.button_A.setIcon(QIcon(base_path+"/rsc/rsc3.png"))
        self.button_A.setIconSize(QSize(40, 40))
        font_52 = QFont('SF Pro Display', 52, QFont.Bold)
        font_27 = QFont('SF Pro Display', 27, QFont.Bold)
        font_19 = QFont('SF Pro Display', 19, QFont.Bold)
        font_12 = QFont('SF Pro Display', 12, QFont.Bold)
        
        
        self.keyboard = None
     
        for widget in self.findChildren(QWidget):
            widget.setFont(font_12)
            widget.setFocusPolicy(Qt.NoFocus)
            
        self.input_1.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        # self.input_1.focusInEvent = self.create_focus_in_handler(self.input_1.focusInEvent)
        # self.input_2.focusInEvent = self.create_focus_in_handler(self.input_2.focusInEvent)
        self.input_2.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_13.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_14.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_15.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_16.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_17.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.label_A.setFont(font_19)
        self.label_3.setFont(font_52)
        self.label_4.setFont(font_19)
        self.label_15.setFont(font_52)
        self.label_16.setFont(font_19)        
        self.label_37.setFont(font_27)
        self.label_41.setFont(font_27)
        self.label_47.setFont(font_27)
        self.label_46.setFont(font_27)
        self.mode = "READY"
        self.screen = 0
        self.int_validator = QIntValidator(self)
        self.process_config = []
        self.time_data = []
        self.force_data = []
        self.rx_temperature = 0
        self.rx_force = 0
        self.ser = None
        self.heater=False
        self.valve1=False
        self.valve2=False
        self.motor_left=False
        self.motor_right=False
        # self.disable_osk()

        self.camera = cv2.VideoCapture(0)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_cam)
        # self.timer.timeout.connect(self.display_cam2)
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.rx_data)
        
        self.button_1.clicked.connect(self.handle_verify_login)
        self.button_A.pressed.connect(self.handle_button_A_pressed)
        self.button_A.clicked.connect(self.handle_back_pressed)
        self.button_2.clicked.connect(lambda: self.handle_screen_change(4))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        self.button_20.clicked.connect(self.handle_create_config)
        self.button_5.clicked.connect(lambda: self.handle_screen_change(5))
        self.button_6.clicked.connect(self.populate_configlist)
        self.button_7.clicked.connect(self.start_process)
        self.button_8.clicked.connect(self.pause_process)
        self.button_9.clicked.connect(self.reset_process)
        self.button_10.clicked.connect(self.handle_delete_configuration)
        self.button_11.clicked.connect(self.handle_delete)
        self.button_12.clicked.connect(self.handle_manual)
        self.button_13.clicked.connect(self.handle_motor_left) # motor left
        #self.button_13.released.connect(self.motor_left_released) # motor left
        self.button_14.clicked.connect(self.handle_motor_right) # motor left
        #self.button_14.pressed.connect(self.motor_right_pressed)  # motor right
        #self.button_14.released.connect(self.motor_right_released)  # motor right
        self.button_15.clicked.connect(self.handle_heater)  # heater on/off
        self.button_16.clicked.connect(self.handle_valve_1)  # valve 1  on/off
        self.button_17.clicked.connect(self.handle_valve_2)  # valve 2  on/off  
        self.button_18.pressed.connect(self.handle_reset_pressed)  # valve 2  on/off  
        self.button_18.released.connect(self.handle_reset_released)  # valve 2  on/off  
        self.configlist.itemClicked.connect(self.load_config)
        self.input_14.setValidator(self.int_validator)
        self.input_15.setValidator(self.int_validator)
        self.input_16.setValidator(self.int_validator)
        self.input_17.setValidator(self.int_validator)
        self.showPopup2 = self.comboBox.showPopup 
        self.comboBox.showPopup= self.load_comlist
        self.load_comlist()
        self.comboBox.currentIndexChanged.connect(self.set_serial)
        self.handle_screen_change(1)
        #self.disable_osk()

    def disable_osk(self):
       #val=os.environ["QT_IM_MODULE"] #= "none"
       print("hello") 



    # def eventFilter(self, obj, event):
    #     self.enable_osk()
    #     return super().eventFilter(obj, event)

    # def enable_osk(self):
    #     os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"

    # def show_keyboard(self):
    #     subprocess.Popen(['osk'])  # For Windows, you can use 'osk'
    # # On Linux, you might use `onboard` or other keyboard apps

    # def hide_keyboard(self):
    #     subprocess.Popen(['taskkill', '/IM', 'osk.exe', '/F'])  # For Windows
    # # On Linux, you might need to kill the process using `pkill onboard`
    
    
    
 # virtual keboard
    
    def show_virtual_keyboard(self, input_field, event=None):
        print(f"Keyboard triggered for: {input_field.objectName()}")  # Debugging
        
        # Check if the current screen allows the virtual keyboard to be shown
        if self.screen not in [1, 3]:  # Only allow the keyboard on screen 1 and 3
            return

        if self.keyboard is None or not self.keyboard.isVisible():
            # If no keyboard is open, create a new one
            self.keyboard = VirtualKeyboard(input_field, self)
            self.keyboard.finished.connect(self.on_keyboard_closed)  # Reset the flag when the keyboard closes
            self.keyboard.show()
        else:
            # If a keyboard is already open, change the focused input field
            self.keyboard.input_field = input_field

    def on_keyboard_closed(self):
        # Safely reset the keyboard reference when it's closed
        self.keyboard = None
    

    def handle_screen_change(self, value):
        # Call close_keyboard to ensure the virtual keyboard is closed when switching screens
        self.close_keyboard()
        
        if value == 1:  # Login Screen
            self.screen = 1
            self.comboBox.hide()
            self.comboBox.setDisabled(True)
            self.button_A.hide()
            self.init_screen_1()
        elif value == 2:  # Menu Screen
            self.screen = 2
            self.comboBox.hide()
            self.button_A.show()
            self.init_screen_2()
        elif value == 3:  # Create Config Screen
            self.screen = 3
            self.comboBox.hide()
            self.init_screen_3()
        elif value == 4:  # Load Config Screen
            self.screen = 4
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_4(delete=False)
        elif value == 5:  # Process Screen
            self.screen = 5
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_5()
        elif value == 6:  # Manual Screen
            self.screen = 6
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_6()

    def close_keyboard(self):
        if self.keyboard is not None:
            self.keyboard.close()  # Close the keyboard if open
            self.keyboard = None
             



    def handle_button_A_pressed(self):
        self.button_A.setIconSize(QSize(36, 36))

    def init_screen_1(self):
        self.screen = 1
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_1.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap(base_path+"/rsc/rsc2.png"))
        self.label_6.hide()
        
         # Connect input_1 and input_2 to trigger virtual keyboard when clicked
        self.input_1.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_1, event)
        self.input_2.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_2, event)

    def handle_focus_event(self, event):
        self.show_virtual_keyboard(event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event
  
    def init_screen_2(self):
        self.screen = 2
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap())
        self.label_A.setText("Main Menu")
        self.screen_1.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()

        self.screen_2.show()
          
    def init_screen_3(self):
        self.screen = 3
        self.label_A.setText("Create Configuration")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_3.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_64.setStyleSheet("color:#FF0000;")
        self.label_64.setText("")
        self.input_13.clear()
        self.input_14.clear()
        self.input_15.clear()
        self.input_16.clear()
        self.input_17.clear()
        
        self.input_13.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_13, event)
        self.input_14.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_14, event)
        self.input_15.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_15, event)
        self.input_16.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_16, event)
        self.input_17.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_17, event)

    def handle_focus_event(self, event):
        self.show_virtual_keyboard(event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

    def init_screen_4(self,delete):
        self.screen = 4
        if(delete):
            self.label_A.setText("Delete Configuration")
            self.button_5.hide()
            self.button_12.hide()
            self.button_11.show()
            self.button_11.setEnabled(False)
        else:
            self.label_A.setText("Load Configuration")
            self.button_5.setEnabled(False)
            self.button_11.hide()
            self.button_12.show()
            self.button_5.show()

        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_4.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.configlist.hide()
        self.label_29.setText("")
        self.label_30.setText("")
        self.label_31.setText("")
        self.label_32.setText("")
        self.label_33.setText("")
        
        

    def init_screen_5(self):
        self.screen = 5
        
        self.label_A.setText("Auto Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_6.hide()
        self.screen_5.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        # shadow1=QGraphicsDropShadowEffect()
        # shadow1.setBlurRadius(30)
        # shadow1.setOffset(0,5)
        # self.button_7.setGraphicsEffect(shadow1)


    def init_screen_6(self):
        self.screen = 6
        self.label_A.setText("Manual Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.show()
        self.button_13.setStyleSheet('background-color:transparent;')
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))
        self.button_13.setIconSize(QSize(100, 100)) 
        self.button_14.setStyleSheet('background-color:transparent;')
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
        self.button_14.setIconSize(QSize(100, 100)) 
        self.button_15.setStyleSheet("background-color:transparent;")
        self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))
        self.button_15.setIconSize(QSize(100, 100)) 
        self.button_16.setStyleSheet("background-color:transparent;")
        self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
        self.button_16.setIconSize(QSize(100, 100)) 
        self.button_17.setStyleSheet("background-color:transparent;")
        self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
        self.button_17.setIconSize(QSize(100, 100))       
        self.button_18.setIcon(QIcon(base_path+"/rsc/cttm_reset.png"))
        self.button_18.setIconSize(QSize(100, 100)) 
        self.label_10.setText("Clamp 2 OFF")
        self.label_7.setText("Clamp 1 OFF")
        self.setStyleSheet("background-color:rgb(250,250,250);")
        print("screen 6")
        self.timer.start()
        self.timer2.start()
        self.heater=False
        self.valve1=False
        self.valve2=False

        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm Exit', 
                                    "Are you sure you want to exit?", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # # Unconditionally send the command to turn off the power supply
                # self.tx_data("OUTP:GEN OFF *IDN\n")
                # print("Power supply turned off before closing GUI")

                # # Send the command to the MCU to stop the process
                # self.tx_data("*1:0:0#", port='mcu')  # Send stop command to MCU
                # print("Stop protocol *1:0:0# sent to MCU")
                
                # Check if the virtual keyboard is open and close it
                if self.keyboard is not None and self.keyboard.isVisible():
                    self.keyboard.close()
                    print("Virtual keyboard closed")

            except Exception as e:
                print(f"Error turning off power supply or sending stop command to MCU: {e}")

            event.accept()  # Proceed with closing the window
        else:
            event.ignore()  # Ignore the close event and keep the window open
        
    def populate_configlist(self):
        if self.configlist.isVisible():
            self.configlist.hide()
        else:
            self.configlist.show()
            self.configlist.clear()
            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None) 
                    for row in reader:
                        if row: 
                            self.configlist.addItem(row[0])  
            list_height = (self.configlist.count()*42) + 2
            if(list_height>350): list_height = 350
            self.configlist.setFixedHeight(list_height)

    def load_config(self):
        selected_items_list = self.configlist.selectedItems()
        if selected_items_list:
            selected_item = selected_items_list[0].text()
            print(f"Selected item text: {selected_item}")

            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None)
                    for row in reader:
                        if row[0] == selected_item:
                            self.process_config = row
                            break
            print("Process Config:", self.process_config)
            self.label_29.setText(self.process_config[0])
            self.label_30.setText(self.process_config[1])
            self.label_31.setText(self.process_config[2])
            self.label_32.setText(self.process_config[3])
            self.label_33.setText(self.process_config[4])
            self.button_5.setEnabled(True)
            self.button_11.setEnabled(True)
            
    def handle_verify_login(self):
        if(self.input_1.text() == "admin" and self.input_2.text() == "admin"):
            self.role = "admin"
            self.button_3.show()
            self.button_10.show()   
            
            self.handle_screen_change(2)
            
        elif(self.input_1.text() == "operator" and self.input_2.text() == "operator"):
            self.role = "operator"
            self.button_3.hide()
            self.button_10.hide()
            
            self.handle_screen_change(2)
        else:
            self.label_6.show()
            self.label_6.setStyleSheet("color:rgb(255,0,0); background:white;")

    def handle_create_config(self):
        
        data = [
            self.input_13.text(),
            self.input_14.text(),
            self.input_15.text(),
            self.input_16.text(),
            self.input_17.text()
        ]

        if any(not field for field in data):
            self.label_64.setText("Error: All fields must be filled")
            self.label_64.setStyleSheet("color:#FF0000;")
            return
        else:
            file_exists = os.path.exists('ConfigFile.csv')
            
            if file_exists:
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None)
                    for row in reader:
                        if self.input_13.text() == row[0]:  # Check if input_3 text exists in the first column
                            self.label_64.setText("Error: Configuration Name already exists")
                            self.label_64.setStyleSheet("color:#FF0000;")
                            return
                        
            with open('ConfigFile.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['ConfigName', 'Linear Speed', 'Distance', 'Temperature', 'PeakForce'])  # Replace with appropriate header names
                writer.writerow(data)
                self.label_64.setText("Configuration has been saved successfully")
                self.label_64.setStyleSheet("color:#009900;")

    def handle_delete_configuration(self):
        self.init_screen_4(True)

    def handle_delete(self):
        reply=QMessageBox.question(self, 'Confirm', 'Are you sure you want to delete this?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
                with open('ConfigFile.csv', 'w', newline='') as file:
                    writer = csv.writer(file)
                    for row in rows:
                        if row[0] != self.process_config[0]:
                            print(self.process_config)
                            writer.writerow(row)
                            self.init_screen_2()
        else:
            print("Action canceled")

        print("delete pressed")

    def start_process(self):
        self.timer.start(1)
        if self.mode == "READY":
            if self.feed_graph.layout() is None:
                print("Creating new layout")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)
                self.feed_graph.setLayout(layout)

            self.ax.set(xlabel='time (s)', ylabel='force (g)')
            self.ax.grid()
            self.line, = self.ax.plot([], [], color=(0,0.5,0.5))
            self.canvas.draw() 
            self.t = 1
        #self.mode = "PROCESSING"
        cmd=TX_START.format(self.label_30.text().zfill(3),self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        #cmd = "*PS:"+ self.label_30.text().zfill(3) + ":" + self.label_31.text().zfill(3) +  ":" +self.label_32.text().zfill(3) +  ":" +self.label_33.text().zfill(3) + "#"
        print(cmd)
        self.tx_data(cmd)
        self.timer2.start()
         
    def pause_process(self):
        # self.timer.stop()
        #self.mode = "PAUSED"
        cmd = TX_PAUSE.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        #cmd = "*PP:000:000:000:000#"
        print(cmd)
        self.tx_data(cmd)

    def reset_process(self):
        self.timer.stop()
        self.ax.clear()
        self.canvas.draw()
        self.time_data = []
        self.force_data = []
        self.feed_cam.setPixmap(QPixmap())
        cmd =TX_RESET.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        print(cmd)
        self.tx_data(cmd)

    def display_cam(self):
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(frame.data, 640, 480, 1920, QImage.Format_RGB888)
            if self.screen == 5:
                self.feed_cam.setPixmap(QPixmap.fromImage(q_img))
            elif self.screen == 6:
                self.feed_cam_2.setPixmap(QPixmap.fromImage(q_img))
        else:
            self.feed_cam.setText("Failed to load Camera!")
            self.feed_cam_2.setText("Failed to load Camera!")

    def display_plot(self):
        self.t = self.t + 1
        self.label_36.setText(str(self.rx_force))
        self.label_37.setText(str(self.rx_temperature))
        self.time_data.append(self.t)
        self.force_data.append(self.rx_force)
        if len(self.time_data) > 25:
            t_data = self.time_data[-25:]
            f_data = self.force_data[-25:]        
            self.line.set_data(t_data, f_data)
        else:
            self.line.set_data(self.time_data, self.force_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        
    def handle_back_pressed(self):
        self.button_A.setIconSize(QSize(40, 40))
        self.label_9.setText("")
        if(self.screen > 1): 
            if (self.screen==6):
                self.screen=4
            elif (self.screen==4):
                self.screen=2
            else:
                self.screen = self.screen - 1
        print(self.screen)
        self.handle_screen_change(self.screen)
        self.heater=False
        self.valve1=False
        self.valve2=False

    def handle_app_quit(self):
        self.close()
     
    def rx_data(self):
        try:
            if self.ser and self.ser.in_waiting > 0:
                my_data = self.read_until_delimiter()
                print("Data received:", my_data)
                ## condition to check formating of data i.e. data[0]=='*'
                #if data is TEMP
                if my_data[1:5]==RX_TEMPERATURE[1:5]:
                    self.rx_temperature = int(my_data[5:len(my_data)-1])
                #if data is FORCE
                elif my_data[1:5]==RX_FORCE[1:5]:
                    self.rx_force=(int(my_data[5:len(my_data)-1]))/100
                #if data is MODE
                elif my_data[0:5]==RX_MODE:
                    if my_data==RX_READY:
                        self.mode="READY"
                    elif my_data==RX_START:
                        self.mode="PROCESSING"
                    elif my_data==RX_PAUSE:
                        self.mode="PAUSED"
                    elif my_data==RX_RESET:
                        self.mode="HOMING"
                self.label_38.setText(self.mode)
                self.label_37.setText(str(self.rx_temperature))
                self.label_47.setText(str(self.rx_temperature))
                self.label_41.setText(str(self.rx_force))
                self.label_46.setText(str(self.rx_force))


            self.handle_screen5()
        except serial.SerialException as e:
            print(f"SerialException: {e}")    
        # save function here

    def tx_data(self,data):
        try:
            self.ser.write(data.encode())
        except Exception as err:
             self.label_9.setText("ERROR: NO SERIAL PORT")
               
    def handle_screen5(self):
        if self.mode == "READY":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(False)
            self.button_9.setEnabled(False)
            self.button_A.setEnabled(True)
        elif self.mode == "PROCESSING":
            self.button_7.setEnabled(False)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(False)
            self.button_A.setEnabled(False)
            self.display_plot()
        elif self.mode == "PAUSED":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(False)
            self.button_9.setEnabled(True)
            self.button_A.setEnabled(False)
        elif self.mode == "HOMING":
            self.button_7.setEnabled(False)
            self.button_8.setEnabled(False)
            self.button_9.setEnabled(False)
            self.button_A.setEnabled(False)

    def load_comlist(self):
        self.comboBox.clear()
        com_ports_list = []
        com_ports = serial.tools.list_ports.comports()
        for port in com_ports:
            self.comboBox.addItem(f"{port.device}")
        self.showPopup2()

    def read_until_delimiter(self):
        data = bytearray()
        delimiter=b'#'
        while True:
            if self.ser.in_waiting > 0:  # Check if there's data waiting in the buffer
                byte = self.ser.read(1)  # Read one byte at a time
                data.extend(byte)
                if byte == delimiter:
                    break
        return data.decode('utf-8')

    def set_serial(self):
        if self.ser != None:
            self.ser.close() 
        if self.comboBox.currentIndex() > -1:
            comPort= self.comboBox.currentText()
            self.ser = serial.Serial(comPort, baudrate=115200, timeout=1)
            
    def handle_manual(self):
        print("on screen 6")
        self.init_screen_6()


    def handle_motor_left(self):
        print("handle motor left")
        self.motor_left=not self.motor_left
        if(self.motor_left):
            self.motor_left_pressed()
        else:
            self.motor_left_released()

    def motor_left_pressed(self):
        print("motor pressed")
        self.button_13.setStyleSheet('background-color:transparent;')
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left_pressed.png"))
        self.tx_data(TX_MOTOR_BACKWARD_START)

    def motor_left_released(self):
        print("motor released")
        self.button_13.setStyleSheet("background-color:transparent;")
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))

        self.tx_data(TX_MOTOR_BACKWARD_STOP)

    
    def handle_motor_right(self):
        print("handle motor right")
        self.motor_right=not self.motor_right
        if(self.motor_right):
            self.motor_right_pressed()
        else:
            self.motor_right_released()

    def motor_right_pressed(self):
        print("motor pressed")
        self.button_14.setStyleSheet("background-color:transparent;")
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right_pressed.png"))

        self.tx_data(TX_MOTOR_FORWARD_START)

    def motor_right_released(self):
        print("motor released")
        self.button_14.setStyleSheet("background-color:transparent;")
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
        self.tx_data(TX_MOTOR_FORWARD_STOP)

    def handle_heater(self):
        self.heater= not self.heater
        if(self.heater): 
            #heater on 
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater_pressed.png"))
            self.tx_data(TX_HEATER_START)
        else: 
            #heater off
            self.tx_data(TX_HEATER_STOP)
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))

        print("heater")

    def handle_valve_1(self):
        self.valve1 = not self.valve1
        if (self.valve1):
            #valve on
            print("value 1 ON") 
            self.label_7.setText("Clamp 1 ON")
            self.button_16.setStyleSheet("background-color:transparent;")
            self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))
            self.tx_data(TX_VALVE1_OPEN)
        else:
            # valve off
            print("value 1 OFF")
            self.label_7.setText("Clamp 1 OFF")
            self.button_16.setStyleSheet("background-color:transparent;")
            self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
            self.tx_data(TX_VALVE1_CLOSE)

    def handle_valve_2(self):
        print("hello from handle_valve_2")
        self.valve2 = not self.valve2
        if (self.valve2):
            #valve on
            print("value 2 ON")
            self.label_10.setText("Clamp 2 ON")
            self.button_17.setStyleSheet("background-color:transparent;")
            self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))
            self.tx_data(TX_VALVE1_OPEN)
        else:
            # valve off
            print("value 2 OFF")
            self.label_10.setText("Clamp 2 OFF")
            self.button_17.setStyleSheet("background-color:transparent;")
            self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))

            self.tx_data(TX_VALVE2_CLOSE)
    
    def handle_reset_pressed(self):
        print("pressed")
        self.button_18.setIcon(QIcon(base_path+"/rsc/cttm_reset_pressed.png"))
        cmd =TX_RESET.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        print(cmd)
        self.tx_data(cmd)

    def handle_reset_released(self):
        print("released")
        self.button_18.setIcon(QIcon(base_path+"/rsc/cttm_reset.png"))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    # window.showFullScreen()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
import os
import time

from PyQt6 import QtCore, QtWidgets, uic
import pyqtgraph as pg
from time import perf_counter
from instruments.KDC101.KDC101Controller import KDC101_Rotation
import numpy as np
from instruments.Lockin.SRS865A import LockInAmplifier


class StepAcquisitionThread(QtCore.QThread):
    #angle = QtCore.pyqtSignal(float, float)  # Signal to send angle updates to the UI
    angle_R = QtCore.pyqtSignal(float, float, float)  # Signal to send lockin updates to the UI
    finished = QtCore.pyqtSignal()
    def __init__(self, Rmount1, lockin1, start_angle, stop_angle, step_angle):
        super(StepAcquisitionThread, self).__init__()
        self.is_running = True
        self.Rmount1 = Rmount1
        self.lockin1 = lockin1
        self.start_angle = start_angle
        self.stop_angle =  stop_angle
        self.step_angle = step_angle
        self.data = []


    def run(self):

        try:
            sweep_steps = np.arange(self.start_angle,self.stop_angle,self.step_angle)
            self.Rmount1.move_absolute(self.start_angle)
            for step in sweep_steps:
                self.Rmount1.move_relative(self.step_angle)
                #RA = self.lockin1.get_channel_data('IN1')
                #RB = self.lockin1.get_channel_data('IN2')
                RA = 1
                RB = 1
                self.data.append((step, RA,RB))
                self.angle_R.emit(step,RA,RB) 
            self.finished.emit()
        except Exception as e:
            print(f"Error: {e}")
            print('Specify start, stop and step')

    def stop(self):
        self.running = False

# class ContiniousAcquisitionThread(QtCore.QThread):
#     angle_R = QtCore.pyqtSignal(float, float)  # Signal to send lockin updates to the UI

#     def __init__(self, Rmount1, start_angle, stop_angle):
#         super(StepAcquisitionThread, self).__init__()
#         self.is_running = True
#         self.Rmount1 = Rmount1
#         self.start = start_angle
#         self.stop =  stop_angle
#         self.data = []

#     def run(self):
#         try:
#             sweep_steps = np.arange(self.start,self.stop,self.step)
#             self.Rmount.move_absolute(self.start)
#             for step in sweep_steps:
#                 self.Rmount.move_relative(self.step)
#                 R = 1
#                 self.data.append((step, R))
#                 self.angle_R.emit(step,R) 
#             self.finished.emit()
#         except Exception as e:
#             print(f"Error: {e}")
#             print('Specify stop and step')

#     def stop(self):
#         self.running = False


    
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Load UI file
        self.ui = uic.loadUi('interface.ui', self)
        
        # Initialize connection state
        self.connection = None
        self.MainThread = None
        self.Rmount = None 
        self.lockin = None
        self.is_jogmode =False
        self.data = []

        self.R_curve = self.ui.LockInAngleGraph.plot(pen='r') 
        self.ui.LockInAngleGraph.setBackground("w")
        self.ui.LockInAngleGraph.getPlotItem().setLabel('bottom', 'Angle (\u00b0)')
        self.ui.LockInAngleGraph.getPlotItem().setLabel('left', 'Reflectivity')
       
       
        # Connect buttons to functions
        
        self.ui.ConnectBT.clicked.connect(self.connect_Rmount)
        self.ui.DisconnectBT.clicked.connect(self.disconnect_Rmount)
        self.ui.ConnectLockinBT.clicked.connect(self.connect_Lockin)
        self.ui.HomeBT.clicked.connect(self.Home)
        self.ui.ForwardBT.clicked.connect(self.go_forward)
        self.ui.BackwardBT.clicked.connect(self.go_backward)
        self.ui.GoBT.clicked.connect(self.sweep)
        self.ui.SaveBT.clicked.connect(self.save_data)


        self.ui.AngleDial.valueChanged.connect(self.value_changed)
        self.ui.AngleDial.sliderMoved.connect(self.slider_position)
        self.ui.AngleDial.sliderPressed.connect(self.slider_pressed)
        self.ui.AngleDial.sliderReleased.connect(self.slider_released)

        


    def value_changed(self, i):
        print(i)

    def slider_position(self, p):
        print("position", p)

    def slider_pressed(self):
        print("Pressed!")

    def slider_released(self):
        print("Released")

    def connect_Rmount(self):
        self.ui.ConnectBT.setEnabled(False)
        try:
            # Establish connection
            self.Rmount = KDC101_Rotation("27257179")
            self.Rmount.connect()
            
            #Start thread
            #self.MainThread = MainThread(self.connection, self.start_time)
            self.ui.AngleTx.setText(f"{self.Rmount.position} \u00b0")
            self.ui.MessageTx.setText(f"Mount connected succesfully.")
            self.connection = True

        except Exception as e:
            print(f"Error: {e}")
            self.ui.MessageTx.setText(f"Could not connect: {e}")
        
    def connect_Lockin(self):
        self.lockin = LockInAmplifier(inifile="lockin_params.ini")
        self.lockin.open_instrument(instrument_address='USB0::0xB506::0x2000::005180::INSTR')
        self.lockin.initialize_lockin()
        self.ui.MessageTx.setText(f"Lock-in connected succesfully.")


    def go_forward(self):
        self.set_jogmode()
        self.Rmount.move_jog(2)
        self.ui.AngleTx.setText(f"{self.Rmount.position} \u00b0")

    def go_backward(self):
        self.set_jogmode()
        self.Rmount.move_jog(1)
        self.ui.AngleTx.setText(f"{self.Rmount.position} \u00b0")

    # def on_move_complete(self):
    #     self.move_thread = None
    #     self.is_moving =False
    #     print("Movement completed!")
    #     # Update the UI with the new position, for example
    #     # self.ui.AngleTx.setText(f"{self.Rmount.get_position()} \u00b0")

    def set_jogmode(self):
        if self.is_jogmode is False:
            self.Rmount.set_jog_mode()
            self.is_jogmode =True
 

    def Home(self):
        try:
            self.Rmount.home()
            self.Rmount.set_motor_params()
            self.ui.MessageTx.setText(f"Device homed.")
        except Exception as e:
            print(e)
            self.ui.MessageTx.setText(f"Error homing device: {e}")

    def sweep(self):
        start = float(self.StartTX.toPlainText())
        stop = float(self.StopTX.toPlainText())
        step = float(self.StepTX.toPlainText())
        
        #self.Rmount.move_absolute(10)
        #self.Rmount.move_absolute(float(10))
        # print(self.Rmount.position)
        # try:
        #     sweep_steps = np.arange(start,stop,step)
        #     self.Rmount.move_absolute(start)
        #     self.ui.AngleTx.setText(f"{self.Rmount.position} \u00b0")
        #     for i in range(len(sweep_steps)):
        #         print(step)
        #         self.Rmount.move_relative(step)
        #         print(self.Rmount.position)
        #         self.R_curve.setData(sweep_steps, [1]*len(sweep_steps))   
        # except Exception as e:
        #     print(f"Error: {e}")
        #     print('Specify stop and step')
        self.ui.MessageTx.setText(f"Starting experiment")
        self.acquisition_thread = StepAcquisitionThread(self.Rmount, self.lockin,  start, stop, step)
        self.acquisition_thread.angle_R.connect(self.update_plot)
        self.acquisition_thread.finished.connect(lambda: print("Experiment Finished"))
        
        self.acquisition_thread.start()

    def update_plot(self, angle, RA,RB):
        self.data.append((angle, RA, RB))
        self.ui.LockInAngleGraph.plot([angle], [RA], pen=None, symbol='o', symbolBrush='r')
        self.ui.LockInAngleGraph.plot([angle], [RB], pen=None, symbol='x', symbolBrush='k')

    def save_data(self):
        if self.data:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data", "", "Text Files (*.txt)")
            if file_path:
                with open(file_path, 'w') as f:
                    f.write("# Angle (degrees)\tPhotodiode A\tPhotodiode B\n")
                    for angle, pd1, pd2 in self.data:
                        f.write(f"{angle}\t{pd1}\t{pd2}\n")
                print("Data saved successfully.")


    def disconnect_Rmount(self):
        self.ui.DisconnectBT.setEnabled(False)
        QtWidgets.QApplication.processEvents()
        if self.MainThread is not None:
            self.MainThread.stop()

        if self.connection is not None:
            self.Rmount.disconnect()

        # **Stop the status update timer**
        self.ui.ConnectBT.setEnabled(True)
        self.ui.DisconnectBT.setEnabled(True)
        self.ui.MessageTx.setText(f"Device disconnected.")


      



        

        


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    #Rmount = KDC101_Rotation("27257179")

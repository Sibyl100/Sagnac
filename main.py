import os
import time

from PyQt6 import QtCore, QtWidgets, uic
import pyqtgraph as pg
from time import perf_counter
from KDC101Controller import KDC101_Rotation


class MainThread(QtCore.QThread):
    angle = QtCore.pyqtSignal(float, float)  # Signal to send temperature updates to the UI
    lockin_signal = QtCore.pyqtSignal(float, float)  # Signal to send pressure updates to the UI

    def __init__(self, connection,start_time, parent=None):
        super(MainThread, self).__init__(parent)
        self.connection = connection
        self.start_time = start_time
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                print()
            except Exception as e:
                print(f"Error in TemperatureThread: {e}")
                self.is_running = False

    def stop(self):
        self.is_running = False
        self.wait()  # Ensure the thread finishes cleanly

class MovementThread(QtCore.QThread):
    move_complete = QtCore.pyqtSignal()  # Signal to notify when the move is complete

    def __init__(self, direction, Rmount):
        super().__init__()
        self.direction = direction
        self.Rmount = Rmount

    def run(self):
        try:
            # Perform the move
            if self.direction == 'forward':
                self.Rmount.move_jog(2)
            elif self.direction == 'backward':
                self.Rmount.move_jog(1)

            # Once the movement is complete, emit the signal to update the UI
            self.move_complete.emit()
        except Exception as e:
            print(f"Movement failed: {e}")
            

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Load UI file
        self.ui = uic.loadUi('interface.ui', self)

        # Initialize connection state
        self.connection = None
        self.temp_thread = None
        self.start_time = None
        self.start_capture = False
        self.MainThread = None
        self.Rmount = None 
        self.lockin_data =[]
        self.angle_data = []
        
        
        #self.R_curve = self.ui.LockInAngleGraph.plot(pen='r') 
        #self.ui.LockInAngleGraph.getPlotItem().setLabel('bottom', 'Angle (\u00b0)')
        #self.ui.LockInAngleGraph.getPlotItem().setLabel('left', 'Reflectivity')
       
       
        # Connect buttons to functions
        
        self.ui.ConnectBT.clicked.connect(self.connect_Rmount)
        self.ui.DisconnectBT.clicked.connect(self.disconnect_Rmount)
        self.ui.HomeBT.clicked.connect(self.Home)
        self.ui.ForwardBT.clicked.connect(self.go_forward)
        self.ui.BackwardBT.clicked.connect(self.go_backward)

        self.ui.AngleDial.valueChanged.connect(self.value_changed)
        self.ui.AngleDial.sliderMoved.connect(self.slider_position)
        self.ui.AngleDial.sliderPressed.connect(self.slider_pressed)
        self.ui.AngleDial.sliderReleased.connect(self.slider_released)
        #self.ui.BackwardBT.valueChanged.connect(self.go_backward)
        

        # Initialize QTimer for status update
        self.status_timer = QtCore.QTimer(self)
        #self.status_timer.timeout.connect(self.print_device_status)  # Call the function at intervals
  

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
        QtWidgets.QApplication.processEvents()
        try:
            # Establish connection
            self.Rmount = KDC101_Rotation("27257212")
            self.Rmount.connect()
            
            # Record the start time
            self.start_time = perf_counter()
            
            #Start thread
            self.MainThread = MainThread(self.connection, self.start_time)
            self.ui.AngleTx.setText(f"{self.Rmount.get_position()} \u00b0")
            self.connection = True

        except Exception as e:
            print(f"Error: {e}")
    

    #def go_forward(self):
        #QtWidgets.QApplication.processEvents()
    #     self.Rmount.move_jog(2)

    # def go_backward(self):
    #     #QtWidgets.QApplication.processEvents()
    #     self.Rmount.move_jog(1)


    def go_forward(self):
        if hasattr(self, 'movement_thread') and self.movement_thread.isRunning():
            return  # Don't start a new move if one is already running

        self.movement_thread = MovementThread('forward', self.Rmount)
        self.movement_thread.move_complete.connect(self.on_move_complete)
        self.movement_thread.start()

    def go_backward(self):
        if hasattr(self, 'movement_thread') and self.movement_thread.isRunning():
            return  # Don't start a new move if one is already running

        self.movement_thread = MovementThread('backward', self.Rmount)
        self.movement_thread.move_complete.connect(self.on_move_complete)
        self.movement_thread.start()

    def on_move_complete(self):
        print("Movement completed!")
        # Update the UI with the new position, for example
        self.ui.AngleTx.setText(f"{self.Rmount.get_position()} \u00b0")

    def Home(self):
        self.ui.HomeBT.setEnabled(False)
        QtWidgets.QApplication.processEvents()
        try:
            self.Rmount.home()
            self.ui.HomeBT.setEnabled(True)
        except:
            self.ui.HomeBT.setEnabled(True)
            print('Error homing device.')
        

    def disconnect_Rmount(self):
        self.ui.DisconnectBT.setEnabled(False)
        QtWidgets.QApplication.processEvents()
        if self.MainThread is not None:
            self.MainThread.stop()

        if self.connection is not None:
            self.Rmount.disconnect()

        # **Stop the status update timer**
        self.status_timer.stop()
        self.ui.ConnectBT.setEnabled(True)
        self.ui.DisconnectBT.setEnabled(True)



      



        

        


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


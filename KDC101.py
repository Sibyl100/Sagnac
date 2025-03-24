
import time
from serial.tools import list_ports
import clr
import re 

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.DCServoCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.KCube.DCServoCLI import *
from System import Decimal

import time
from decimal import Decimal

class DeviceController:
    def __init__(self, serial_no):
        """Initialize the device controller with a serial number."""
        self.serial_no = serial_no
        self.device = None
        self.device_info = None

    def connect(self):
        """Build the device list."""
        DeviceManagerCLI.BuildDeviceList()
        self.device = KCubeDCServo.CreateKCubeDCServo(self.serial_no)
        self.device.Connect(self.serial_no)
        time.sleep(0.25)
        self.device.StartPolling(250)
        time.sleep(0.25)  # Allow settings to be sent

        self.device.EnableDevice()
        time.sleep(0.25)  # Wait for device to enable
      
        self.device_info = self.device.GetDeviceInfo()
        print('Device description:',self.device_info.Description)

        if not self.device.IsSettingsInitialized():
            print('Initializing settings')
            self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert self.device.IsSettingsInitialized() is True

        m_config = self.device.LoadMotorConfiguration(self.serial_no,
                                                          DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)
        print(m_config)
        m_config.DeviceSettingsName = "PRMTZ8"
        m_config.UpdateCurrentConfiguration()
        print(m_config)
        self.device.SetSettings(self.device.MotorDeviceSettings, True, False)

    def home_device(self):
        """Home the device."""
        try:
            print("Homing Actuator")
            self.device.Home(60000)  # 10s timeout, blocking call
        except Exception as e:
            print(f"Error homing device: {e}")

    def move_device(self, position):
        """Move the device to a specified position."""
        try:

            d = Decimal(float(position))
            print(f'Moving to position {position}')
            print(self.device)
            self.device.MoveTo(d, 20000)  # 10s timeout again
            time.sleep(1)

            print(f'Device now at position {self.device.Position}')
            time.sleep(1)
        except Exception as e:
            print(f"Error moving device: {e}")

    def disconnect_device(self):
        """Disconnect the device."""
        try:
            self.device.Disconnect()
            print("disconnected")
        except Exception as e:
            print(f"Error disconnecting device: {e}")




# Example usage
if __name__ == "__main__":
    serial_no = "27257212"
    device_controller = DeviceController(serial_no)
    device_controller.connect()
    device_controller.home_device()
    time.sleep(2)
    
    device_controller.move_device(5)
    device_controller.disconnect_device()
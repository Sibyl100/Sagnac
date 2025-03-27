import time
import os
import sys
from ctypes import *

class KDC101_Rotation:
    def __init__(self, serial_num: str):
        """
        Initialize the KDC101 controller with the given serial number.
        :param serial_num: The serial number of the KDC101 device.
        """
        self.serial_num = c_char_p(serial_num.encode('utf-8'))
        
        if sys.version_info < (3, 8):
            os.chdir(r"C:\\Program Files\\Thorlabs\\Kinesis")
        else:
            os.add_dll_directory(r"C:\\Program Files\\Thorlabs\\Kinesis")
        
        self.lib = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")

    def build_device_list(self):
        if self.lib.TLI_BuildDeviceList() == 0:
            device_list_size = self.lib.TLI_GetDeviceListSize()
            serial_numbers = create_string_buffer(100)
            self.lib.TLI_GetDeviceListByTypeExt(serial_numbers, 100, 27)
            serial_list = serial_numbers.value.decode().split(",")
            if self.serial_num.value.decode() in serial_list:
                print(f"Device {self.serial_num.value.decode()} found.")
            else:
                print(f"Device {self.serial_num.value.decode()} not found.")
                raise ConnectionError("Device not found.")
        else:
            raise ConnectionError("Failed to build device list.")


    def connect(self):
        """
        Connect to the KDC101 device.
        """
        self.build_device_list()
        self.lib.CC_Open(self.serial_num)
        self.lib.CC_StartPolling(self.serial_num, c_int(200))
        print("Device connected.")
    
    def wait_for_message(self, expected_id):
        msg_type, msg_id, msg_data = c_ushort(), c_ushort(), c_ulong()
        while True:
            self.lib.CC_WaitForMessage(self.serial_num, byref(msg_type), byref(msg_id), byref(msg_data))
            
            if msg_type.value == 2 and msg_id.value == expected_id:
                break


    def clear_message_queue(self):
        self.lib.CC_ClearMessageQueue(self.serial_num)
    
    def home(self):
        """
        Home the device.
        """
        time.sleep(0.25)
        self.clear_message_queue()
        self.lib.CC_Home(self.serial_num)
        self.wait_for_message(expected_id=0)
        print("Device homed.")
    
    def set_motor_params(self, steps_per_rev=1919.64186, gbox_ratio=1.0, pitch=1.0):
        """
        Set motor parameters for real-to-device unit conversion.
        """
        self.lib.CC_SetMotorParamsExt(self.serial_num, c_double(steps_per_rev), c_double(gbox_ratio), c_double(pitch))
        print("Motor parameters set.")
    
    
    
    def move_absolute(self, target_position):
        """
        Move the device to an absolute position.
        :param target_position: The target position in real units (\u00b0).
        """
        time.sleep(0.25)
        self.clear_message_queue()

        new_pos_real = c_double(target_position)
        new_pos_dev = c_int()
        self.lib.CC_GetDeviceUnitFromRealValue(self.serial_num, new_pos_real, byref(new_pos_dev), 0)
        
        self.lib.CC_SetMoveAbsolutePosition(self.serial_num, new_pos_dev)
        time.sleep(0.25)
        self.lib.CC_MoveAbsolute(self.serial_num)
        print(f"Moving to {target_position} \u00b0.")
        self.wait_for_message(expected_id=1)

    def move_relative(self, displacement):
        """
        Move relative to previous position in real units.
        """
        disp_real = c_double(displacement)
        disp_dev = c_int()
        self.lib.CC_GetDeviceUnitFromRealValue(self.serial_num, disp_real, byref(disp_dev), 0)
        
        self.lib.CC_MoveRelative(self.serial_num, disp_dev)
        print(f"Moving relatively by {displacement}\u00b0.")
        self.wait_for_message(expected_id=1)
        #print("Current position: {} \u00b0".format(self.position))

    def set_jog_mode(self):
        self.lib.CC_SetJogMode(self.serial_num, c_short(2), c_short(1))
        v_real = c_int(15)
        v_dev_u = c_int()
        self.lib.CC_GetDeviceUnitFromRealValue(self.serial_num, v_real, byref(v_dev_u), 0)
        
        self.lib.CC_SetJogVelParams(self.serial_num,v_dev_u,v_dev_u)
        self.set_jog_step_size(3)

    def move_jog(self, direction):
        """
        Move jogging, 2 for going forward and 1 for going backwards. 
        """
        #self.lib.CC_SetJogMode(self.serial_num, c_short(2), c_short(1))

        #self.lib.CC_GetJogMode(self.serial_num,c_short(2),c_short(1) )
        if direction not in [1, 2]:
            raise ValueError("Invalid jog direction. Use 2 for forwards or 1 for backwards.")
        
        self.lib.CC_MoveJog(self.serial_num, c_short( direction))
        #sts =self.wait_for_message(1)
        #print(sts)
        print(f"Jogging in direction: {'Backwards' if direction == 1 else 'Forward'}.")

    def set_jog_step_size(self, step_size):
        new_jog_step_real = c_double(step_size)
        new_jog_step_dev = c_uint()
        self.lib.CC_GetDeviceUnitFromRealValue(self.serial_num, new_jog_step_real, byref(new_jog_step_dev), 0)
        self.lib.CC_SetJogStepSize(self.serial_num, new_jog_step_dev)
        print(f"Jog step size set to {step_size}\u00b0.")


    def get_velocity(self):
        velocity_dev, acceleration_dev = c_int32(), c_int32()
        self.lib.CC_GetVelParams(self.serial_num, byref(acceleration_dev), byref(velocity_dev))
        velocity_real, acceleration_real = c_int(), c_int()
        self.lib.CC_GetRealValueFromDeviceUnit(self.serial_num,velocity_dev, velocity_real, c_int(1))
        print(f"Current velocity: {velocity_real.value}\u00b0/s")
        return velocity_real.value
    
    
    def set_velocity(self, velocity):
        time.sleep(0.25)
        self.clear_message_queue()
        if velocity > 0:
            current_velocity, current_acceleration = c_int(), c_int()
            self.lib.CC_GetVelParams(self.serial_num, byref(current_acceleration), byref(current_velocity))
            self.lib.CC_SetVelParams(self.serial_num, current_acceleration, c_int(velocity))
            print(f"Velocity set to {velocity}.")

    def polling(self,rate):
        """
        Starts the internal polling loop which continuously requests position and status.
        Specify polling rate in milliseconds. 
        """

        self.lib.CC_StartPolling(self.serial_num, c_int(rate))
    
    def disconnect(self):
        """
        Disconnect the device.
        """
        self.lib.CC_StopPolling(self.serial_num)
        self.lib.CC_Close(self.serial_num)
        print("Device disconnected.")

    @property
    def position(self):
        """
        Get the current position of the device in real units.
        """
        self.lib.CC_RequestPosition(self.serial_num)
        
        dev_pos = c_int(self.lib.CC_GetPosition(self.serial_num))

        real_pos = c_double()
        self.lib.CC_GetRealValueFromDeviceUnit(self.serial_num, dev_pos, byref(real_pos), 0)
        return real_pos.value
    
    
if __name__ == "__main__":

    controller = KDC101_Rotation("27257179")
    controller.connect()
    controller.home()
    controller.set_motor_params()
    controller.position
    controller.get_velocity()
    controller.move_absolute(5.0)

    
    #controller.disconnect()


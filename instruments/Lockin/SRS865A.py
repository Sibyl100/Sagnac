#By Sandeep Feb 2024
# import visa
import pyvisa
import configparser
import numpy as np
import time
import math
from struct import unpack_from
config = configparser.ConfigParser()

class LockInAmplifier:
    time_constant_dict = {'1 us': 0, '3 us': 1, '10 us': 2, '30 us': 3, '100 us': 4, '300 us': 5,
                          '1 ms': 6, '3 ms': 7, '10 ms': 8, '30 ms': 9, '100 ms': 10, '300 ms': 11,
                          '1 s': 12, '3 s': 13, '10 s': 14, '30 s': 15, '100 s': 16, '300 s': 17,
                          '1 ks': 18, '3 ks': 19, '10 ks': 20, '30 ks': 21
                          }
    
    sensitivity_dict = {
        "1 V": 0,"500 mV": 1,"200 mV": 2,"100 mV": 3,"50 mV": 4,"20 mV": 5,"10 mV": 6,"5 mV": 7,"2 mV": 8,"1 mV": 9,
        "500 uV": 10,"200 uV": 11,"100 uV": 12,"50 uV": 13,"20 uV": 14,"10 uV": 15,"5 uV": 16,"2 uV": 17,"1 uV": 18,
        "500 nV": 19,"200 nV": 20,"100 nV": 21,"50 nV": 22,"20 nV": 23,"10 nV": 24,"5 nV": 25,"2 nV": 26,"1 nV": 27
        }
    input_range_dict ={'1 V':0, '300 mV':1, '100 mV':2, '30 mV':3 ,'10 mV':4}

    filter_dict ={'6 dB':0, '12 dB':1, '18 dB':2, '24 dB':3}


    def __init__(self, inifile):
        self.config = configparser.ConfigParser()
        self.config.read(inifile)
    def open_instrument(self, instrument_address):
        self.inst = pyvisa.ResourceManager().open_resource(instrument_address)

    def close_instrument(self):
        if self.inst:
            self.inst.close()
            self.inst = None
    def timeout(self, ms=1000):
        self.inst.timeout = int(ms)

    def get_timeconstant(self):
        return list(self.time_constant_dict.keys())[int(self.inst.query("OFLT?"))]

    def set_timeconstant(self, value, unit):
        index = self.time_constant_dict.get(f"{value} {unit}")
        if index is not None:
            self.inst.write(f"OFLT {index}")
            return f"time constant set to {self.get_timeconstant()}"
        else:
            return "Invalid time constant value or unit"
    def get_sensitivity(self):
        return list(self.sensitivity_dict.keys())[int(self.inst.query('SCAL?'))]
    
    def set_sensitivity(self, value, unit):
        index = self.sensitivity_dict.get(f"{value} {unit}")
        if index is not None:
            self.inst.write(f"SCAL {index}")
            return f"sensitivity set to {self.get_sensitivity()}"
        else:
            return "Invalid sensitivity value or unit"
    def get_inputrange(self):
        return list(self.input_range_dict.keys())[int(self.inst.query('IRNG?'))]
    
    def set_inputrange(self, value, unit):
        index = self.input_range_dict.get(f"{value} {unit}")
        if index is not None:
            self.inst.write(f"IRNG {index}")
            return f"inputrange set to {self.get_inputrange()}"
        else:
            return "Invalid inputrange value or unit"
    def get_filterslope(self):
        return list(self.filter_dict.keys())[int(self.inst.query('OFSL?'))]
    
    def set_filterslope(self, value, unit='dB'):
        index = self.filter_dict.get(f"{value} {unit}")
        if index is not None:
            self.inst.write(f"OFSL {index}")
            return f"filter slope set to {self.get_filterslope()}"
        else:
            return "Invalid filter value"
    def get_sync_filter(self):
        return ['OFF', 'ON'][int(self.inst.query("SYNC?"))]
    def set_sync_filter(self, value ='OFF'):
        self.inst.write(f"SYNC {value}")
    def get_input_channel(self):
        return ['A', 'A-B'][int(self.inst.query("ISRC?"))]
    def set_input_channel(self, value ='A'):
        self.inst.write(f"ISRC {value}")
    def get_coupling(self):
        return ['AC', 'DC'][int(self.inst.query("ICPL?"))]
    def set_coupling(self, value ='AC'):
        self.inst.write(f"ICPL {value}")
    def get_ground(self):
        return ['FLOAT', 'GROUND'][int(self.inst.query("IGND?"))]
    def set_ground(self, value ='FLOAT'):
        self.inst.write(f"IGND {value}")
    def get_input_mode(self):
        return ['VOLTAGE', 'CURRENT'][int(self.inst.query("IVMD?"))]
    def set_input_mode(self, value ='VOLTAGE'):
        self.inst.write(f"IVMD {value}")
    def get_current_range(self):
        return ['1 uA', '10 nA'][int(self.inst.query("ICUR?"))]
    def set_current_range(self, value ='1 uA'):
        indx ={'1 uA':0, '10 nA':1}[value]
        self.inst.write(f"ICUR {indx}")
    def get_reference_source(self):
        return ['INT', 'EXT', 'DUAL', 'CHOP'][int(self.inst.query("RSRC?"))]
    def set_reference_source(self, value ='EXT'):
        self.inst.write(f"RSRC {value}")
    def get_reference_trigger(self):
        return ['SIN', 'POSTTL', 'NEGTTL'][int(self.inst.query("RTRG?"))]
    def set_reference_trigger(self, value ='SIN'):
        self.inst.write(f"RTRG {value}")
    def get_reference_trigger_impedance(self):
        return ['50OHMS', '1MEG'][int(self.inst.query("REFZ?"))]
    def set_reference_impedance(self, value ='50OHM'):
        self.inst.write(f"REFZ {value}")
    def get_external_ref_freq(self):
        return f'{self.inst.query('FREQEXT?')} Hz'
    
    def get_phase(self):
        return f'{float(self.inst.query('PHAS?'))} Deg'
    def auto_phase(self):
        self.inst.write(f"APHS")
    def set_phase(self, value):
        self.inst.write(f"PHAS {value} DEG")

    
    def initialize_lockin(self):
        self.set_sensitivity(value=int(self.config['SENSITIVITY']['val']), unit= self.config['SENSITIVITY']['unit'])
        self.set_timeconstant(value=int(self.config['TIME CONSTANT']['val']), unit= self.config['TIME CONSTANT']['unit'])
        self.set_inputrange(value=int(self.config['INPUT RANGE']['val']), unit= self.config['INPUT RANGE']['unit'])
        self.set_filterslope(value=int(self.config['FILTER']['val']))
        self.set_sync_filter(value=self.config['Sync']['val'])
        self.set_input_channel(value=self.config['INPUT CHANNEL']['val'])
        self.set_coupling(value=self.config['COUPLE']['val'])
        self.set_ground(value=self.config['GROUND']['val'])
        self.set_input_mode(value= self.config['INPUT']['val'])
        self.set_current_range(value=self.config['CURRENT']['val'])
        self.set_reference_source(value=self.config['Ref SOURCE']['val'])
        self.set_reference_trigger(value=self.config['TRIGGER']['val'])
        self.set_reference_impedance(value= self.config['Ref IMPEDANCE']['val'])
        self.timeout(ms=10000)
    
    def get_channel_data(self, channel= 'X'):
        "X, Y, IN, R ..."
        self.inst.write(f'OUTP? {channel}')
        data =  self.inst.read_raw()
        return float(data.strip())
    
    
    def get_multiple_channel_data(self, channels= 'X, Y, IN1'):
        "2 or 3 channels"
        self.inst.write(f'SNAP? {channels}')
        byte_string =  self.inst.read_raw()
        regular_string = byte_string.decode('utf-8')  # Convert byte string to regular string
        floats_list = [float(x) for x in regular_string.split(',')]
        return floats_list
    
    def display_AuxIn1(self):
        "change theta display to Aux In 1"
        self.inst.write('CDSP 3, 4')

    def get_captureratemax(self):
        """return maximum capture rate in Hz, this value  is determined by the time constant"""
        return self.inst.query('CAPTURERATEMAX?')
    def set_capturerate(self, n=5):
        """ sets capture rate = (captureratemax/2^n)
            n is limitted to 0<=n<=20
        """
        self.inst.write(f'CAPTURERATE {int(n)}')
    def get_capturerate(self):
        return self.inst.query('CAPTURERATE?')
    def set_capturelen_kbytes(self, n):
        if n<=4096:
            self.inst.write(f'CAPTURELEN {int(n)}')
    def set_capturelen_and_channel(self, num_points, channels='XY' ):
        num_of_channels = len(channels)
        self.set_captureconfig_channels(channels=channels)
        capturelen_kbytes = (num_points * num_of_channels * 4) / 1024
        next_closer_capturelen_kbytes = int(((capturelen_kbytes // 2) + 1) * 2) if capturelen_kbytes <= 4096 else print(
            'reduce the sampling rate')
        self.set_capturelen_kbytes(n=next_closer_capturelen_kbytes)


    def set_captureconfig_channels(self, channels ='XY'):
        """ X|XY|RT|XYRT"""
        self.inst.write(f'CAPTURECFG {channels}')
    def get_capture_num_of_channels(self):
        """ 0:X, 1:XY, 2:RT, 3:XYRT"""
        return {0: 1, 1: 2, 2: 2, 3: 4}.get(int(self.inst.query('CAPTURECFG?')), None)
    def start_capture(self, mode="immediate"):
        """immediate or trigstart """
        if mode == "immediate":
            self.inst.write(f'CAPTURESTART ONE, IMM')
        elif mode == "trigstart":
            self.inst.write(f'CAPTURESTART ONE, TRIG')
    def stop_capture(self):
        """ stops data capture after capturing next 2kbytes"""
        self.inst.write(f'CAPTURESTOP')
    def get_num_of_capturebytes_sofar(self):
        return int(self.inst.query('CAPTUREBYTES?'))
    def get_total_kbytes_captured(self):
        return int(self.inst.query('CAPTUREPROG?'))
    def get_data_binaryblock(self, offse_kbytes=0, len_kbytes=64):
        """ maximum amount of data can obtain one time is 64 kB 
        add offset to get the rest"""
        self.inst.write(f'CAPTUREGET? {offse_kbytes}, {len_kbytes}')
        data =  self.inst.read_raw()
        return data
    
    def get_capture_status(self):
        staus_int =int(self.inst.query(f'CAPTURESTAT?'))
        if staus_int ==0:
            status = 'awaiting'
        elif staus_int ==3: 
            status = 'triggered'
        elif staus_int ==6: 
            status ='done' 
        else:
            status =None
        
        return status

    
    def capture_data_trig_start(self, channels='XY',print_status=True):
        
        self.start_capture(mode="trigstart")
    

    

    
    def capture_data(self, num_points, channels='XY', mode="immediate", print_status=True):

        num_of_channels = len(channels)
        # self.set_captureconfig_channels(channels=channels)
        capturelen_kbytes = (num_points * num_of_channels * 4) / 1024
        next_closer_capturelen_kbytes = int(((capturelen_kbytes // 2) + 1) * 2) if capturelen_kbytes <= 4096 else print(
            'reduce the sampling rate')
        # self.set_capturelen_kbytes(n=next_closer_capturelen_kbytes)

        self.start_capture(mode=mode)
       

        status = self.get_capture_status()
        print('*'*20)
        print('*'*15)
        print(f'Step1: Lockin capturing data...trigger status: {status}' )
       
        condition_satisfied = False

        while True:
            try:
                status = self.get_capture_status()
                if status =='triggered':
                    if not condition_satisfied:
                        print("Step3: Lockin capture triggered")
                        condition_satisfied =True

                if status == 'done':
                    print("Step5: Lockin capture finished")
                    break
            except ValueError as ve:
                print("error occured while querying lockin status", ve)
            
            except Exception as e:
                print(e)

            time.sleep(1)



        # if print_status:
        #     while (num_bytes_sofar := self.get_num_of_capturebytes_sofar()) < num_points * 4 * num_of_channels:
        #         print(f'capture status: {self.inst.query(f'CAPTURESTAT?')}')
        #         time.sleep(1)
        #         print(
        #             f'bytes so far: {num_bytes_sofar}/{next_closer_capturelen_kbytes * 1024}--- points so far: {int((num_bytes_sofar / 4) / num_of_channels)}/{num_points}')
                

        bytes_captured = self.get_total_kbytes_captured() * 1024

      
       
        print(f'\t amount of data captured: {bytes_captured} bytes ,{bytes_captured / 1024} kB')
        # print("""Excess data points are captured until the buffer is filled. The buffer length is limited to 1 ≤ n ≤ 4096,
        #     where n is even. The buffer length is measured in kilobytes """)
        # self.stop_capture()






    def capture_data_continuous(self, channels='XY', mode="immediate", print_status=True):
        """immediate or trigstop """
        num_of_channels = len(channels)
        self.set_captureconfig_channels(channels=channels)

        if mode == "immediate":
            self.inst.write(f'CAPTURESTART CONT, IMM')
        elif mode == " trigstop":
            self.inst.write(f'CAPTURESTART CONT, TRIG')

        if print_status:

            time.sleep(1)
            num_bytes_sofar = self.get_num_of_capturebytes_sofar()
            print(f'num of points sofar: {num_bytes_sofar/(num_of_channels*4)}')


    def retrieve_data(self,num_points,  channels='XY',  print_status=True):
        bytes_captured = self.get_total_kbytes_captured() * 1024
        num_of_channels = len(channels)
        i_bytes_remaining = min(bytes_captured, num_points * 4 * num_of_channels)
        i_block_offset = 0
        f_data = []
        data_block_retrieved =False
        while i_bytes_remaining > 0:
            try:
                i_block_cnt = min(64, int(math.ceil(i_bytes_remaining / 1024.0)))
                buf = self.get_data_binaryblock(i_block_offset, i_block_cnt)
                data_block_retrieved =True
            except ValueError as ve:
                print("Error occurred while retrieving data:", ve)
                data_block_retrieved =False
            except Exception as e:
                print("An unexpected error occurred while retrieving data:", e)
                data_block_retrieved =False
                
            if data_block_retrieved:
                raw_data = buf[2 + int(chr(buf[1])):]
                i_bytes_to_convert = min(i_bytes_remaining, len(raw_data))
                f_block_data = list(unpack_from('<%df' % (i_bytes_to_convert / 4), raw_data))
                f_data += f_block_data
                i_block_offset += i_block_cnt
                i_bytes_remaining -= i_block_cnt * 1024

            
            time.sleep(0.5)

        channel_data = {str(i): [] for i in range(num_of_channels)}
        for i, value in enumerate(f_data[:int(num_points * num_of_channels)]):
            channel_data[str(i % num_of_channels)].append(value)
        if print_status:
            print('Step7: data Retrieved')

        return channel_data
    
    def retrieve_data_for_continuous_aquisition(self,num_points,  channels='XY',  print_status=True):
        bytes_captured = self.get_total_kbytes_captured() * 1024
        num_of_channels = len(channels)
        i_bytes_remaining = bytes_captured
        i_block_offset = 0
        f_data = []
        while i_bytes_remaining > 0:
            i_block_cnt = min(64, int(math.ceil(i_bytes_remaining / 1024.0)))
            buf = self.get_data_binaryblock(i_block_offset, i_block_cnt)
            raw_data = buf[2 + int(chr(buf[1])):]
            i_bytes_to_convert = min(i_bytes_remaining, len(raw_data))
            f_block_data = list(unpack_from('<%df' % (i_bytes_to_convert / 4), raw_data))
            f_data += f_block_data
            i_block_offset += i_block_cnt
            i_bytes_remaining -= i_block_cnt * 1024
            time.sleep(0.2)

        channel_data = {str(i): [] for i in range(num_of_channels)}
        for i, value in enumerate(f_data):
            channel_data[str(i % num_of_channels)].append(value)
        for key in list(channel_data):
            channel_data[key] =np.array(channel_data[key])
            tolerance = 1e-100
            non_zero_indices =np.where(np.abs(channel_data[key]) > tolerance)[0]
            channel_data[key] =channel_data[key][non_zero_indices]
            channel_data[key] =  channel_data[key][-num_points:]
        if print_status:
            print('data Retrieved')
        return channel_data
    

    
    def get_data_ascii(self,n):
        """ return return single data of diffrent channel
        """
        return self.inst.query(f'CAPTUREVAL? {n}')
        
 
 


# Example usage:
if __name__ == "__main__":
    amplifier = LockInAmplifier(inifile="lockin_params.ini")
    amplifier.open_instrument(instrument_address='USB0::0xB506::0x2000::005180::INSTR')
    print(amplifier.inst.query('*IDN?'))
    print(amplifier.get_phase())
    amplifier.initialize_lockin()
    amplifier.timeout(ms=20000)
    print('channel X, Y AUX IN')
    print(amplifier.get_multiple_channel_data(channels= 'X, Y, IN1'))
    amplifier.display_AuxIn1()
    print('captureratemax')
    print(amplifier.get_captureratemax())
    amplifier.set_capturerate(n=6)
    print('capturerate')
    capture_rate = float(amplifier.get_capturerate())
    print(capture_rate)
    
    # measurement time
    measurement_time =350/20 # for covering 600mm with 20mm/s speed
    measurement_time*capture_rate
    num_points = int(np.round(measurement_time*capture_rate))
    
    amplifier.capture_data(num_points, channels ='XY', mode="immediate")
    channel_data_dict =amplifier.retrieve_data(num_points, channels ='XY', print_status=True)
    print(f'first data of diffrent channels {amplifier.get_data_ascii(0)}')


    amplifier.set_capturelen_kbytes(n=next_closer_capturelen_xy_kbytes)
    amplifier.set_captureconfig_channels(channels ='XY')
   
    

    amplifier.close_instrument()


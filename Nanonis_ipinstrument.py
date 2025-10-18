# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 17:36:23 2023

@author: k.jin  <k.jin@fz-juelich.de>
"""
import os
import time
from qcodes.instrument import IPInstrument, InstrumentBase
from qcodes.instrument.parameter import Parameter,ParameterWithSetpoints
import logging
import numpy as np
from typing import Dict,List,Union,Any,Tuple
import qcodes.validators as vals
from qcodes.utils.validators import Arrays,Enum
from qcodes import logger
from Nanonis_ipinstrumentbase import NanonisIPInstrumentbase
from typing import Literal
#from Nanonis_biasspectra import Bias_spctra

log = logging.getLogger(__name__)
Nanonis_LOGGER = '.'.join((InstrumentBase.__module__, 'com', 'visa'))
logger.get_log_file_name()

class NanonisIPInstrument(NanonisIPInstrumentbase):
    def __init__(self,name, configpath,timeout,**kwargs: Any):
        super().__init__(name, configpath, timeout, **kwargs)



        #initialize the instrument
        #self.signals_name_list = self.get_channel_list()
        self.signals_channel_dict = self.get_channel_dict()
        self.z_range_limit =  self.get_z_range_lim()

     
        self.add_parameter(name='It',
                           label='tunneling current',
                           unit='A',
                           get_cmd = self.get_It,
                           docstring="the tunneling current measured"
                           )

        self.add_parameter(name='It_setpoint',
                           label='tunneling current setpoint',
                           unit='A',
                           get_cmd = self.get_It_setpoint,
                           set_cmd = 'ZCtrl.SetpntSet {}',
                           docstring = "the setpoint of tunneling current.",
                           vals = vals.Numbers(0,10e-9)
                           )

        self.add_parameter(name='bias',
                           label='bias',
                           unit='V',
                           get_cmd = self.get_bias,
                           set_cmd = 'Bias.Set {}',
                           vals= vals.Numbers(-10, 10),
                           step = 0.025,
                           inter_delay = 0.4,
                           )
        
        self.add_parameter(name='topo',
                           label='topo',
                           unit='m',
                           get_cmd = self.get_topo,
                           vals = vals.Numbers(self.z_range_limit['low_limit'],self.z_range_limit['high_limit'])
                           )
                           
        self.add_parameter(name = 'z_controller',
                            label = 'z_controller',
                            set_cmd = 'setFeedback {}',
                            get_cmd = self.get_feedback,
                            val_mapping = {
                                'off':0,
                                'on':1,
                            },
                            vals = Enum('on','off')
                            )
    

        ## bias spectro:
        #self.write('openBiasSpec') 
        #self.update_bias_spec_props()
       # self.add_parameter(name='didv',
       #                    label='dI/dV',
       #                    parameter_class= Bias_spctra,
       #                    data_getter = self.do_biasspec,
       #                    bias_prop = self.get_bias_spec_props,
       #                    channel_index = self.get_didv_chanel_index(channel_name ='LI Demod 1 X (A)')
       #                    )
        
        
    def get_channel_dict(self) -> Dict[str,int]:
        """
        Create a dictionary mapping channel names to their corresponding index.

        Summary Line:
        Maps signal names to indices.

        Arguments/Parameters:
        - None

        Return Values:
        - Dict[str, int]: A dictionary where keys are signal names and values are their indices.
        """

        channel_list = self.ask('Signals.NamesGet')['Signals names']
        channel_dic = {channel: index for index, channel in enumerate(channel_list)}
        return channel_dic
    
    def get_signal_name_list(self) -> list[str] :
        """
        Retrieve the list of measurement channel names.

        Summary Line:
        Retrieves available measurement channel names.

        Arguments/Parameters:
        - None

        Return Values:
        - List[str]: A list of measurement channel names.
        """

        return self.ask('Signals.MeasNamesGet')['Measurement channels list']

    def get_channel_value(self,channel_name:str) -> float:
        """
        Get the current value of a specified channel.

        Summary Line:
        Fetches the current measurement value of the given channel.

        Arguments/Parameters:
        - channel_name (str): The name of the channel to retrieve the value for.

        Return Values:
        - float: The current value of the specified channel.
        """
        if channel_name not in self.signals_channel_dict:
            available = list(self.signals_channel_dict.keys())
            raise ValueError(f"Channel '{channel_name}' not found. available channels: {available}")
        
        index = self.signals_channel_dict[channel_name]
        values = self.ask(f'Signals.ValGet {index} 0')['Signal value']
        return values
    
    def get_channel_values(self, channel_names: List[str]) -> np.ndarray:
        """
        Get the current values of multiple specified channels using a single multi-value query.

        Summary Line:
        Fetches current measurement values for a list of channel names efficiently.

        Arguments/Parameters:
        - channel_names (List[str]): A list of channel names to retrieve values for.

        Return Values:
        - np.ndarray: An array of the current values corresponding to the provided channel names.
        """
        missing_channels = [ch for ch in channel_names if ch not in self.signals_channel_dict]
        if missing_channels:
            raise ValueError(f"Channels not found: {missing_channels}. Available: {list(self.signals_channel_dict)}")

        indices = [self.signals_channel_dict[ch] for ch in channel_names]
        
        response = self.ask(f'Signals.ValsGet {len(indices)} {indices} 0')
        values = response['Signals values']
        return np.array(values, dtype=float)


    def get_It(self) ->float:
        return self.get_channel_value('Current (A)')

    def get_bias(self)->float:
        return self.ask('Bias.Get')['Bias value (V)']

    def get_It_setpoint(self) ->float:
        return self.ask('ZCtrl.SetpntGet')['Z-Controller setpoint']
    
    def set_It_setpoint(self,setpoint:float) ->None:
        if type(setpoint) != float:
            raise TypeError(f'{setpoint} is not a float.')
        if not -10e-9 < setpoint < 10e-9:
            raise ValueError(f'{setpoint} is out of the range. The valid range is [-10, 10]')
        return self.write(f'ZCtrl.SetpntSet {setpoint}')

    def set_bias(self,value:float):
        if type(value) != float:
            raise TypeError(f'{value} is not a float.')
        if not -10 < value < 10:
            raise ValueError(f'{value} is out of the range. The valid range is [-10, 10]')
        self.write(f'setBias {value}')

    def get_topo(self) -> float:
        return self.ask('ZCtrl.ZPosGet')['Z position (m)']
    
    def get_z_range_lim(self):
        z_range_lim_message = self.ask('ZCtrl.LimitsGet')
        high_limit = z_range_lim_message['Z high limit (m)'] # position of fully retracted
        low_limit = z_range_lim_message['Z low limit (m)']  # position of fully extented
        return {'low_limit':low_limit,'high_limit':high_limit}

    def get_feedback(self):
        return self.ask('ZCtrl.OnOffGet')['Z-Controller status']


    def do_retract(self):
        self.write('ZCtrl.Withdraw  1 -1')
        time.sleep(0.1)
        z_pos = self.topo.get()
        if z_pos < self.z_range_limit['high_limit']:
            raise RuntimeError('tip is not fully retracted!')
        # check the current!

    
    def do_autoapproach(self, mode: str = 'blocking')-> None:
        """
        Initiate the auto-approach sequence.

        Summary Line:
        Performs tip auto-approach in either 'blocking' or 'nonblocking' mode.

        Arguments/Parameters:
        - mode (str): Approach mode, either 'blocking' (waits until approach completes) or 'nonblocking'.

        Return Values:
        - None
        """
        mode = mode.lower()
        if mode not in {'blocking', 'nonblocking'}:
            raise ValueError("Mode must be either 'blocking' or 'nonblocking'.")
        
        self.write('AutoApproach.Open')
        time.sleep(0.1)
        self.write('AutoApproach.OnOffSet 1')

        if mode == 'blocking':
            time.sleep(0.1)
            approached_status = self.ask('AutoApproach.OnOffGet')['Status']
            while approached_status  == 1:
                time.sleep(1)
                approached_status = self.ask('AutoApproach.OnOffGet')['Status']
            print('The tip is approached.')
   
    
    def coarse_motor(self,direction:str,steps:int,) -> None:
        """
        Move the coarse motor in a specified direction by a given number of steps.

        Summary Line:
        Moves the tip using coarse motor control along X, Y, or Z directions.

        Arguments/Parameters:
        - direction (str): Movement direction, one of '+X', '-X', '+Y', '-Y', '+Z', '-Z'.
        - steps (int): Number of steps to move; sign determines direction.

        Return Values:
        - None
        """
        corase_direction_map ={
            "+X" : 0,
            "-X" : 1,
            "+Y" : 2,
            "-Y" : 3,
            "+Z" : 4,
            "-Z" : 5,
            }
        if steps == 0:
            return None
        direction = direction.strip()

        if steps < 0:
            steps = abs(steps)
            if direction.startswith('+'):
                direction = direction.replace('+', '-')
            elif direction.startswith('-'):
                direction = direction.replace('-', '+')
     
        if direction not in corase_direction_map:
            raise ValueError("Direction must be one of '+X', '-X', '+Y', '-Y', '+Z', or '-Z'.")
       
        direction_index = corase_direction_map[direction]
       
        self.write(f'Motor.StartMove {direction_index} {steps} 0 1')

    def regulate_z(self,regulate_z_value:float, max_attempts: int = 10)-> None:
        """
        Regulate the Z position of the tip to fall within (regulate_z_value, lower limit position).
        Retracts and re-approaches the tip until it is within a specified Z range.

        Arguments/Parameters:
        - regulate_z_value (float): Upper bound for Z position regulation.

        Return Values:
        - None
        """
        lower_limit  = self.z_range_limit['low_limit'] # position of tip fully extented
        upper_limit = self.z_range_limit['high_limit'] # position of tip fully retracted

        if not lower_limit  < regulate_z_value < upper_limit:
            raise ValueError(f'{regulate_z_value} is out of the range. The valid range is [{lower_limit}, {upper_limit}]')
        
        def in_target_range(z: float) -> bool:
            return lower_limit < z < regulate_z_value

        if self.z_controller.get() == 'on':
            if in_target_range(self.topo.get()):
                return
            else: 
                self.do_retract()
                time.sleep(0.1)
                self.coarse_motor('+Z',3)  
        else:
            self.do_autoapproach()
            time.sleep(0.1)
            if  in_target_range(self.topo.get()):
                return
            else:
                self.do_retract()
                time.sleep(0.1)
                self.coarse_motor('+Z',3)
    
        # Keep regulating until within the desired range

        for attempt in range(1, max_attempts + 1):
            self.do_autoapproach()
            if in_target_range(self.topo.get()):
                print(f'Z is regulated')
                return
            else:
                self.do_retract()
                time.sleep(0.1)
                self.coarse_motor('+Z',3)
                time.sleep(0.1)

        raise RuntimeError(f"Failed to regulate Z after {max_attempts} attempts.")

    def get_current_scan_line(self, timeout: int = 10) -> Tuple[int, int]:
        """
        Query the current scan line number and scan direction after waiting for the end of a line.

        Args:
            timeout (int): Timeout duration in milliseconds to wait for end-of-line signal.

        Returns:
            Tuple[int, int]: A tuple containing:
                - Line number (int): Current scan line number.
                - Type of movement (int): Indicates scan direction:
                    0 = forward,
                    1 = backward,
                    2 = moved to scan frame center,
                    3 = moved to start point before scan.

        Raises:
            RuntimeError: If expected keys are missing in the response.
            TypeError: If response values are not integers.
        """
        response = self.ask(f"Scan.WaitEndOfLine {timeout}")

        try:
            line = response["Line number"]
            direction = response["Type of movement"]
        except KeyError as e:
            raise RuntimeError(f"Missing expected key in response: {e}")

        if not isinstance(line, int) or not isinstance(direction, int):
            raise TypeError("Expected both 'Line number' and 'Type of movement' to be integers.")

        return line, direction



    def get_bias_spec_props(self) ->dict:
        props = self.ask_raw('getBiasprops',[])
        return props
    
    def update_bias_spec_props(self) -> None:
        self.bias_prop  = self.get_bias_spec_props()
        self.number_of_points = self.bias_prop['Number of points']
        self.bias_spec_channels =  self.bias_prop['Channels']

    def get_didv_chanel_index(self,channel_name = 'LI Demod 1 X (A)') -> int:
        try:
            return self.bias_spec_channels.index(channel_name)
        except:
            raise ValueError(f'{channel_name} is not in the bias spec channel list.')

    def do_biasspec(self) -> dict:
        spec = self.ask('doBiasSpec2 1 0 bias_spectroscopy')
        return spec 
    
    def scan_action(self, action: int, direction: Literal[0, 1] = 1, blocking: bool = False, timeout: float = 10.0) -> None:
        """
        Send a scan control action to the microscope.

        Args:
            action (int): The scan action code:
                        0 = Start, 1 = Stop, 2 = Pause, 3 = Resume,
                        4 = Freeze, 5 = Unfreeze, 6 = Go to Center
            direction (0 or 1): Scan direction (0 = down, 1 = up)
            blocking (bool): If True, wait until scan reaches expected state.
            timeout (float): Max time in seconds to wait if blocking is True.

        Raises:
            RuntimeError: If scan does not reach expected state within timeout.
            ValueError: If input values are out of valid range.
        """
        if action not in range(7):
            raise ValueError(f"Invalid scan action: {action}")
        if direction not in (0, 1):
            raise ValueError(f"Invalid scan direction: {direction}")

        self.write(f"Scan.Action {action} {direction}")

        if blocking:
            expected_running = int(action == 0)  # expect 1 if Start, 0 otherwise
            t_start = time()

            while time() - t_start < timeout:
                status = self.ask("Scan.StatusGet")
                if "Scan status" not in status:
                    raise RuntimeError("Missing 'Scan status' in Scan.StatusGet response.")

                running = status["Scan status"]
                if bool(running) == bool(expected_running):
                    return

                sleep(0.1)

            raise RuntimeError(f"Scan did not {'start' if expected_running else 'stop'} within {timeout:.1f} seconds.")

    def stepper(self,direction: str,steps: int,regulate_z_value: float = 100E-9,  scan_direction: int = 1,scan_timeout: int = 5) -> None:
        """
        Perform a safe step motion: retract tip, move, regulate tip, and scan one line.

        Args:
            direction (str): Movement direction, one of {'+X', '-X', '+Y', '-Y'}.
            steps (int): Number of coarse motor steps in the given direction.
            regulate_z_value (float): Target Z value to re-approach safely after motion.
            scan_timeout (int): Timeout (ms) for Scan.WaitEndOfLine.

        Raises:
            ValueError: If an invalid direction is provided.
            """
        if direction not in {'+X', '-X', '+Y', '-Y'}:
            raise ValueError(f"Invalid direction: {direction}")

        print("Retracting tip...")
        self.scan_action(action = 1, direction=scan_direction, blocking=False)
        time.sleep(0.1)
        self.do_retract()
        time.sleep(0.1)

        self.coarse_motor('+Z', 3)
        print("Tip retracted safely.")
        time.sleep(0.1)
        print(f"Moving {steps} steps in {direction}...")
        self.coarse_motor(direction, steps)
        time.sleep(0.1)
        print(f"Regulating tip to {regulate_z_value}...")
        self.regulate_z(regulate_z_value)
        time.sleep(0.1)

        print("Scanning 1 line...")
        self.scan_action(action=0, direction=scan_direction, blocking=False)
        time.sleep(scan_timeout)
        while True:
            line_number, movement_type = self.get_current_scan_line(timeout=int(100))
            time.sleep(0.1)
            if movement_type == 1 and line_number == 1:
                self.scan_action(action = 1, direction=scan_direction, blocking=False)

                print("First downward line completed → stopping scan.")
                break


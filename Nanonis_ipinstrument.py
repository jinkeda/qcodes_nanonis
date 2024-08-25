# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 17:36:23 2023

@author: k.jin
"""
import os
import time
from qcodes.instrument import IPInstrument, InstrumentBase
from qcodes.instrument.parameter import Parameter,ParameterWithSetpoints
import logging
from typing import Dict,List,Union,Any,Tuple
import qcodes.validators as vals
from qcodes.utils.validators import Arrays,Enum
from qcodes import logger
from Nanonis_ipinstrumentbase import NanonisIPInstrumentbase
from Nanonis_biasspectra import Bias_spctra

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
                           set_cmd = 'setCurrent {}',
                           docstring = "the setpoint of tunneling current.",
                           vals = vals.Numbers(0,10e-9)
                           )

        self.add_parameter(name='bias',
                           label='bias',
                           unit='V',
                           get_cmd = self.get_bias,
                           set_cmd = self.set_bias,
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
        self.write('openBiasSpec') 
        self.update_bias_spec_props()
        self.add_parameter(name='didv',
                           label='dI/dV',
                           parameter_class= Bias_spctra,
                           data_getter = self.do_biasspec,
                           bias_prop = self.get_bias_spec_props,
                           channel_index = self.get_didv_chanel_index(channel_name ='LI Demod 1 X (A)')
                           )
        
        
    def get_channel_dict(self):
        channel_list = self.ask_raw('getSignalMeasureName',[])['Measurement channels list']
        channel_dic = {channel: index for index, channel in enumerate(channel_list)}
        return channel_dic
    
    def get_signal_name_list(self) :
        self.ask_raw('getSignalMeasureName',[])['Measurement channels list']

    def get_It(self) ->float:
        current_channel = self.signals_channel_dict['Current (A)']
        return self.ask_raw('getCurrentSignal',[current_channel,1])['Signal value']

    def get_It_setpoint(self) ->float:
        return self.ask_raw('getCurrent',[])['Z-Controller setpoint']


    def get_bias(self)->float:
        return self.ask_raw('getBias',[])['Bias value (V)']

    def set_bias(self,value:float):
        self.write_raw('setBias',[value])

    def get_topo(self) -> float:
        return self.ask('getZ')['Z position (m)']
    
    def get_z_range_lim(self):
        z_range_lim_message = self.ask_raw('getZrange',[])
        high_limit = z_range_lim_message['Z high limit (m)'] # position of fully retracted
        low_limit = z_range_lim_message['Z low limit (m)']  # position of fully extented
        return {'low_limit':low_limit,'high_limit':high_limit}

    def get_feedback(self):
        return self.ask('getFeedback')['Z-Controller status']


    def do_retract(self):
        self.write('rectractZ 1 -1')
        time.sleep(0.1)
        z_pos = self.topo.get()
        if z_pos < self.z_range_limit['high_limit']:
            raise RuntimeError('tip is not fully retracted!')
        # check the current!
    
    def do_autoapproach(self, mode = 'blocking'):
        self.write_raw('openAutoApproach',[])
        if mode == 'nonblocking':
            self.write_raw('doAutoApproach',[1])
        elif mode == 'blocking':
            self.write_raw('doAutoApproach',[1])
            approached = self.ask_raw('getAutoApproach',[])['Status']
            while approached  == 1:
                approached = self.ask_raw('getAutoApproach',[])['Status']
                time. sleep(1)
            print('The tip is approached.')
        else:
            raise ValueError('Only blocking and nonblocking are possible.')
    
    def coarse_motor(self,direction:str,steps:int,):
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
        elif steps < 0:
            steps = abs(steps)
            if "+" in direction:
                direction_parse = direction.replace("+",'-')
            elif "-" in direction: 
                direction_parse = direction.replace("-",'+')
        elif steps > 0:
            direction_parse = direction
        try:
            direction_index = corase_direction_map[direction_parse]
        except:
            raise ValueError('directon can not recogonize. +X, -X,+Y,-Y and +Z, -Z')
        self.write(f'doCoarseMotion {direction_index} {steps}')

    def regulate_z(self,regulate_z_value:float):

        lowerest = self.z_range_limit['low_limit'] # position of tip fully extented
        highest = self.z_range_limit['high_limit'] 

        if not lowerest < regulate_z_value < highest:
            raise ValueError(f'{regulate_z_value} is out of the range. The valid range is [{lowerest}, {highest}]')

        if self.z_controller.get() == 'on':
            if lowerest < self.topo.get() < regulate_z_value:
                return
            else: 
                self.do_retract()
                time.sleep(0.1)
                self.coarse_motor('+Z',3)
            
        self.do_autoapproach()

        while not lowerest < self.topo.get() < regulate_z_value:
            self.do_retract()
            time.sleep(0.1)
            self.coarse_motor('+Z',3)
            self.do_autoapproach()
        print(f'Z is regulated')

    def stepper(self,direction:str,distance:float,regulate_z:float= None):

        """
        distance : the lateral movement distance in the unit of m
        control_z: the regulated tip distance for obtaining the tunneling current
        """

        if direction not in ['+X','-X','+Y','-Y']:
            raise ValueError('directon can not recogonize. Available directions: +X, -X,+Y,-Y')

        # first retract the tip
        self.do_retract()
        time.sleep(0.1)
        #Coarse motion retract the tip
        self.coarse_motor('+Z',3)
        time.sleep(0.1)
        #Get the coarse motor constnats in the moving direction. The constant is in the unit of m/pulse
        coarseMotionConstants_dict = self.config['CoarseMotionConstants']
        coarseMotionConstants = coarseMotionConstants_dict[direction]
        steps = int(distance/coarseMotionConstants)
        # need write log infor
        log.info('Coarse movement in {direction} for {distance} m')
        self.coarse_motor(direction,steps)
        time.sleep(0.1)
        # approach the tip
        if not regulate_z:
            self.do_autoapproach()
        else:
            self.regulate_z(regulate_z_value = regulate_z)

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
    
    def scan(self)->None: 
        self.ask('doScan')
        time.sleep(2)
        while self.ask('scanStatus')['Scan status']:
            time.sleep(2)
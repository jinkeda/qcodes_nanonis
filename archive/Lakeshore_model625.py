import pyvisa

from pyvisa.constants import StopBits, Parity
from qcodes import VisaInstrument
from qcodes import initialise_database,load_or_create_experiment
from qcodes.logger import get_instrument_logger

import qcodes.validators as vals

import qcodes as qc
import time

from qcodes.instrument.parameter import Parameter
from qcodes.instrument.specialized_parameters import ElapsedTimeParameter

import matplotlib.pyplot
import matplotlib.pyplot as plt

import numpy as np

from tqdm import tqdm
from qcodes.dataset.measurements import Measurement
from qcodes.dataset.experiment_container import new_experiment


from qcodes.dataset.plotting import plot_dataset
from qcodes.instrument.specialized_parameters import ElapsedTimeParameter
#from qcodes import MatPlot

class Lakeshore_Model625(VisaInstrument):
   def __init__(self, name: str,  address: str, **kwargs):
      super().__init__(name, address, terminator='\n', **kwargs)
      self.visa_handle.baud_rate = 9600
      self.visa_handle.data_bits = 7
      self.visa_handle.parity = Parity.odd
      self.visa_handle.stop_bits = StopBits.one

      self.add_parameter(name='B_field',
                           unit = 'T',
                           set_cmd=self.set_field,
                           get_cmd='RDGF?',
                           get_parser=float,
                           vals=vals.Numbers(-5, 5),
                           step = 0.05,
                           #inter_delay = 250,
                           )
      self.add_parameter(name='oer_quench',
                           get_cmd=self._get_oer_quench_bit,
                           get_parser=int,
                           val_mapping={'no quench detected': 0,
                                        'quench detected': 1}
                           )
      self.add_parameter(name='voltage',
                           unit = 'V',
                           get_cmd='RDGV?',
                           get_parser=float,
                           )
      self.add_parameter(name='current',
                           unit = 'A',
                           get_cmd='RDGI?',
                           get_parser=float,
                           vals=vals.Numbers(-60, 60)
                           )
            

      self.connect_message()

 #  def set_field(self, target_value: float):
 #     self.write('SETF {}'.format(target_value))
 #     time.sleep(1)
 #     while not np.allclose(self.B_field.get(),target_value,atol = 0.01):
 #        time.sleep(1)
 #     self.log.debug(f'Starting blocking ramp of {self.name} to {target_value}')
   def set_field(self, target_value: float, poll_interval: float = 1, atol: float = 0.0003) -> None:
      """
      Ramp the magnetic field to the target value, blocking until complete, with tqdm progress bar.

      Summary Line:
      Blocks and waits until magnetic field reaches the target value, showing progress with tqdm.

      Arguments/Parameters:
      - target_value (float): Desired magnetic field value.
      - poll_interval (float): Time in seconds between checks.
      - atol (float): Absolute tolerance for completion (default 0.001 T).

      Return Values:
      - None
      """
      self.write(f'SETF {target_value}')
      time.sleep(1)
      self.log.debug(f'Starting blocking ramp of {self.name} to {target_value:.3f} T')

      with tqdm(desc=f'Ramping {self.name}', unit='T', leave=False) as pbar:
         while True:
               current = self.B_field.get()
               delta = abs(current - target_value)
               pbar.set_postfix(field=current, target=target_value, delta=delta)
               if np.allclose(current, target_value, atol=atol):
                  break
               time.sleep(poll_interval)

               
   def _get_operational_errors(self) -> str:
        """
        Error Status Query

        Returns
        -------
            error status
        """
        error_status_register = self.ask('ERST?')
        # three bytes are read at the same time, the middle one is the operational error status
        operational_error_registor = error_status_register.split(',')[1]
        
        #prepend zeros to bit-string such that it always has length 9
        oer_bit_str = bin(int(operational_error_registor))[2:].zfill(9)
        return oer_bit_str

   def _get_oer_quench_bit(self) -> int:
        """
        Returns the oer quench bit

        Returns
        -------
            quench bit
        """
        return int(self._get_operational_errors()[3])

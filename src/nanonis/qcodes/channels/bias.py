# -*- coding: utf-8 -*-
"""
Bias Channel for QCoDeS

QCoDeS InstrumentChannel wrapper for Nanonis Bias commands.
"""

from qcodes.instrument import InstrumentChannel
from qcodes.parameters import Parameter
from qcodes.validators import Numbers


class BiasChannel(InstrumentChannel):
    """
    QCoDeS channel for Nanonis Bias control.
    
    Provides parameters and methods for controlling the bias voltage.
    
    Parameters:
        voltage: Current bias voltage (V), gettable and settable
        
    Example:
        >>> nanonis = NanonisInstrument('nanonis', '127.0.0.1', 6501, 'configs/commands')
        >>> nanonis.bias.voltage(0.5)  # Set to 0.5V
        >>> print(nanonis.bias.voltage())  # Read current value
    """
    
    def __init__(self, parent, name: str, controller):
        super().__init__(parent, name)
        self._ctrl = controller
        
        # Main voltage parameter
        self.voltage = Parameter(
            'voltage',
            instrument=self,
            label='Bias Voltage',
            unit='V',
            vals=Numbers(-10, 10),
            get_cmd=self._get_voltage,
            set_cmd=self._set_voltage,
            docstring='Bias voltage applied to the sample',
        )
        
    def _get_voltage(self) -> float:
        """Get current bias voltage."""
        return self._ctrl.send('Bias.Get')
    
    def _set_voltage(self, voltage: float) -> None:
        """Set bias voltage."""
        self._ctrl.send('Bias.Set', voltage)
    
    def pulse(
        self,
        width: float,
        voltage: float,
        z_hold: bool = True,
    ) -> None:
        """
        Apply a bias pulse.
        
        Args:
            width: Pulse width in seconds
            voltage: Pulse voltage in V
            z_hold: Whether to hold Z-controller during pulse
        """
        # Simplified pulse command - full implementation would use Bias.Pulse
        original = self._get_voltage()
        self._set_voltage(voltage)
        import time
        time.sleep(width)
        self._set_voltage(original)

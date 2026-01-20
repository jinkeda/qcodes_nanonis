# -*- coding: utf-8 -*-
"""
Nanonis QCoDeS Instrument

Main QCoDeS Instrument class for Nanonis integration.
"""

from pathlib import Path
from typing import Any, Union, Optional
from qcodes.instrument import Instrument

from ..command import NanonisController
from .channels import BiasChannel, ScanChannel


class NanonisInstrument(Instrument):
    """
    QCoDeS Instrument for Nanonis SPM controller.
    
    This is Layer 3 of the architecture, providing QCoDeS integration
    on top of the NanonisController (Layer 2).
    
    Submodules:
        bias: BiasChannel for voltage control
        scan: ScanChannel for scan control
        
    Example:
        >>> from nanonis.qcodes import NanonisInstrument
        >>> from qcodes import Station, Measurement
        >>> 
        >>> # Create instrument
        >>> nanonis = NanonisInstrument(
        ...     'nanonis',
        ...     host='127.0.0.1',
        ...     port=6501,
        ...     config_path='configs/nanonis_tcp.yaml'
        ... )
        >>> 
        >>> # Use QCoDeS parameters
        >>> nanonis.bias.voltage(0.5)
        >>> print(nanonis.bias.voltage())
        >>> 
        >>> # Use in Station
        >>> station = Station()
        >>> station.add_component(nanonis)
        >>> 
        >>> # Use in Measurement
        >>> meas = Measurement()
        >>> meas.register_parameter(nanonis.bias.voltage)
        >>> 
        >>> # Direct Layer 2 access if needed
        >>> nanonis.send('Custom.Command', arg1, arg2)
        >>> 
        >>> # Clean up
        >>> nanonis.close()
    """
    
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        config_path: Union[str, Path],
        timeout: float = 10.0,
        **kwargs,
    ):
        """
        Initialize the Nanonis instrument.
        
        Args:
            name: QCoDeS instrument name
            host: Nanonis host IP address
            port: Nanonis TCP port (typically 6501)
            config_path: Path to command configuration file (YAML or JSON)
            timeout: Socket timeout in seconds
            **kwargs: Additional arguments passed to Instrument base class
        """
        super().__init__(name, **kwargs)
        
        # Create and connect the controller
        self._controller = NanonisController(host, port, config_path, timeout)
        self._controller.connect()
        
        # Create submodules (channels)
        self.bias = BiasChannel(self, 'bias', self._controller)
        self.add_submodule('bias', self.bias)
        
        self.scan = ScanChannel(self, 'scan', self._controller)
        self.add_submodule('scan', self.scan)
        
        # Store connection info
        self._host = host
        self._port = port
    
    @property
    def controller(self) -> NanonisController:
        """Access to underlying controller for advanced usage."""
        return self._controller
    
    def send(self, command: str, *args) -> Any:
        """
        Send a command directly via Layer 2.
        
        This provides direct access to any command in the registry,
        bypassing the QCoDeS parameter system.
        
        Args:
            command: Command name (e.g., 'ZCtrl.OnOffSet')
            *args: Command arguments
            
        Returns:
            Command result
        """
        return self._controller.send(command, *args)
    
    def list_commands(self, prefix: str = '') -> list:
        """List available commands, optionally filtered by prefix."""
        return self._controller.list_commands(prefix)
    
    def list_modules(self) -> list:
        """List available command modules."""
        return self._controller.list_modules()
    
    def get_idn(self) -> dict:
        """
        Get instrument identification.
        
        Returns:
            Dictionary with vendor, model, serial, firmware info
        """
        return {
            'vendor': 'SPECS',
            'model': 'Nanonis',
            'serial': f'{self._host}:{self._port}',
            'firmware': 'Unknown',
        }
    
    def close(self) -> None:
        """Close the instrument and disconnect."""
        self._controller.disconnect()
        super().close()
    
    def __repr__(self) -> str:
        status = "connected" if self._controller.is_connected else "disconnected"
        return f"NanonisInstrument('{self.name}', {self._host}:{self._port}, {status})"

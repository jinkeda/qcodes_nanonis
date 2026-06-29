# -*- coding: utf-8 -*-
"""
Scan Channel for QCoDeS

QCoDeS InstrumentChannel wrapper for Nanonis Scan commands.
"""

from typing import Dict, Literal
from qcodes.instrument import InstrumentChannel
from qcodes.parameters import Parameter
from qcodes.validators import Numbers


class ScanChannel(InstrumentChannel):
    """
    QCoDeS channel for Nanonis Scan control.
    
    Provides parameters and methods for controlling the scanner.
    
    Parameters:
        center_x: Scan center X position (m)
        center_y: Scan center Y position (m)  
        width: Scan width (m)
        height: Scan height (m)
        angle: Scan angle (degrees)
        
    Methods:
        start(): Start scanning
        stop(): Stop scanning
        set_frame(): Set all frame parameters at once
        
    Example:
        >>> nanonis = NanonisInstrument('nanonis', '127.0.0.1', 6501, 'configs/commands')
        >>> nanonis.scan.width(100e-9)  # Set 100nm scan width
        >>> nanonis.scan.start()
    """
    
    def __init__(self, parent, name: str, controller):
        super().__init__(parent, name)
        self._ctrl = controller
        
        # Frame parameters
        self.center_x = Parameter(
            'center_x',
            instrument=self,
            label='Scan Center X',
            unit='m',
            vals=Numbers(-1e-3, 1e-3),
            get_cmd=lambda: self._get_frame()['center_x'],
            docstring='X position of scan center',
        )
        
        self.center_y = Parameter(
            'center_y',
            instrument=self,
            label='Scan Center Y',
            unit='m',
            vals=Numbers(-1e-3, 1e-3),
            get_cmd=lambda: self._get_frame()['center_y'],
            docstring='Y position of scan center',
        )
        
        self.width = Parameter(
            'width',
            instrument=self,
            label='Scan Width',
            unit='m',
            vals=Numbers(1e-12, 1e-3),
            get_cmd=lambda: self._get_frame()['width'],
            docstring='Width of scan frame',
        )
        
        self.height = Parameter(
            'height',
            instrument=self,
            label='Scan Height',
            unit='m',
            vals=Numbers(1e-12, 1e-3),
            get_cmd=lambda: self._get_frame()['height'],
            docstring='Height of scan frame',
        )
        
        self.angle = Parameter(
            'angle',
            instrument=self,
            label='Scan Angle',
            unit='deg',
            vals=Numbers(-180, 180),
            get_cmd=lambda: self._get_frame()['angle'],
            docstring='Rotation angle of scan frame',
        )
    
    def _get_frame(self) -> Dict[str, float]:
        """Get current scan frame parameters."""
        return self._ctrl.send('Scan.FrameGet')
    
    def set_frame(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        angle: float = 0.0,
    ) -> None:
        """
        Set all scan frame parameters at once.
        
        Args:
            center_x: X position of scan center (m)
            center_y: Y position of scan center (m)
            width: Width of scan frame (m)
            height: Height of scan frame (m)
            angle: Rotation angle (degrees)
        """
        self._ctrl.send('Scan.FrameSet', center_x, center_y, width, height, angle)
    
    def start(self, direction: Literal['up', 'down'] = 'up') -> None:
        """
        Start scanning.
        
        Args:
            direction: Scan direction, 'up' or 'down'
        """
        dir_val = 0 if direction == 'up' else 1
        self._ctrl.send('Scan.Action', 0, dir_val)
    
    def stop(self) -> None:
        """Stop scanning."""
        self._ctrl.send('Scan.Action', 1, 0)
    
    def pause(self) -> None:
        """Pause scanning."""
        self._ctrl.send('Scan.Action', 2, 0)
    
    def resume(self) -> None:
        """Resume scanning."""
        self._ctrl.send('Scan.Action', 3, 0)

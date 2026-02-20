# -*- coding: utf-8 -*-
"""
Command Proxies

Optional convenience classes for common Nanonis operations.
These provide a more Pythonic API for frequently used commands.
"""

from typing import Dict, Any, Optional, Literal


class BiasProxy:
    """
    Convenience proxy for Bias commands.
    
    Example:
        >>> ctrl = NanonisController(...)
        >>> bias = BiasProxy(ctrl)
        >>> bias.set(0.5)
        >>> print(bias.get())
    """
    
    def __init__(self, controller):
        self._ctrl = controller
    
    def set(self, voltage: float) -> None:
        """Set the bias voltage."""
        self._ctrl.send('Bias.Set', voltage)
    
    def get(self) -> float:
        """Get the current bias voltage."""
        return self._ctrl.send('Bias.Get')
    
    def pulse(self, **kwargs) -> Any:
        """Execute a bias pulse."""
        return self._ctrl.send('Bias.Pulse', **kwargs)
    
    @property
    def voltage(self) -> float:
        """Current bias voltage (property-style access)."""
        return self.get()
    
    @voltage.setter
    def voltage(self, value: float) -> None:
        self.set(value)


class ScanProxy:
    """
    Convenience proxy for Scan commands.
    
    Example:
        >>> ctrl = NanonisController(...)
        >>> scan = ScanProxy(ctrl)
        >>> scan.set_frame(0, 0, 100e-9, 100e-9)
        >>> scan.start()
    """
    
    def __init__(self, controller):
        self._ctrl = controller
    
    def set_frame(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        angle: float = 0.0,
    ) -> None:
        """Set the scan frame parameters."""
        self._ctrl.send('Scan.FrameSet', center_x, center_y, width, height, angle)
    
    def get_frame(self) -> Dict[str, float]:
        """Get the current scan frame parameters."""
        return self._ctrl.send('Scan.FrameGet')
    
    def start(self, direction: Literal['up', 'down'] = 'up') -> None:
        """Start scanning."""
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


class ZControllerProxy:
    """
    Convenience proxy for Z-Controller commands.
    
    Example:
        >>> ctrl = NanonisController(...)
        >>> zctrl = ZControllerProxy(ctrl)
        >>> zctrl.on()
        >>> print(zctrl.setpoint)
    """
    
    def __init__(self, controller):
        self._ctrl = controller
    
    def on(self) -> None:
        """Turn on the Z-controller."""
        self._ctrl.send('ZCtrl.OnOffSet', 1)
    
    def off(self) -> None:
        """Turn off the Z-controller."""
        self._ctrl.send('ZCtrl.OnOffSet', 0)
    
    def is_on(self) -> bool:
        """Check if Z-controller is on."""
        return bool(self._ctrl.send('ZCtrl.OnOffGet'))
    
    def get_setpoint(self) -> float:
        """Get the current setpoint."""
        return self._ctrl.send('ZCtrl.SetpntGet')
    
    def set_setpoint(self, value: float) -> None:
        """Set the setpoint."""
        self._ctrl.send('ZCtrl.SetpntSet', value)
    
    @property
    def setpoint(self) -> float:
        """Current setpoint (property-style access)."""
        return self.get_setpoint()
    
    @setpoint.setter
    def setpoint(self, value: float) -> None:
        self.set_setpoint(value)


class TipProxy:
    """
    Convenience proxy for tip-related commands.
    """
    
    def __init__(self, controller):
        self._ctrl = controller
    
    def withdraw(self) -> None:
        """Withdraw the tip."""
        self._ctrl.send('ZCtrl.Withdraw', 1, 10000)
    
    def approach(self) -> None:
        """Approach the surface."""
        self._ctrl.send('AutoApproach.Open')
        self._ctrl.send('AutoApproach.OnOffSet', 1)


class MotorProxy:
    """
    Convenience proxy for coarse motor commands.
    """
    
    DIRECTIONS = {
        '+X': 0, '-X': 1,
        '+Y': 2, '-Y': 3,
        '+Z': 4, '-Z': 5,
    }
    
    def __init__(self, controller):
        self._ctrl = controller
    
    def move(self, direction: str, steps: int) -> None:
        """
        Move the coarse motor.
        
        Args:
            direction: One of '+X', '-X', '+Y', '-Y', '+Z', '-Z'
            steps: Number of steps to move
        """
        if direction not in self.DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction}")
        
        dir_idx = self.DIRECTIONS[direction]
        self._ctrl.send('Motor.StartMove', dir_idx, steps, 1)

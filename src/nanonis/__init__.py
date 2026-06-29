# -*- coding: utf-8 -*-
"""
Nanonis Python Library

A layered library for communicating with Nanonis SPM controllers.

Layers:
    - Layer 1 (Protocol): Low-level TCP communication
    - Layer 2 (Command): Command encoding/decoding and dispatch
    - Layer 3 (QCoDeS): QCoDeS Instrument integration (optional)
    
Example (standalone, Layer 2):
    >>> from nanonis.command import NanonisController
    >>> 
    >>> with NanonisController('127.0.0.1', 6501, 'configs/commands') as ctrl:
    ...     ctrl.send('Bias.Set', 0.5)
    ...     voltage = ctrl.send('Bias.Get')
    ...     print(f"Voltage: {voltage} V")
    
Example (QCoDeS, Layer 3):
    >>> from nanonis.qcodes import NanonisInstrument
    >>> 
    >>> nanonis = NanonisInstrument('nanonis', '127.0.0.1', 6501, 'configs/commands')
    >>> nanonis.bias.voltage(0.5)
    >>> print(nanonis.bias.voltage())
    >>> nanonis.close()
"""

from .protocol import (
    NanonisTCPClient,
    NanonisError,
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)
from .command import (
    NanonisController,
    CommandRegistry,
    CommandEncoder,
    CommandDecoder,
)

__version__ = '0.1.0'

__all__ = [
    # Protocol layer
    'NanonisTCPClient',
    'NanonisError',
    'NanonisConnectionError',
    'NanonisProtocolError',
    'NanonisTimeoutError',
    # Command layer
    'NanonisController',
    'CommandRegistry',
    'CommandEncoder',
    'CommandDecoder',
]

# Lazy import for QCoDeS layer (optional dependency)
def __getattr__(name):
    if name == 'NanonisInstrument':
        from .qcodes import NanonisInstrument
        return NanonisInstrument
    raise AttributeError(f"module 'nanonis' has no attribute '{name}'")

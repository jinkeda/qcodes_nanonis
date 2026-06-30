# -*- coding: utf-8 -*-
"""
Nanonis QCoDeS Integration Layer

Provides QCoDeS Instrument and Channel wrappers for Nanonis.
"""

from .instrument import NanonisInstrument
from .channels import BiasChannel, ScanChannel
from .spectroscopy import (
    RegisteredBiasSpectroscopy,
    RegisteredTrace,
    add_bias_spectroscopy_result,
    create_bias_spectroscopy_measurement,
    register_bias_spectroscopy,
)

__all__ = [
    'NanonisInstrument',
    'BiasChannel',
    'ScanChannel',
    'RegisteredBiasSpectroscopy',
    'RegisteredTrace',
    'add_bias_spectroscopy_result',
    'create_bias_spectroscopy_measurement',
    'register_bias_spectroscopy',
]

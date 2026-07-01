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
from .scan import (
    RegisteredScan,
    RegisteredScanChannel,
    add_scan_result,
    create_scan_measurement,
    register_scan_result,
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
    'RegisteredScan',
    'RegisteredScanChannel',
    'add_scan_result',
    'create_scan_measurement',
    'register_scan_result',
]

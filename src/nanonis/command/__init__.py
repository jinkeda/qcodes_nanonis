# -*- coding: utf-8 -*-
"""
Nanonis Command Layer

Provides command encoding/decoding and the main controller interface.
"""

from .registry import (
    ArgDefinition,
    CommandDefinition,
    CommandRegistry,
    VariableLengthConstraint,
)
from .exceptions import NanonisArgumentError
from .encoder import CommandEncoder, CommandDecoder
from .controller import NanonisController
from .proxies import (
    BiasProxy,
    ScanProxy,
    ZControllerProxy,
    TipProxy,
    MotorProxy,
)

__all__ = [
    # Core
    'NanonisController',
    'CommandRegistry',
    'CommandDefinition',
    'ArgDefinition',
    'VariableLengthConstraint',
    'NanonisArgumentError',
    'CommandEncoder',
    'CommandDecoder',
    # Proxies
    'BiasProxy',
    'ScanProxy',
    'ZControllerProxy',
    'TipProxy',
    'MotorProxy',
]

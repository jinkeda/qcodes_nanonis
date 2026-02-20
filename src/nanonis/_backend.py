# -*- coding: utf-8 -*-
"""
Backend detection for optional Rust acceleration.

This module provides centralized detection of the optional Rust backend
(nanonis_core), avoiding code duplication across the codebase.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import nanonis_core
    RUST_AVAILABLE = True
    logger.info("Rust backend available")
except ImportError:
    nanonis_core = None  # type: ignore
    RUST_AVAILABLE = False
    logger.debug("Rust backend not available, using pure Python")


def get_rust_module():
    """
    Get the Rust module or None if unavailable.
    
    Returns:
        The nanonis_core module if available, None otherwise
    """
    return nanonis_core if RUST_AVAILABLE else None

"""
ArteFact - A comprehensive forensic analysis toolkit
===================================================

A professional-grade digital forensics toolkit with dark-mode aesthetics
and comprehensive analysis capabilities.

Author: Rizzy1857
Version: 1.0.0 "Final Evidence"
"""

__version__ = "1.0.0"
__codename__ = "Final Evidence"
__author__ = "Rizzy1857"
__email__ = "Rizzy1857@gmail.com"

# Make core components easily accessible
from Artefact.core import get_config, get_logger
from Artefact.error_handler import ArtefactError, handle_error

__all__ = [
    '__version__',
    '__codename__',
    '__author__',
    '__email__',
    'get_config',
    'get_logger',
    'ArtefactError',
    'handle_error'
]

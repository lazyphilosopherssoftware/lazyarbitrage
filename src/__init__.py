"""
Arbitrage Bot Package

A cryptocurrency arbitrage bot that monitors multiple exchanges
for triangular arbitrage opportunities.
"""

__version__ = "1.0.0"
__author__ = "Lazy Philosopher Software"

from . import arbitrage
from . import config_loader
from . import exchange_wrapper

__all__ = [
    'arbitrage',
    'config_loader',
    'exchange_wrapper'
]

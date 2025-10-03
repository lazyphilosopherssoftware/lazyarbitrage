#!/usr/bin/env python3
"""
Main entry point for the arbitrage bot.
"""

import sys
import os
import asyncio

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

from arbitrage import main

if __name__ == "__main__":
    asyncio.run(main())

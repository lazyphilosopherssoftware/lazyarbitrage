"""
Main arbitrage bot orchestration module.
Coordinates data collection and arbitrage detection across exchanges.
"""

import asyncio
import logging
import config_loader
import data_manager
import arbitrage_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load and validate global configuration
config_loader.config.load()


async def main():
    """Main entry point for the arbitrage bot"""
    tasks = []
    exchanges = config_loader.config.exchange_ids
    all_symbols = config_loader.config.get_all_symbols()
    testnet = config_loader.config.testnet_enabled

    logger.info(f"Starting arbitrage bot with exchanges: {exchanges}")
    logger.info(f"Monitoring symbols: {all_symbols}")
    logger.info(f"Minimum profit threshold: {config_loader.config.min_profit_percentage}%")
    logger.info(f"Testnet mode: {testnet}")

    # Start monitoring task for each exchange
    for exchange_id in exchanges:
        # Get symbols for this specific exchange
        exchange_symbols = config_loader.config.get_exchange_symbols(exchange_id)
        tasks.append(data_manager.monitor_exchange_with_retry(exchange_id, exchange_symbols, testnet))

    # Start arbitrage detection task
    tasks.append(arbitrage_detector.detect_arbitrage())

    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
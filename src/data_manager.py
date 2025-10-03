"""
Data management module for collecting, validating, and storing price data from exchanges.
Handles WebSocket and REST API data ingestion with validation and enhancement.
"""

import asyncio
import time
import logging
import collections
import exchange_wrapper

logger = logging.getLogger(__name__)

# Data storage: Dict of deques for recent data (limit to last N entries)
data_store = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.deque(maxlen=100)))  # exchange -> symbol -> deque of (timestamp, data)


def validate_and_enhance_price_data(raw_data, exchange_id, symbol):
    """
    Validate that price data has required fields for arbitrage trading.
    Returns enhanced data if valid, None if invalid.
    """
    if not raw_data:
        logger.info(f"Rejecting empty data for {exchange_id}:{symbol}")
        return None

    # Check required fields
    required_fields = ['bid', 'ask', 'bidVolume', 'askVolume']
    missing_fields = [field for field in required_fields if field not in raw_data or raw_data[field] is None]

    if missing_fields:
        logger.info(f"Rejecting data for {exchange_id}:{symbol} - missing fields: {missing_fields}")
        return None

    # Check for valid bid/ask values
    try:
        bid = float(raw_data['bid'])
        ask = float(raw_data['ask'])
    except (ValueError, TypeError):
        logger.info(f"Rejecting data for {exchange_id}:{symbol} - invalid bid/ask values")
        return None

    if bid <= 0 or ask <= 0 or ask < bid:
        logger.info(f"Rejecting data for {exchange_id}:{symbol} - invalid prices: bid={bid}, ask={ask}")
        return None

    # Convert to float and validate
    try:
        bid_volume = float(raw_data['bidVolume'])
        ask_volume = float(raw_data['askVolume'])
    except (ValueError, TypeError):
        logger.info(f"Rejecting data for {exchange_id}:{symbol} - invalid volume values")
        return None

    if bid_volume <= 0 or ask_volume <= 0:
        logger.info(f"Rejecting data for {exchange_id}:{symbol} - missing/zero volume: bid_vol={bid_volume}, ask_vol={ask_volume}")
        return None

    # Create enhanced data with normalized field names and calculations
    enhanced_data = {}
    enhanced_data['bid'] = bid
    enhanced_data['ask'] = ask
    enhanced_data['bid_volume'] = bid_volume  # Normalize field name
    enhanced_data['ask_volume'] = ask_volume  # Normalize field name

    # Calculate spread percentage
    enhanced_data['spread_pct'] = (ask - bid) / bid * 100

    # Calculate volume score (0-100 based on USD liquidity)
    min_volume_usd = min(bid * bid_volume, ask * ask_volume)
    # Logarithmic scale: $1K=20, $10K=40, $100K=80, $1M=100
    enhanced_data['volume_score'] = min(100, max(0, 20 * (min_volume_usd / 1000) ** 0.3))

    return enhanced_data


def get_tradeable_price(exchange_id, symbol, max_age_seconds, min_volume_usd):
    """Get price data only if fresh and has sufficient volume for trading"""
    if not data_store[exchange_id][symbol]:
        return None

    timestamp, price_data = data_store[exchange_id][symbol][-1]  # O(1) access

    # Staleness check
    age_seconds = time.time() - timestamp
    if age_seconds > max_age_seconds:
        logger.info(f"Stale data for {exchange_id}:{symbol} - age: {age_seconds:.1f}s (max: {max_age_seconds}s)")
        return None

    # Volume check (data is already validated and enhanced)
    min_available_volume = min(
        price_data['bid'] * price_data['bid_volume'],
        price_data['ask'] * price_data['ask_volume']
    )

    #if min_available_volume < min_volume_usd:
    #    logger.info(f"Insufficient volume for {exchange_id}:{symbol} - available: ${min_available_volume:.0f} (min: ${min_volume_usd})")
    #    return None

    return price_data


def get_price_data(exchange_id, symbol):
    """Get the latest price data for a symbol on an exchange (legacy function for compatibility)"""
    import config_loader
    return get_tradeable_price(
        exchange_id,
        symbol,
        config_loader.config.max_age_seconds,
        config_loader.config.min_volume_usd_spatial
    )


async def monitor_websocket(exchange, exchange_id, symbols):
    """Monitor exchange using WebSocket (infinite loop)"""
    while True:
        try:
            tasks = []
            for symbol in symbols:
                tasks.append(exchange.watch_ticker(symbol))
                tasks.append(exchange.watch_order_book(symbol, limit=10))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"WebSocket error on {exchange_id}: {result}")
                    continue

                # Timestamp and store data
                ts = time.time()
                if 'symbol' in result:
                    symbol = result['symbol']
                    # Validate and enhance price data before storing
                    enhanced_data = validate_and_enhance_price_data(result, exchange_id, symbol)
                    if enhanced_data:
                        data_store[exchange_id][symbol].append((ts, enhanced_data))

            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"WebSocket error on {exchange_id}: {e}")
            logger.info(f"Falling back to REST API for {exchange_id}")
            import config_loader
            poll_interval = config_loader.config.get_exchange_poll_interval(exchange_id)
            await poll_exchange_rest_api(exchange, exchange_id, symbols, poll_interval)
            return


async def poll_exchange_rest_api(exchange, exchange_id, symbols, poll_interval_seconds=1.0):
    """Poll exchange using REST API when WebSocket is not supported"""
    logger.info(f"Using REST API polling for {exchange_id} (interval: {poll_interval_seconds}s)")

    while True:
        try:
            for symbol in symbols:
                try:
                    # Fetch ticker data using REST API
                    ticker = await exchange.fetch_ticker(symbol)
                    ts = time.time()
                    # Validate and enhance price data before storing
                    enhanced_data = validate_and_enhance_price_data(ticker, exchange_id, symbol)
                    if enhanced_data:
                        data_store[exchange_id][symbol].append((ts, enhanced_data))
                except Exception as e:
                    logger.error(f"REST API error fetching {symbol} on {exchange_id}: {e}")

                await asyncio.sleep(poll_interval_seconds)  # Poll at configured interval for REST
        except Exception as e:
            logger.error(f"REST API error on {exchange_id}: {e}")
            await asyncio.sleep(5)


async def monitor_exchange_with_retry(exchange_id, symbols, use_testnet, max_retries=5):
    """Monitor exchange with retry logic for network failures"""
    for attempt in range(max_retries):
        try:
            await monitor_exchange(exchange_id, symbols, use_testnet)
            return  # Success, exit retry loop
        except Exception as e:
            wait_time = min(300, (2 ** attempt) * 10)  # Exponential backoff, max 5 minutes
            if attempt < max_retries - 1:
                logger.warning(f"Exchange {exchange_id} failed (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying {exchange_id} in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Exchange {exchange_id} failed permanently after {max_retries} attempts: {e}")
                logger.error(f"Giving up on {exchange_id}")


async def monitor_exchange(exchange_id, symbols, use_testnet):
    """Monitor exchange for price data using WebSocket or REST API polling"""
    wrapper = None
    try:
        logger.info(f"Initializing connection to {exchange_id}...")

        # Create wrapper and initialize exchange
        wrapper = exchange_wrapper.ExchangeWrapper(exchange_id, symbols, use_testnet)
        await wrapper.__aenter__()

        logger.info(f"Successfully connected to {exchange_id}")

        # Only proceed with WebSocket if BOTH are available
        if wrapper.supports_websocket():
            # Use WebSocket with both ticker and orderbook
            await monitor_websocket(wrapper.exchange, exchange_id, symbols)
        else:
            logger.info(f"WebSocket incomplete for {exchange_id} (need both ticker and orderbook), using REST API polling")
            import config_loader
            poll_interval = config_loader.config.get_exchange_poll_interval(exchange_id)
            await poll_exchange_rest_api(wrapper.exchange, exchange_id, symbols, poll_interval)

    except Exception as e:
        # Enhanced error handling with specific error types
        error_msg = str(e)
        if "DNS" in error_msg or "resolve" in error_msg.lower():
            logger.error(f"DNS resolution failed for {exchange_id}: {e}")
            logger.info(f"This is usually a temporary network issue. The system will retry automatically.")
        elif "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
            logger.error(f"SSL/Certificate error for {exchange_id}: {e}")
        elif "timeout" in error_msg.lower():
            logger.error(f"Connection timeout for {exchange_id}: {e}")
        else:
            logger.error(f"Failed to initialize {exchange_id}: {e}")

        # Re-raise to trigger retry logic
        raise
    finally:
        # Ensure exchange is properly closed
        if wrapper:
            try:
                await wrapper.__aexit__(None, None, None)
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup for {exchange_id}: {cleanup_error}")

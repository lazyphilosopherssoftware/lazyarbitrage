"""
Arbitrage detection module for identifying triangular and spatial arbitrage opportunities.
Handles both single-exchange triangular arbitrage and cross-exchange spatial arbitrage.
"""

import asyncio
import logging
import data_manager
import config_loader

logger = logging.getLogger(__name__)


def detect_triangular_arbitrage_single_exchange(exchange_id, symbols, min_profit_percentage):
    """Detect triangular arbitrage opportunities on a single exchange"""
    opportunities = []

    # Get all available tradeable price data for this exchange
    import config_loader
    price_data = {}
    for symbol in symbols:
        data = data_manager.get_tradeable_price(
            exchange_id,
            symbol,
            config_loader.config.max_age_seconds,
            config_loader.config.min_volume_usd_triangular
        )
        if data:  # Data is already validated and enhanced
            price_data[symbol] = data

    # Check for triangular opportunities
    # Example: BTC/USDT -> ETH/BTC -> ETH/USDT -> BTC/USDT
    triangles = [
        ('BTC/USDT', 'ETH/BTC', 'ETH/USDT'),
        # Add more triangles as needed
    ]

    for base_quote, alt_base, alt_quote in triangles:
        if all(pair in price_data for pair in [base_quote, alt_base, alt_quote]):
            # Path: USDT -> BTC -> ETH -> USDT
            # Step 1: Buy BTC with USDT (pay ask price)
            usdt_to_btc_rate = 1 / price_data[base_quote]['ask']  # BTC per USDT

            # Step 2: Buy ETH with BTC (pay ask price)
            btc_to_eth_rate = price_data[alt_base]['ask']  # ETH per BTC

            # Step 3: Sell ETH for USDT (receive bid price)
            eth_to_usdt_rate = price_data[alt_quote]['bid']  # USDT per ETH

            # Calculate final USDT after full cycle starting with 1 USDT
            final_usdt = 1 * usdt_to_btc_rate * btc_to_eth_rate * eth_to_usdt_rate
            profit_percentage = (final_usdt - 1) * 100

            if profit_percentage > min_profit_percentage:
                opportunities.append({
                    'type': 'triangular',
                    'exchange': exchange_id,
                    'path': f'{base_quote} -> {alt_base} -> {alt_quote}',
                    'profit_percentage': profit_percentage,
                    'details': {
                        'step1': f"Buy BTC at {price_data[base_quote]['ask']:.8f}",
                        'step2': f"Buy ETH at {price_data[alt_base]['ask']:.8f}",
                        'step3': f"Sell ETH at {price_data[alt_quote]['bid']:.8f}"
                    }
                })

    return opportunities


def detect_spatial_arbitrage_cross_exchange(symbol, exchanges, min_profit_percentage):
    """Detect spatial arbitrage opportunities across exchanges for a specific symbol"""
    opportunities = []

    # Get tradeable price data from all exchanges for this symbol
    import config_loader
    exchange_prices = {}
    for exchange_id in exchanges:
        data = data_manager.get_tradeable_price(
            exchange_id,
            symbol,
            config_loader.config.max_age_seconds,
            config_loader.config.min_volume_usd_spatial
        )
        if data:  # Data is already validated and enhanced
            exchange_prices[exchange_id] = data

    if len(exchange_prices) < 2:
        return opportunities

    # Find best buy and sell opportunities
    exchanges_list = list(exchange_prices.keys())
    for i, buy_exchange in enumerate(exchanges_list):
        for sell_exchange in exchanges_list[i+1:]:
            buy_price = exchange_prices[buy_exchange]['ask']  # Price we pay to buy
            sell_price = exchange_prices[sell_exchange]['bid']  # Price we receive when selling

            profit_percentage = (sell_price - buy_price) / buy_price * 100

            if profit_percentage > min_profit_percentage:
                opportunities.append({
                    'type': 'spatial',
                    'symbol': symbol,
                    'buy_exchange': buy_exchange,
                    'sell_exchange': sell_exchange,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'profit_percentage': profit_percentage
                })

            # Check reverse direction
            reverse_profit = (buy_price - sell_price) / sell_price * 100
            if reverse_profit > min_profit_percentage:
                opportunities.append({
                    'type': 'spatial',
                    'symbol': symbol,
                    'buy_exchange': sell_exchange,
                    'sell_exchange': buy_exchange,
                    'buy_price': exchange_prices[sell_exchange]['ask'],
                    'sell_price': exchange_prices[buy_exchange]['bid'],
                    'profit_percentage': reverse_profit
                })

    return opportunities


def add_more_triangular_patterns(symbols):
    """
    Generate additional triangular arbitrage patterns based on available symbols.
    This is a placeholder for more sophisticated pattern discovery.
    """
    triangles = [
        ('BTC/USDT', 'ETH/BTC', 'ETH/USDT'),
    ]

    # Add more patterns based on common crypto pairs
    if all(pair in symbols for pair in ['BTC/USDT', 'LTC/BTC', 'LTC/USDT']):
        triangles.append(('BTC/USDT', 'LTC/BTC', 'LTC/USDT'))

    if all(pair in symbols for pair in ['BTC/USDT', 'ADA/BTC', 'ADA/USDT']):
        triangles.append(('BTC/USDT', 'ADA/BTC', 'ADA/USDT'))

    if all(pair in symbols for pair in ['ETH/USDT', 'BTC/ETH', 'BTC/USDT']):
        triangles.append(('ETH/USDT', 'BTC/ETH', 'BTC/USDT'))

    return triangles


async def detect_arbitrage():
    """Main arbitrage detection loop - checks both triangular and spatial opportunities"""
    import config_loader
    all_symbols = config_loader.config.get_all_symbols()
    min_profit_percentage = config_loader.config.min_profit_percentage

    while True:
        exchanges = list(data_manager.data_store.keys())
        all_opportunities = []

        # Detect triangular arbitrage on each exchange
        for exchange_id in exchanges:
            exchange_symbols = [symbol for symbol in all_symbols if data_manager.data_store[exchange_id][symbol]]
            triangular_opps = detect_triangular_arbitrage_single_exchange(
                exchange_id, exchange_symbols, min_profit_percentage
            )
            all_opportunities.extend(triangular_opps)

        # Detect spatial arbitrage across exchanges
        for symbol in all_symbols:
            spatial_opps = detect_spatial_arbitrage_cross_exchange(
                symbol, exchanges, min_profit_percentage
            )
            all_opportunities.extend(spatial_opps)

        # Log opportunities
        for opp in all_opportunities:
            if opp['type'] == 'triangular':
                logger.warning(f"Triangular arbitrage on {opp['exchange']}: {opp['path']} = {opp['profit_percentage']:.2f}%")
                logger.info(f"Steps: {opp['details']['step1']}, {opp['details']['step2']}, {opp['details']['step3']}")
            elif opp['type'] == 'spatial':
                logger.warning(f"Spatial arbitrage {opp['symbol']}: Buy on {opp['buy_exchange']} @ {opp['buy_price']:.8f}, "
                              f"Sell on {opp['sell_exchange']} @ {opp['sell_price']:.8f} = {opp['profit_percentage']:.2f}%")

        await asyncio.sleep(0.05)  # High-frequency check
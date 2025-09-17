import ccxt.pro as ccxt
import asyncio
import os
import logging
import time
import json

# --- Configuration & Logging Setup ---
# Load configuration from file
try:
    with open('exchanges_config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logging.error("exchanges_config.json not found. Please create it from exchanges_config.example.json")
    exit(1)

# Define the trading pairs and the exchanges to monitor.
EXCHANGES = list(config['exchanges'].keys())
SYMBOL = config['symbol']
# Minimum profitable price difference after accounting for all fees.
MIN_PROFIT_PERCENTAGE = config['min_profit_percentage']
TRADE_VOLUME = config['trade_volume']
TRADE_FEE_PERCENTAGE = config['trade_fee_percentage']

# Set up logging for detailed bot activity and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitrage_bot.log"),
        logging.StreamHandler()
    ]
)

# --- Core Bot Logic ---
# Global dictionary to store the latest prices from each exchange
latest_prices = {ex_id: {'bid': None, 'ask': None} for ex_id in EXCHANGES}

async def watch_ticker(exchange, symbol):
    """
    Asynchronously watches the ticker stream for a symbol using WebSockets.
    This function will update the global 'latest_prices' dictionary.
    """
    try:
        while True:
            # The watch_ticker method streams real-time data from the exchange.
            ticker = await exchange.watch_ticker(symbol)
            if ticker:
                latest_prices[exchange.id]['bid'] = ticker['bid']
                latest_prices[exchange.id]['ask'] = ticker['ask']
                logging.info(f"Updated price from {exchange.id}: Bid={ticker['bid']:.4f}, Ask={ticker['ask']:.4f}")

    except ccxt.NetworkError as e:
        logging.error(f"Network error on {exchange.id} stream: {e}")
    except ccxt.ExchangeError as e:
        logging.error(f"Exchange error on {exchange.id} stream: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in {exchange.id} stream: {e}")
    finally:
        await exchange.close()

def check_for_arbitrage():
    """
    Checks for arbitrage opportunities based on the latest prices.
    This is an immediate check that runs whenever a price is updated.
    """
    exchanges_with_prices = [ex_id for ex_id in EXCHANGES if latest_prices[ex_id]['bid'] and latest_prices[ex_id]['ask']]
    
    if len(exchanges_with_prices) < 2:
        return

    # Iterate through all pairs of exchanges to find opportunities
    for i in range(len(exchanges_with_prices)):
        for j in range(i + 1, len(exchanges_with_prices)):
            ex1_id = exchanges_with_prices[i]
            ex2_id = exchanges_with_prices[j]
            
            ex1_data = latest_prices[ex1_id]
            ex2_data = latest_prices[ex2_id]

            # Scenario 1: Buy on ex1, sell on ex2
            buy_price = ex1_data['ask']
            sell_price = ex2_data['bid']
            profit_margin = ((sell_price - buy_price) / buy_price) * 100
            profit_after_fees = profit_margin - (2 * TRADE_FEE_PERCENTAGE * 100) # Subtract fees for both trades

            if profit_after_fees >= MIN_PROFIT_PERCENTAGE:
                logging.info(f"ARBITRAGE OPPORTUNITY DETECTED! Buy {SYMBOL} on {ex1_id} at {buy_price:.4f} and sell on {ex2_id} at {sell_price:.4f}.")
                logging.info(f"Potential Profit (after fees): {profit_after_fees:.4f}%")
                # This is where we'd trigger a trade execution function in a real bot.
                # Since execute_trades() is an async function, we can't call it directly here.
                # In a real bot, we'd use a queue or a separate task to handle this.
                return

            # Scenario 2: Buy on ex2, sell on ex1
            buy_price = ex2_data['ask']
            sell_price = ex1_data['bid']
            profit_margin = ((sell_price - buy_price) / buy_price) * 100
            profit_after_fees = profit_margin - (2 * TRADE_FEE_PERCENTAGE * 100)

            if profit_after_fees >= MIN_PROFIT_PERCENTAGE:
                logging.info(f"ARBITRAGE OPPORTUNITY DETECTED! Buy {SYMBOL} on {ex2_id} at {buy_price:.4f} and sell on {ex1_id} at {sell_price:.4f}.")
                logging.info(f"Potential Profit (after fees): {profit_after_fees:.4f}%")
                # This is where we'd trigger a trade execution.
                return
    
async def execute_trades(buy_exchange, sell_exchange, symbol, volume, buy_price, sell_price):
    """
    Executes the buy and sell orders on the respective exchanges.
    Note: For a millisecond bot, order execution is a complex, separate process
    that must handle latency, partial fills, and more. This function is a simplified example.
    """
    try:
        logging.info(f"Attempting to execute trades...")
        buy_order = await buy_exchange.create_limit_buy_order(symbol, volume, buy_price)
        logging.info(f"Buy order placed on {buy_exchange.id}: {buy_order['id']}")
        
        sell_order = await sell_exchange.create_limit_sell_order(symbol, volume, sell_price)
        logging.info(f"Sell order placed on {sell_exchange.id}: {sell_order['id']}")
        logging.info("Trades placed. Awaiting order fulfillment...")

    except ccxt.InsufficientFunds as e:
        logging.error(f"Trade execution failed due to insufficient funds: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during trade execution: {e}")

async def main():
    """The main entry point for the asynchronous bot."""
    logging.info("Starting crypto arbitrage bot with WebSockets...")
    exchanges = {}
    for ex_id in EXCHANGES:
        exchange_class = getattr(ccxt, ex_id)
        exchanges[ex_id] = exchange_class({
            'apiKey': config['exchanges'][ex_id]['apiKey'],
            'secret': config['exchanges'][ex_id]['secret'],
            'urls': {'api': config['exchanges'][ex_id]['url']},
            'enableRateLimit': True,
        })
    
    # Create tasks to watch the tickers for each exchange
    tasks = [watch_ticker(exchanges[ex_id], SYMBOL) for ex_id in EXCHANGES]
    
    # We will also run a separate task to continuously check for opportunities
    tasks.append(asyncio.create_task(periodic_check()))
    
    await asyncio.gather(*tasks)

async def periodic_check():
    """
    A separate task to continuously check for arbitrage opportunities.
    This runs independently of the WebSocket updates.
    """
    while True:
        check_for_arbitrage()
        # This sleep is now very short since we are event-driven.
        # It ensures the loop doesn't hog the CPU.
        await asyncio.sleep(0.01)


if __name__ == "__main__":
    if not all(config['exchanges'][ex_id]['apiKey'] and config['exchanges'][ex_id]['secret'] for ex_id in EXCHANGES):
        logging.error("Please set your API keys in exchanges_config.json")
        print("Copy exchanges_config.example.json to exchanges_config.json and fill in your API keys and secrets.")
    else:
        asyncio.run(main())

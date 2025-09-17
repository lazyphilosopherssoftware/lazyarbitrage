# Lazy Arbitrage Bot

A cryptocurrency arbitrage bot that monitors price differences between exchanges.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your API keys as environment variables:
```bash
export BINANCE_API_KEY='YOUR_BINANCE_API_KEY'
export BINANCE_API_SECRET='YOUR_BINANCE_API_SECRET'
export KRAKEN_API_KEY='YOUR_KRAKEN_API_KEY'
export KRAKEN_API_SECRET='YOUR_KRAKEN_API_SECRET'
```

5. Run the bot:
```bash
python arbitrage.py
```

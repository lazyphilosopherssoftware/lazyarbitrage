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

4. Copy the config file and input the correct values:
```bash
cp config.example.jsonc config.jsonc
vi config.jsonc
```

5. Run the bot:
```bash
python main.py
```

## Testing

Run tests from the test directory:
```bash
cd test
python run_tests.py
```

See `test/TESTING.md` for detailed testing instructions.

## Features

- Monitors multiple exchanges simultaneously
- Detects triangular arbitrage opportunities
- WebSocket and REST API support

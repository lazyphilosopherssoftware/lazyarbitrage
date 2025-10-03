import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)


class ExchangeWrapper:
    """RAII-style wrapper for CCXT exchanges that automatically closes on destruction"""
    
    def __init__(self, exchange_id, symbols, use_testnet=False):
        self.exchange_id = exchange_id
        self.symbols = symbols
        self.use_testnet = use_testnet
        self.exchange = None
        self._closed = False
    
    async def __aenter__(self):
        """Async context manager entry - equivalent to constructor"""
        self.exchange = getattr(ccxt, self.exchange_id)()
        
        # Check if testnet/sandbox mode is requested and supported
        if self.use_testnet:
            if hasattr(self.exchange, 'set_sandbox_mode') and 'test' in self.exchange.urls:
                self.exchange.set_sandbox_mode(True)
                logger.info(f"Enabled sandbox mode for {self.exchange_id}")
            else:
                logger.error(f"Exchange {self.exchange_id} does not support sandbox mode.")
                raise ValueError(f"Exchange {self.exchange_id} does not support sandbox mode")
        
        await self.exchange.load_markets()
        return self  # Return self instead of exchange
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - equivalent to destructor"""
        if self.exchange and not self._closed:
            logger.info(f"Closing exchange {self.exchange_id}")
            await self.exchange.close()
            self._closed = True
    
    def __del__(self):
        """Fallback destructor (though __aexit__ should handle most cases)"""
        if self.exchange and hasattr(self.exchange, 'close') and not self._closed:
            # Note: This is synchronous, so it's just a fallback
            logger.warning(f"Exchange {self.exchange_id} was not properly closed")
    
    def get_websocket_support(self):
        """Check which WebSocket methods are supported for the exchange"""
        if not self.exchange:
            return {'ticker': False, 'orderbook': False}
        
        return {
            'ticker': self.exchange.has.get('watchTicker', False),
            'orderbook': self.exchange.has.get('watchOrderBook', False)
        }
    
    def supports_websocket(self):
        """Check if exchange supports both ticker and orderbook WebSocket methods"""
        support = self.get_websocket_support()
        return support['ticker'] and support['orderbook']
    
    def get_symbols(self):
        """Get the symbols this wrapper is monitoring"""
        return self.symbols
    
    def get_exchange_id(self):
        """Get the exchange ID"""
        return self.exchange_id

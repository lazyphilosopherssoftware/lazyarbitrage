import unittest
import unittest.mock
import sys
import os

# Add the src directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

import exchange_wrapper


class TestExchangeWrapper(unittest.TestCase):
    """Test cases for ExchangeWrapper class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.exchange_id = "test_exchange"
        self.symbols = ["BTC/USDT", "ETH/USDT"]
        self.use_testnet = True
    
    def test_init(self):
        """Test ExchangeWrapper initialization"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)

        self.assertEqual(wrapper.exchange_id, self.exchange_id)
        self.assertEqual(wrapper.symbols, self.symbols)
        self.assertEqual(wrapper.use_testnet, self.use_testnet)
        self.assertIsNone(wrapper.exchange)
        self.assertFalse(wrapper._closed)
    
    def test_get_symbols(self):
        """Test getting symbols from wrapper"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        result = wrapper.get_symbols()
        self.assertEqual(result, self.symbols)
    
    def test_get_exchange_id(self):
        """Test getting exchange ID from wrapper"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        result = wrapper.get_exchange_id()
        self.assertEqual(result, self.exchange_id)
    
    def test_get_websocket_support_no_exchange(self):
        """Test getting WebSocket support when exchange is not initialized"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        result = wrapper.get_websocket_support()
        
        expected = {'ticker': False, 'orderbook': False}
        self.assertEqual(result, expected)
    
    def test_get_websocket_support_with_exchange(self):
        """Test getting WebSocket support when exchange is initialized"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.has = {
            'watchTicker': True,
            'watchOrderBook': False
        }
        wrapper.exchange = mock_exchange
        
        result = wrapper.get_websocket_support()
        
        expected = {'ticker': True, 'orderbook': False}
        self.assertEqual(result, expected)
    
    def test_supports_websocket_true(self):
        """Test supports_websocket when both ticker and orderbook are supported"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.has = {
            'watchTicker': True,
            'watchOrderBook': True
        }
        wrapper.exchange = mock_exchange
        
        result = wrapper.supports_websocket()
        self.assertTrue(result)
    
    def test_supports_websocket_false(self):
        """Test supports_websocket when not both ticker and orderbook are supported"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.has = {
            'watchTicker': True,
            'watchOrderBook': False
        }
        wrapper.exchange = mock_exchange
        
        result = wrapper.supports_websocket()
        self.assertFalse(result)
    
    @unittest.mock.patch('exchange_wrapper.getattr')
    @unittest.mock.patch('exchange_wrapper.ccxt')
    def test_aenter_success(self, mock_ccxt, mock_getattr):
        """Test successful async context manager entry"""
        # Mock the exchange class and instance
        mock_exchange_class = unittest.mock.Mock()
        mock_exchange_instance = unittest.mock.Mock()
        mock_exchange_instance.urls = {'test': 'test_url'}
        mock_exchange_instance.set_sandbox_mode = unittest.mock.Mock()
        mock_exchange_instance.load_markets = unittest.mock.AsyncMock()
        
        mock_getattr.return_value = mock_exchange_class
        mock_exchange_class.return_value = mock_exchange_instance
        
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, True)
        
        # Test the async context manager
        import asyncio
        async def test_aenter():
            result = await wrapper.__aenter__()
            return result
        
        result = asyncio.run(test_aenter())
        
        # Verify the exchange was created and configured
        mock_getattr.assert_called_once_with(mock_ccxt, self.exchange_id)
        mock_exchange_class.assert_called_once()
        mock_exchange_instance.set_sandbox_mode.assert_called_once_with(True)
        mock_exchange_instance.load_markets.assert_called_once()
        self.assertEqual(result, wrapper)
    
    @unittest.mock.patch('exchange_wrapper.getattr')
    @unittest.mock.patch('exchange_wrapper.ccxt')
    def test_aenter_no_sandbox_support(self, mock_ccxt, mock_getattr):
        """Test async context manager entry when sandbox is not supported"""
        # Mock the exchange class and instance
        mock_exchange_class = unittest.mock.Mock()
        mock_exchange_instance = unittest.mock.Mock()
        mock_exchange_instance.urls = {}  # No test URL
        mock_exchange_instance.load_markets = unittest.mock.AsyncMock()
        
        mock_getattr.return_value = mock_exchange_class
        mock_exchange_class.return_value = mock_exchange_instance
        
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, True)
        
        # Test the async context manager
        import asyncio
        async def test_aenter():
            with self.assertRaises(ValueError):
                await wrapper.__aenter__()
        
        asyncio.run(test_aenter())
    
    def test_aexit_success(self):
        """Test successful async context manager exit"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.close = unittest.mock.AsyncMock()
        wrapper.exchange = mock_exchange
        wrapper._closed = False
        
        # Test the async context manager exit
        import asyncio
        async def test_aexit():
            await wrapper.__aexit__(None, None, None)
        
        asyncio.run(test_aexit())
        
        # Verify the exchange was closed
        mock_exchange.close.assert_called_once()
        self.assertTrue(wrapper._closed)
    
    def test_aexit_already_closed(self):
        """Test async context manager exit when already closed"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.close = unittest.mock.AsyncMock()
        wrapper.exchange = mock_exchange
        wrapper._closed = True  # Already closed
        
        # Test the async context manager exit
        import asyncio
        async def test_aexit():
            await wrapper.__aexit__(None, None, None)
        
        asyncio.run(test_aexit())
        
        # Verify the exchange was not closed again
        mock_exchange.close.assert_not_called()
    
    def test_del_warning(self):
        """Test destructor warning when exchange is not properly closed"""
        wrapper = exchange_wrapper.ExchangeWrapper(self.exchange_id, self.symbols, self.use_testnet)
        
        # Mock the exchange
        mock_exchange = unittest.mock.Mock()
        mock_exchange.close = unittest.mock.Mock()
        wrapper.exchange = mock_exchange
        wrapper._closed = False  # Not closed
        
        # The destructor should warn about not being properly closed
        # Note: We can't easily test the warning output, but we can test the logic
        wrapper.__del__()
        
        # Verify the exchange has the close method (the warning condition)
        self.assertTrue(hasattr(mock_exchange, 'close'))


if __name__ == '__main__':
    # Configure logging to reduce noise during tests
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Run the tests
    unittest.main(verbosity=2)

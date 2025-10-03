import unittest
import unittest.mock
import asyncio
import sys
import os

# Add the src directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)


class TestArbitrage(unittest.TestCase):
    """Test cases for arbitrage module"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.valid_config_data = {
            "exchanges": {
                "kraken": {
                    "symbols": ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
                },
                "bitfinex": {
                    "symbols": ["BTC/USDT", "ETH/USDT"]
                }
            },
            "min_profit_percentage": 0.5,
            "testnet": True,
            "max_age_seconds": 5,
            "min_volume_usd": {
                "triangular": 5000,
                "spatial": 10000
            }
        }

        # Clear module cache to ensure clean state
        modules_to_clear = ['arbitrage', 'data_manager', 'arbitrage_detector']
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

    @unittest.mock.patch('config_loader.config.load')
    @unittest.mock.patch('config_loader.config._config_data')
    @unittest.mock.patch('data_manager.monitor_exchange_with_retry')
    @unittest.mock.patch('arbitrage_detector.detect_arbitrage')
    def test_main_starts_all_tasks(
        self,
        mock_detect_arbitrage,
        mock_monitor_exchange,
        mock_config_data,
        mock_config_load
    ):
        """Test that main() starts monitoring tasks for all exchanges and arbitrage detection"""
        # Setup config data
        mock_config_data.__getitem__.side_effect = self.valid_config_data.__getitem__
        mock_config_data.__contains__.side_effect = self.valid_config_data.__contains__
        mock_config_data.get = self.valid_config_data.get

        # Create async mock coroutines that complete quickly
        async def mock_monitor_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_detect_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        mock_monitor_exchange.side_effect = [mock_monitor_coro(), mock_monitor_coro()]
        mock_detect_arbitrage.return_value = mock_detect_coro()

        # Import and run main
        import arbitrage

        # Run main with a timeout to prevent hanging
        async def run_with_timeout():
            try:
                await asyncio.wait_for(arbitrage.main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # Must time out since tasks run indefinitely

        asyncio.run(run_with_timeout())

        # Verify monitoring was started for each exchange (2 exchanges)
        self.assertEqual(mock_monitor_exchange.call_count, 2)

        # Verify monitor_exchange_with_retry was called with correct arguments
        calls = mock_monitor_exchange.call_args_list
        call_args = [(call[0][0], set(call[0][1]), call[0][2]) for call in calls]

        # Verify testnet was passed correctly
        for call in call_args:
            self.assertIn(call[0], ["kraken", "bitfinex"])  # Check that kraken and bitfinex were both called
            self.assertTrue(call[2])  # testnet should be True

        # Verify arbitrage detection was started
        mock_detect_arbitrage.assert_called_once()

    @unittest.mock.patch('config_loader.config.load')
    @unittest.mock.patch('config_loader.config._config_data')
    @unittest.mock.patch('data_manager.monitor_exchange_with_retry')
    @unittest.mock.patch('arbitrage_detector.detect_arbitrage')
    def test_main_with_single_exchange(
        self,
        mock_detect_arbitrage,
        mock_monitor_exchange,
        mock_config_data,
        mock_config_load
    ):
        """Test that main() works with a single exchange"""
        # Setup config data with single exchange
        single_exchange_config = {
            "exchanges": {
                "kraken": {
                    "symbols": ["BTC/USDT"]
                }
            },
            "min_profit_percentage": 1.0,
            "testnet": False,
            "max_age_seconds": 5,
            "min_volume_usd": {
                "triangular": 5000,
                "spatial": 10000
            }
        }

        mock_config_data.__getitem__.side_effect = single_exchange_config.__getitem__
        mock_config_data.__contains__.side_effect = single_exchange_config.__contains__
        mock_config_data.get = single_exchange_config.get

        # Create async mock coroutines
        async def mock_monitor_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_detect_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        mock_monitor_exchange.return_value = mock_monitor_coro()
        mock_detect_arbitrage.return_value = mock_detect_coro()

        # Import and run main
        import arbitrage

        # Run main with a timeout
        async def run_with_timeout():
            try:
                await asyncio.wait_for(arbitrage.main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

        asyncio.run(run_with_timeout())

        # Verify monitoring was started for single exchange
        self.assertEqual(mock_monitor_exchange.call_count, 1)
        mock_monitor_exchange.assert_called_with("kraken", ["BTC/USDT"], False)

        # Verify arbitrage detection was started
        mock_detect_arbitrage.assert_called_once()

    @unittest.mock.patch('config_loader.config.load')
    @unittest.mock.patch('config_loader.config._config_data')
    @unittest.mock.patch('data_manager.monitor_exchange_with_retry')
    @unittest.mock.patch('arbitrage_detector.detect_arbitrage')
    def test_main_testnet_disabled(
        self,
        mock_detect_arbitrage,
        mock_monitor_exchange,
        mock_config_data,
        mock_config_load
    ):
        """Test that main() passes testnet=False when testnet is disabled"""
        # Setup config data with testnet disabled
        testnet_disabled_config = {
            "exchanges": {
                "kraken": {
                    "symbols": ["BTC/USDT"]
                }
            },
            "min_profit_percentage": 0.5,
            "testnet": False,
            "max_age_seconds": 5,
            "min_volume_usd": {
                "triangular": 5000,
                "spatial": 10000
            }
        }

        mock_config_data.__getitem__.side_effect = testnet_disabled_config.__getitem__
        mock_config_data.__contains__.side_effect = testnet_disabled_config.__contains__
        mock_config_data.get = testnet_disabled_config.get

        # Create async mock coroutines
        async def mock_monitor_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_detect_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        mock_monitor_exchange.return_value = mock_monitor_coro()
        mock_detect_arbitrage.return_value = mock_detect_coro()

        # Import and run main
        import arbitrage

        # Run main with a timeout
        async def run_with_timeout():
            try:
                await asyncio.wait_for(arbitrage.main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

        asyncio.run(run_with_timeout())

        # Verify testnet=False was passed
        mock_monitor_exchange.assert_called_with("kraken", ["BTC/USDT"], False)

    @unittest.mock.patch('config_loader.config.load')
    @unittest.mock.patch('config_loader.config._config_data')
    @unittest.mock.patch('data_manager.monitor_exchange_with_retry')
    @unittest.mock.patch('arbitrage_detector.detect_arbitrage')
    def test_main_no_exchanges(
        self,
        mock_detect_arbitrage,
        mock_monitor_exchange,
        mock_config_data,
        mock_config_load
    ):
        """Test that main() handles empty exchange list"""
        # Setup config data with no exchanges
        no_exchange_config = {
            "exchanges": {},
            "min_profit_percentage": 0.5,
            "testnet": True,
            "max_age_seconds": 5,
            "min_volume_usd": {
                "triangular": 5000,
                "spatial": 10000
            }
        }

        mock_config_data.__getitem__.side_effect = no_exchange_config.__getitem__
        mock_config_data.__contains__.side_effect = no_exchange_config.__contains__
        mock_config_data.get = no_exchange_config.get

        # Create async mock coroutine
        async def mock_detect_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        mock_detect_arbitrage.return_value = mock_detect_coro()

        # Import and run main
        import arbitrage

        # Run main with a timeout
        async def run_with_timeout():
            try:
                await asyncio.wait_for(arbitrage.main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

        asyncio.run(run_with_timeout())

        # Verify no monitoring tasks were started
        mock_monitor_exchange.assert_not_called()

        # Verify arbitrage detection was still started
        mock_detect_arbitrage.assert_called_once()

    @unittest.mock.patch('config_loader.jsonc_parser.parser.JsoncParser.parse_file')
    def test_module_imports_successfully(self, mock_parse_file):
        """Test that the arbitrage module can be imported"""
        # Mock the config loading
        mock_parse_file.return_value = self.valid_config_data

        # Import should not raise an exception
        try:
            import arbitrage
            self.assertIsNotNone(arbitrage)
        except Exception as e:
            self.fail(f"Module import failed: {e}")

    @unittest.mock.patch('config_loader.config._config_data')
    @unittest.mock.patch('data_manager.monitor_exchange_with_retry')
    @unittest.mock.patch('arbitrage_detector.detect_arbitrage')
    @unittest.mock.patch('logging.Logger.info')
    def test_main_logs_startup_info(
        self,
        mock_log_info,
        mock_detect_arbitrage,
        mock_monitor_exchange,
        mock_config_data
    ):
        """Test that main() logs startup information"""
        # Setup config data
        mock_config_data.__getitem__.side_effect = self.valid_config_data.__getitem__
        mock_config_data.__contains__.side_effect = self.valid_config_data.__contains__
        mock_config_data.get = self.valid_config_data.get

        # Create async mock coroutines
        async def mock_monitor_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_detect_coro(*args, **kwargs):
            await asyncio.sleep(0.01)

        mock_monitor_exchange.side_effect = [mock_monitor_coro(), mock_monitor_coro()]
        mock_detect_arbitrage.return_value = mock_detect_coro()

        # Import and run main
        import arbitrage

        # Run main with a timeout
        async def run_with_timeout():
            try:
                await asyncio.wait_for(arbitrage.main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

        asyncio.run(run_with_timeout())

        # Verify logging calls were made
        log_calls = mock_log_info.call_args_list
        log_messages = [str(call[0][0]) if call[0] else "" for call in log_calls]

        # Check for key log messages
        self.assertTrue(
            any("Starting arbitrage bot" in msg for msg in log_messages),
            f"Expected 'Starting arbitrage bot' in log messages: {log_messages}"
        )
        self.assertTrue(
            any("Monitoring symbols" in msg for msg in log_messages),
            f"Expected 'Monitoring symbols' in log messages: {log_messages}"
        )
        self.assertTrue(
            any("Minimum profit threshold" in msg for msg in log_messages),
            f"Expected 'Minimum profit threshold' in log messages: {log_messages}"
        )
        self.assertTrue(
            any("Testnet mode" in msg for msg in log_messages),
            f"Expected 'Testnet mode' in log messages: {log_messages}"
        )


if __name__ == '__main__':
    # Configure logging to reduce noise during tests
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)

    # Run the tests
    unittest.main(verbosity=2)

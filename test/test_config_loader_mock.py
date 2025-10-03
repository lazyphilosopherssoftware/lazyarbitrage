import unittest
import sys
import os
import unittest.mock

# Add the src directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)


class TestConfigLoaderMock(unittest.TestCase):
    """Test cases for config_loader module using mocks"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.valid_config = {
            "exchanges": {
                "kraken": {
                    "symbols": ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
                },
                "bitfinex": {
                    "symbols": ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
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
    
    @unittest.mock.patch('config_loader.jsonc_parser.parser.JsoncParser.parse_file')
    def test_load_config_success(self, mock_parse_file):
        """Test successful config loading with mocked JsoncParser"""
        # Mock the JsoncParser.parse_file static method
        mock_parse_file.return_value = self.valid_config

        # Import here to avoid module loading issues
        import config_loader

        result = config_loader.load_config("test.jsonc")
        self.assertEqual(result, self.valid_config)
        mock_parse_file.assert_called_once_with("test.jsonc")
    
    @unittest.mock.patch('config_loader.jsonc_parser.parser.JsoncParser.parse_file')
    def test_load_config_file_not_found(self, mock_parse_file):
        """Test config loading when file doesn't exist"""
        # Mock the JsoncParser.parse_file method to raise FileNotFoundError
        mock_parse_file.side_effect = FileNotFoundError("File not found")

        # Import here to avoid module loading issues
        import config_loader

        with self.assertRaises(SystemExit):
            config_loader.load_config("nonexistent.jsonc")
    
    @unittest.mock.patch('config_loader.jsonc_parser.parser.JsoncParser.parse_file')
    def test_load_config_invalid_json(self, mock_parse_file):
        """Test config loading with invalid JSON"""
        import json

        # Mock the JsoncParser.parse_file method to raise JSONDecodeError
        mock_parse_file.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        # Import here to avoid module loading issues
        import config_loader

        with self.assertRaises(SystemExit):
            config_loader.load_config("invalid.jsonc")
    
    def test_validate_config_success(self):
        """Test successful config validation"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.validate_config(self.valid_config)
        self.assertTrue(result)
    
    def test_validate_config_missing_exchanges(self):
        """Test config validation with missing exchanges key"""
        invalid_config = {
            "min_profit_percentage": 0.5,
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_missing_min_profit(self):
        """Test config validation with missing min_profit_percentage key"""
        invalid_config = {
            "exchanges": {
                "kraken": {"symbols": ["BTC/USDT"]}
            },
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_missing_testnet(self):
        """Test config validation with missing testnet key"""
        invalid_config = {
            "exchanges": {
                "kraken": {"symbols": ["BTC/USDT"]}
            },
            "min_profit_percentage": 0.5
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_exchanges_not_dict(self):
        """Test config validation when exchanges is not a dictionary"""
        invalid_config = {
            "exchanges": "not_a_dict",
            "min_profit_percentage": 0.5,
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_exchange_missing_symbols(self):
        """Test config validation when exchange is missing symbols"""
        invalid_config = {
            "exchanges": {
                "kraken": {}  # Missing symbols
            },
            "min_profit_percentage": 0.5,
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_symbols_not_list(self):
        """Test config validation when symbols is not a list"""
        invalid_config = {
            "exchanges": {
                "kraken": {"symbols": "not_a_list"}
            },
            "min_profit_percentage": 0.5,
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_min_profit_not_number(self):
        """Test config validation when min_profit_percentage is not a number"""
        invalid_config = {
            "exchanges": {
                "kraken": {"symbols": ["BTC/USDT"]}
            },
            "min_profit_percentage": "not_a_number",
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_testnet_not_boolean(self):
        """Test config validation when testnet is not a boolean"""
        invalid_config = {
            "exchanges": {
                "kraken": {"symbols": ["BTC/USDT"]}
            },
            "min_profit_percentage": 0.5,
            "testnet": "not_a_boolean"
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        with self.assertRaises(SystemExit):
            config_loader.validate_config(invalid_config)
    
    def test_get_exchange_ids(self):
        """Test getting exchange IDs from config"""
        # Import here to avoid module loading issues
        import config_loader

        result = config_loader.get_exchange_ids(self.valid_config)
        expected = ["kraken", "bitfinex"]
        self.assertEqual(set(result), set(expected))  # Order doesn't matter
    
    def test_get_all_symbols(self):
        """Test getting all unique symbols from config"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.get_all_symbols(self.valid_config)
        expected = ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
        self.assertEqual(set(result), set(expected))  # Order doesn't matter
    
    def test_get_all_symbols_with_duplicates(self):
        """Test getting all symbols when exchanges have overlapping symbols"""
        config_with_duplicates = {
            "exchanges": {
                "exchange1": {"symbols": ["BTC/USDT", "ETH/USDT"]},
                "exchange2": {"symbols": ["ETH/USDT", "ETH/BTC"]}
            },
            "min_profit_percentage": 0.5,
            "testnet": True
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.get_all_symbols(config_with_duplicates)
        expected = ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
        self.assertEqual(set(result), set(expected))
        self.assertEqual(len(result), 3)  # No duplicates
    
    def test_get_exchange_symbols(self):
        """Test getting symbols for a specific exchange"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.get_exchange_symbols(self.valid_config, "kraken")
        expected = ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
        self.assertEqual(result, expected)
    
    def test_get_exchange_symbols_nonexistent(self):
        """Test getting symbols for non-existent exchange"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.get_exchange_symbols(self.valid_config, "nonexistent")
        self.assertIsNone(result)
    
    def test_get_min_profit_percentage(self):
        """Test getting minimum profit percentage"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.get_min_profit_percentage(self.valid_config)
        self.assertEqual(result, 0.5)
    
    def test_get_min_profit_percentage_missing(self):
        """Test getting minimum profit percentage when missing (should raise KeyError)"""
        config_without_min_profit = {
            "exchanges": {"kraken": {"symbols": ["BTC/USDT"]}},
            "testnet": True
        }

        # Import here to avoid module loading issues
        import config_loader

        with self.assertRaises(KeyError):
            config_loader.get_min_profit_percentage(config_without_min_profit)
    
    def test_is_testnet_enabled(self):
        """Test checking if testnet is enabled"""
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.is_testnet_enabled(self.valid_config)
        self.assertTrue(result)
    
    def test_is_testnet_enabled_false(self):
        """Test checking when testnet is disabled"""
        config_with_testnet_false = {
            "exchanges": {"kraken": {"symbols": ["BTC/USDT"]}},
            "min_profit_percentage": 0.5,
            "testnet": False
        }
        
        # Import here to avoid module loading issues
        import config_loader
        
        result = config_loader.is_testnet_enabled(config_with_testnet_false)
        self.assertFalse(result)
    
    def test_is_testnet_enabled_missing(self):
        """Test checking testnet when missing (should raise KeyError)"""
        config_without_testnet = {
            "exchanges": {"kraken": {"symbols": ["BTC/USDT"]}},
            "min_profit_percentage": 0.5
        }

        # Import here to avoid module loading issues
        import config_loader

        with self.assertRaises(KeyError):
            config_loader.is_testnet_enabled(config_without_testnet)

    def test_get_exchange_poll_interval(self):
        """Test getting poll interval for a specific exchange"""
        import config_loader

        result = config_loader.get_exchange_poll_interval(self.valid_config, "kraken")
        self.assertEqual(result, 1.0)  # Default value

    def test_get_exchange_poll_interval_custom(self):
        """Test getting custom poll interval for a specific exchange"""
        config_with_custom_poll = {
            "exchanges": {
                "binance": {
                    "symbols": ["BTC/USDT"],
                    "poll_interval_seconds": 0.5
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

        import config_loader

        result = config_loader.get_exchange_poll_interval(config_with_custom_poll, "binance")
        self.assertEqual(result, 0.5)

    def test_get_exchange_poll_interval_nonexistent(self):
        """Test getting poll interval for non-existent exchange returns default"""
        import config_loader

        result = config_loader.get_exchange_poll_interval(self.valid_config, "nonexistent")
        self.assertEqual(result, 1.0)  # Default value


if __name__ == '__main__':
    # Configure logging to reduce noise during tests
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Run the tests
    unittest.main(verbosity=2)

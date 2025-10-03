import sys
import logging
import jsonc_parser.parser

logger = logging.getLogger(__name__)


class Config:
    """Global configuration singleton"""
    _instance = None
    _config_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def load(self, config_path='config.jsonc'):
        """Load configuration from JSONC file"""
        try:
            self._config_data = jsonc_parser.parser.JsoncParser.parse_file(config_path)
            logger.info(f"Configuration loaded successfully from {config_path}")
            self._validate()
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.error("Aborting program.")
            sys.exit(1)

    def _validate(self):
        """Validate that the configuration has the required structure"""
        if not self._config_data:
            raise ValueError("No configuration data loaded")

        required_keys = ['exchanges', 'min_profit_percentage', 'testnet', 'max_age_seconds', 'min_volume_usd']

        for key in required_keys:
            if key not in self._config_data:
                logger.error(f"Missing required configuration key: {key}")
                sys.exit(1)

        # Validate exchanges structure
        if not isinstance(self._config_data['exchanges'], dict):
            logger.error("'exchanges' must be a dictionary")
            sys.exit(1)

        for exchange_id, exchange_config in self._config_data['exchanges'].items():
            if 'symbols' not in exchange_config:
                logger.error(f"Exchange '{exchange_id}' missing 'symbols' key")
                sys.exit(1)

            if not isinstance(exchange_config['symbols'], list):
                logger.error(f"Exchange '{exchange_id}' symbols must be a list")
                sys.exit(1)

        # Validate numeric values
        if not isinstance(self._config_data['min_profit_percentage'], (int, float)):
            logger.error("'min_profit_percentage' must be a number")
            sys.exit(1)

        if not isinstance(self._config_data['testnet'], bool):
            logger.error("'testnet' must be a boolean")
            sys.exit(1)

        # Validate max_age_seconds
        if not isinstance(self._config_data['max_age_seconds'], (int, float)) or self._config_data['max_age_seconds'] <= 0:
            logger.error("'max_age_seconds' must be a positive number")
            sys.exit(1)

        # Validate min_volume_usd structure
        if not isinstance(self._config_data['min_volume_usd'], dict):
            logger.error("'min_volume_usd' must be a dictionary")
            sys.exit(1)

        required_volume_keys = ['triangular', 'spatial']
        for key in required_volume_keys:
            if key not in self._config_data['min_volume_usd']:
                logger.error(f"Missing required min_volume_usd key: {key}")
                sys.exit(1)

            if not isinstance(self._config_data['min_volume_usd'][key], (int, float)) or self._config_data['min_volume_usd'][key] <= 0:
                logger.error(f"'min_volume_usd.{key}' must be a positive number")
                sys.exit(1)

        logger.info("Configuration validation passed")

    @property
    def exchanges(self):
        """Get exchanges configuration"""
        return self._config_data['exchanges']

    @property
    def exchange_ids(self):
        """Get list of exchange IDs"""
        return list(self._config_data['exchanges'].keys())

    @property
    def min_profit_percentage(self):
        """Get minimum profit percentage"""
        return self._config_data['min_profit_percentage']

    @property
    def testnet_enabled(self):
        """Check if testnet mode is enabled"""
        return self._config_data['testnet']

    @property
    def max_age_seconds(self):
        """Get maximum age for price data in seconds"""
        return self._config_data['max_age_seconds']

    @property
    def min_volume_usd_triangular(self):
        """Get minimum volume for triangular arbitrage in USD"""
        return self._config_data['min_volume_usd']['triangular']

    @property
    def min_volume_usd_spatial(self):
        """Get minimum volume for spatial arbitrage in USD"""
        return self._config_data['min_volume_usd']['spatial']

    def get_exchange_symbols(self, exchange_id):
        """Get symbols for a specific exchange"""
        return self._config_data['exchanges'].get(exchange_id, {}).get('symbols')

    def get_exchange_poll_interval(self, exchange_id):
        """Get poll interval for a specific exchange in seconds (default: 1.0)"""
        return self._config_data['exchanges'].get(exchange_id, {}).get('poll_interval_seconds', 1.0)

    def get_all_symbols(self):
        """Get all unique symbols from all exchanges"""
        symbols = set()
        for exchange_config in self._config_data['exchanges'].values():
            symbols.update(exchange_config['symbols'])
        return list(symbols)


# Global config instance
config = Config()


def load_config(config_path='config.jsonc'):
    """Load configuration from JSONC file (JSON with comments)"""
    try:
        config = jsonc_parser.parser.JsoncParser.parse_file(config_path)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        logger.error("Aborting program.")
        sys.exit(1)


def validate_config(config):
    """Validate that the configuration has the required structure"""
    required_keys = ['exchanges', 'min_profit_percentage', 'testnet', 'max_age_seconds', 'min_volume_usd']
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration key: {key}")
            sys.exit(1)
    
    # Validate exchanges structure
    if not isinstance(config['exchanges'], dict):
        logger.error("'exchanges' must be a dictionary")
        sys.exit(1)
    
    for exchange_id, exchange_config in config['exchanges'].items():
        if 'symbols' not in exchange_config:
            logger.error(f"Exchange '{exchange_id}' missing 'symbols' key")
            sys.exit(1)

        if not isinstance(exchange_config['symbols'], list):
            logger.error(f"Exchange '{exchange_id}' symbols must be a list")
            sys.exit(1)
    
    # Validate numeric values
    if not isinstance(config['min_profit_percentage'], (int, float)):
        logger.error("'min_profit_percentage' must be a number")
        sys.exit(1)
    
    if not isinstance(config['testnet'], bool):
        logger.error("'testnet' must be a boolean")
        sys.exit(1)

    # Validate max_age_seconds
    if not isinstance(config['max_age_seconds'], (int, float)) or config['max_age_seconds'] <= 0:
        logger.error("'max_age_seconds' must be a positive number")
        sys.exit(1)

    # Validate min_volume_usd structure
    if not isinstance(config['min_volume_usd'], dict):
        logger.error("'min_volume_usd' must be a dictionary")
        sys.exit(1)

    required_volume_keys = ['triangular', 'spatial']
    for key in required_volume_keys:
        if key not in config['min_volume_usd']:
            logger.error(f"Missing required min_volume_usd key: {key}")
            sys.exit(1)

        if not isinstance(config['min_volume_usd'][key], (int, float)) or config['min_volume_usd'][key] <= 0:
            logger.error(f"'min_volume_usd.{key}' must be a positive number")
            sys.exit(1)

    logger.info("Configuration validation passed")
    return True


def get_exchange_ids(config):
    """Get list of exchange IDs from config"""
    return list(config['exchanges'].keys())


def get_all_symbols(config):
    """Get all unique symbols from all exchanges"""
    symbols = set()
    for exchange_config in config['exchanges'].values():
        symbols.update(exchange_config['symbols'])
    return list(symbols)


def get_exchange_symbols(config, exchange_id):
    """Get symbols for a specific exchange"""
    return config['exchanges'].get(exchange_id, {}).get('symbols')


def get_exchange_poll_interval(config, exchange_id):
    """Get poll interval for a specific exchange in seconds (default: 1.0)"""
    return config['exchanges'].get(exchange_id, {}).get('poll_interval_seconds', 1.0)


def get_min_profit_percentage(config):
    """Get minimum profit percentage from config"""
    return config['min_profit_percentage']


def is_testnet_enabled(config):
    """Check if testnet mode is enabled"""
    return config['testnet']


def get_max_age_seconds(config):
    """Get maximum age for price data in seconds"""
    return config['max_age_seconds']


def get_min_volume_usd_triangular(config):
    """Get minimum volume for triangular arbitrage in USD"""
    return config['min_volume_usd']['triangular']


def get_min_volume_usd_spatial(config):
    """Get minimum volume for spatial arbitrage in USD"""
    return config['min_volume_usd']['spatial']

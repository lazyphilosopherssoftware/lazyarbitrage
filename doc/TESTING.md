# Testing Guide

This document explains how to run tests for the arbitrage bot project.

## Running Tests

All tests use Python's built-in unittest module. Run commands from the project root:

```bash
# Run all tests
python -m unittest discover -s test -p "test_*.py" -v

# Run specific test file
python -m unittest test.test_config_loader_mock -v
python -m unittest test.test_exchange_wrapper -v
python -m unittest test.test_simple -v

# Run specific test class
python -m unittest test.test_config_loader_mock.TestConfigLoader -v

# Run specific test method
python -m unittest test.test_config_loader_mock.TestConfigLoader.test_load_config_success -v
```

## Adding New Tests

When adding new functionality, follow these guidelines:

1. **Test File Naming**: Use `test_*.py` pattern
2. **Test Class Naming**: Use `Test*` pattern
3. **Test Method Naming**: Use `test_*` pattern
4. **Test Organization**: Group related tests in the same class
5. **Mocking**: Use `unittest.mock` for external dependencies
6. **Async Tests**: Use `asyncio.run()` for testing async functions

### Example Test Structure

```python
import unittest
from unittest.mock import Mock, patch

class TestMyModule(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method"""
        pass

    def test_success_case(self):
        """Test successful operation"""
        # Arrange
        # Act
        # Assert
        pass

    def test_error_case(self):
        """Test error handling"""
        # Arrange
        # Act & Assert
        with self.assertRaises(ValueError):
            # Code that should raise ValueError
            pass
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run all tests with exit code
python -m unittest discover -s test -p "test_*.py"
```

The command returns exit code 0 for success, 1 for failure.
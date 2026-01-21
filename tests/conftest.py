"""
Pytest fixtures for MT5-Docker testing

This module provides common fixtures for unit and integration tests,
including mocked ZMQ sockets and test data.
"""

import json
import pytest
import zmq
from unittest.mock import MagicMock
from pathlib import Path


# Test configuration constants
HOST = "localhost"
SYSTEM_PORT = 2201
DATA_PORT = 2202
LIVE_PORT = 2203
STREAM_PORT = 2204


@pytest.fixture
def mock_zmq_context(mocker):
    """
    Mock ZMQ Context for unit tests.

    Returns a mocked context that creates mock sockets.
    """
    mock_context = MagicMock(spec=zmq.Context)
    mock_socket = MagicMock(spec=zmq.Socket)
    mock_context.socket.return_value = mock_socket
    return mock_context


@pytest.fixture
def mock_zmq_socket(mocker):
    """
    Mock ZMQ Socket for unit tests.

    Returns a configured mock socket with common methods.
    """
    mock_socket = MagicMock(spec=zmq.Socket)
    mock_socket.send_string = MagicMock()
    mock_socket.recv_string = MagicMock(return_value='{"status": "ok"}')
    mock_socket.connect = MagicMock()
    mock_socket.close = MagicMock()
    mock_socket.setsockopt = MagicMock()
    return mock_socket


@pytest.fixture
def mock_system_socket(mock_zmq_socket):
    """Mock System socket (REQ) - for sending commands"""
    mock_zmq_socket.recv_string.return_value = '{"status": "ok", "action": "received"}'
    return mock_zmq_socket


@pytest.fixture
def mock_data_socket(mock_zmq_socket):
    """Mock Data socket (PULL) - for receiving command responses"""
    mock_zmq_socket.recv_string.return_value = json.dumps({
        "error": False,
        "description": "Success",
        "data": {}
    })
    return mock_zmq_socket


@pytest.fixture
def mock_live_socket(mock_zmq_socket):
    """Mock Live socket (PULL) - for receiving live price data"""
    mock_zmq_socket.recv_string.return_value = json.dumps({
        "symbol": "EURUSD",
        "bid": 1.0850,
        "ask": 1.0852,
        "time": "2025-01-13 10:00:00"
    })
    return mock_zmq_socket


@pytest.fixture
def mock_stream_socket(mock_zmq_socket):
    """Mock Stream socket (PULL) - for receiving trade events"""
    mock_zmq_socket.recv_string.return_value = json.dumps({
        "event": "trade",
        "ticket": 12345,
        "type": "buy",
        "volume": 0.1
    })
    return mock_zmq_socket


@pytest.fixture
def sample_account_response():
    """Sample account info response"""
    return {
        "error": False,
        "description": "Success",
        "data": {
            "login": 12345678,
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "margin_free": 10000.0,
            "margin_level": 0.0,
            "profit": 0.0,
            "currency": "USD",
            "leverage": 100,
            "server": "Demo-Server",
            "company": "Demo Company"
        }
    }


@pytest.fixture
def sample_balance_response():
    """Sample balance response"""
    return {
        "error": False,
        "description": "Success",
        "data": {
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "margin_free": 10000.0,
            "margin_level": 0.0,
            "profit": 0.0
        }
    }


@pytest.fixture
def sample_symbol_info_response():
    """Sample symbol info response"""
    return {
        "error": False,
        "description": "Success",
        "data": {
            "symbol": "EURUSD",
            "digits": 5,
            "point": 0.00001,
            "spread": 2,
            "trade_contract_size": 100000.0,
            "trade_mode": 4,
            "volume_min": 0.01,
            "volume_max": 500.0,
            "volume_step": 0.01,
            "currency_base": "EUR",
            "currency_profit": "USD",
            "currency_margin": "EUR",
            "swap_long": -0.8,
            "swap_short": 0.2,
            "swap_mode": 0
        }
    }


@pytest.fixture
def sample_rates_response():
    """Sample historical rates response"""
    return {
        "error": False,
        "description": "Success",
        "data": [
            {
                "time": "2025-01-13 09:00:00",
                "open": 1.0850,
                "high": 1.0860,
                "low": 1.0845,
                "close": 1.0855,
                "tick_volume": 150,
                "spread": 2,
                "real_volume": 0
            },
            {
                "time": "2025-01-13 10:00:00",
                "open": 1.0855,
                "high": 1.0870,
                "low": 1.0850,
                "close": 1.0865,
                "tick_volume": 200,
                "spread": 2,
                "real_volume": 0
            }
        ]
    }


@pytest.fixture
def sample_trade_response():
    """Sample trade execution response"""
    return {
        "error": False,
        "description": "Success",
        "data": {
            "ticket": 12345678,
            "retcode": 10009,
            "deal": 12345679,
            "order": 12345680,
            "volume": 0.1,
            "price": 1.0855,
            "comment": "Trade executed successfully"
        }
    }


@pytest.fixture
def sample_error_response():
    """Sample error response"""
    return {
        "error": True,
        "description": "Invalid symbol",
        "error_code": 4301
    }


@pytest.fixture
def response_samples_dir():
    """Path to response samples directory"""
    return Path(__file__).parent.parent / "data" / "response_samples"


@pytest.fixture
def load_response_sample(response_samples_dir):
    """
    Factory fixture to load response samples from JSON files.

    Usage:
        def test_something(load_response_sample):
            account_data = load_response_sample("account_response.json")
    """
    def _load(filename):
        file_path = response_samples_dir / filename
        if not file_path.exists():
            pytest.skip(f"Response sample not found: {filename}")
        with open(file_path, "r") as f:
            return json.load(f)
    return _load


@pytest.fixture(scope="session")
def integration_test_config():
    """
    Configuration for integration tests.

    Override these values via environment variables for CI/CD:
    - MT5_HOST
    - MT5_SYSTEM_PORT
    - MT5_DATA_PORT
    - MT5_LIVE_PORT
    - MT5_STREAM_PORT
    """
    import os
    return {
        "host": os.getenv("MT5_HOST", "localhost"),
        "system_port": int(os.getenv("MT5_SYSTEM_PORT", SYSTEM_PORT)),
        "data_port": int(os.getenv("MT5_DATA_PORT", DATA_PORT)),
        "live_port": int(os.getenv("MT5_LIVE_PORT", LIVE_PORT)),
        "stream_port": int(os.getenv("MT5_STREAM_PORT", STREAM_PORT)),
    }


@pytest.fixture
def skip_if_no_mt5(integration_test_config):
    """
    Skip integration tests if MT5 is not available.

    Attempts to connect to MT5 system socket. If connection fails,
    the test is skipped.
    """
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 1000)
    socket.setsockopt(zmq.SNDTIMEO, 1000)

    try:
        socket.connect(f"tcp://{integration_test_config['host']}:{integration_test_config['system_port']}")
        socket.send_string('{"action": "PING"}')
        socket.recv_string()
        socket.close()
        context.term()
    except zmq.Again:
        socket.close()
        context.term()
        pytest.skip("MT5 server not available")
    except Exception as e:
        socket.close()
        context.term()
        pytest.skip(f"Cannot connect to MT5: {e}")


# Pytest configuration hooks
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require MT5 connection)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 5 seconds)"
    )
    config.addinivalue_line(
        "markers", "streaming: Tests that involve live data streaming"
    )

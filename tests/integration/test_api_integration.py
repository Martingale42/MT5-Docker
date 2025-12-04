"""
Integration tests for MT5 JsonAPI ZeroMQ connectivity

These tests require a running MT5 instance with JsonAPI Expert Advisor.
Run with: pytest -m integration
"""

import pytest
import time
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from zmq_client import JsonAPIClient


@pytest.fixture(scope="module")
def mt5_client(integration_test_config, skip_if_no_mt5):
    """
    Fixture that creates and yields an MT5 client connection.

    Scope: module - reuse same connection for all tests in this module.
    """
    client = JsonAPIClient(
        host=integration_test_config["host"],
        system_port=integration_test_config["system_port"],
        data_port=integration_test_config["data_port"],
        live_port=integration_test_config["live_port"],
        stream_port=integration_test_config["stream_port"],
        verbose=False
    )
    yield client
    client.close()


@pytest.mark.integration
class TestBasicConnectivity:
    """Test basic connectivity and account operations"""

    def test_get_account_information(self, mt5_client):
        """Test retrieving account information"""
        # Send command
        ack = mt5_client.send_command("ACCOUNT")
        assert ack is not None, "No ACK received from system socket"

        # Receive response
        time.sleep(0.5)
        data = mt5_client.receive_data()

        # Assertions
        assert data is not None, "No data received"
        assert not data.get("error", True), f"Error in response: {data.get('description')}"
        assert "data" in data, "Missing 'data' field in response"

        # Validate account data structure
        account_data = data["data"]
        required_fields = ["login", "balance", "equity", "currency", "leverage"]
        for field in required_fields:
            assert field in account_data, f"Missing required field: {field}"

        # Validate data types
        assert isinstance(account_data["login"], int), "login should be integer"
        assert isinstance(account_data["balance"], (int, float)), "balance should be numeric"
        assert isinstance(account_data["equity"], (int, float)), "equity should be numeric"

    def test_get_balance(self, mt5_client):
        """Test retrieving account balance"""
        ack = mt5_client.send_command("BALANCE")
        assert ack is not None

        time.sleep(0.5)
        data = mt5_client.receive_data()

        assert data is not None
        assert not data.get("error", True)
        assert "data" in data

        balance_data = data["data"]
        assert "balance" in balance_data
        assert "equity" in balance_data
        assert isinstance(balance_data["balance"], (int, float))


@pytest.mark.integration
class TestSymbolConfiguration:
    """Test symbol configuration and subscription"""

    def test_configure_symbol(self, mt5_client):
        """Test configuring a symbol for streaming"""
        ack = mt5_client.send_command(
            "CONFIG",
            actionType="CONFIG",
            symbol="XAUUSD.sml",
            chartTF="M1"
        )
        assert ack is not None

        time.sleep(0.5)
        data = mt5_client.receive_data()

        assert data is not None
        assert not data.get("error", True), f"Error configuring symbol: {data.get('description')}"


@pytest.mark.integration
class TestMarketData:
    """Test historical market data retrieval"""

    def test_get_historical_bars(self, mt5_client):
        """Test retrieving historical OHLC bar data"""
        # Get data from 7 days ago to now
        from_date = int(time.time()) - (7 * 24 * 60 * 60)

        ack = mt5_client.send_command(
            "HISTORY",
            actionType="DATA",
            symbol="XAUUSD.sml",
            chartTF="M1",
            fromDate=from_date,
            toDate=int(time.time())
        )
        assert ack is not None

        time.sleep(1)
        data = mt5_client.receive_data()

        assert data is not None
        assert not data.get("error", True), f"Error getting market data: {data.get('description')}"
        assert "data" in data
        assert isinstance(data["data"], list), "Market data should be a list"
        assert len(data["data"]) > 0, "Should receive at least one bar"

        # Validate bar structure
        if len(data["data"]) > 0:
            bar = data["data"][0]
            expected_fields = ["time", "open", "high", "low", "close", "tick_volume"]
            for field in expected_fields:
                assert field in bar, f"Missing field in bar: {field}"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.streaming
class TestLiveStreaming:
    """Test live price streaming (requires time to wait for updates)"""

    def test_live_bar_stream(self, mt5_client):
        """Test subscribing to live M1 bar updates"""
        # Configure symbol for live streaming
        mt5_client.send_command("CONFIG", actionType="CONFIG", symbol="XAUUSD.sml", chartTF="M1")
        time.sleep(1)
        mt5_client.receive_data()  # Drain configuration response

        # Listen for live prices
        # M1 bars update every 60 seconds, so we wait 70 seconds
        count = 0
        start_time = time.time()
        max_wait = 70

        while time.time() - start_time < max_wait:
            data = mt5_client.receive_live()
            if data:
                count += 1

                # Validate live data structure
                assert "symbol" in data
                assert "timeframe" in data
                assert "data" in data

                bar_data = data.get("data", [])
                if isinstance(bar_data, list) and len(bar_data) >= 6:
                    # Bar data: [time, open, high, low, close, volume, ...]
                    assert len(bar_data) >= 6, "Bar data should have at least 6 elements"

                # If we got at least one update, test passes
                # (No need to wait full 70 seconds in CI)
                if count >= 1:
                    break

        # Note: This test may fail if run during low market activity
        # or if timing doesn't align with bar close
        assert count > 0, "Should receive at least one live price update"

    def test_tick_stream(self, mt5_client):
        """Test subscribing to real-time tick stream (bid/ask)"""
        # Configure symbol for tick streaming
        mt5_client.send_command("CONFIG", actionType="CONFIG", symbol="BTCUSD", chartTF="TICK")
        time.sleep(1)
        mt5_client.receive_data()  # Drain configuration response

        # Listen for tick data
        count = 0
        start_time = time.time()
        max_wait = 15  # 15 seconds

        while time.time() - start_time < max_wait:
            data = mt5_client.receive_live()
            if data:
                count += 1

                # Validate tick data structure
                assert "symbol" in data
                assert "data" in data

                tick_data = data.get("data", [])
                if isinstance(tick_data, list) and len(tick_data) >= 3:
                    # Tick data: [time_ms, bid, ask, ...]
                    time_ms, bid, ask = tick_data[0], tick_data[1], tick_data[2]
                    assert isinstance(time_ms, (int, float))
                    assert isinstance(bid, (int, float))
                    assert isinstance(ask, (int, float))
                    assert ask >= bid, "Ask should be >= Bid"

                # If we got some tick updates, test passes
                if count >= 3:
                    break

        # Note: This test may fail if market is closed or low activity
        assert count > 0, "Should receive at least one tick update"


@pytest.mark.integration
class TestEconomicCalendar:
    """Test economic calendar data retrieval"""

    def test_get_calendar_data(self, mt5_client):
        """Test retrieving economic calendar events"""
        # Get calendar data for last 3 days
        from_date = int(time.time()) - (3 * 24 * 60 * 60)

        ack = mt5_client.send_command(
            "CALENDAR",
            actionType="DATA",
            symbol="XAUUSD.sml",
            fromDate=from_date
        )
        assert ack is not None

        time.sleep(1)
        data = mt5_client.receive_data(timeout_ms=10000)  # Longer timeout for calendar

        assert data is not None

        # Calendar data may be empty if no events in date range
        # So we just check for valid response structure
        if not data.get("error", False):
            if "data" in data:
                assert isinstance(data["data"], list), "Calendar data should be a list"
        else:
            # If error, just log it (calendar API may not be available on all accounts)
            pytest.skip(f"Calendar data not available: {data.get('description')}")


@pytest.mark.integration
class TestSymbolInfo:
    """Test symbol information retrieval"""

    def test_get_single_symbol_info(self, mt5_client):
        """Test retrieving information for a single symbol"""
        ack = mt5_client.send_command(
            "SYMBOL_INFO",
            symbol="EURUSD"
        )
        assert ack is not None

        time.sleep(0.5)
        data = mt5_client.receive_data()

        assert data is not None
        assert not data.get("error", True), f"Error getting symbol info: {data.get('description')}"
        assert "data" in data

        symbol_data = data["data"]
        # Should return data for single symbol
        if isinstance(symbol_data, dict):
            assert "symbol" in symbol_data
            assert "digits" in symbol_data
        elif isinstance(symbol_data, list):
            assert len(symbol_data) > 0
            assert "symbol" in symbol_data[0]

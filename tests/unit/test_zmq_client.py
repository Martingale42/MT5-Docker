"""
Unit tests for JsonAPIClient

Tests the ZMQ client logic without requiring MT5 connection.
"""

import pytest
import json
import zmq
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from zmq_client import JsonAPIClient


@pytest.mark.unit
class TestJsonAPIClientInit:
    """Test client initialization"""

    @patch('zmq.Context')
    def test_client_initialization_default_ports(self, mock_context_class):
        """Test client initializes with default ports"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        client = JsonAPIClient(host="testhost", verbose=False)

        # Verify context created
        mock_context_class.assert_called_once()

        # Verify 4 sockets created
        assert mock_context.socket.call_count == 4

        # Verify socket connections
        calls = mock_socket.connect.call_args_list
        assert len(calls) == 4
        assert calls[0][0][0] == "tcp://testhost:2201"  # System port
        assert calls[1][0][0] == "tcp://testhost:2202"  # Data port
        assert calls[2][0][0] == "tcp://testhost:2203"  # Live port
        assert calls[3][0][0] == "tcp://testhost:2204"  # Stream port

    @patch('zmq.Context')
    def test_client_initialization_custom_ports(self, mock_context_class):
        """Test client initializes with custom ports"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        client = JsonAPIClient(
            host="customhost",
            system_port=3001,
            data_port=3002,
            live_port=3003,
            stream_port=3004,
            verbose=False
        )

        calls = mock_socket.connect.call_args_list
        assert calls[0][0][0] == "tcp://customhost:3001"
        assert calls[1][0][0] == "tcp://customhost:3002"
        assert calls[2][0][0] == "tcp://customhost:3003"
        assert calls[3][0][0] == "tcp://customhost:3004"

    @patch('zmq.Context')
    def test_client_sets_socket_timeouts(self, mock_context_class):
        """Test that socket timeouts are configured"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        client = JsonAPIClient(host="testhost", verbose=False)

        # Verify setsockopt called for timeouts
        assert mock_socket.setsockopt.call_count >= 4


@pytest.mark.unit
class TestJsonAPIClientCommands:
    """Test sending commands"""

    @patch('zmq.Context')
    def test_send_command_basic(self, mock_context_class):
        """Test sending a basic command"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        # Mock system socket response
        mock_socket.recv_string.return_value = '{"status": "ok"}'

        client = JsonAPIClient(host="testhost", verbose=False)
        response = client.send_command("ACCOUNT")

        # Verify command sent
        mock_socket.send_string.assert_called()
        sent_message = mock_socket.send_string.call_args[0][0]
        sent_data = json.loads(sent_message)

        assert sent_data["action"] == "ACCOUNT"
        assert response == '{"status": "ok"}'

    @patch('zmq.Context')
    def test_send_command_with_parameters(self, mock_context_class):
        """Test sending command with additional parameters"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket
        mock_socket.recv_string.return_value = '{"status": "ok"}'

        client = JsonAPIClient(host="testhost", verbose=False)
        client.send_command("CONFIG", symbol="EURUSD", chartTF="M1")

        sent_message = mock_socket.send_string.call_args[0][0]
        sent_data = json.loads(sent_message)

        assert sent_data["action"] == "CONFIG"
        assert sent_data["symbol"] == "EURUSD"
        assert sent_data["chartTF"] == "M1"

    @patch('zmq.Context')
    def test_send_command_timeout(self, mock_context_class):
        """Test handling timeout when sending command"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        # Simulate timeout
        mock_socket.recv_string.side_effect = zmq.Again()

        client = JsonAPIClient(host="testhost", verbose=False)
        response = client.send_command("ACCOUNT")

        assert response is None


@pytest.mark.unit
class TestJsonAPIClientReceive:
    """Test receiving data"""

    @patch('zmq.Context')
    def test_receive_data_success(self, mock_context_class):
        """Test successfully receiving data"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        response_data = {"error": False, "data": {"balance": 10000}}
        mock_socket.recv_string.return_value = json.dumps(response_data)

        client = JsonAPIClient(host="testhost", verbose=False)
        data = client.receive_data()

        assert data is not None
        assert data["error"] is False
        assert data["data"]["balance"] == 10000

    @patch('zmq.Context')
    def test_receive_data_timeout(self, mock_context_class):
        """Test handling timeout when receiving data"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        mock_socket.recv_string.side_effect = zmq.Again()

        client = JsonAPIClient(host="testhost", verbose=False)
        data = client.receive_data()

        assert data is None

    @patch('zmq.Context')
    def test_receive_data_invalid_json(self, mock_context_class):
        """Test handling invalid JSON response"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        mock_socket.recv_string.return_value = "invalid json {"

        client = JsonAPIClient(host="testhost", verbose=False)
        data = client.receive_data()

        assert data is not None
        assert data["error"] is True
        assert "JSON decode error" in data["description"]

    @patch('zmq.Context')
    def test_receive_live_success(self, mock_context_class):
        """Test receiving live price data"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        live_data = {"symbol": "EURUSD", "data": [1234567890, 1.0850, 1.0852]}
        mock_socket.recv_string.return_value = json.dumps(live_data)

        client = JsonAPIClient(host="testhost", verbose=False)
        data = client.receive_live()

        assert data is not None
        assert data["symbol"] == "EURUSD"
        assert len(data["data"]) == 3

    @patch('zmq.Context')
    def test_receive_stream_success(self, mock_context_class):
        """Test receiving trade stream data"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        stream_data = {"event": "trade", "ticket": 12345}
        mock_socket.recv_string.return_value = json.dumps(stream_data)

        client = JsonAPIClient(host="testhost", verbose=False)
        data = client.receive_stream()

        assert data is not None
        assert data["event"] == "trade"
        assert data["ticket"] == 12345


@pytest.mark.unit
class TestJsonAPIClientContextManager:
    """Test context manager functionality"""

    @patch('zmq.Context')
    def test_context_manager_closes_sockets(self, mock_context_class):
        """Test that context manager properly closes sockets"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        with JsonAPIClient(host="testhost", verbose=False) as client:
            pass

        # Verify all sockets closed
        assert mock_socket.close.call_count == 4
        # Verify context terminated
        mock_context.term.assert_called_once()

    @patch('zmq.Context')
    def test_manual_close(self, mock_context_class):
        """Test manual close method"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        client = JsonAPIClient(host="testhost", verbose=False)
        client.close()

        assert mock_socket.close.call_count == 4
        mock_context.term.assert_called_once()


@pytest.mark.unit
class TestJsonAPIClientVerboseMode:
    """Test verbose logging"""

    @patch('zmq.Context')
    @patch('builtins.print')
    def test_verbose_mode_prints_messages(self, mock_print, mock_context_class):
        """Test that verbose mode prints debug messages"""
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_context_class.return_value = mock_context
        mock_context.socket.return_value = mock_socket
        mock_socket.recv_string.return_value = '{"status": "ok"}'

        client = JsonAPIClient(host="testhost", verbose=True)

        # Check that connection messages were printed
        assert mock_print.call_count >= 4  # At least one print per socket

        # Send command and check it prints
        mock_print.reset_mock()
        client.send_command("ACCOUNT")

        # Should print sending message and ACK
        assert mock_print.call_count >= 1

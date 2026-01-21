# MT5-Docker Development Guide

## Project Overview

MetaTrader 5 running in Docker with JsonAPI Expert Advisor for ZeroMQ-based algorithmic trading. Python 3.13+, pytest, ruff for linting.

## Quick Reference

```bash
# Run tests
uv run pytest                           # All tests
uv run pytest tests/unit/               # Unit tests only (no MT5 needed)
uv run pytest -m integration            # Integration tests (MT5 required)

# Lint and format
uv run ruff check scripts/ tests/       # Lint
uv run ruff format scripts/ tests/      # Format

# Docker
docker compose up mt5zmq                # Trading service only
docker compose up                       # Full stack with monitoring
```

## Architecture

### ZeroMQ 4-Socket Design

| Socket | Port | Pattern   | Purpose                    |
|--------|------|-----------|----------------------------|
| System | 2201 | REQ/REP   | Commands and acknowledgments |
| Data   | 2202 | PUSH/PULL | Command responses          |
| Live   | 2203 | PUSH/PULL | Real-time price updates    |
| Stream | 2204 | PUSH/PULL | Trade events               |

**Why 4 sockets?** Separates command/response flow from live data streams. Prevents blocking - a slow command response doesn't delay price updates.

### Response Format

All API responses follow this structure:
```json
{
  "error": false,
  "description": "Success message",
  "data": { ... }
}
```
**Always check the `error` field before processing `data`.**

## Code Conventions

### Python Style

- **Type hints**: Required on all functions
- **Docstrings**: Google format with Args, Returns, Raises
- **Error handling**: Catch specific exceptions, include context in messages
- **Imports**: Standard library → third-party → local (ruff handles ordering)

### Testing

- **Unit tests** (`tests/unit/`): Mock ZeroMQ sockets, no external dependencies
- **Integration tests** (`tests/integration/`): Require running MT5 container
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.streaming`
- **Coverage**: 70% minimum required

Add response samples to `data/response_samples/` when testing new API endpoints.

### Naming

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Key Files

| Path | Purpose |
|------|---------|
| `src/mt5_jsonapi/client.py` | Core JsonAPIClient implementation |
| `src/mt5_jsonapi/__init__.py` | Package exports |
| `tests/conftest.py` | Test fixtures and mocks |
| `data/response_samples/` | JSON samples for testing |
| `docs/` | API guides (TRADE_GUIDE.md, HIST_DATA_GUIDE.md, etc.) |

## Common Patterns

### Using JsonAPIClient

```python
from mt5_jsonapi import JsonAPIClient

with JsonAPIClient(host="localhost", timeout=5000) as client:
    # Send command and get acknowledgment
    ack = client.send_command({"action": "CONFIG"})
    if ack.get("error"):
        raise RuntimeError(ack.get("description"))

    # Receive actual response data
    response = client.receive_data(timeout=10000)
    if response and not response.get("error"):
        process(response["data"])
```

### Adding Tests

```python
# Unit test - mock everything
@pytest.mark.unit
def test_client_timeout(mock_zmq_context):
    mock_zmq_context.socket.return_value.recv.side_effect = zmq.Again()
    with JsonAPIClient() as client:
        result = client.receive_data(timeout=100)
    assert result is None

# Integration test - needs MT5
@pytest.mark.integration
def test_account_info(integration_client):
    response = integration_client.send_command({"action": "ACCOUNT"})
    assert not response.get("error")
```

## Do Not

- **Hardcode credentials** - Use environment variables or `.env`
- **Block on live sockets** - Use appropriate timeouts
- **Skip `error` field checks** - API errors return valid JSON with `"error": true`
- **Mix socket concerns** - Each socket has a specific purpose
- **Commit without tests** - New API features need both unit and integration tests

## Troubleshooting

| Issue | Check |
|-------|-------|
| Connection timeout | Is MT5 container running? VNC accessible? |
| `zmq.Again` exception | Normal for timeouts - handle gracefully |
| JSON decode error | Log raw message for debugging, check MT5 EA logs |
| Integration tests skipped | Set env vars: `MT5_HOST`, `MT5_SYSTEM_PORT`, etc. |

## Documentation

Keep `docs/` guides synchronized with code changes. Each API endpoint should have corresponding documentation and response samples.

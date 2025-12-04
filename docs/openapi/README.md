# MT5-Docker OpenAPI Documentation

This directory contains the OpenAPI 3.0 specification and Swagger UI for the MT5-Docker JsonAPI.

## Files

- **mt5-api-spec.yaml** - OpenAPI 3.0 specification defining all API endpoints
- **index.html** - Swagger UI interface for interactive API documentation

## Viewing the Documentation

### Option 1: Docker Compose (Recommended)

Start the Swagger UI service:

```bash
docker-compose --profile docs up swagger-ui
```

Then open your browser to: http://localhost:8080

This will display the interactive Swagger UI where you can:
- Browse all API endpoints
- See request/response schemas
- View examples
- Try out API calls (if MT5 is running)

### Option 2: Local Python Server

If you have Python installed, you can serve the documentation locally:

```bash
cd docs/openapi
python3 -m http.server 8000
```

Then open: http://localhost:8000

### Option 3: Direct File Access

You can also open `index.html` directly in your browser, but you may encounter CORS issues
when loading the YAML spec.

## Validating the Specification

To validate the OpenAPI spec for correctness:

```bash
# Install validator
pip install openapi-spec-validator

# Run validation
python3 scripts/validate_openapi.py
```

## API Overview

The MT5-Docker JsonAPI uses a multi-socket ZeroMQ architecture:

- **Port 2201** - System Socket (REQ/REP) - Send commands, receive ACK
- **Port 2202** - Data Socket (PUSH/PULL) - Receive command responses
- **Port 2203** - Live Socket (PUSH/PULL) - Receive live price streams
- **Port 2204** - Stream Socket (PUSH/PULL) - Receive trade confirmations

## Available Endpoints

- `/account` - Get account information
- `/balance` - Get account balance
- `/config` - Subscribe to symbol data
- `/history/bars` - Get historical OHLC data
- `/history/ticks` - Get historical tick data
- `/positions` - Get open positions
- `/orders` - Get pending orders
- `/trade` - Submit trading orders
- `/symbol-info` - Get symbol specifications
- `/calendar` - Get economic calendar

## Integration Examples

### Python with ZeroMQ

```python
from scripts.zmq_client import JsonAPIClient

# Connect to MT5
client = JsonAPIClient(host="localhost")

# Get account info
client.send_command("ACCOUNT")
data = client.receive_data()
print(data)

# Close connection
client.close()
```

See `tests/integration/test_api_integration.py` for more examples.

## Generating Client SDKs

You can use the OpenAPI spec to generate client libraries in various languages:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate \
  -i docs/openapi/mt5-api-spec.yaml \
  -g python \
  -o generated/python-client

# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/openapi/mt5-api-spec.yaml \
  -g typescript-axios \
  -o generated/typescript-client
```

## Contributing

If you find errors or omissions in the API documentation:

1. Update `mt5-api-spec.yaml`
2. Run validation: `python3 scripts/validate_openapi.py`
3. Test in Swagger UI
4. Submit a pull request

## Resources

- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [MT5 Documentation](https://www.mql5.com/en/docs)

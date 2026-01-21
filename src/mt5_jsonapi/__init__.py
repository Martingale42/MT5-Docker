"""
MT5 JsonAPI - Python client for MetaTrader 5 JsonAPI Expert Advisor.

Example usage:
    from mt5_jsonapi import JsonAPIClient

    with JsonAPIClient(host="localhost") as client:
        client.send_command("ACCOUNT")
        data = client.receive_data()
        print(data)
"""

from mt5_jsonapi.client import JsonAPIClient

__all__ = ["JsonAPIClient"]
__version__ = "0.1.0"

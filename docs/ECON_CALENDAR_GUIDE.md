# Economic Calendar API Guide

## Overview

MT5 JsonAPI provides access to the economic calendar, which contains scheduled economic events, news releases, and indicators that can impact market prices. This is useful for avoiding trading during high-impact news or for event-driven trading strategies.

## Command: CALENDAR

The `CALENDAR` action retrieves economic calendar events for a date range, optionally filtered by symbol currencies.

### Request Format

```python
{
    "action": "CALENDAR",
    "actionType": "DATA",
    "symbol": "EURUSD",       # Optional: filter by symbol currencies
    "fromDate": 1699900800,   # Unix timestamp (required)
    "toDate": 1700000000      # Unix timestamp (optional, defaults to now)
}
```

---

## Basic Usage

### Get All Economic Events

Retrieve all economic calendar events for a date range (all currencies).

**Request:**
```python
import zmq
import json
import time

context = zmq.Context()

# System socket
system_socket = context.socket(zmq.REQ)
system_socket.connect("tcp://localhost:2201")
system_socket.setsockopt(zmq.RCVTIMEO, 5000)

# Data socket
data_socket = context.socket(zmq.PULL)
data_socket.connect("tcp://localhost:2202")
data_socket.setsockopt(zmq.RCVTIMEO, 10000)

# Get calendar events for the last 7 days
from_date = int(time.time()) - (7 * 24 * 60 * 60)
to_date = int(time.time())

command = {
    "action": "CALENDAR",
    "actionType": "DATA",
    "fromDate": from_date,
    "toDate": to_date
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()  # "OK"

# Receive calendar data
response = data_socket.recv_string()
calendar = json.loads(response)
print(calendar)
```

**Response Format:**
```json
{
  "data": [
    [
      "2025.11.03 16:45",              // [0] Date/time
      "USD",                           // [1] Currency
      "3",                             // [2] Importance (1=low, 2=med, 3=high)
      "S&P Global Manufacturing PMI",  // [3] Event name
      "United States(US)",             // [4] Country
      "52.5",                          // [5] Actual value
      "52.3",                          // [6] Forecast value
      "52.1"                           // [7] Previous value
    ],
    [
      "2025.11.04 08:30",
      "EUR",
      "2",
      "Retail Sales m/m",
      "Germany(DE)",
      "0.5",
      "0.3",
      "0.2"
    ],
    ...
  ]
}
```

### Get Events for Specific Symbol

Filter calendar events by the currencies of a trading symbol.

**Request:**
```python
# Get events for EURUSD (filters to EUR and USD events only)
command = {
    "action": "CALENDAR",
    "actionType": "DATA",
    "symbol": "EURUSD",        # ← Filters to EUR and USD currencies
    "fromDate": from_date,
    "toDate": to_date
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
calendar = json.loads(response)
```

This will only return events for:
- Base currency (EUR in EURUSD)
- Profit currency (USD in EURUSD)

**Example symbols:**
- `EURUSD` → EUR and USD events
- `GBPJPY` → GBP and JPY events
- `XAUUSD.sml` → XAU and USD events (gold)
- `BTCUSD` → BTC and USD events

---

## Event Data Structure

Each calendar event is an array with 8 elements:

| Index | Field | Type | Description |
|-------|-------|------|-------------|
| 0 | DateTime | string | Event date and time (format: "YYYY.MM.DD HH:MM") |
| 1 | Currency | string | Currency code (USD, EUR, GBP, etc.) |
| 2 | Importance | string | Impact level: "1" (low), "2" (medium), "3" (high) |
| 3 | Event Name | string | Economic indicator or event name |
| 4 | Country | string | Country name and code |
| 5 | Actual | string | Actual released value (null if not released yet) |
| 6 | Forecast | string | Forecasted value (null if not available) |
| 7 | Previous | string | Previous period value (null if not available) |

**Note:** Values may be `null` (Python `None`) if not available or not yet released.

---

## Complete Example: Calendar Monitor

```python
#!/usr/bin/env python3
"""
Economic Calendar Monitor
Displays upcoming high-impact economic events
"""
import zmq
import json
import time
from datetime import datetime, timedelta

class EconomicCalendar:
    def __init__(self, host="localhost"):
        self.context = zmq.Context()

        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:2201")
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)

        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:2202")
        self.data_socket.setsockopt(zmq.RCVTIMEO, 10000)

    def get_events(self, symbol=None, days_back=7, days_forward=7):
        """
        Get economic calendar events

        Args:
            symbol: Optional symbol to filter by currencies (e.g., "EURUSD")
            days_back: How many days in the past to retrieve
            days_forward: How many days in the future to retrieve
        """
        from_date = int(time.time()) - (days_back * 24 * 60 * 60)
        to_date = int(time.time()) + (days_forward * 24 * 60 * 60)

        command = {
            "action": "CALENDAR",
            "actionType": "DATA",
            "fromDate": from_date,
            "toDate": to_date
        }

        if symbol:
            command["symbol"] = symbol

        self.system_socket.send_string(json.dumps(command))
        ack = self.system_socket.recv_string()

        try:
            response = self.data_socket.recv_string()
            return json.loads(response)
        except zmq.Again:
            print("Timeout retrieving calendar data")
            return {"data": []}

    def parse_event(self, event_array):
        """Parse event array into dictionary"""
        if not event_array or len(event_array) < 8:
            return None

        return {
            "datetime": event_array[0],
            "currency": event_array[1],
            "importance": int(event_array[2]) if event_array[2] else 0,
            "event_name": event_array[3],
            "country": event_array[4],
            "actual": event_array[5],
            "forecast": event_array[6],
            "previous": event_array[7]
        }

    def display_events(self, symbol=None, min_importance=2, upcoming_only=True):
        """
        Display calendar events in formatted table

        Args:
            symbol: Filter by symbol currencies
            min_importance: Minimum importance level (1-3)
            upcoming_only: Show only future events
        """
        calendar_data = self.get_events(symbol=symbol)
        events = calendar_data.get("data", [])

        if not events:
            print("No calendar events found")
            return

        # Parse and filter events
        parsed_events = []
        now = datetime.now()

        for event_array in events:
            event = self.parse_event(event_array)
            if not event:
                continue

            # Parse event datetime
            try:
                event_time = datetime.strptime(event["datetime"], "%Y.%m.%d %H:%M")
            except ValueError:
                continue

            # Filter by importance
            if event["importance"] < min_importance:
                continue

            # Filter upcoming only
            if upcoming_only and event_time < now:
                continue

            event["event_time"] = event_time
            parsed_events.append(event)

        # Sort by datetime
        parsed_events.sort(key=lambda x: x["event_time"])

        # Display
        print("=" * 100)
        print(f"ECONOMIC CALENDAR - {symbol if symbol else 'ALL CURRENCIES'}")
        print(f"Showing events with importance >= {min_importance}/3")
        print("=" * 100)

        importance_symbols = {1: "●", 2: "●●", 3: "●●●"}

        for event in parsed_events:
            # Time until event
            time_diff = event["event_time"] - now
            if time_diff.total_seconds() > 0:
                hours_until = time_diff.total_seconds() / 3600
                if hours_until < 24:
                    time_str = f"in {hours_until:.1f}h"
                else:
                    time_str = f"in {hours_until/24:.1f}d"
            else:
                time_str = "Past"

            importance_str = importance_symbols.get(event["importance"], "?")

            print(f"\n{event['datetime']} ({time_str})")
            print(f"  {importance_str} [{event['currency']}] {event['event_name']}")
            print(f"  Country: {event['country']}")

            # Show values if available
            if event["actual"] or event["forecast"] or event["previous"]:
                values = []
                if event["actual"]:
                    values.append(f"Actual: {event['actual']}")
                if event["forecast"]:
                    values.append(f"Forecast: {event['forecast']}")
                if event["previous"]:
                    values.append(f"Previous: {event['previous']}")
                print(f"  {' | '.join(values)}")

        print("\n" + "=" * 100)
        print(f"Total events: {len(parsed_events)}")

    def get_upcoming_high_impact(self, symbol=None, hours_ahead=24):
        """
        Get high-impact events in the next N hours

        Returns:
            List of high-impact events
        """
        calendar_data = self.get_events(symbol=symbol, days_back=0, days_forward=1)
        events = calendar_data.get("data", [])

        high_impact_events = []
        now = datetime.now()
        cutoff_time = now + timedelta(hours=hours_ahead)

        for event_array in events:
            event = self.parse_event(event_array)
            if not event or event["importance"] < 3:
                continue

            try:
                event_time = datetime.strptime(event["datetime"], "%Y.%m.%d %H:%M")
            except ValueError:
                continue

            if now <= event_time <= cutoff_time:
                event["event_time"] = event_time
                high_impact_events.append(event)

        return high_impact_events

    def should_avoid_trading(self, symbol, minutes_before=30, minutes_after=30):
        """
        Check if trading should be avoided due to upcoming high-impact news

        Args:
            symbol: Trading symbol to check
            minutes_before: Minutes before event to avoid trading
            minutes_after: Minutes after event to avoid trading

        Returns:
            (should_avoid: bool, reason: str)
        """
        events = self.get_upcoming_high_impact(
            symbol=symbol,
            hours_ahead=(minutes_before + minutes_after) / 60
        )

        if not events:
            return False, None

        now = datetime.now()

        for event in events:
            event_time = event["event_time"]
            time_before = event_time - timedelta(minutes=minutes_before)
            time_after = event_time + timedelta(minutes=minutes_after)

            if time_before <= now <= time_after:
                time_until = (event_time - now).total_seconds() / 60
                if time_until > 0:
                    reason = f"High-impact {event['currency']} event in {time_until:.0f} min: {event['event_name']}"
                else:
                    reason = f"High-impact {event['currency']} event {-time_until:.0f} min ago: {event['event_name']}"
                return True, reason

        return False, None

    def close(self):
        self.system_socket.close()
        self.data_socket.close()
        self.context.term()

# Usage examples
if __name__ == "__main__":
    calendar = EconomicCalendar()

    try:
        # Display upcoming high-impact events for EURUSD
        print("\n1. Upcoming high-impact EUR and USD events:")
        calendar.display_events(symbol="EURUSD", min_importance=3, upcoming_only=True)

        # Check if we should avoid trading
        print("\n2. Trading safety check:")
        should_avoid, reason = calendar.should_avoid_trading("EURUSD")
        if should_avoid:
            print(f"⚠ AVOID TRADING: {reason}")
        else:
            print("✓ Safe to trade - no high-impact news nearby")

        # Get upcoming events for any symbol
        print("\n3. Next 24h high-impact events:")
        events = calendar.get_upcoming_high_impact(hours_ahead=24)
        for event in events:
            print(f"  • {event['datetime']} - {event['currency']}: {event['event_name']}")

    finally:
        calendar.close()
```

---

## Use Cases

### 1. Avoid Trading During News

```python
calendar = EconomicCalendar()

# Before placing a trade, check for high-impact news
should_avoid, reason = calendar.should_avoid_trading("EURUSD", minutes_before=30)
if should_avoid:
    print(f"Delaying trade: {reason}")
else:
    # Place trade
    trader.market_buy("EURUSD", 0.1)
```

### 2. Event-Driven Trading

```python
# Monitor for specific events
events = calendar.get_upcoming_high_impact(symbol="GBPUSD", hours_ahead=1)

for event in events:
    if "NFP" in event["event_name"] or "Employment" in event["event_name"]:
        print(f"Preparing for NFP release at {event['datetime']}")
        # Set up breakout orders
```

### 3. Filter by Currency

```python
# Get only USD events
calendar_data = calendar.get_events(symbol="EURUSD")
for event_array in calendar_data["data"]:
    event = calendar.parse_event(event_array)
    if event["currency"] == "USD":
        print(f"{event['datetime']}: {event['event_name']}")
```

### 4. Daily News Brief

```python
# Morning routine: check today's events
print("Today's high-impact economic events:")
calendar.display_events(min_importance=3, upcoming_only=True)
```

---

## Importance Levels

| Level | Symbol | Description | Examples |
|-------|--------|-------------|----------|
| 1 | ● | Low impact | Manufacturing indices, minor speeches |
| 2 | ●● | Medium impact | Retail sales, trade balance, consumer confidence |
| 3 | ●●● | High impact | NFP, interest rate decisions, GDP, CPI, FOMC |

**High-impact events (Level 3)** typically cause significant price volatility:
- Non-Farm Payrolls (NFP)
- Federal Reserve interest rate decisions
- Central bank policy announcements
- GDP releases
- CPI (inflation) data

---

## Performance Considerations

1. **Response Size**: Calendar data can be large for long date ranges
   - Limit date ranges to necessary periods
   - Use `symbol` parameter to filter by specific currencies

2. **Caching**: Calendar data doesn't change frequently
   - Cache results for a few minutes
   - Refresh only when needed

3. **Timezone**: Event times are in MT5 server timezone
   - Convert to your local timezone for display
   - Account for daylight saving time changes

---

## Error Handling

```python
try:
    calendar_data = calendar.get_events(symbol="EURUSD")

    if not calendar_data or "data" not in calendar_data:
        print("No calendar data available")
    elif len(calendar_data["data"]) == 0:
        print("No events in date range")
    else:
        # Process events
        for event_array in calendar_data["data"]:
            event = calendar.parse_event(event_array)
            if event:
                print(event)

except zmq.Again:
    print("Timeout retrieving calendar data")
except json.JSONDecodeError as e:
    print(f"Error parsing calendar data: {e}")
```

---

## See Also

- [Live Data Guide](LIVE_DATA_GUIDE.md) - Monitor price reactions during news
- [Trade Guide](TRADE_GUIDE.md) - Event-driven trading strategies
- [Account Guide](ACCOUNT_GUIDE.md) - Check positions before news events

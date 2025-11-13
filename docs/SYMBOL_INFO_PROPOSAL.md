# Proposal: Add SYMBOL_INFO Action to JsonAPI

## Problem

MT5-Docker's JsonAPI doesn't support the `INSTRUMENTS` action. To integrate with Nautilus Trader, we need detailed symbol specifications to create proper `Instrument` objects.

## Solution

Add a `SYMBOL_INFO` action to JsonAPI.mq5 that queries MT5's SymbolInfo functions and returns comprehensive symbol specifications.

## Request Format

```json
{
  "action": "SYMBOL_INFO",
  "symbol": "EURAUD"
}
```

Or request multiple symbols:

```json
{
  "action": "SYMBOL_INFO",
  "symbols": ["EURAUD", "EURUSD", "XAUUSD.sml", "BTCUSD"]
}
```

Or get all symbols:

```json
{
  "action": "SYMBOL_INFO"
}
```

## Response Format (data_port 2202)

```json
{
  "error": false,
  "symbols": [
    {
      "symbol": "EURAUD",
      "description": "Euro vs Australian Dollar",
      "base_currency": "EUR",
      "quote_currency": "AUD",
      "profit_currency": "AUD",
      "margin_currency": "EUR",

      "digits": "5",
      "point": "0.00001000",
      "spread": "15",
      "stops_level": "5",

      "contract_size": "100000.00000",
      "tick_value": "0.66666000",
      "tick_size": "0.00001000",

      "volume_min": "0.01000",
      "volume_max": "500.00000",
      "volume_step": "0.01000",
      "volume_limit": "0.00000",

      "swap_long": "-0.59000",
      "swap_short": "0.05000",
      "swap_mode": "0",

      "trade_mode": "0",
      "trade_execution": "1",
      "trade_calc_mode": "0",

      "expiration_mode": "15",
      "filling_mode": "1",
      "order_mode": "127",

      "margin_initial": "0.00000",
      "margin_maintenance": "0.00000",
      "margin_hedged": "100000.00000",
      "margin_hedged_use_leg": "false",

      "option_mode": "0",
      "option_right": "0",

      "select": "true",
      "visible": "true",
      "session_deals": "1234",
      "session_buy_orders": "567",
      "session_sell_orders": "891",
      "volume": "12345678.00000",
      "volumehigh": "23456789.00000",
      "volumelow": "1234567.00000",

      "time": "1699900800",
      "bid": "1.62345000",
      "bidhigh": "1.62500000",
      "bidlow": "1.62100000",
      "ask": "1.62360000",
      "askhigh": "1.62515000",
      "asklow": "1.62115000",
      "last": "1.62352000",
      "lasthigh": "1.62510000",
      "lastlow": "1.62110000",

      "trade_tick_value": "0.66666000",
      "trade_tick_value_profit": "0.66666000",
      "trade_tick_value_loss": "0.66666000",
      "trade_tick_size": "0.00001000",
      "trade_contract_size": "100000.00000",

      "start_time": "0",
      "expiration_time": "0",

      "trade_stops_level": "5",
      "trade_freeze_level": "0"
    }
  ]
}
```

**Note**: All numeric values are returned as strings because MQL5's CJAVal library requires string assignments for JSON values.

## MQL5 Implementation

Add this function to JsonAPI.mq5:

```mql5
//+------------------------------------------------------------------+
//| Get Symbol Information                                            |
//+------------------------------------------------------------------+
void GetSymbolInfo(CJAVal &dataObject) {
    CJAVal response, symbols_array;

    bool get_all_symbols = false;
    string symbol_list[];

    // Check if requesting specific symbols
    if (dataObject.FindKey("symbol") >= 0) {
        // Single symbol
        ArrayResize(symbol_list, 1);
        symbol_list[0] = dataObject["symbol"].ToStr();
    }
    else if (dataObject.FindKey("symbols") >= 0) {
        // Multiple symbols
        int symbol_count = dataObject["symbols"].Size();
        ArrayResize(symbol_list, symbol_count);
        for (int i = 0; i < symbol_count; i++) {
            symbol_list[i] = dataObject["symbols"][i].ToStr();
        }
    }
    else {
        // Get all symbols
        get_all_symbols = true;
        int total = SymbolsTotal(true);
        ArrayResize(symbol_list, total);
        for (int i = 0; i < total; i++) {
            symbol_list[i] = SymbolName(i, true);
        }
    }

    // Query information for each symbol
    for (int i = 0; i < ArraySize(symbol_list); i++) {
        string symbol = symbol_list[i];

        // Check if symbol exists
        if (!SymbolInfoInteger(symbol, SYMBOL_SELECT)) {
            continue;  // Skip invalid symbols
        }

        CJAVal info;

        // Basic info
        info["symbol"] = symbol;
        info["description"] = SymbolInfoString(symbol, SYMBOL_DESCRIPTION);
        info["base_currency"] = SymbolInfoString(symbol, SYMBOL_CURRENCY_BASE);
        info["quote_currency"] = SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT);
        info["profit_currency"] = SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT);
        info["margin_currency"] = SymbolInfoString(symbol, SYMBOL_CURRENCY_MARGIN);

        // Precision
        info["digits"] = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        info["point"] = SymbolInfoDouble(symbol, SYMBOL_POINT);
        info["spread"] = (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD);
        info["stops_level"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);

        // Contract specifications
        info["contract_size"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);
        info["tick_value"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
        info["tick_size"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);

        // Volume limits
        info["volume_min"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        info["volume_max"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        info["volume_step"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        info["volume_limit"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME_LIMIT);

        // Swap
        info["swap_long"] = SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG);
        info["swap_short"] = SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT);
        info["swap_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_SWAP_MODE);

        // Trade modes
        info["trade_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
        info["trade_execution"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_EXECUTION_MODE);
        info["trade_calc_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_CALC_MODE);

        // Order/execution modes
        info["expiration_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_EXPIRATION_MODE);
        info["filling_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
        info["order_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_ORDER_MODE);

        // Margin
        info["margin_initial"] = SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL);
        info["margin_maintenance"] = SymbolInfoDouble(symbol, SYMBOL_MARGIN_MAINTENANCE);
        info["margin_hedged"] = SymbolInfoDouble(symbol, SYMBOL_MARGIN_HEDGED);
        info["margin_hedged_use_leg"] = (bool)SymbolInfoInteger(symbol, SYMBOL_MARGIN_HEDGED_USE_LEG);

        // Options (if applicable)
        info["option_mode"] = (int)SymbolInfoInteger(symbol, SYMBOL_OPTION_MODE);
        info["option_right"] = (int)SymbolInfoInteger(symbol, SYMBOL_OPTION_RIGHT);

        // Status
        info["select"] = (bool)SymbolInfoInteger(symbol, SYMBOL_SELECT);
        info["visible"] = (bool)SymbolInfoInteger(symbol, SYMBOL_VISIBLE);

        // Session statistics
        info["session_deals"] = (long)SymbolInfoInteger(symbol, SYMBOL_SESSION_DEALS);
        info["session_buy_orders"] = (long)SymbolInfoInteger(symbol, SYMBOL_SESSION_BUY_ORDERS);
        info["session_sell_orders"] = (long)SymbolInfoInteger(symbol, SYMBOL_SESSION_SELL_ORDERS);
        info["volume"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME);
        info["volumehigh"] = SymbolInfoDouble(symbol, SYMBOL_VOLUMEHIGH);
        info["volumelow"] = SymbolInfoDouble(symbol, SYMBOL_VOLUMELOW);

        // Current prices
        info["time"] = (long)SymbolInfoInteger(symbol, SYMBOL_TIME);
        info["bid"] = SymbolInfoDouble(symbol, SYMBOL_BID);
        info["bidhigh"] = SymbolInfoDouble(symbol, SYMBOL_BIDHIGH);
        info["bidlow"] = SymbolInfoDouble(symbol, SYMBOL_BIDLOW);
        info["ask"] = SymbolInfoDouble(symbol, SYMBOL_ASK);
        info["askhigh"] = SymbolInfoDouble(symbol, SYMBOL_ASKHIGH);
        info["asklow"] = SymbolInfoDouble(symbol, SYMBOL_ASKLOW);
        info["last"] = SymbolInfoDouble(symbol, SYMBOL_LAST);
        info["lasthigh"] = SymbolInfoDouble(symbol, SYMBOL_LASTHIGH);
        info["lastlow"] = SymbolInfoDouble(symbol, SYMBOL_LASTLOW);

        // Trade-specific values
        info["trade_tick_value"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
        info["trade_tick_value_profit"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_PROFIT);
        info["trade_tick_value_loss"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
        info["trade_tick_size"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
        info["trade_contract_size"] = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);

        // Time restrictions
        info["start_time"] = (long)SymbolInfoInteger(symbol, SYMBOL_START_TIME);
        info["expiration_time"] = (long)SymbolInfoInteger(symbol, SYMBOL_EXPIRATION_TIME);

        // Freeze/stops levels
        info["trade_stops_level"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
        info["trade_freeze_level"] = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL);

        symbols_array.Add(info);
    }

    response["error"] = false;
    response["symbols"].Set(symbols_array);

    string t = response.Serialize();
    if(debug) Print(t);
    InformClientSocket(dataSocket, t);
}
```

Then add to the action dispatcher:

```mql5
void RequestHandler(string action, CJAVal &message) {
    // ... existing code ...
    else if(action=="SYMBOL_INFO")  {GetSymbolInfo(message);}
    // ... rest of code ...
}
```

## Integration with Nautilus Trader

Once this is implemented in JsonAPI.mq5:

1. **Rust side**: Add `Mt5SymbolInfo` struct and parser
2. **Rust side**: Modify `request_instruments()` to use SYMBOL_INFO action
3. **Rust side**: Create proper `CurrencyPair`/`CryptoPerpetual` instruments from specs
4. **Python side**: Works automatically since it uses the Rust client

## Benefits

- ✅ Proper instrument specifications from MT5
- ✅ Accurate pricing precision, lot sizes, margins
- ✅ No hardcoded values
- ✅ Works for ANY broker's symbols
- ✅ Handles forex, commodities, crypto, indices, etc.
- ✅ Production-ready solution

## Alternative (Temporary Workaround)

For immediate testing, we can use a config-based approach with hardcoded instruments, but this is not sustainable for production.

# Deserialization Error Fix

## Problem

JsonAPI.mq5 was crashing and unbinding all ZMQ sockets when it received malformed JSON data. This caused the "Deserialization Error" alert (image30.png) and complete shutdown of all connections (image31.png).

### Symptoms
- Alert: "Deserialization Error"
- Expert log shows: "ExpertRemove() function called"
- All sockets unbind: ports 2201-2204
- JsonAPI stops responding
- Requires manual restart

### Root Cause

In JsonAPI.mq5 lines 327-331 (original code):
```mql5
if(!message.Deserialize(msg)){
    ActionDoneOrError(65537, __FUNCTION__);
    Alert("Deserialization Error");
    ExpertRemove();  // <-- KILLS ENTIRE EA!
}
```

When `Deserialize()` failed, the EA called `ExpertRemove()` which completely shut down the expert advisor and unbinded all ZMQ sockets. This is too aggressive - one bad message shouldn't crash the entire system.

### Potential Triggers
1. Network corruption/packet loss
2. Client timeout causing retry with partial data
3. SYMBOL_INFO taking too long (>5s) when querying all symbols
4. Race conditions with multiple concurrent requests

## Solution

### 1. Robust Error Handling in JsonAPI.mq5

**File**: `/home/cy/Code/MT5/MT5-Docker/Metatrader/MQL5/Experts/JsonAPI.mq5`

**Lines 327-346**: Replaced `ExpertRemove()` with graceful error handling:

```mql5
// Deserialize msg to CJAVal array
if(!message.Deserialize(msg)){
    Print("ERROR: Failed to deserialize message: ", msg);
    Print("ERROR: Message length: ", StringLen(msg));

    // Send error response to client instead of crashing
    CJAVal errorResponse;
    errorResponse["error"] = true;
    long error_code = 65537;
    errorResponse["error_code"] = IntegerToString(error_code);
    errorResponse["error_description"] = "JSON deserialization failed";
    errorResponse["invalid_message"] = msg;

    // Respond to sys socket
    InformClientSocket(sysSocket, "ERROR");
    // Send error details to data socket
    InformClientSocket(dataSocket, errorResponse.Serialize());

    // Log but don't crash - continue processing next messages
    return;
}
```

**Benefits**:
- Logs the bad message for debugging
- Sends error response to client (not silence)
- Continues running - future valid requests still work
- No more catastrophic failures

### 2. Enhanced Logging in GetSymbolInfo

**Lines 588**: Added logging when querying all symbols:
```mql5
Print("SYMBOL_INFO: Querying all symbols (", total, " total)");
```

**Lines 722-726**: Added summary logging:
```mql5
int symbols_returned = symbols_array.Size();
Print("SYMBOL_INFO: Returning ", symbols_returned, " symbols (from ", ArraySize(symbol_list), " requested)");

string t = response.Serialize();
Print("SYMBOL_INFO: Response size: ", StringLen(t), " bytes");
```

**Benefits**:
- Track timing of SYMBOL_INFO requests
- Identify if responses are too large
- Debug which requests are slow

### 3. Client-Side Error Handling in Nautilus

**File**: `/home/cy/Code/MT5/nautilus_trader/crates/adapters/mt5/src/websocket/client.rs`

**Lines 374-379**: Check for ERROR response in `send_sys_request()`:
```rust
// Check for ERROR response from MT5
if response == "ERROR" {
    return Err(Mt5Error::Parse(
        "MT5 returned ERROR - deserialization failed on MT5 side".to_string()
    ));
}
```

**Lines 399-408**: Check for error JSON in `receive_data_response()`:
```rust
// Check if response is an error message
if response.contains("\"error\":true") || response.contains("\"error\": true") {
    // Try to parse error details
    if let Ok(error_json) = serde_json::from_str::<serde_json::Value>(&response) {
        if let Some(desc) = error_json.get("error_description").and_then(|v| v.as_str()) {
            return Err(Mt5Error::Parse(format!("MT5 error: {}", desc)));
        }
    }
    return Err(Mt5Error::Parse(format!("MT5 returned error: {}", response)));
}
```

**Benefits**:
- Client gets meaningful error messages
- Errors propagate properly instead of silent failures
- Easier debugging when issues occur

## Testing

### Manual Test
1. Compile updated JsonAPI.mq5 in MT5
2. Build Nautilus: `make build-debug`
3. Send intentionally malformed JSON to test error handling
4. Verify JsonAPI logs error but continues running
5. Verify subsequent valid requests still work

### Expected Behavior

**Before Fix**:
- Bad JSON → Alert → ExpertRemove() → All sockets unbind → Complete failure

**After Fix**:
- Bad JSON → Log error → Send error response → Continue running → Next request works

## Deployment

1. **Update MT5-Docker**:
   ```bash
   cd /home/cy/Code/MT5/MT5-Docker/Metatrader/MQL5/Experts
   # Compile JsonAPI.mq5 in MetaEditor
   # Restart the EA in MT5
   ```

2. **Update Nautilus Trader**:
   ```bash
   cd /home/cy/Code/MT5/nautilus_trader
   make build-debug  # or make build-release
   ```

## Future Improvements

1. **Add retry logic** in Nautilus client for transient errors
2. **Rate limiting** on SYMBOL_INFO to prevent overwhelming MT5
3. **Caching** of symbol info to reduce repeated queries
4. **Metrics** to track error frequency and types
5. **Health check endpoint** to monitor JsonAPI status

## Related Issues

- SYMBOL_INFO implementation: `/home/cy/Code/MT5/MT5-Docker/docs/SYMBOL_INFO_PROPOSAL.md`
- Response formats: `/home/cy/Code/MT5/MT5-Docker/docs/RESPONSE_FORMATS.md`

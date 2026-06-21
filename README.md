# Keylogger - Educational Purpose Only

⚠️ **WARNING**: This tool is for educational purposes only. Use only on systems you own or have explicit permission to test.

## Overview

A Windows keylogger that captures keystrokes and sends them to a remote server via TCP socket connection.

## Features

### Fixed Issues (v2.0)

1. **Comprehensive Error Handling**
   - Try-except blocks for all network operations
   - Graceful handling of connection failures
   - Automatic reconnection with configurable retry logic   

2. **Correct Caps Lock & Shift Logic**
   - Fixed inverted Caps Lock detection
   - Proper XOR logic: uppercase when exactly one of (Shift, Caps Lock) is active
   - Correct handling of Shift+number combinations (e.g., Shift+1 = "!")

3. **Configuration File Support**
   - External `config.json` for easy configuration
   - No hardcoded server addresses
   - Configurable reconnection parameters

4. **Robust Network Handling**
   - Connection timeout (10 seconds)
   - Automatic reconnection on network failure
   - Configurable max retry attempts
   - Proper socket cleanup

5. **Improved Code Quality**
   - Named constants instead of magic numbers
   - Comprehensive docstrings
   - Logging system for debugging and monitoring
   - Type safety improvements

6. **Complete ASCII Table**
   - Fixed gaps in key mappings
   - Proper Shift key mappings for special characters
   - Support for all common keys

7. **Resource Management**
   - Proper socket cleanup with try-finally
   - Graceful shutdown on Ctrl+C
   - Error logging for debugging

## Configuration

Edit `config.json` to customize settings:

```json
{
    "server_address": "127.0.0.1",
    "server_port": 9000,
    "reconnect_delay": 5,
    "max_reconnect_attempts": 10,
    "poll_interval": 0.01
}
```

### Configuration Parameters

- **server_address**: IP address of the receiving server
- **server_port**: Port number for the connection
- **reconnect_delay**: Seconds to wait between reconnection attempts
- **max_reconnect_attempts**: Maximum number of reconnection attempts before giving up
- **poll_interval**: Keyboard polling interval in seconds (0.01 = 10ms)

## Usage

1. **Set up the receiving server** (example using netcat):
   ```bash
   nc -l -p 9000
   ```

2. **Configure the keylogger**:
   - Edit `config.json` with your server details

3. **Run the keylogger**:
   ```bash
   python main.py
   ```

4. **Monitor logs**:
   - Check `keylogger.log` for connection status and errors
   - Console output shows real-time status

## Logging

The keylogger creates a `keylogger.log` file with detailed information:
- Connection attempts and status
- Reconnection events
- Errors and exceptions
- Startup and shutdown events

## Technical Details

### Key Features

- **Polling Rate**: 10ms (configurable)
- **Key State Tracking**: Prevents duplicate key events
- **Case Logic**: Proper handling of Caps Lock + Shift combinations
- **Special Characters**: Correct Shift mappings (!, @, #, etc.)
- **Network Protocol**: TCP socket with UTF-8 encoding

### Constants

```python
KEY_PRESSED = 0x8000      # Key press detection mask
CAPS_LOCK_ON = 0x0001     # Caps Lock state mask
VK_CAPITAL = 0x14         # Caps Lock virtual key code
VK_LSHIFT = 0xA0          # Left Shift virtual key code
VK_RSHIFT = 0xA1          # Right Shift virtual key code
```

## Security Considerations

1. **Unencrypted Communication**: Data is sent over plain TCP. For production use, implement SSL/TLS encryption.
2. **No Authentication**: The server connection has no authentication mechanism.
3. **Logging**: Keystrokes are logged to file - ensure proper file permissions.
4. **Legal Compliance**: Only use on systems you own or have explicit written permission to test.

## Improvements Over Original

| Issue | Original | Fixed |
|-------|----------|-------|
| Error Handling | None | Comprehensive try-except blocks |
| Caps Lock Logic | Inverted | Correct XOR logic |
| Shift Handling | Missing | Full support for Shift combinations |
| Configuration | Hardcoded | External config.json |
| Reconnection | None | Automatic with retry logic |
| Logging | None | File and console logging |
| Resource Cleanup | Missing | Proper socket cleanup |
| ASCII Table | Incomplete | Complete with Shift mappings |
| Magic Numbers | Used | Named constants |
| Documentation | Minimal | Comprehensive docstrings |

## Requirements

- Python 3.6+
- Windows OS (uses `ctypes.windll.user32`)
- Network access to server

## License

Educational use only. Use responsibly and legally.

## Disclaimer

This software is provided for educational purposes only. The authors are not responsible for any misuse or damage caused by this program. Always obtain proper authorization before monitoring any system."# Keylogger" 

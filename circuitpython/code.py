# SPDX-FileCopyrightText: 2020 Brian Lough (Original WiFi-Tetris-Clock)
# SPDX-FileCopyrightText: 2024 Adapted for Matrix Portal
#
# SPDX-License-Identifier: MIT

"""
Tetris Clock for Adafruit Matrix Portal Starter Kit (ADABOX 016)
Adapted from https://github.com/witnessmenow/WiFi-Tetris-Clock

A WiFi clock that displays the time using falling Tetris blocks.

Hardware:
- Adafruit Matrix Portal
- 64x32 RGB LED Matrix

Setup:
1. Copy settings.toml.template to settings.toml and fill in your WiFi credentials
2. Copy this file (code.py) to your CIRCUITPY drive
3. Install required libraries (see README.md)

Serial Debug:
Connect via USB and use a serial terminal (e.g., screen, PuTTY, or Mu editor)
at 115200 baud to see debug output.
"""

print("=" * 40)
print("Tetris Clock - Starting up...")
print("=" * 40)

print("[DEBUG] Importing os...")
import os
print("[DEBUG] Importing time...")
import time
print("[DEBUG] Importing board...")
import board
print("[DEBUG] Importing displayio...")
import displayio
print("[DEBUG] Importing Matrix from adafruit_matrixportal.matrix...")
from adafruit_matrixportal.matrix import Matrix
print("[DEBUG] Importing Network from adafruit_matrixportal.network...")
from adafruit_matrixportal.network import Network
print("[DEBUG] All imports successful!")

# Helper function to parse boolean from settings.toml string values
def get_bool_env(key, default):
    """Get a boolean value from settings.toml (values are strings)"""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")


def get_float_env(key, default):
    """Get a float value from settings.toml"""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def get_int_env(key, default):
    """Get an integer value from settings.toml"""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


# Configuration - loaded from settings.toml with defaults
TWELVE_HOUR_FORMAT = get_bool_env("TWELVE_HOUR_FORMAT", True)
FORCE_REFRESH = get_bool_env("FORCE_REFRESH", True)
BRIGHTNESS = get_float_env("BRIGHTNESS", 0.3)
TIME_SYNC_RETRIES = get_int_env("TIME_SYNC_RETRIES", 3)
TIME_SYNC_RETRY_DELAY = get_int_env("TIME_SYNC_RETRY_DELAY", 5)
DAILY_RECONNECT_HOUR = get_int_env("DAILY_RECONNECT_HOUR", 2)
DAILY_RECONNECT_MINUTE = get_int_env("DAILY_RECONNECT_MINUTE", 1)

# Fixed display constants
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
SCALE = 2  # Scale factor for blocks (2 = 2x2 pixel blocks)

print(f"[DEBUG] Configuration loaded:")
print(f"[DEBUG]   TWELVE_HOUR_FORMAT: {TWELVE_HOUR_FORMAT}")
print(f"[DEBUG]   FORCE_REFRESH: {FORCE_REFRESH}")
print(f"[DEBUG]   BRIGHTNESS: {BRIGHTNESS}")
print(f"[DEBUG]   TIME_SYNC_RETRIES: {TIME_SYNC_RETRIES}")
print(f"[DEBUG]   TIME_SYNC_RETRY_DELAY: {TIME_SYNC_RETRY_DELAY}")
print(f"[DEBUG]   DAILY_RECONNECT_HOUR: {DAILY_RECONNECT_HOUR}")
print(f"[DEBUG]   DAILY_RECONNECT_MINUTE: {DAILY_RECONNECT_MINUTE}")

# Tetris block colors - matching original library
# Color index in fall instructions: 0=Red, 1=Green, 2=Blue, 3=White, 4=Yellow, 5=Cyan, 6=Magenta, 7=Orange
# Index 8 is Black (background) for our bitmap
TETRIS_COLORS = [
    0x800000,  # 0: Red (dimmed)
    0x008000,  # 1: Green (dimmed)
    0x000080,  # 2: Blue (dimmed)
    0x606060,  # 3: White (dimmed)
    0x808000,  # 4: Yellow (dimmed)
    0x008080,  # 5: Cyan (dimmed)
    0x800080,  # 6: Magenta (dimmed)
    0x804000,  # 7: Orange (dimmed)
    0x000000,  # 8: Black (background)
]

# Color index for background (black)
COLOR_BLACK = 8

# Fall instructions for each digit
# Format: (blocktype, color, x_pos, y_stop, num_rot)
# Blocktype: 0=Square, 1=L, 2=J, 3=I, 4=S, 5=Z, 6=T, 7=Corner
# Colors: 1=Red, 2=Green, 3=Blue, 4=Yellow, 5=Magenta, 6=Cyan, 7=Orange

# Original number patterns from TetrisNumbers.h
# Format: (blocktype, color, x_pos, y_stop, num_rot)
# Blocktype: 0=Square, 1=L, 2=J, 3=I, 4=S, 5=Z, 6=T, 7=Corner
# Colors: 0=Red, 1=Green, 2=Blue, 3=White, 4=Yellow, 5=Cyan, 6=Magenta, 7=Orange

NUM_0 = [
    (2, 5, 4, 16, 0), (4, 7, 2, 16, 1), (3, 4, 0, 16, 1), (6, 6, 1, 16, 1),
    (5, 1, 4, 14, 0), (6, 6, 0, 13, 3), (5, 1, 4, 12, 0), (5, 1, 0, 11, 0),
    (6, 6, 4, 10, 1), (6, 6, 0, 9, 1), (5, 1, 1, 8, 1), (2, 5, 3, 8, 3)
]

NUM_1 = [
    (2, 5, 4, 16, 0), (3, 4, 4, 15, 1), (3, 4, 5, 13, 3), (2, 5, 4, 11, 2),
    (0, 0, 4, 8, 0)
]

NUM_2 = [
    (0, 0, 4, 16, 0), (3, 4, 0, 16, 1), (1, 2, 1, 16, 3), (1, 2, 1, 15, 0),
    (3, 4, 1, 12, 2), (1, 2, 0, 12, 1), (2, 5, 3, 12, 3), (0, 0, 4, 10, 0),
    (3, 4, 1, 8, 0), (2, 5, 3, 8, 3), (1, 2, 0, 8, 1)
]

NUM_3 = [
    (1, 2, 3, 16, 3), (2, 5, 0, 16, 1), (3, 4, 1, 15, 2), (0, 0, 4, 14, 0),
    (3, 4, 1, 12, 2), (1, 2, 0, 12, 1), (3, 4, 5, 12, 3), (2, 5, 3, 11, 0),
    (3, 4, 1, 8, 0), (1, 2, 0, 8, 1), (2, 5, 3, 8, 3)
]

NUM_4 = [
    (0, 0, 4, 16, 0), (0, 0, 4, 14, 0), (3, 4, 1, 12, 0), (1, 2, 0, 12, 1),
    (2, 5, 0, 10, 0), (2, 5, 3, 12, 3), (3, 4, 4, 10, 3), (2, 5, 0, 9, 2),
    (3, 4, 5, 10, 1)
]

NUM_5 = [
    (0, 0, 0, 16, 0), (2, 5, 2, 16, 1), (2, 5, 3, 15, 0), (3, 4, 5, 16, 1),
    (3, 4, 1, 12, 0), (1, 2, 0, 12, 1), (2, 5, 3, 12, 3), (0, 0, 0, 10, 0),
    (3, 4, 1, 8, 2), (1, 2, 0, 8, 1), (2, 5, 3, 8, 3)
]

NUM_6 = [
    (2, 5, 0, 16, 1), (5, 1, 2, 16, 1), (6, 6, 0, 15, 3), (6, 6, 4, 16, 3),
    (5, 1, 4, 14, 0), (3, 4, 1, 12, 2), (2, 5, 0, 13, 2), (3, 4, 2, 11, 0),
    (0, 0, 0, 10, 0), (3, 4, 1, 8, 0), (1, 2, 0, 8, 1), (2, 5, 3, 8, 3)
]

NUM_7 = [
    (0, 0, 4, 16, 0), (1, 2, 4, 14, 0), (3, 4, 5, 13, 1), (2, 5, 4, 11, 2),
    (3, 4, 1, 8, 2), (2, 5, 3, 8, 3), (1, 2, 0, 8, 1)
]

NUM_8 = [
    (3, 4, 1, 16, 0), (6, 6, 0, 16, 1), (3, 4, 5, 16, 1), (1, 2, 2, 15, 3),
    (4, 7, 0, 14, 0), (1, 2, 1, 12, 3), (6, 6, 4, 13, 1), (2, 5, 0, 11, 1),
    (4, 7, 0, 10, 0), (4, 7, 4, 11, 0), (5, 1, 0, 8, 1), (5, 1, 2, 8, 1),
    (1, 2, 4, 9, 2)
]

NUM_9 = [
    (0, 0, 0, 16, 0), (3, 4, 2, 16, 0), (1, 2, 2, 15, 3), (1, 2, 4, 15, 2),
    (3, 4, 1, 12, 2), (3, 4, 5, 12, 3), (5, 1, 0, 12, 0), (1, 2, 2, 11, 3),
    (5, 1, 4, 9, 0), (6, 6, 0, 10, 1), (5, 1, 0, 8, 1), (6, 6, 2, 8, 2)
]

NUMBERS = [NUM_0, NUM_1, NUM_2, NUM_3, NUM_4, NUM_5, NUM_6, NUM_7, NUM_8, NUM_9]

# AM/PM letters using simplified block patterns
# Format: list of (x, y) coordinates for each block
LETTER_A = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4), (1, 4)]
LETTER_P = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (0, 3), (0, 4)]
LETTER_M = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (2, 2), (3, 1), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)]

# Distance between digits
TETRIS_DISTANCE_BETWEEN_DIGITS = 7
TETRIS_Y_DROP_DEFAULT = 16


def get_credentials():
    """Get WiFi credentials from settings.toml"""
    print("[DEBUG] Reading credentials from settings.toml...")
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    timezone = os.getenv("TIMEZONE", "America/New_York")

    print(f"[DEBUG] SSID found: {'Yes' if ssid else 'No'}")
    print(f"[DEBUG] Password found: {'Yes' if password else 'No'}")
    print(f"[DEBUG] Timezone: {timezone}")

    if ssid and password:
        print(f"[DEBUG] Credentials loaded successfully for network: {ssid}")
        return ssid, password, timezone

    print("=" * 40)
    print("ERROR: WiFi credentials not found!")
    print("Please create settings.toml from settings.toml.template")
    print("=" * 40)
    raise RuntimeError("WiFi credentials not configured")


class TetrisClock:
    """Main Tetris Clock class using proper Tetris block shapes"""

    def __init__(self):
        print("[DEBUG] TetrisClock.__init__() starting...")

        # Initialize the matrix
        print("[DEBUG] Initializing LED matrix...")
        try:
            self.matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=2)
            self.display = self.matrix.display
            # Reduce auto-refresh to prevent flashing
            self.display.auto_refresh = False
            print("[DEBUG] LED matrix initialized successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to initialize LED matrix: {e}")
            raise

        # Create a bitmap for drawing
        print("[DEBUG] Creating display bitmap...")
        self.bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, len(TETRIS_COLORS))

        # Create the palette
        self.palette = displayio.Palette(len(TETRIS_COLORS))
        for i, color in enumerate(TETRIS_COLORS):
            self.palette[i] = color

        # Create a TileGrid and Group
        self.grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.group = displayio.Group()
        self.group.append(self.grid)
        self.display.root_group = self.group
        print("[DEBUG] Display setup complete!")

        # Get credentials and connect to WiFi
        print("[DEBUG] Getting WiFi credentials...")
        ssid, password, self.timezone = get_credentials()

        # Initialize network
        print("[DEBUG] Initializing network with NeoPixel status indicator...")
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=True)

        print(f"[DEBUG] Connecting to WiFi network: {ssid}")
        try:
            self.network.connect()
            print("[DEBUG] WiFi connected successfully!")
        except Exception as e:
            print(f"[ERROR] WiFi connection failed: {e}")
            raise

        # Animation state for each number position (up to 6 positions)
        self.num_states = []
        for _ in range(6):
            self.num_states.append({
                'num_to_draw': -1,
                'fallindex': 0,
                'blockindex': 0,
                'x_shift': 0
            })

        self.size_of_value = 4
        self.last_time = ""
        self.show_colon = True
        self.finished_animating = True
        self.last_daily_reconnect_day = -1  # Track last day we did daily reconnect
        print("[DEBUG] TetrisClock.__init__() complete!")

    def sync_time_with_retry(self, max_retries=None, retry_delay=None):
        """Sync time with worldtimeapi.org with retry logic for resilience.

        Args:
            max_retries: Number of retry attempts (default from settings)
            retry_delay: Seconds between retries (default from settings)

        Returns:
            True if time sync was successful, False otherwise
        """
        if max_retries is None:
            max_retries = TIME_SYNC_RETRIES
        if retry_delay is None:
            retry_delay = TIME_SYNC_RETRY_DELAY

        TIME_URL = f"http://worldtimeapi.org/api/timezone/{self.timezone}"

        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Time sync attempt {attempt + 1}/{max_retries}...")
                print(f"[DEBUG] Fetching time from {TIME_URL}")
                response = self.network.fetch(TIME_URL)
                time_data = response.json()
                datetime_str = time_data["datetime"]
                date_part, time_part = datetime_str.split("T")
                year, month, day = [int(x) for x in date_part.split("-")]
                time_part = time_part.split(".")[0]
                hour, minute, second = [int(x) for x in time_part.split(":")]
                import rtc
                r = rtc.RTC()
                r.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
                print(f"[DEBUG] Time synchronized: {hour:02d}:{minute:02d}:{second:02d}")
                return True
            except Exception as e:
                print(f"[WARNING] Time sync attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)

        print("[WARNING] All time sync attempts failed, continuing with system time...")
        return False

    def reconnect_wifi(self):
        """Reconnect to WiFi network. Used to refresh connection and catch DST changes.

        Returns:
            True if reconnection was successful, False otherwise
        """
        print("[DEBUG] Reconnecting WiFi...")
        try:
            # Disconnect first if connected
            try:
                print("[DEBUG] Disconnecting from WiFi...")
                import wifi
                wifi.radio.stop_station()
                time.sleep(2)  # Wait for disconnect to complete
            except Exception as e:
                print(f"[DEBUG] Disconnect note: {e}")

            # Reconnect
            print("[DEBUG] Reconnecting to WiFi...")
            self.network.connect()
            print("[DEBUG] WiFi reconnected successfully!")
            return True
        except Exception as e:
            print(f"[ERROR] WiFi reconnection failed: {e}")
            return False

    def clear_display(self):
        """Clear the display bitmap"""
        for x in range(DISPLAY_WIDTH):
            for y in range(DISPLAY_HEIGHT):
                self.bitmap[x, y] = COLOR_BLACK

    def draw_block(self, x, y, color_index, scale=SCALE):
        """Draw a scaled block at the specified position"""
        for dx in range(scale):
            for dy in range(scale):
                px = x + dx
                py = y + dy
                if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                    self.bitmap[px, py] = color_index

    def draw_shape(self, blocktype, color_idx, x_pos, y_pos, num_rot, scale=SCALE):
        """Draw a Tetris shape at the given position with rotation"""
        # Tetris block shapes - each is a list of (dx, dy) offsets from origin
        # Blocks are drawn from bottom-left origin, Y increases upward in game coords
        # but on display Y=0 is top, so we invert

        offset1 = 1 * scale
        offset2 = 2 * scale
        offset3 = 3 * scale

        # Square (O-piece)
        if blocktype == 0:
            self.draw_block(x_pos, y_pos, color_idx, scale)
            self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
            self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
            self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
            return

        # L-Shape
        if blocktype == 1:
            if num_rot == 0:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
            elif num_rot == 1:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos - offset1, color_idx, scale)
            elif num_rot == 2:
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset2, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
            else:  # num_rot == 3
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos - offset1, color_idx, scale)
            return

        # J-Shape (reverse L)
        if blocktype == 2:
            if num_rot == 0:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset2, color_idx, scale)
            elif num_rot == 1:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
            elif num_rot == 2:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset2, color_idx, scale)
            else:  # num_rot == 3
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
            return

        # I-Shape
        if blocktype == 3:
            if num_rot == 0 or num_rot == 2:  # Horizontal
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset3, y_pos, color_idx, scale)
            else:  # Vertical
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset3, color_idx, scale)
            return

        # S-Shape
        if blocktype == 4:
            if num_rot == 0 or num_rot == 2:
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
            else:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos - offset1, color_idx, scale)
            return

        # Z-Shape (reverse S)
        if blocktype == 5:
            if num_rot == 0 or num_rot == 2:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset2, color_idx, scale)
            else:
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
            return

        # T-Shape
        if blocktype == 6:
            if num_rot == 0:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
            elif num_rot == 1:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset2, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
            elif num_rot == 2:
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset2, y_pos - offset1, color_idx, scale)
            else:  # num_rot == 3
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset2, color_idx, scale)
            return

        # Corner-Shape (3 blocks in L corner)
        if blocktype == 7:
            if num_rot == 0:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
            elif num_rot == 1:
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
            elif num_rot == 2:
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)
                self.draw_block(x_pos, y_pos - offset1, color_idx, scale)
            else:  # num_rot == 3
                self.draw_block(x_pos, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos, color_idx, scale)
                self.draw_block(x_pos + offset1, y_pos - offset1, color_idx, scale)

    def set_time(self, time_str, force_refresh=False):
        """Set the time to display with animation"""
        time_str = time_str.replace(":", "")
        self.size_of_value = 4

        for pos in range(4):
            x_offset = pos * TETRIS_DISTANCE_BETWEEN_DIGITS * SCALE
            if pos >= 2:
                x_offset += 3 * SCALE  # Extra space for colon

            char = time_str[pos] if pos < len(time_str) else ' '
            number = int(char) if char.isdigit() else -1

            # Only update if different or forced
            if force_refresh or number != self.num_states[pos]['num_to_draw']:
                self.num_states[pos]['num_to_draw'] = number
                self.num_states[pos]['x_shift'] = x_offset
                self.num_states[pos]['fallindex'] = 0
                self.num_states[pos]['blockindex'] = 0

    def draw_numbers(self, x, y_finish, display_colon=True):
        """Draw the numbers with falling animation"""
        finished_animating = True
        y = y_finish - (TETRIS_Y_DROP_DEFAULT * SCALE)

        for numpos in range(self.size_of_value):
            num = self.num_states[numpos]['num_to_draw']
            if num < 0 or num > 9:
                continue

            fall_data = NUMBERS[num]
            num_blocks = len(fall_data)
            state = self.num_states[numpos]

            # Draw falling shape
            if state['blockindex'] < num_blocks:
                finished_animating = False
                block = fall_data[state['blockindex']]
                blocktype, color, bx, y_stop, num_rot = block

                # Handle rotation animation
                rotations = num_rot
                if rotations == 1:
                    if state['fallindex'] < y_stop // 2:
                        rotations = 0
                elif rotations == 2:
                    if state['fallindex'] < y_stop // 3:
                        rotations = 0
                    elif state['fallindex'] < (y_stop * 2) // 3:
                        rotations = 1
                elif rotations == 3:
                    if state['fallindex'] < y_stop // 4:
                        rotations = 0
                    elif state['fallindex'] < y_stop // 2:
                        rotations = 1
                    elif state['fallindex'] < (y_stop * 3) // 4:
                        rotations = 2

                # Draw the falling block
                self.draw_shape(
                    blocktype, color,
                    x + (bx * SCALE) + state['x_shift'],
                    y + (state['fallindex'] * SCALE) - SCALE,
                    rotations, SCALE
                )

                state['fallindex'] += 1
                if state['fallindex'] > y_stop:
                    state['fallindex'] = 0
                    state['blockindex'] += 1

            # Draw already dropped shapes
            if state['blockindex'] > 0:
                for i in range(state['blockindex']):
                    block = fall_data[i]
                    blocktype, color, bx, y_stop, num_rot = block
                    self.draw_shape(
                        blocktype, color,
                        x + (bx * SCALE) + state['x_shift'],
                        y + (y_stop * SCALE) - SCALE,
                        num_rot, SCALE
                    )

        # Draw colon
        if display_colon:
            colon_x = x + (TETRIS_DISTANCE_BETWEEN_DIGITS * 2 * SCALE)
            colon_size = 2 * SCALE
            # Upper dot
            for dx in range(colon_size):
                for dy in range(colon_size):
                    px = colon_x + dx
                    py = y + (8 * SCALE) + dy
                    if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                        self.bitmap[px, py] = 3  # White
            # Lower dot
            for dx in range(colon_size):
                for dy in range(colon_size):
                    px = colon_x + dx
                    py = y + (12 * SCALE) + dy
                    if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                        self.bitmap[px, py] = 3  # White

        return finished_animating

    def draw_colon(self, x, y, show=True):
        """Draw or hide the colon"""
        color = 3 if show else COLOR_BLACK  # White or black
        colon_x = x + (TETRIS_DISTANCE_BETWEEN_DIGITS * 2 * SCALE)
        colon_size = 2 * SCALE

        # Upper dot
        for dx in range(colon_size):
            for dy in range(colon_size):
                px = colon_x + dx
                py = y + (8 * SCALE) + dy
                if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                    self.bitmap[px, py] = color
        # Lower dot
        for dx in range(colon_size):
            for dy in range(colon_size):
                px = colon_x + dx
                py = y + (12 * SCALE) + dy
                if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                    self.bitmap[px, py] = color

    def draw_ampm(self, ampm, x, y):
        """Draw AM or PM indicator in small text on the right side"""
        if not ampm:
            return

        # Simple 3x5 pixel font for A, M, P
        # Each letter is 3 pixels wide, 5 pixels tall
        letter_a = [
            (1, 0),
            (0, 1), (2, 1),
            (0, 2), (1, 2), (2, 2),
            (0, 3), (2, 3),
            (0, 4), (2, 4)
        ]
        letter_m = [
            (0, 0), (4, 0),
            (0, 1), (1, 1), (3, 1), (4, 1),
            (0, 2), (2, 2), (4, 2),
            (0, 3), (4, 3),
            (0, 4), (4, 4)
        ]
        letter_p = [
            (0, 0), (1, 0), (2, 0),
            (0, 1), (2, 1),
            (0, 2), (1, 2), (2, 2),
            (0, 3),
            (0, 4)
        ]

        color = 3  # White for AM/PM

        # Draw first letter (A or P)
        first_letter = letter_a if ampm == "AM" else letter_p
        for dx, dy in first_letter:
            px = x + dx
            py = y + dy
            if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                self.bitmap[px, py] = color

        # Draw M (offset by 4 pixels for A or 4 for P)
        m_offset = 4 if ampm == "AM" else 4
        for dx, dy in letter_m:
            px = x + m_offset + dx
            py = y + dy
            if 0 <= px < DISPLAY_WIDTH and 0 <= py < DISPLAY_HEIGHT:
                self.bitmap[px, py] = color

    def get_current_time(self):
        """Get the current time formatted for display"""
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min

        if TWELVE_HOUR_FORMAT:
            ampm = "AM" if hour < 12 else "PM"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour -= 12
            time_str = f"{hour:2d}:{minute:02d}"
        else:
            time_str = f"{hour:02d}:{minute:02d}"
            ampm = ""

        return time_str, ampm

    def run(self):
        """Main loop"""
        last_second = -1
        last_minute = -1

        print("[DEBUG] run() method starting...")
        print("[DEBUG] Syncing time with network...")

        # Sync time on startup using worldtimeapi.org with retries
        self.sync_time_with_retry()

        print("[DEBUG] Entering main loop...")

        # Animation position - adjusted for the display
        x_pos = 2  # X position for 12-hour format
        y_finish = 26  # Y finish position
        ampm_x = 55  # X position for AM/PM (right side of display)
        ampm_y = 2   # Y position for AM/PM (top)
        current_ampm = ""

        while True:
            current_time = time.localtime()
            current_second = current_time.tm_sec
            current_minute = current_time.tm_min

            # Get formatted time
            time_str, ampm = self.get_current_time()

            # Check if minute changed
            if current_minute != last_minute or last_minute == -1:
                print(f"[DEBUG] Updating display - Time: {time_str} {ampm}")
                self.set_time(time_str, FORCE_REFRESH)
                self.finished_animating = False
                current_ampm = ampm
                last_minute = current_minute

            # Update animation
            if not self.finished_animating:
                self.clear_display()
                self.finished_animating = self.draw_numbers(x_pos, y_finish, self.show_colon)
                # Draw AM/PM indicator
                if TWELVE_HOUR_FORMAT and current_ampm:
                    self.draw_ampm(current_ampm, ampm_x, ampm_y)
                # Manual refresh to prevent flashing
                self.display.refresh()

            # Blink colon every second
            if current_second != last_second:
                self.show_colon = not self.show_colon
                if self.finished_animating:
                    y = y_finish - (TETRIS_Y_DROP_DEFAULT * SCALE)
                    self.draw_colon(x_pos, y, self.show_colon)
                    # Manual refresh
                    self.display.refresh()
                last_second = current_second

            # Daily WiFi reconnection to catch daylight saving time changes
            current_hour = current_time.tm_hour
            current_day = current_time.tm_mday
            if (current_hour == DAILY_RECONNECT_HOUR and
                    current_minute == DAILY_RECONNECT_MINUTE and
                    current_day != self.last_daily_reconnect_day):
                print(f"[DEBUG] Daily WiFi reconnection at {DAILY_RECONNECT_HOUR:02d}:{DAILY_RECONNECT_MINUTE:02d}...")
                self.last_daily_reconnect_day = current_day
                if self.reconnect_wifi():
                    # After reconnection, sync time to catch any DST changes
                    self.sync_time_with_retry()

            # Resync time periodically (every hour on the hour)
            elif current_minute == 0 and current_second == 0:
                print("[DEBUG] Hourly time resync...")
                self.sync_time_with_retry(max_retries=1, retry_delay=0)

            time.sleep(0.05)


# Main entry point
if __name__ == "__main__":
    print("[DEBUG] Main entry point reached")
    print("[DEBUG] Creating TetrisClock instance...")
    try:
        clock = TetrisClock()
        print("[DEBUG] TetrisClock instance created, starting run()...")
        clock.run()
    except Exception as e:
        print("=" * 40)
        print(f"[FATAL ERROR] {type(e).__name__}: {e}")
        print("=" * 40)
        print("[DEBUG] The clock has stopped due to an error.")
        print("[DEBUG] Check the error message above for details.")
        # Keep the error visible
        while True:
            time.sleep(1)

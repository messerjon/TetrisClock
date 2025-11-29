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
1. Copy secrets.py.template to secrets.py and fill in your WiFi credentials
   OR copy settings.toml.template to settings.toml (for CircuitPython 8.x+)
2. Copy this file (code.py) to your CIRCUITPY drive
3. Install required libraries (see README.md)
"""

import os
import time
import board
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import random

# Configuration
TWELVE_HOUR_FORMAT = True  # Set to False for 24-hour format
FORCE_REFRESH = True       # Animate all digits on each minute change
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Tetris block colors (RGB565)
TETRIS_COLORS = [
    0xFF0000,  # Red
    0x00FF00,  # Green
    0x0000FF,  # Blue
    0xFFFF00,  # Yellow
    0xFF00FF,  # Magenta
    0x00FFFF,  # Cyan
    0xFFA500,  # Orange
]

# Tetris digit patterns (simplified for LED matrix)
# Each digit is represented as a list of block positions
DIGIT_PATTERNS = {
    '0': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
    '1': [(1,0),(1,1),(1,2),(1,3),(1,4)],
    '2': [(0,0),(1,0),(2,0),(2,1),(0,2),(1,2),(2,2),(0,3),(0,4),(1,4),(2,4)],
    '3': [(0,0),(1,0),(2,0),(2,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
    '4': [(0,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(2,3),(2,4)],
    '5': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
    '6': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
    '7': [(0,0),(1,0),(2,0),(2,1),(2,2),(2,3),(2,4)],
    '8': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
    '9': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
    ':': [(1,1),(1,3)],
    ' ': [],
    'A': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(2,3),(0,4),(2,4)],
    'P': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(0,4)],
    'M': [(0,0),(4,0),(0,1),(1,1),(3,1),(4,1),(0,2),(2,2),(4,2),(0,3),(4,3),(0,4),(4,4)],
}


def get_credentials():
    """
    Get WiFi credentials from secrets.py or settings.toml

    For CircuitPython 8.x+, credentials can be stored in settings.toml
    For older versions, use secrets.py

    Returns:
        tuple: (ssid, password, timezone)
    """
    # First try settings.toml (CircuitPython 8.x+ auto-loads this)
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    timezone = os.getenv("TIMEZONE", "America/New_York")

    if ssid and password:
        return ssid, password, timezone

    # Fallback to secrets.py
    try:
        from secrets import secrets
        return secrets["ssid"], secrets["password"], secrets.get("timezone", "America/New_York")
    except ImportError:
        print("ERROR: WiFi credentials not found!")
        print("Please create secrets.py from secrets.py.template")
        print("OR create settings.toml from settings.toml.template")
        raise RuntimeError("WiFi credentials not configured")


class TetrisBlock:
    """Represents a falling Tetris block"""

    def __init__(self, target_x, target_y, color):
        self.x = target_x
        self.y = -3  # Start above the display
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        self.falling = True
        self.fall_speed = 1

    def update(self):
        """Update block position"""
        if self.falling:
            self.y += self.fall_speed
            if self.y >= self.target_y:
                self.y = self.target_y
                self.falling = False
        return not self.falling


class TetrisClock:
    """Main Tetris Clock class"""

    def __init__(self):
        # Initialize the matrix
        self.matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=4)
        self.display = self.matrix.display

        # Create bitmap for drawing
        self.bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 9)
        self.palette = displayio.Palette(9)
        self.palette[0] = 0x000000  # Black background
        for i, color in enumerate(TETRIS_COLORS):
            self.palette[i + 1] = color
        self.palette[8] = 0xFFFFFF  # White for colon

        # Create tile grid
        self.grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.group = displayio.Group()
        self.group.append(self.grid)
        self.display.root_group = self.group

        # Get credentials and connect to WiFi
        ssid, password, self.timezone = get_credentials()

        # Initialize network
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=False)

        print(f"Connecting to WiFi: {ssid}")
        self.network.connect()
        print("WiFi connected!")

        # Animation state
        self.blocks = []
        self.last_time = ""
        self.last_ampm = ""
        self.show_colon = True
        self.animation_complete = True

    def clear_display(self):
        """Clear the display bitmap"""
        for x in range(DISPLAY_WIDTH):
            for y in range(DISPLAY_HEIGHT):
                self.bitmap[x, y] = 0

    def draw_block(self, x, y, color_index):
        """Draw a single block at the specified position"""
        if 0 <= x < DISPLAY_WIDTH and 0 <= y < DISPLAY_HEIGHT:
            self.bitmap[x, y] = color_index

    def get_current_time(self):
        """Get the current time from the network"""
        try:
            # Use network time
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
        except Exception as e:
            print(f"Error getting time: {e}")
            return "00:00", ""

    def create_digit_animation(self, digit, x_offset, y_offset, color_index):
        """Create falling blocks for a digit"""
        if digit not in DIGIT_PATTERNS:
            return []

        pattern = DIGIT_PATTERNS[digit]
        blocks = []

        for px, py in pattern:
            block = TetrisBlock(
                x_offset + px * 2,
                y_offset + py * 2,
                color_index
            )
            blocks.append(block)

        # Randomize fall order
        random.shuffle(blocks)
        return blocks

    def animate_time(self, time_str, ampm):
        """Create animation for the time display"""
        self.blocks = []
        self.animation_complete = False

        # Calculate positions for time digits
        x_positions = [2, 10, 18, 28, 36, 44]  # Positions for H1, H2, :, M1, M2

        # Create blocks for each character
        delay_counter = 0
        for i, char in enumerate(time_str):
            if i < len(x_positions):
                color_index = (i % len(TETRIS_COLORS)) + 1
                digit_blocks = self.create_digit_animation(
                    char,
                    x_positions[i],
                    10,
                    color_index
                )
                if digit_blocks:
                    # Add delay to stagger the animations
                    for block in digit_blocks:
                        block.y -= delay_counter
                    self.blocks.extend(digit_blocks)
                    delay_counter += 3

        # Add AM/PM indicator if in 12-hour mode
        if ampm:
            ampm_x = 52
            for i, char in enumerate(ampm):
                color_index = ((5 + i) % len(TETRIS_COLORS)) + 1
                digit_blocks = self.create_digit_animation(
                    char,
                    ampm_x,
                    10 + i * 10,
                    color_index
                )
                if digit_blocks:
                    for block in digit_blocks:
                        block.y -= delay_counter
                    self.blocks.extend(digit_blocks)
                    delay_counter += 2

    def update_animation(self):
        """Update all falling blocks"""
        if not self.blocks:
            self.animation_complete = True
            return

        all_landed = True
        for block in self.blocks:
            if not block.update():
                all_landed = False

        self.animation_complete = all_landed

    def draw_frame(self):
        """Draw the current frame"""
        self.clear_display()

        # Draw all blocks at their current positions
        for block in self.blocks:
            # Draw 2x2 block
            for dx in range(2):
                for dy in range(2):
                    self.draw_block(
                        int(block.x) + dx,
                        int(block.y) + dy,
                        block.color
                    )

    def draw_colon(self, x, y, visible):
        """Draw blinking colon"""
        color_index = 8 if visible else 0  # White or black

        # Top dot
        self.draw_block(x, y + 4, color_index)
        self.draw_block(x + 1, y + 4, color_index)
        self.draw_block(x, y + 5, color_index)
        self.draw_block(x + 1, y + 5, color_index)

        # Bottom dot
        self.draw_block(x, y + 10, color_index)
        self.draw_block(x + 1, y + 10, color_index)
        self.draw_block(x, y + 11, color_index)
        self.draw_block(x + 1, y + 11, color_index)

    def run(self):
        """Main run loop"""
        last_second = -1
        last_minute = -1

        print("Tetris Clock starting...")
        print("Getting initial time...")

        # Sync time on startup
        try:
            self.network.get_local_time()
            print("Time synchronized!")
        except Exception as e:
            print(f"Warning: Could not sync time: {e}")

        while True:
            current_time = time.localtime()
            current_second = current_time.tm_sec
            current_minute = current_time.tm_min

            # Get formatted time
            time_str, ampm = self.get_current_time()

            # Check if minute changed or this is the first run
            if current_minute != last_minute or last_minute == -1:
                # Check if we need to animate
                if time_str != self.last_time or FORCE_REFRESH:
                    print(f"Time: {time_str} {ampm}")
                    self.animate_time(time_str, ampm)
                    self.last_time = time_str
                    self.last_ampm = ampm

                last_minute = current_minute

            # Update animation
            if not self.animation_complete:
                self.update_animation()
                self.draw_frame()

            # Blink colon every second
            if current_second != last_second:
                self.show_colon = not self.show_colon
                if self.animation_complete:
                    self.draw_colon(22, 8, self.show_colon)
                last_second = current_second

            # Resync time periodically (every hour)
            if current_minute == 0 and current_second == 0:
                try:
                    self.network.get_local_time()
                except Exception:
                    pass

            time.sleep(0.05)


# Main entry point
if __name__ == "__main__":
    clock = TetrisClock()
    clock.run()

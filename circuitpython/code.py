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
print("[DEBUG] Importing random...")
import random
print("[DEBUG] All imports successful!")

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
    Get WiFi credentials from settings.toml

    CircuitPython 8.x+ automatically loads settings.toml from the CIRCUITPY drive.

    Returns:
        tuple: (ssid, password, timezone)
    """
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
    print("Make sure settings.toml is in the root of CIRCUITPY drive")
    print("=" * 40)
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
        print("[DEBUG] TetrisClock.__init__() starting...")

        # Initialize the matrix
        print("[DEBUG] Initializing LED matrix...")
        try:
            self.matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=4)
            self.display = self.matrix.display
            print("[DEBUG] LED matrix initialized successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to initialize LED matrix: {e}")
            raise

        # Create bitmap for drawing
        print("[DEBUG] Creating display bitmap and palette...")
        self.bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 9)
        self.palette = displayio.Palette(9)
        self.palette[0] = 0x000000  # Black background
        for i, color in enumerate(TETRIS_COLORS):
            self.palette[i + 1] = color
        self.palette[8] = 0xFFFFFF  # White for colon

        # Create tile grid
        print("[DEBUG] Creating tile grid...")
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
        print("[DEBUG] (NeoPixel should be flashing during connection)")
        try:
            self.network.connect()
            print("[DEBUG] WiFi connected successfully!")
        except Exception as e:
            print(f"[ERROR] WiFi connection failed: {e}")
            raise

        # Animation state
        self.blocks = []
        self.last_time = ""
        self.last_ampm = ""
        self.show_colon = True
        self.animation_complete = True
        print("[DEBUG] TetrisClock.__init__() complete!")

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

        # Randomize fall order (CircuitPython doesn't have random.shuffle)
        for i in range(len(blocks) - 1, 0, -1):
            j = random.randint(0, i)
            blocks[i], blocks[j] = blocks[j], blocks[i]
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

        print("[DEBUG] run() method starting...")
        print("[DEBUG] Syncing time with network...")

        # Sync time on startup using worldtimeapi.org (no Adafruit IO needed)
        try:
            # Use worldtimeapi.org for time sync - doesn't require Adafruit IO account
            TIME_URL = f"http://worldtimeapi.org/api/timezone/{self.timezone}"
            print(f"[DEBUG] Fetching time from {TIME_URL}")
            response = self.network.fetch(TIME_URL)
            time_data = response.json()
            # Parse the datetime string (format: "2024-01-15T10:30:45.123456-05:00")
            datetime_str = time_data["datetime"]
            # Extract date and time parts
            date_part, time_part = datetime_str.split("T")
            year, month, day = [int(x) for x in date_part.split("-")]
            time_part = time_part.split(".")[0]  # Remove microseconds
            hour, minute, second = [int(x) for x in time_part.split(":")]
            # Set the RTC
            import rtc
            r = rtc.RTC()
            r.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
            print(f"[DEBUG] Time synchronized: {hour:02d}:{minute:02d}:{second:02d}")
        except Exception as e:
            print(f"[WARNING] Could not sync time: {e}")
            print("[DEBUG] Continuing with system time...")

        print("[DEBUG] Entering main loop...")
        loop_count = 0

        while True:
            current_time = time.localtime()
            current_second = current_time.tm_sec
            current_minute = current_time.tm_min

            # Debug output every 100 loops (approximately every 5 seconds)
            loop_count += 1
            if loop_count % 100 == 0:
                print(f"[DEBUG] Loop #{loop_count}, time: {current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}")

            # Get formatted time
            time_str, ampm = self.get_current_time()

            # Check if minute changed or this is the first run
            if current_minute != last_minute or last_minute == -1:
                # Check if we need to animate
                if time_str != self.last_time or FORCE_REFRESH:
                    print(f"[DEBUG] Updating display - Time: {time_str} {ampm}")
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
                print("[DEBUG] Hourly time resync...")
                try:
                    TIME_URL = f"http://worldtimeapi.org/api/timezone/{self.timezone}"
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
                    print("[DEBUG] Time resync successful!")
                except Exception as e:
                    print(f"[WARNING] Time resync failed: {e}")

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
        # Keep running so the error message stays visible
        while True:
            time.sleep(1)

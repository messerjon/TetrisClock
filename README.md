# TetrisClock

A WiFi clock that displays the time using falling Tetris blocks. Adapted from [WiFi-Tetris-Clock](https://github.com/witnessmenow/WiFi-Tetris-Clock) for the Adafruit Matrix Portal Starter Kit (ADABOX 016).

This code was converted from C++ to CircuitPython using [GitHub Copilot](https://github.com/features/copilot).

![Tetris Clock Animation](https://thumbs.gfycat.com/RecklessSpecificKoodoo-size_restricted.gif)

## Hardware

You can purchase the complete kit from:
- [Adafruit - Matrix Portal Starter Kit (Product 4812)](https://www.adafruit.com/product/4812)
- [DigiKey - Adafruit Matrix Portal Starter Kit](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4812/15189153)

Or purchase components separately:
- [Adafruit Matrix Portal](https://www.adafruit.com/product/4745) - The brains of the operation
- [64x32 RGB LED Matrix Panel](https://www.adafruit.com/product/2278) - Included in ADABOX 016
- USB-C power supply (5V 4A recommended)

## Software Setup

### 1. Install CircuitPython

Download and install the latest CircuitPython for the Matrix Portal:
- https://circuitpython.org/board/matrixportal_m4/

### 2. Install Required Libraries

Copy the following libraries to your `CIRCUITPY/lib` folder. You can get them from the [CircuitPython Library Bundle](https://circuitpython.org/libraries):

- `adafruit_matrixportal/`
- `adafruit_portalbase/`
- `adafruit_display_text/`
- `adafruit_bitmap_font/`
- `adafruit_esp32spi/`
- `adafruit_requests.mpy`
- `adafruit_bus_device/`
- `neopixel.mpy`
- `adafruit_fakerequests.mpy`
- `adafruit_io/`
- `adafruit_connection_manager.mpy`
- `adafruit_minimqtt/` (folder - required by network module)

### 3. Configure WiFi Credentials (Important!)

Your WiFi credentials must be configured locally and are NOT stored in GitHub.

1. Copy `circuitpython/settings.toml.template` to your `CIRCUITPY` drive as `settings.toml`
2. Edit `settings.toml` with your credentials:

```toml
CIRCUITPY_WIFI_SSID = "YourWiFiNetworkName"
CIRCUITPY_WIFI_PASSWORD = "YourWiFiPassword"
TIMEZONE = "America/New_York"
```

### 4. Copy the Code

Copy `circuitpython/code.py` to your `CIRCUITPY` drive.

## Configuration Options

All configuration options can be set in `settings.toml`. The following options are available:

### Display Settings

```toml
TWELVE_HOUR_FORMAT = "true"    # Set to "false" for 24-hour format
FORCE_REFRESH = "true"         # Animate all digits on each minute change
BRIGHTNESS = "0.3"             # LED brightness (0.0 to 1.0)
```

### Time Sync Settings

```toml
TIME_SYNC_RETRIES = "3"        # Number of retries for initial time sync
TIME_SYNC_RETRY_DELAY = "5"    # Seconds to wait between retry attempts
TIME_SYNC_INTERVAL = "900"     # Seconds between periodic time syncs (default: 900 = 15 minutes)
DAILY_RECONNECT_HOUR = "2"     # Hour to reconnect WiFi daily (0-23) for daylight savings
DAILY_RECONNECT_MINUTE = "1"   # Minute to reconnect WiFi daily (0-59)
```

The clock automatically performs periodic time syncs to prevent clock drift. The Matrix Portal (ESP32) does not have a hardware real-time clock (RTC), so it relies on the microcontroller's internal oscillator which can drift over time. By default, the clock resyncs every 15 minutes (900 seconds) to maintain accuracy. You can adjust this interval using `TIME_SYNC_INTERVAL` - lower values provide better accuracy but consume more network bandwidth.

The clock also reconnects to WiFi and resyncs time daily at the configured time (default 02:01) to catch daylight saving time changes.

## Timezone Configuration

Find your timezone string from the [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

Common examples:
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `Europe/London` - UK
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan

## Security Note

The `settings.toml` file is included in `.gitignore` to prevent accidental commits of your WiFi credentials. Always keep your credentials private!

## Troubleshooting

### Using Serial Debug Output

The code includes detailed debug output over USB serial. To view it:

1. **Connect via USB** - Keep the Matrix Portal connected to your computer via USB-C
2. **Open a serial terminal** at 115200 baud:
   - **Mu Editor** (recommended for beginners): Click "Serial" button
   - **macOS/Linux**: `screen /dev/tty.usbmodem* 115200` or `screen /dev/ttyACM0 115200`
   - **Windows**: Use PuTTY or similar, select the COM port at 115200 baud
   - **Arduino IDE**: Tools → Serial Monitor, set baud to 115200

3. **Press the reset button** on the Matrix Portal to see the full startup sequence

You should see output like:
```
========================================
Tetris Clock - Starting up...
========================================
[DEBUG] Importing os...
[DEBUG] Importing time...
...
[DEBUG] Credentials loaded successfully for network: YourNetwork
[DEBUG] Connecting to WiFi network: YourNetwork
...
```

### Clock shows wrong time
- Check your timezone setting in `settings.toml`
- Ensure WiFi is connected (NeoPixel will flash during connection)

### "WiFi credentials not found" error
- Make sure you created `settings.toml` from `settings.toml.template`
- Check that the file is on the root of your `CIRCUITPY` drive
- Verify the file has the correct format (no typos in variable names)

### Display not working
- Ensure the matrix is properly connected to the Matrix Portal
- Check power supply - the matrix requires significant power (5V 4A recommended)
- Check serial output for any error messages

### Nothing happens at startup
- Connect via serial to see debug output
- Check that `code.py` is in the root of the CIRCUITPY drive
- Make sure all required libraries are in the `lib` folder
- Try pressing the reset button on the Matrix Portal

## Credits

- Original WiFi-Tetris-Clock by [Brian Lough](https://github.com/witnessmenow/WiFi-Tetris-Clock)
- Code converted from C++ to CircuitPython using [GitHub Copilot](https://github.com/features/copilot)
- [TetrisMatrixDraw library](https://github.com/toblum/TetrisAnimation) for inspiration
- [Adafruit](https://www.adafruit.com/) for the amazing Matrix Portal hardware and libraries

## License

MIT License - See original project for full details.
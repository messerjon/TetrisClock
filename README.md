# TetrisClock

A WiFi clock that displays the time using falling Tetris blocks. Adapted from [WiFi-Tetris-Clock](https://github.com/witnessmenow/WiFi-Tetris-Clock) for the Adafruit Matrix Portal Starter Kit (ADABOX 016).

![Tetris Clock Animation](https://thumbs.gfycat.com/RecklessSpecificKoodoo-size_restricted.gif)

## Hardware

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

You can customize the clock by editing the configuration section at the top of `code.py`:

```python
TWELVE_HOUR_FORMAT = True   # Set to False for 24-hour format
FORCE_REFRESH = True        # Animate all digits on each minute change
```

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
- [TetrisMatrixDraw library](https://github.com/toblum/TetrisAnimation) for inspiration
- [Adafruit](https://www.adafruit.com/) for the amazing Matrix Portal hardware and libraries

## License

MIT License - See original project for full details.
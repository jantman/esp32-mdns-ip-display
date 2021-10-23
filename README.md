# esp32-mdns-ip-display

ESP32 / MicroPython project to show an mDNS hostname and current IP on a small display

## Overview

My local makerspace has a bunch of 3D printers; they all use normal dynamic DHCP leases and rely on [mDNS](https://en.wikipedia.org/wiki/Multicast_DNS) to be found. Unfortunately some people don't have working mDNS clients on their laptops, so they have trouble connecting to the printers. This project pairs an [ESP32](https://en.wikipedia.org/wiki/ESP32) microcontroller running [MicroPython](https://micropython.org/) with a 16x2 or 20x4 display. Once configured with WiFi settings and a hostname to query, it will periodically resolve the hostname to its IP via mDNS and display the hostname and IP. The idea is to power this small setup via USB and place it next to the relevant printer.

## Hardware

For microcontrollers, I used off-brand ESP32 clones from Amazon, specifically the [DORHEA 4PCS ESP32 Development Board ESP-32S Microcontroller Processor Integrated Chip CP2102 WiFi NodeMCU-32S ESP-WROOM-32 Compatible with Ardu ino IDE](https://www.amazon.com/gp/product/B086MLNH7N/) which currently cost $30 USD for a 4-pack. **Note** that I use the ESP32 because its MicroPython port includes built-in support for mDNS A record lookups, so no additional libraries or code are needed for that.

The display I'm currently using is a [SeeedStudio Grove LCD with RGB Backlight](https://wiki.seeedstudio.com/Grove-LCD_RGB_Backlight/); the backlight is nice for showing status. Expect other displays to be supported soon.

## Getting Started

1. Clone this repository locally and set up a Python >= 3.4 (currently tested using 3.9) virtualenv with ``python3 -mvenv venv`` and then activate with ``source venv/bin/activate``.
2. From the [MicroPython ESP32 Downloads](https://micropython.org/download/esp32/) download the latest ESP32 stable build. This project is currently written for v1.17 and is tested using the ``esp32-20210902-v1.17.bin`` image.
3. Install [esptool](https://github.com/espressif/esptool/) with ``pip install esptool``
4. Plug the ESP32 into your computer via USB, find the port/device that it was given (i.e. ``dmesg``), change port ownership to your user if needed. This tutorial assumes that your device is on ``/dev/ttyUSB0``.
5. Clear the flash on the ESP32: ``esptool.py --port /dev/ttyUSB0 erase_flash``
6. Write the new MicroPython firmware ``esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 115200 write_flash -z 0x1000 esp32-20210902-v1.17.bin``

### Installation

1. Install [mpremote](https://pypi.org/project/mpremote/) for deploying files and accessing the REPL: ``pip install mpremote``
2. Copy [config_example.py](config_example.py) to ``config.py`` and edit as needed.
3. Write the config file to the ESP32: ``mpremote fs cp config.py :config.py``
4. Write the application to the ESP32: ``mpremote fs cp main.py :main.py``
5. Get a REPL on the device ``mpremote repl`` and then soft-reset it to run the application with Ctrl+D. You should see some debugging output, and the result of mDNS address resolution.

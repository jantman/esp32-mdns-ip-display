"""
ESP32 mDNS hostname / IP lookup display screen

https://github.com/jantman/esp32-mdns-ip-display

MIT License

Copyright (c) 2021 Jason Antman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import machine
import micropython
import network
from machine import Pin, I2C
from socket import getaddrinfo
from binascii import hexlify
micropython.alloc_emergency_exception_buf(100)
from time import sleep

from config import SSID, WPA_KEY, HOSTNAME, SCL_PIN, SDA_PIN

def debugprint(*args):
    print(*args)


class UnknownHostException(Exception):
    pass


class Display:

    NUM_LINES: int = 2
    NUM_CHARS: int = 16

    def __init__(self):
        debugprint(f'Initialize I2C SCL={SCL_PIN} SDA={SDA_PIN}')
        self.i2c: I2C = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
        debugprint('I2C initialized')

    def set_text(self, hostname: str, ip: str, refresh: bool = True):
        raise NotImplementedError()

    def set_backlight(self, red: int, green: int, blue: int):
        pass


class GroveLcdRgbDisplay(Display):
    """
    This is for the SeeedStudio Grove LCD RGB backlight.
    https://www.seeedstudio.com/Grove-LCD-RGB-Backlight.html

    Wiring:

    GND - GND
    VCC - VIN (5v)
    SDA - Pin 19
    SCL - Pin 18
    """

    DISPLAY_RGB_ADDR: int = 0x62
    DISPLAY_TEXT_ADDR: int = 0x3e

    def __init__(self):
        super(GroveLcdRgbDisplay, self).__init__()

    def set_text(self, hostname: str, ip: str, refresh: bool = True):
        debugprint(f'Set display text: {hostname}\n{ip}')
        self._set_text(f'{hostname}\n{ip}', refresh=refresh)

    def set_backlight(self, red: int, green: int, blue: int):
        for x in [red, green, blue]:
            assert -1 < x < 256
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 0, bytearray([0]))
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 1, bytearray([0]))
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 0x08, bytearray([0xaa]))
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 4, bytearray([red]))
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 3, bytearray([green]))
        self.i2c.writeto_mem(self.DISPLAY_RGB_ADDR, 2, bytearray([blue]))

    # send command to display (no need for external use)
    def _text_command(self, cmd: int):
        self.i2c.writeto_mem(self.DISPLAY_TEXT_ADDR, 0x80, bytearray([cmd]))

    def _set_text(self, text: str, refresh: bool = True):
        if refresh:
            self._text_command(0x01)  # clear display
        else:
            self._text_command(0x02)  # return home
        sleep(.05)
        self._text_command(0x08 | 0x04)  # display on, no cursor, blink
        self._text_command(0x28)  # 2 lines
        sleep(.05)
        count: int = 0
        row: int = 0
        if not refresh:
            while len(text) < self.NUM_LINES * self.NUM_CHARS:  # clears the rest of the screen
                text += ' '
        for c in text:
            if c == '\n' or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self._text_command(0xc0)
                if c == '\n':
                    continue
            count += 1
            self.i2c.writeto_mem(
                self.DISPLAY_TEXT_ADDR, 0x40, bytearray([ord(c)])
            )


class MdnsHostDisplay:

    def __init__(self):
        self._display: Display = GroveLcdRgbDisplay()
        self._display.set_backlight(255, 255, 0)
        self._display.set_text('Booting...', '')
        debugprint('Instantiate WLAN')
        self.wlan: network.WLAN = network.WLAN(network.STA_IF)
        debugprint('connect_wlan()')
        self._connect_wlan()
        self._mac: str = hexlify(self.wlan.config('mac'), ':').decode()
        debugprint(f'My MAC: {self._mac}')

    def run(self):
        debugprint("Enter loop...")
        unknowns: int = 0
        while True:
            try:
                ip = self._get_ip()
                unknowns = 0
                self._display.set_backlight(0, 255, 0)
            except UnknownHostException:
                unknowns += 1
                ip = '<unknown>'
                self._display.set_backlight(255, 0, 0)
                if unknowns > 10:
                    machine.soft_reset()
            debugprint(f'IP: {ip}')
            self._display.set_text(HOSTNAME, ip)
            # This causes a small blink on the display, to show that we're
            # still running...
            for x in range(0, 11):
                sleep(5)
                self._display.set_text(HOSTNAME, ip)

    def _get_ip(self) -> str:
        addr: str = f'{HOSTNAME}.local'
        try:
            debugprint(f'getaddrinfo({addr}, 80)')
            return getaddrinfo(addr, 80)[0][4][0]
        except Exception as ex:
            debugprint(f'getaddrinfo exception: {ex}')
            raise UnknownHostException

    def _connect_wlan(self):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            debugprint('connecting to network...')
            self.wlan.connect(SSID, WPA_KEY)
            while not self.wlan.isconnected():
                pass
        debugprint('network config:', self.wlan.ifconfig())


if __name__ == '__main__':
    MdnsHostDisplay().run()

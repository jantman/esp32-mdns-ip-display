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

micropython.alloc_emergency_exception_buf(100)

import network
from machine import Pin, I2C
from socket import getaddrinfo
from binascii import hexlify
from time import sleep

from esp8266_i2c_lcd import I2cLcd
from config import (
    SSID, WPA_KEY, HOSTNAME, SCL_PIN, SDA_PIN, DISPLAY_I2C_ADDR,
    DISPLAY_NUM_COLS, DISPLAY_NUM_LINES
)


def debugprint(*args):
    print(*args)


class UnknownHostException(Exception):
    pass


class MdnsHostDisplay:

    def __init__(self):
        i2c = I2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        self.lcd = I2cLcd(
            i2c, DISPLAY_I2C_ADDR, DISPLAY_NUM_LINES, DISPLAY_NUM_COLS
        )
        self.lcd.putstr('Booting...')
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
            except UnknownHostException:
                unknowns += 1
                ip = '<unknown>'
                if unknowns > 10:
                    machine.soft_reset()
            debugprint(f'IP: {ip}')
            self.lcd.clear()
            self.lcd.putstr(f'{HOSTNAME}\n{ip}')
            # This causes a small blink on the display, to show that we're
            # still running...
            for x in range(0, 11):
                sleep(5)
                self.lcd.clear()
                self.lcd.putstr(f'{HOSTNAME}\n{ip}')

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

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

import micropython
import network
from socket import getaddrinfo
from binascii import hexlify
micropython.alloc_emergency_exception_buf(100)

from config import SSID, WPA_KEY, HOSTNAME

def debugprint(*args):
    print(*args)


class MdnsHostDisplay:

    def __init__(self):
        debugprint('Instantiate WLAN')
        self.wlan: network.WLAN = network.WLAN(network.STA_IF)
        debugprint('connect_wlan()')
        self._connect_wlan()
        self._mac: str = hexlify(self.wlan.config('mac'), ':').decode()
        debugprint(f'My MAC: {self._mac}')

    def run(self):
        debugprint("Enter loop...")
        print(self._get_ip())

    def _get_ip(self) -> str:
        addr: str = f'{HOSTNAME}.local'
        try:
            debugprint(f'getaddrinfo({addr}, 80)')
            return getaddrinfo(addr, 80)[0][4][0]
        except Exception as ex:
            debugprint(f'getaddrinfo exception: {ex}')
            return '<unknown>'

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

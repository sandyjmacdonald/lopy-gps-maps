import _thread
import socket
import pycom
import utime
from machine import WDT
from machine import RTC
from network import LoRa

## Set RTC for timestamping (although it's not currently used)

rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
utime.sleep_ms(750)

print("\nRTC Set from NTP to UTC:", rtc.now())

utime.timezone(7200)

print("Adjusted from UTC to EST timezone", utime.localtime(), "\n")

## Set up the LoRa in longer range mode

lora = LoRa(mode=LoRa.LORA, frequency=868000000, tx_power=14, bandwidth=LoRa.BW_125KHZ, sf=7)
l = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
l.setblocking(False)

## Set up web socket

wdt = WDT(timeout=5000)
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

s = socket.socket()
s.settimeout(1)
s.bind(addr)
s.listen(1)

print("listening on", addr)

## Threaded server

def _serve():
    while True:
        wdt.feed()
        method, route, proto = None, None, None
        ts = utime.time()

        try:
            cl, addr = s.accept()

        except OSError:
            continue

        print("client connected from", addr)

        while True:
            try:
                line = cl.readline()
                print(line)

                ## Only handle GET requests

                if line[0:3] == b"GET":
                    method, route, proto = line.split(b" ")

                if not line or line == b'\r\n':
                    break

            except MemoryError:
                cl.send(" ")
                cl.close()
                continue

        ## Boilerplate JSON response
        
        response = """HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Cache-Control: no-cache
Pragma: no-cache
Content-Type: application/javascript\r\n\r\n{
    "position": {
        "latitude": %f, 
        "longitude": %f
    }, 
    "message": "%s", 
    "timestamp": %i
}"""

        ## Crude hack to handle URL routes

        if route is not None:
            route = route.split(b"/")
            route.pop(0)
            print(route)

            ## If position.json is requested then receive LoRa message from sender

            if route[0] == b"position.json":
                msg = l.recv(64)

                ## Decode and split out into latitude and longitude

                if not msg == b"":
                    msg = msg.decode("utf-8")
                    lat, lon = [float(i) for i in msg.split(",")]
                    response = response % (lat, lon, "success", ts)
                    print(response)
                
                ## Otherwise, send 404

                else:
                    response = """HTTP/1.1 404 Not Found
Access-Control-Allow-Origin: *
Cache-Control: no-cache
Pragma: no-cache
"""
                    print(response)

            ## Handles missing routes by sending 404

            else:
                response = """HTTP/1.1 404 Not Found
Access-Control-Allow-Origin: *
Cache-Control: no-cache
Pragma: no-cache
"""
        
        cl.send(response)
        cl.close()

## Start the thread

_thread.start_new_thread(_serve, ())
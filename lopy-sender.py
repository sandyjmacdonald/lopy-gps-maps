import time
import gc
import socket
from L76GNSS import L76GNSS
from pytrack import Pytrack
from network import LoRa

## Set up the LoRa in longer range mode

lora = LoRa(mode=LoRa.LORA, frequency=868000000, tx_power=14, bandwidth=LoRa.BW_125KHZ, sf=7)
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

## Enable garbage collection

time.sleep(2)
gc.enable()

## Set up GPS with modest timeout

py = Pytrack()
l76 = L76GNSS(py, timeout=10)

## Defaults for last known latitude, longitude

last_lon = 0
last_lat = 0

min_twitch = 0.000010  ## Attempts to reduce local twitchiness

while True:
    coord = l76.coordinates()  ## Gets coordinates
    if not coord == (None, None):
        lat, lon = coord
    	if abs(lat - last_lat) > min_twitch or abs(lon - last_lon) > min_twitch:
            s.send("%f,%f" % (lat, lon))  ## Send the coordinates over LoRa
            last_lat = lat
            last_lon = lon
        else:
            s.send("%f,%f" % (last_lat, last_lon))  ## Send last known coordinates
        print(lat, lon)
    else:
        print("No coordinates found")
import time
import network
import espnow
import asyncio
import neopixel
import machine
import json

# A pos/neg integer to adjust the ticks_ms value. will be set by receiving sync messages.
time_delta = 0
master_mode = True
last_packet_received = time.ticks_ms()

def get_time():
    return time.ticks_add(time.ticks_ms(), time_delta)

def mac2str(bytestring):
    return ':'.join('{:02x}'.format(b) for b in bytestring)

"""
function called when we receive a message
"""
def recv_cb(e):
    while True:
        mac, msg = e.irecv(0)
        if mac is None:
            return
        print(mac, msg)

def setup_network():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    en = espnow.ESPNow()
    en.active(True)
    en.add_peer(b'\xff\xff\xff\xff\xff\xff')
    en.irq(recv_cb)
    return (sta, en)
    
sta, en = setup_network()

#give the network the time to communicate.
time.sleep(.2)

mac = sta.config("mac")
print("mac:",mac2str(mac))
#en.config(rate=0) #1Mit long preamble

async def animate():
    while True:
        strand = neopixel.NeoPixel(machine.Pin(2),5)
        frame = (get_time() // 100) % 5
        for i in range(5): strand[i] = (16,0,0)
        strand[frame] = (0,0,64)
        strand.write()
        await asyncio.sleep_ms(30)

async def send_time(en):
    while True:
        if master_mode:
            en.send(b'\xff\xff\xff\xff\xff\xff', json.dumps({"time":get_time()}).encode())
        await asyncio.sleep_ms(1000)        

async def main(en):
    display_thread = asyncio.create_task(animate())
    time_thread = asyncio.create_task(send_time(en))
    await display_thread

asyncio.run(main(en))
        

"""
async
1) setup stuff
2) run send time every x ms (1000 for test)
3) run update animation every 33ms
"""



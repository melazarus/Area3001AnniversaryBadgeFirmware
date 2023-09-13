# a firmware for the Area3001 10Y badge.
import aioespnow
import asyncio
import json
import machine
import neopixel
import network
import time

from animations import Fri3d2022 as animation

DEBUG = const(False)
CHANNEL = const(1)
TX_DELAY = const(1)
NEOPIXEL_PIN = const(2)
FRAMERATE = const(30)
STRAND_LENGTH = const(5)

def log(*args):
    if DEBUG:
        print(*args)

"""
    Animation section
"""

def get_frame_count(animation):
    if "frame_count" not in animation:
        animation["frame_count"] = sum([x[0] for x in animation["frames"]])
    return animation["frame_count"]

def get_active_frame(animation, frame_num):
    index = 0
    frame = animation["frames"][index]
    max_frame = frame[0]
    while max_frame <= frame_num:
        index += 1
        frame = animation["frames"][index]
        max_frame += frame[0]
    return frame, max_frame

def str2color(color):
    assert len(color) == 3
    return [int(x,16)*17 for x in color]

def wheel(index:int, volume:int=255) -> tuple(int,int,int):
    index = index % 360
    volume = max(volume,1)
    volume = min(volume,255)
    if index < 60:
        return (volume,index*volume//60,0)
    if index < 120:
        return((120-index)*volume//60,volume,0)
    if index < 180:
        return (0,volume,(index-120)*volume//60)
    if index < 240:
        return (0,(240-index)*volume//60,volume)
    if index < 300:
        return ((index-240)*volume//60,0,volume)
    return (volume,0,(360-index)*volume//60)

def process_rgb(strand, pixel_index, r):
    pixels = 1
    if type(r[-1]) is int:
        pixels = r[-1]
    for i in range(pixels):
        strand[pixel_index+i] = str2color(r[0])
    return pixels

def process_wheel(strand, pixel_index, r, offset):
    pixels = 1
    if type(r[-1]) is int:
        pixels = r[-1]
    steps = 360 // pixels
    if r[1] == ">":
        for i in range(0,pixels):
            strand[pixel_index+i] = wheel(i*steps+offset,50)
    if r[1] == "<":
        for i in range(0, pixels):
            strand[pixel_index+(pixels-i-1)] = wheel((pixels-i)*steps+offset)
    return pixels

def show_frame(strand, animation, frame_num):
    frame_count = get_frame_count(animation)
    buffer = [(0,0,0)]*STRAND_LENGTH
    assert frame_count > frame_num, "frame number is to high"
    active_frame, max_frame = get_active_frame(animation, frame_num)
    pixel_index=0
    for r in active_frame[1:]:
        if len(r[0]) == 3: pixel_index += process_rgb(buffer, pixel_index, r)
        if r[0] == "W": pixel_index += process_wheel(buffer, pixel_index, r, (max_frame-frame_num)*5)
    for i in range(STRAND_LENGTH):
        strand[i] = buffer[animation["mapping"][i]]
    strand.write()

async def animation_task(network_time_service, pin):
    #setup neopixels
    strand = neopixel.NeoPixel(machine.Pin(pin),STRAND_LENGTH)
    frame_length = 1000//FRAMERATE
    frame_count = get_frame_count(animation)
    last_frame = 0
    while True:
        network_time = network_time_service.ticks_ms()
        if network_time < last_frame or network_time > (last_frame+frame_length):
            frame_id = network_time//frame_length
            last_frame = frame_id*frame_length
            show_frame(strand, animation, frame_id%frame_count)
        await asyncio.sleep(0)

"""
    Time sync via ESPNOW section
"""
    
class EspnowTimeSync():
    def __init__(self):
        self._espnow = None
        self._is_master = False
        self._sta_mac = None
        self._time_delta = 0
        self._last_time_received = time.ticks_ms()
        self._packets_received = 0
        
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.config(channel=CHANNEL)
        self._sta_mac = sta.config("mac")

        self._espnow = aioespnow.AIOESPNow()
        self._espnow.active(True)
        self._espnow.add_peer(b'\xff\xff\xff\xff\xff\xff')

    async def listener(self):
        log("listener started")
        async for mac, msg in self._espnow:
            log("packet")
            now = time.ticks_ms()
            delta_time = self.ticks_ms()
            if mac is None:
                continue
            log(f"mac > self._sta_mac =",mac > self._sta_mac)
            if mac > self._sta_mac or self._packets_received < 3:
                message = json.loads(msg.decode())
                self._time_delta = message["time"]-now
                log("set time")
                self._last_time_received = time.ticks_ms()
                if self._is_master:
                    self._is_master = False
                    log("demoting")
                self._packets_received += 1
        log("listener stopped")

    async def sender(self):
        while True:
            if self._is_master:
                await self._espnow.asend(b'\xff\xff\xff\xff\xff\xff', json.dumps({"time":self.ticks_ms()}).encode())
                log("tx")
            elif time.ticks_ms() - self._last_time_received > (TX_DELAY*3*1000):
                self._is_master = True
                log("promoting to master")
            log("time:",self.ticks_ms())
            await asyncio.sleep(TX_DELAY)
            
    def ticks_ms(self):
        return time.ticks_add(time.ticks_ms(), self._time_delta)
    

#send updates
    #get package
    
"""
    Code entry point
"""
    
async def main():
    network_time = EspnowTimeSync()
    animation_task_instance = asyncio.create_task(animation_task(network_time, NEOPIXEL_PIN))
    listener_task_instance = asyncio.create_task(network_time.listener())
    sender_task_instance = asyncio.create_task(network_time.sender())
    #network_task_instance = asyncio.create_task(espnow_network(state_object))
    await animation_task_instance


asyncio.run(main())
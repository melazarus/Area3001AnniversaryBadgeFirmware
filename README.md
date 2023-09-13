# Area3001AnniversaryBadgeFirmware
Test firmware for the Area3001 anniversary badge.

**Content:**
* [Installation](#installation)
* [How it works](#how-it-works)

# installation
1) Download micropython for ESP32.  
   This firmware depends on the espnow feature of ESP. This is not yet available in 1.20.0   
   [Download](https://micropython.org/download/ESP32_GENERIC/) a Nightly build untill the espnow feature is in the release version  
2) Flash the firmware to the badge using your favorite tool   
   _See instructions on the download page_
3) Copy the files inside the sources directory to the root of the ESP filesystem.   
   This can be done using [Thonny](https://thonny.org/), [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) or other tools.
   
# How it works

## Time synchronization
1) On startup the ESP will listen for any packet containing a time value inside a JSON document. If such a packet is received within 3 seconds it will synchronize it's time value with the remote ESP.
2) If no other devices are found it will assume a master role and start transmitting it's own time every second.
3) if other devices are allready there it can do 2 things.  
  a) the other mac is larger: exit master mode, stop broadcasting  
  b) there is not higher mac: enter master mode
4) When the current master stops transmitting for more than 3 seconds all ESP's will enter master mode and broadcast their current time. The ESP with the highest mac address wins and becomes the new master.

## Animation
The animation is devided in frames of each 33ms long (30FPS).  
A every 33ms a function is called to draw a frame. the id of the frame is calculated by taking the modulus of the current network time devided by 33.   
`
frame_id = (network_time // frame_length) % frame_count
`

Frame types that are currently implemented:
- solid color
- Color wheel. (left or right shifting)

Some ideas of frame types I like to add are: wheel that shifts in time, sparkle, gradient (moving or solid), chase and bounce.   
In a future version I might be tempted to add regions that each have their own animaton, however I feel this is a bit overkill for now :)


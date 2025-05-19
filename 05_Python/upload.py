# -*- coding: utf-8 -*-
"""
Created on Tue May  6 09:32:57 2025
@author: Jon Dawson, Joe G. (Feinmechaniker)

The original tool comes from Jon Dawson
https://github.com/dawsonjon/PicoRX/tree/master/memory_loader

The tool saves a data block with frequency information on the
Pi-Pico-RX. The frequency information is saved in a CSV file.
A configuration with the name of the CSV file and the COM port can be found 
in the file config.json.

1. Menu -> HW Config
2. HW Config -> USB Upload
3. USB Upload -> Ready for memories
4. start -> upload.py

Program history
05.05.2025    V. 1.0    Start
07.05.2025    V. 1.1    Modes definitions corrected (see rx_definitions.h) 
17.05.2025    V. 1.2    9kHz frequency step for Europe, Asia, Central and South America
"""

__version__ = '1.2'
__author__ = 'Jon Dawson, Joe G. (Feinmechaniker)'


import serial
import struct
import json

def load_config(path="config.json"):
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        dateiname = config.get("filename")
        com_port = config.get("com_port")
        if not dateiname or not com_port:
            raise ValueError("Missing entries in the configuration file.")
        return dateiname, com_port
    except FileNotFoundError:
        print(f"File '{path}' not found.")
    except json.JSONDecodeError:
        print("Error reading the JSON file.")
    except Exception as e:
        print(f"An error has occurred: {e}")
    return None, None


def read_csv(filename):
  channels = []
  with open(filename) as inf:
    for line in inf:
      line = line.strip()
      line = line.split(",")
      line = [i.strip() for i in line]
      channels.append(line)
  return channels

def pack(string):
    return (ord(string[0]) << 24) + (ord(string[1]) << 16) + (ord(string[2]) << 8) + ord(string[3])

def convert_channel_to_hex(channel):
  name, frequency, min_frequency, max_frequency, mode, agc_speed, step = channel

  if len(name) < 16:
    name += " " * (16-len(name))

  modes = { "AM" :0, "AMS":1, "LSB":2, "USB":3, "NFM":4, "CW" :5 }
  agc_speeds = {"FAST": 0, "NORMAL": 1, "SLOW": 2, "VERY SLOW": 3}
  steps = { "10Hz": 0, "50Hz": 1, "100Hz": 2, "1kHz": 3, "5kHz": 4, "9kHz": 5, "10kHz": 6, "12.5kHz": 7, "25kHz": 8, "50kHz": 9, "100kHz": 10,}

  data = [
    int(frequency)&0xffffffff,     #0
    modes[mode],                   #1
    agc_speeds[agc_speed],         #2
    steps[step],                   #3
    int(max_frequency)&0xffffffff, #4
    int(min_frequency)&0xffffffff, #5
    pack(name[0:4]),               #6
    pack(name[4:8]),               #7
    pack(name[8:12]),              #8
    pack(name[12:16]),             #9
    0xffffffff,                    #a
    0xffffffff,                    #b
    0xffffffff,                    #c
    0xffffffff,                    #d
    0xffffffff,                    #e
    0xffffffff,                    #f
  ]
  return data, name.strip()

def read_memory(filename):
  data = read_csv(filename)[1:]
  data = [convert_channel_to_hex(i) for i in data]
  data = data[:512]
  return data
    
filename, port = load_config()
if not filename or not port:
    exit(1)

#send csv file to pico via USB
print("wait for upload...")
buffer = read_memory(filename)
with serial.Serial(port, 12000000, rtscts=1) as ser:

    #clear any data in buffer
    while ser.in_waiting:
      ser.read(ser.in_waiting)

    with open(filename, 'rb') as input_file:
      for index, (channel, name) in enumerate(buffer, start=1):
        for location in channel:
          data = bytes("%x\n" % (location), "utf8")  
          ser.write(bytes("%x\n"%(location), "utf8"))
          ser.readline()
        print(f"send [{index}]: {name}")  
      ser.write(bytes("q\n", "utf8"))
      print("Transmission completed - all channels have been sent successfully.")


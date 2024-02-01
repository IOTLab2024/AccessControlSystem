#!/usr/bin/env python3

from typing import NamedTuple
from datetime import datetime

import sys
import time
import RPi.GPIO as GPIO
import board
from neopixel import NeoPixel
from mfrc522 import MFRC522
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
import lib.oled.SSD1331 as SSD1331

from config import *


Color = NamedTuple(
    'Color', [
        ('red', int), 
        ('green', int), 
        ('blue', int)
    ]
)
BLANK_COLOR = Color(0, 0, 0)
RED_COLOR = Color(255, 0, 0)
GREEN_COLOR = Color(0, 255, 0)

FONT_LARGE = ImageFont.truetype('./lib/oled/Font.ttf', 20)
FONT_SMALL = ImageFont.truetype('./lib/oled/Font.ttf', 13)

BROKER = '10.108.33.123'
room_name: str

client = mqtt.Client()
pixels = NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
rfid_reader = MFRC522()

# display = SSD1331.SSD1331()
# display.Init()
# display.clear()
# image = Image.new("RGB", (display.width, display.height), "WHITE")
# draw = ImageDraw.Draw(image)

def buzzer_state(state):
    GPIO.output(buzzerPin, not state)

def buzzer_pattern(iterations: int, buzzer_length: float, pause_length: float):
    for i in range(iterations):
        buzzer_state(True)
        time.sleep(buzzer_length)
        buzzer_state(False)
        if i != iterations:
            time.sleep(pause_length)

def read_success(timestamp):
    pixels.fill(GREEN_COLOR)
    pixels.show()
    # draw.text((8, 0), u'hello', font=FONT_LARGE, fill="BLACK")
    # display.ShowImage(image, 0, 0)
    buzzer_pattern(iterations=1, buzzer_length=1, pause_length=0)
    pixels.fill(BLANK_COLOR)
    pixels.show()

def read_failure():
    pixels.fill(RED_COLOR)
    pixels.show()
    buzzer_pattern(iterations=3, buzzer_length=0.5, pause_length=0.25)
    pixels.fill(BLANK_COLOR)
    pixels.show()

def on_connect(client, userdata, flags, rc):
    print(f'Connected with result code {rc}')
    client.subscribe(f'server/{room_name}/register-room')

def on_message(client, userdata, message):
    topic = message.topic.split('/')
    message_decoded = str(message.payload.decode('utf-8'))
    
    action = topic[2]
    
    print(str(topic) + ' ')
    print(message_decoded)

    if action == 'register-room':
        if message_decoded == 'success':
            print('Room added to database')
        elif message_decoded == 'failure':
            print('Room adding to database failed') 
    elif action == 'scan-card':
        if message_decoded == 'closed':
            read_failure()
        else:
            timestamp = message_decoded.split(';')[1]
            read_success(timestamp)
            
def register_room():
    try:
        client.publish(f'client/{room_name}/register-room', 'register')
        time.sleep(2)
    except KeyboardInterrupt:
        client.disconnect()
    
scan_log = {}
               
def read_rfid_data():
    (status, TagType) = rfid_reader.MFRC522_Request(rfid_reader.PICC_REQIDL)
    if status == rfid_reader.MI_OK:
        (status, uid) = rfid_reader.MFRC522_Anticoll()
        if status == rfid_reader.MI_OK:
            scan_datetime = datetime.now()
            rfid = 0
            for i in range(0, len(uid)):
                rfid += uid[i] << (i*8)
            # print(f'Card ID: {rfid}')
            # print(f'Date and time of scanning: {scan_datetime}')
            scan_timestamp = datetime.timestamp(scan_datetime)
            if rfid in scan_log:
                if scan_timestamp - scan_log[rfid] < 5.0:
                    return
            scan_log[rfid] = scan_timestamp
            scan_datetime_str = datetime.strftime(scan_datetime, '%Y-%m-%d %H:%M:%S')
            client.publish(f'client/{room_name}/scan-card/{rfid}', scan_datetime_str)
            client.subscribe(f'server/{room_name}/scan-card/{rfid}')


if __name__ == '__main__':
    client.on_connect = on_connect
    client.on_message = on_message
    
    room_name = '-'.join(
        input('Enter room name: ').strip().lower().split()
    )
    
    client.connect(BROKER)
    client.loop_start()
    
    try:
        register_room()
        while True:
            read_rfid_data()
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        GPIO.cleanup()

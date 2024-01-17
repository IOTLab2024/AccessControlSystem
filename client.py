#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
from datetime import datetime
from config import *
from mfrc522 import MFRC522
import neopixel
import board
import RPi.GPIO as GPIO

Color = tuple[int, int, int]
BLANK_COLOR = Color(0, 0, 0)
RED_COLOR = Color(255, 0, 0)
GREEN_COLOR = Color(0, 255, 0)

pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)

room_name = "room1"

def buzzer_state(state):
    GPIO.output(buzzerPin, not state)  # pylint: disable=no-member

def buzzer_pattern(iterations: int, buzzer_length: float, pause_length: float):
    for i in range(iterations):
        buzzer_state(True)
        time.sleep(buzzer_length)
        buzzer_state(False)
        if i != iterations:
            time.sleep(pause_length)

def read_success():
    pixels.fill(GREEN_COLOR)
    buzzer_pattern(iterations=1, buzzer_length=1, pause_length=0)
    pixels.fill(BLANK_COLOR)

def read_failure():
    pixels.fill(RED_COLOR)
    buzzer_pattern(iterations=3, buzzer_length=0.5, pause_length=0.25)
    pixels.fill(BLANK_COLOR)


def blink():
    GPIO.output(led1, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(led1, GPIO.LOW)
    time.sleep(1)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(f"server/room/{room_name}")
    

def on_message(client, userdata, message):
    topic = message.topic.split("/")
    message_decoded = str(message.payload.decode("utf-8"))
    action = topic[1]
    return_message: str

    if action == "room":
        room_name = topic[2]
        if message_decoded == "success":
            print("Room added to database")
        elif  message_decoded == "failure":
            print("Room adding to database failed")
            
    elif action == "card":
        if message_decoded == "closed":
            read_failure()
        else:
            read_success()
               

def get_rfid_publish_data(client):
    rifd_reader = MFRC522()
    last_scan = datetime.timestamp(datetime.now()) - 5
    while True:
        if datetime.timestamp(datetime.now()) - last_scan > 5.0:
            (status, TagType) = rifd_reader.MFRC522_Request(rifd_reader.PICC_REQIDL)
            if status == rifd_reader.MI_OK:
                (status, uid) = rifd_reader.MFRC522_Anticoll()
                if status == rifd_reader.MI_OK:
                    dt = datetime.now()
                    num = 0
                    for i in range(0, len(uid)):
                        num += uid[i] << (i*8)
                    print(f"Card read UID: {num}")
                    print(f"Date and time of scanning: {dt}")
                    client.publish(f"client/card/{num}", f"{dt}, {room_name}")
                    client.subscribe(f"server/card/{num}")

def register_room(client):
    try:
        client.publish(f"client/room/{room_name}", room_name)
        # Wait for the server response
        time.sleep(2)
    except KeyboardInterrupt:
        client.disconnect()

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect() # TODO: add broker ip address/port

    # Register room
    register_room(client)
    # Get RFID data
    get_rfid_publish_data(client)
        

if __name__ == '__main__':
    main()

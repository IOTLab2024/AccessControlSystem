#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import sqlite3
import time

connection = sqlite3.connect('iotDB.db')
cursor = connection.cursor()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code {rc}")
    client.subscribe("client/room/+")
    client.subscribe("client/card/+")

def on_message(client, userdata, message):
    topic = message.topic.split("/")
    message_decoded = str(message.payload.decode("utf-8"))
    action = topic[1]
    return_message: str
    
    if action == "room":
        room_name = topic[2]
        if register_room(room_name):
            return_message = "success"
        else:
            return_message = "failure"
        client.publish(f"server/{action}/{room_name}", return_message)
    elif action == "card":
        rfid = topic[2]
        if validate_card(rfid, message_decoded):
            if is_user_in_room(rfid):
                return_message = "exit"
            else:
                return_message = "entry"
            #return_message = f"Card {rfid} is authenticated"
        else:
            return_message = "closed"
        client.publish(f"server/{action}/{rfid}", return_message)
            
    
def register_room(room_name):
    try:
        cursor.execute(f"INSERT INTO Room (name) VALUES ('{room_name}')")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        return False

def validate_card(rfid, message):
    cursor.execute(f"""
        SELECT *
        FROM User
        WHERE rfid = '{rfid}' AND is_authenticated = 1
    """)
    result = cursor.fetchone()
    if result:
        connection.commit()
        return True
    else:
        cursor.execute(f"INSERT INTO User (rfid) VALUES ('{rfid}')")
        connection.commit()
        # If no matching record is found, the card is not valid
        return False

def get_id_from_rfid(rfid):
    cursor.execute(f"""
        SELECT user_id
        FROM User
        WHERE rfid = '{rfid}'
    """)
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

def is_user_in_room(rfid):
    user_id = get_id_from_rfid(rfid)
    cursor.execute(f"""
        SELECT *
        FROM CurrentUserRoom
        WHERE user_id = {user_id}
    """)
    result = cursor.fetchone()
    if result:
        # User is in room
        cursor.execute(f"""
            DELETE FROM CurrentUserRoom
            WHERE user_id = {user_id}
        """)
        cursor.execute(f"""
            INSERT INTO Log (user_id, room_id, entry_timestamp, exit_timestamp)
            VALUES ({user_id}, {result[1]}, '{result[2]}', '{time.strftime('%Y-%m-%d %H:%M:%S')}')
        """)
        connection.commit()
        return True
    else:
        # User is not in room
        cursor.execute(f"""
            SELECT room_id
            FROM Room
            WHERE name = 'room1'
        """)
        room_id = cursor.fetchone()[0]
        cursor.execute(f"""
            INSERT INTO CurrentUserRoom (user_id, room_id, entry_timestamp)
            VALUES ({user_id}, {room_id}, '{time.strftime('%Y-%m-%d %H:%M:%S')}')
        """)
        connection.commit()
        return False
            
def run_server():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

if __name__ == "__main__":
    run_server()
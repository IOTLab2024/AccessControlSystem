#!/usr/bin/env python3

from pathlib import Path
import sqlite3
import time
import paho.mqtt.client as mqtt


BROKER = '10.108.33.123'
DATABASE_PATH = Path(__file__).parent / 'iotDB.db'

client = mqtt.Client()

def establish_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    return connection, cursor

def on_connect(client, userdata, flags, rc):
    print(f'Connected with result code {rc}')
    client.subscribe('client/room/+')
    client.subscribe('client/card/+')

def on_message(client, userdata, message):
    topic = message.topic.split('/')
    print(str(topic) + ' ')
    message_decoded = str(message.payload.decode('utf-8'))
    print(message_decoded)
    subject = topic[1]
    return_message: str
    
    if subject == 'room':
        room_name = topic[2]
        if register_room(room_name):
            return_message = 'success'
        else:
            return_message = 'failure'
        client.publish(f'server/{subject}/{room_name}', return_message)
    elif subject == 'card':
        rfid = topic[2]
        if validate_card(rfid, message_decoded):
            if is_user_in_room(rfid):
                return_message = 'exit'
            else:
                return_message = 'entry'
        else:
            return_message = 'closed'
        client.publish(f'server/{subject}/{rfid}', return_message)

def register_room(room_name):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'INSERT INTO Room (name) VALUES ("{room_name}")')
        connection.commit()
        return True
    except Exception as e:
        print(e)
        return False

def validate_card(rfid, message):
    connection, cursor = establish_database_connection()
    cursor.execute(f'''
        SELECT *
        FROM User
        WHERE rfid = '{rfid}' AND is_authorized = 1
    ''')
    result = cursor.fetchone()
    if result:
        connection.commit()
        connection.close()
        return True
    else:
        try:
            cursor.execute(f'INSERT INTO User (rfid) VALUES ("{rfid}")')
            connection.commit()
        except:
            pass
        # If no matching record is found, the card is not valid
        connection.close()
        return False

def get_id_from_rfid(rfid):
    connection, cursor = establish_database_connection()
    cursor.execute(f'''
        SELECT user_id
        FROM User
        WHERE rfid = '{rfid}'
    ''')
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0]
    else:
        return None

def is_user_in_room(rfid):
    connection, cursor = establish_database_connection()
    user_id = get_id_from_rfid(rfid)
    cursor.execute(f'''
        SELECT *
        FROM CurrentUserRoom
        WHERE user_id = {user_id}
    ''')
    result = cursor.fetchone()
    if result:
        # User is in room
        cursor.execute(f'''
            DELETE FROM CurrentUserRoom
            WHERE user_id = {user_id}
        ''')
        cursor.execute(f'''
            INSERT INTO Log (user_id, room_id, entry_timestamp, exit_timestamp)
            VALUES ({user_id}, {result[1]}, '{result[2]}', '{time.strftime('%Y-%m-%d %H:%M:%S')}')
        ''')
        connection.commit()
        connection.close()
        return True
    else:
        # User is not in room
        cursor.execute(f'''
            SELECT room_id
            FROM Room
            WHERE name = 'room1'
        ''')
        room_id = cursor.fetchone()[0]
        cursor.execute(f'''
            INSERT INTO CurrentUserRoom (user_id, room_id, entry_timestamp)
            VALUES ({user_id}, {room_id}, '{time.strftime('%Y-%m-%d %H:%M:%S')}')
        ''')
        connection.commit()
        connection.close()
        return False
            

if __name__ == '__main__':
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(BROKER)
    client.loop_start()
    
    try:
        while True:
            ...
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
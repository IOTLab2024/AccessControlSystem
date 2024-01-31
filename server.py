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
        room_name = message_decoded.split(',')[1].strip()
        if validate_card(rfid, room_name, message_decoded):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if is_user_in_room(rfid, room_name, timestamp):
                return_message = f'exit;{timestamp};{room_name}'
            else:
                return_message = f'entry;{timestamp};{room_name}'
        else:
            return_message = 'closed'
        client.publish(f'server/{subject}/{rfid}', return_message)

def get_user_id_room_id(rfid, room_name):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'''
            SELECT User.user_id FROM User
            WHERE User.rfid = "{rfid}"
        ''')
        user_id = cursor.fetchone()
        cursor.execute(f'''
            SELECT Room.room_id FROM Room
            WHERE Room.name = "{room_name}"
        ''')
        room_id = cursor.fetchone()
        connection.close()
        return user_id, room_id
    except Exception as e:
        print(e)
        return None

def register_room(room_name):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'INSERT INTO Room (name) VALUES ("{room_name}")')
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print(e)
        return False

def validate_card(rfid, room_name, message):
    connection, cursor = establish_database_connection()
    user_id, room_id = get_user_id_room_id(rfid, room_name)
    cursor.execute(f'''
        SELECT *
        FROM AuthenticatedUserRoom
        WHERE user_id = "{user_id}" AND room_id = "{room_id}"
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
        WHERE rfid = "{rfid}"
    ''')
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0]
    else:
        return None

def is_user_in_room(rfid, room_name, timestamp):
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
            VALUES ({user_id}, {result[1]}, "{result[2]}", "{timestamp}")
        ''')
        connection.commit()
        connection.close()
        return True
    else:
        # User is not in room
        cursor.execute(f'''
            SELECT room_id
            FROM Room
            WHERE name = "{room_name}"
        ''')
        room_id = cursor.fetchone()[0]
        cursor.execute(f'''
            INSERT INTO CurrentUserRoom (user_id, room_id, entry_timestamp)
            VALUES ({user_id}, {room_id}, "{timestamp}")
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
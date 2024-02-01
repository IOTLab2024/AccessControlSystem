#!/usr/bin/env python3

import paho.mqtt.client as mqtt

from database import establish_database_connection
from admin import get_user_id_from_rfid, get_room_id_from_name


BROKER = '10.108.33.123'

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f'Connected with result code {rc}')
    client.subscribe('client/+/register-room')
    client.subscribe('client/+/scan-card/+')

def on_message(client, userdata, message):
    topic = message.topic.split('/')
    message_decoded = str(message.payload.decode('utf-8'))
    
    room_name = topic[1]
    action = topic[2]
    
    # print(str(topic) + ' ')
    # print(message_decoded)

    return_message: str
    if action == 'register-room':
        if register_room(room_name):
            return_message = 'success'
        else:
            return_message = 'failure'
        client.publish(f'server/{room_name}/{action}', return_message)
    elif action == 'scan-card':
        rfid = topic[3]
        timestamp = message_decoded
        if validate_card(rfid, room_name):
            if is_user_in_room(rfid, room_name, timestamp):
                return_message = f'exit;{timestamp}'
            else:
                return_message = f'entry;{timestamp}'
        else:
            return_message = 'closed'
        client.publish(f'server/{room_name}/{action}/{rfid}', return_message)

def register_room(room_name):
    try:
        connection, cursor = establish_database_connection()
        
        cursor.execute('INSERT INTO Room (name) VALUES (?)', (room_name,))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print(e)
        return False

def validate_card(rfid, room_name):
    user_id = get_user_id_from_rfid(rfid)
    room_id = get_room_id_from_name(room_name)
    connection, cursor = establish_database_connection()
    
    cursor.execute('''
        SELECT * FROM AuthenticatedUserRoom
        WHERE user_id = ? AND room_id = ?
    ''', (user_id, room_id))
    result = cursor.fetchone()
    if result:
        connection.commit()
        connection.close()
        return True
    else:
        try:
            cursor.execute('INSERT INTO User (rfid) VALUES (?)', (rfid,))
            connection.commit()
        except:
            pass
        connection.close()
        # If no matching record is found, the card is not valid
        return False


def is_user_in_room(rfid, room_name, timestamp):
    user_id = get_user_id_from_rfid(rfid)
    room_id = get_room_id_from_name(room_name)
    connection, cursor = establish_database_connection()
    
    cursor.execute('''
        SELECT * FROM CurrentUserRoom
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    if result:
        # User is in room
        cursor.execute('''
            DELETE FROM CurrentUserRoom
            WHERE user_id = ?
        ''', (user_id,))
        cursor.execute('''
            INSERT INTO Log (user_id, room_id, entry_timestamp, exit_timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, result[1], result[2], timestamp,))
        connection.commit()
        connection.close()
        return True
    else:
        # User is not in room
        cursor.execute('''
            INSERT INTO CurrentUserRoom (user_id, room_id, entry_timestamp)
            VALUES (?, ?, ?)
        ''', (user_id, room_id, timestamp,))
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

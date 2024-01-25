#!/usr/bin/env python3

from pathlib import Path
import os
import sqlite3


DATABASE_PATH = Path(__file__).parent / 'iotDB.db'

def delete_database():
    if DATABASE_PATH.exists():
        os.remove(DATABASE_PATH)
        print('Old database deleted.')


def create_database():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    
    cursor.execute('''
        CREATE TABLE User (
            user_id INTEGER PRIMARY KEY,
            rfid TEXT UNIQUE,
            is_authorized BOOLEAN DEFAULT false
        )
    ''')

    cursor.execute('''
        CREATE INDEX idx_rfid 
        ON User (rfid);
    ''')

    cursor.execute('''
        CREATE TABLE Room (
            room_id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE CurrentUserRoom (
            user_id INTEGER,
            room_id INTEGER,
            entry_timestamp DATETIME,
            PRIMARY KEY (user_id, room_id),
            FOREIGN KEY (user_id) REFERENCES User(user_id),
            FOREIGN KEY (room_id) REFERENCES Room(room_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE Log (
            log_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            room_id INTEGER,
            entry_timestamp DATETIME,
            exit_timestamp DATETIME,
            FOREIGN KEY (user_id) REFERENCES User(user_id),
            FOREIGN KEY (room_id) REFERENCES Room(room_id)
        )
    ''')
    
    connection.commit()
    connection.close()
    print('New database created')


if __name__ == '__main__':
    delete_database()
    create_database()
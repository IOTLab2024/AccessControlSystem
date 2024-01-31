#!/usr/bin/env python3

from pathlib import Path
import sqlite3
import argparse


DATABASE_PATH = Path(__file__).parent / 'iotDB.db'

def establish_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    return connection, cursor

def get_users(authorized: bool = False):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'SELECT rfid FROM User WHERE is_authorized = {authorized}')
        users = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    return users

def display_authorized_users():
    try:
        authorized_users = get_users(True)
        
        if not authorized_users:
            print('No authorized users.')
            return
            
        for i, user in enumerate(authorized_users, 1):
            print(f'{i}. {user[0]}')
    except Exception as e:
        print(e)
        return

def display_unauthorized_users():
    try:
        unauthorized_users = get_users(False)
        
        if not unauthorized_users:
            print('No unauthorized users.')
            return
            
        for i, user in enumerate(unauthorized_users, 1):
            print(f'{i}. {user[0]}')
    except Exception as e:
        print(e)
        return

def authorize_user(rfid: str):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'UPDATE User SET is_authorized = true WHERE rfid = "{rfid}"')
        connection.commit()
        connection.close()
        print(f'User with RFID {rfid} authorized successfully.')
    except Exception as e:
        print(e)
        return

def authorize_user_room(rfid: str, room_name: str):
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
        cursor.execute(f'''
            INSERT INTO AuthenticatedUserRoom (user_id, room_id)
            VALUES ({user_id}, {room_id})
        ''')
        connection.commit()
        connection.close()
        print(f'User with RFID {rfid} was granted access to room {room_name}.')
    except Exception as e:
        print(e)
        return


def display_users_in_room(room_name):
    try:
        connection, cursor = establish_database_connection()
        cursor.execute(f'''
            SELECT User.rfid FROM User
            INNER JOIN CurrentUserRoom ON User.user_id = CurrentUserRoom.user_id
            INNER JOIN Room ON CurrentUserRoom.room_id = Room.room_id
            WHERE Room.name = "{room_name}"
        ''')
        users = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    
    if users:
        print(f'Users in room "{room_name}": {", ".join(user[0] for user in users)}')
    else:
        print(f'No users in room "{room_name}".')

def display_current_users():
    try:
        connection, cursor = establish_database_connection()
        cursor.execute('''
            SELECT User.rfid, Room.name FROM User
            INNER JOIN CurrentUserRoom ON User.user_id = CurrentUserRoom.user_id
            INNER JOIN Room ON CurrentUserRoom.room_id = Room.room_id
        ''')
        user_room_data = cursor.fetchall()
        connection.close()

    
        if not user_room_data:
            print('No users are currently active in any room.')
            return
        
        print('Currently active users:')
        for user, room in user_room_data:
            print(f'{user} is in room "{room}".')
    except Exception as e:
        print(e)
        return

def display_recent_logs():
    try:
        connection, cursor = establish_database_connection()
        cursor.execute('''
            SELECT User.rfid, Room.name, Log.entry_timestamp, Log.exit_timestamp FROM User
            INNER JOIN Log ON User.user_id = Log.user_id
            INNER JOIN Room ON Log.room_id = Room.room_id
            ORDER BY Log.entry_timestamp DESC
            LIMIT 10
        ''')
        logs = cursor.fetchall()
        connection.close()
    
        if not logs:
            print('No recent logs.')
            return
    
        print('Recent logs:')
        for user, room, entry_time, exit_time in logs:
            exit_info = f', exited at {exit_time}' if exit_time else ''
            print(f'{user} entered room "{room}" at {entry_time}{exit_info}.')
    except Exception as e:
        print(e)
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI program for managing the database.')
    parser.add_argument('--authorized-users', action='store_true', help='Display all currently authorized users.')
    parser.add_argument('--unauthorized-users', action='store_true', help='Display all currently unauthorized users.')
    parser.add_argument('--authorize', type=str, help='Authorize user with specified RFID.')
    parser.add_argument('--users-in-room', type=str, help='Display users in a specific room.')
    parser.add_argument('--current-users', action='store_true', help='Display currently active users.')
    parser.add_argument('--recent-logs', action='store_true', help='Display recent logs.')

    args = parser.parse_args()

    if args.authorized_users:
        display_authorized_users()
    elif args.unauthorized_users:
        display_unauthorized_users()
    elif args.authorize is not None:
        authorize_user(args.authorize)
    elif args.users_in_room:
        display_users_in_room(args.users_in_room)
    elif args.current_users:
        display_current_users()
    elif args.recent_logs:
        display_recent_logs()
    else:
        print('No valid command provided. Use --help for usage information.')

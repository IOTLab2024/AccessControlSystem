#!/usr/bin/env python3

import argparse

from database import establish_database_connection


def get_user_id_from_rfid(rfid: str):
    try:
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            SELECT User.id FROM User
            WHERE User.rfid = ?
        ''', (rfid,))
        user_id = cursor.fetchone()
        connection.close()
        if not user_id:
            raise Exception(f'User with RFID {rfid} does not exist.')
        return user_id[0]
    except Exception as e:
        print(e)
        return
    
def get_room_id_from_name(name: str):
    try:
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            SELECT Room.id FROM Room
            WHERE Room.name = ?
        ''', (name,))
        room_id = cursor.fetchone()
        connection.close()
        if not room_id:
            raise Exception(f'Room with name {name} does not exist.')
        return room_id[0]
    except Exception as e:
        print(e)
        return
    
def display_users():
    try:
        connection, cursor = establish_database_connection()
        
        cursor.execute('SELECT rfid FROM User')
        users = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    
    if users:
        print(f'Users: {", ".join(user[0] for user in users)}')
    else:
        print('No users.')
        
def dipslay_rooms():
    try:
        connection, cursor = establish_database_connection()
        
        cursor.execute('SELECT name FROM Room')
        rooms = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    
    if rooms:
        print(f'Rooms: {", ".join(room[0] for room in rooms)}')
    else:
        print('No rooms.')
        
def display_user_authorized_rooms(rfid: str):
    try:
        user_id = get_user_id_from_rfid(rfid)
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            SELECT Room.name FROM Room
            INNER JOIN AuthenticatedUserRoom ON Room.id = AuthenticatedUserRoom.room_id
            WHERE AuthenticatedUserRoom.user_id = ?
        ''', (user_id,))
        rooms = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    
    if rooms:
        print(f'Rooms authorized for user with RFID {rfid}:')
        for room in rooms:
            print(f'{room[0]}')
    else:
        print(f'No rooms authorized for user with RFID {rfid}.')
        
def display_room_authorized_users(room_name: str):
    try:
        room_id = get_room_id_from_name(room_name)
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            SELECT User.rfid FROM User
            INNER JOIN AuthenticatedUserRoom ON User.id = AuthenticatedUserRoom.user_id
            WHERE AuthenticatedUserRoom.room_id = ?
        ''', (room_id,))
        users = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(e)
        return
    
    if users:
        print(f'Users authorized for room "{room_name}": {", ".join(user[0] for user in users)}')
    else:
        print(f'No users authorized for room "{room_name}".')


def authorize_user_room(rfid: str, room_name: str):
    try:
        user_id = get_user_id_from_rfid(rfid)
        room_id = get_room_id_from_name(room_name)
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            INSERT INTO AuthenticatedUserRoom (user_id, room_id)
            VALUES (?, ?)
        ''', (user_id, room_id,))
        connection.commit()
        connection.close()
        print(f'User with RFID {rfid} was granted access to room {room_name}.')
    except Exception as e:
        print(e)
        return

def display_users_in_room(room_name):
    try:
        room_id = get_room_id_from_name(room_name)
        connection, cursor = establish_database_connection()
        
        cursor.execute('''
            SELECT User.rfid FROM User
            INNER JOIN CurrentUserRoom ON User.id = CurrentUserRoom.user_id
            WHERE CurrentUserRoom.room_id = ?
        ''', (room_id,))
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
            INNER JOIN CurrentUserRoom ON User.id = CurrentUserRoom.user_id
            INNER JOIN Room ON CurrentUserRoom.room_id = Room.id
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
            INNER JOIN Log ON User.id = Log.user_id
            INNER JOIN Room ON Log.room_id = Room.id
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
    parser.add_argument('--users', action='store_true', help='Display all users.')
    parser.add_argument('--rooms', action='store_true', help='Display all rooms.')
    parser.add_argument('--user-rooms', type=str, help='Display all rooms a user with specified RFID has access to. (Format: --user-rooms <rfid>)')
    parser.add_argument('--room-users', type=str, help='Display all users a room with specified name can be accessed by. (Format: --room-users <room_name>)')
    parser.add_argument('--authorize', type=str, nargs=2, help='Grant access to a room with specified name to a user with specified RFID. (Format: --authorize <rfid> <room_name>)')
    parser.add_argument('--users-in-room', type=str, help='Display users in a room with specified name. (Format: --users-in-room <room_name>)')
    parser.add_argument('--current-users', action='store_true', help='Display currently active users.')
    parser.add_argument('--recent-logs', action='store_true', help='Display recent logs.')

    args = parser.parse_args()
    
    if args.users:
        display_users()
    elif args.rooms:
        dipslay_rooms()
    elif args.user_rooms:
        display_user_authorized_rooms(args.user_rooms)
    elif args.room_users:
        display_room_authorized_users(args.room_users)
    elif args.authorize is not None:
        authorize_user_room(args.authorize[0], args.authorize[1])
    elif args.users_in_room:
        display_users_in_room(args.users_in_room)
    elif args.current_users:
        display_current_users()
    elif args.recent_logs:
        display_recent_logs()
    else:
        print('No valid command provided. Use --help for usage information.')

import sqlite3
import argparse
from datetime import datetime

DATABASE_NAME = "iotDB.db"

def get_authenticated_users():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT rfid FROM User WHERE is_authenticated = true")
    authenticated_users = cursor.fetchall()
    connection.close()
    return authenticated_users

def authorize_user(user_number):
    authenticated_users = get_authenticated_users()

    if 1 <= user_number <= len(authenticated_users):
        selected_user_rfid = authenticated_users[user_number - 1][0]
        connection = sqlite3.connect(DATABASE_NAME)
        cursor = connection.cursor()
        cursor.execute("UPDATE User SET is_authenticated = true WHERE rfid = ?", (selected_user_rfid,))
        connection.commit()
        connection.close()
        print(f"User with RFID {selected_user_rfid} authorized successfully.")
    else:
        print("Invalid user number. Please choose a valid number.")

def display_authenticated_users():
    authenticated_users = get_authenticated_users()

    if authenticated_users:
        print("Authenticated users:")
        for i, user in enumerate(authenticated_users, 1):
            print(f"{i}. {user[0]}")
    else:
        print("No authenticated users.")

def display_users_in_room(room_name):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT User.rfid FROM User
        INNER JOIN CurrentUserRoom ON User.user_id = CurrentUserRoom.user_id
        INNER JOIN Room ON CurrentUserRoom.room_id = Room.room_id
        WHERE Room.name = ?
    """, (room_name,))
    users = cursor.fetchall()
    connection.close()
    
    if users:
        print(f"Users in room '{room_name}': {', '.join(user[0] for user in users)}")
    else:
        print(f"No users in room '{room_name}'.")

def display_current_users():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT User.rfid, Room.name FROM User
        INNER JOIN CurrentUserRoom ON User.user_id = CurrentUserRoom.user_id
        INNER JOIN Room ON CurrentUserRoom.room_id = Room.room_id
    """)
    user_room_data = cursor.fetchall()
    connection.close()
    
    if user_room_data:
        print("Currently active users:")
        for user, room in user_room_data:
            print(f"{user} is in room '{room}'.")
    else:
        print("No users are currently active in any room.")

def display_recent_logs():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT User.rfid, Room.name, Log.entry_timestamp, Log.exit_timestamp FROM User
        INNER JOIN Log ON User.user_id = Log.user_id
        INNER JOIN Room ON Log.room_id = Room.room_id
        ORDER BY Log.entry_timestamp DESC
        LIMIT 10
    """)
    logs = cursor.fetchall()
    connection.close()
    
    if logs:
        print("Recent logs:")
        for user, room, entry_time, exit_time in logs:
            exit_info = f", exited at {exit_time}" if exit_time else ""
            print(f"{user} entered room '{room}' at {entry_time}{exit_info}.")
    else:
        print("No recent logs.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CLI program for managing the database.")
    parser.add_argument('--authorize', type=str, help='Authorize user with specified RFID.')
    parser.add_argument('--users-in-room', type=str, help='Display users in a specific room.')
    parser.add_argument('--current-users', action='store_true', help='Display currently active users.')
    parser.add_argument('--recent-logs', action='store_true', help='Display recent logs.')

    args = parser.parse_args()

    if args.authorize is not None:
        display_authenticated_users()
        authorize_user(args.authorize)
    elif args.users_in_room:
        display_users_in_room(args.users_in_room)
    elif args.current_users:
        display_current_users()
    elif args.recent_logs:
        display_recent_logs()
    else:
        print("No valid command provided. Use --help for usage information.")

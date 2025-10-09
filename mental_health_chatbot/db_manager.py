import sqlite3
from datetime import datetime

DB_NAME = 'saathi_chat_history.db'

def init_db():
    """Initializes the SQLite database and creates the chat table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Saves a single chat message to the database."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (date, time, role, content)
        VALUES (?, ?, ?, ?)
    ''', (date_str, time_str, role, content))
    conn.commit()
    conn.close()



def view_all_data():
    """Retrieves and prints all data from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_data')
    data = cursor.fetchall()
    
    conn.close()
    
    print("\n--- All Stored Submissions ---")
    if not data:
        print("No data currently stored.")
        return

    # Print headers
    print(f"{'ID':<4} {'Name':<15} {'College':<25} {'Submission Time':<20} {'Message'}")
    print("-" * 80)
    
    # Print rows
    for row in data:
        # Truncate message for clean printing
        message_display = row[3][:40] + '...' if len(row[3]) > 40 else row[3]
        print(f"{row[0]:<4} {row[1]:<15} {row[2]:<25} {row[4]:<20} {message_display}")
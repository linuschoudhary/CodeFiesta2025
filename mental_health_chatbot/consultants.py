import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import streamlit as st

# Database for consultants
CONSULTANTS_DB = 'consultants.db'

def init_consultants_db():
    """Initialize the consultants database"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience_years INTEGER,
            availability TEXT DEFAULT '9 AM - 6 PM',
            is_active BOOLEAN DEFAULT 1,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample consultants if table is empty
    cursor.execute("SELECT COUNT(*) FROM consultants")
    if cursor.fetchone()[0] == 0:
        sample_consultants = [
            ('Dr. Prateeksha Khichi', 'sarah.johnson@mentalhealth.com', '+1-555-0101', 'Clinical Psychology', 12, '9 AM - 5 PM'),
            ('Dr. Sunil Choudhary', 'michael.chen@therapy.com', '+1-555-0102', 'Cognitive Behavioral Therapy', 8, '10 AM - 7 PM'),
            ('Dr. Abhishek Shrivastav', 'priya.sharma@counseling.com', '+1-555-0103', 'Trauma Therapy', 15, '8 AM - 4 PM'),
            ('Dr. Piyush Choudhan', 'robert.brown@psychiatry.com', '+1-555-0104', 'Psychiatry', 20, '9 AM - 6 PM'),
            ('Ms. Dipesh Soni', 'emily.davis@support.com', '+1-555-0105', 'Crisis Counseling', 6, '24/7 On-call')
        ]
        cursor.executemany('''
            INSERT INTO consultants (name, email, phone, specialization, experience_years, availability)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_consultants)
    
    conn.commit()
    conn.close()

def get_all_consultants():
    """Get all active consultants"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, email, phone, specialization, experience_years, availability 
        FROM consultants 
        WHERE is_active = 1
        ORDER BY experience_years DESC
    ''')
    consultants = cursor.fetchall()
    conn.close()
    return consultants

def get_consultant_by_id(consultant_id):
    """Get consultant by ID"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM consultants WHERE id = ? AND is_active = 1
    ''', (consultant_id,))
    consultant = cursor.fetchone()
    conn.close()
    return consultant

def add_consultant(name, email, phone, specialization, experience_years, availability):
    """Add a new consultant"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO consultants (name, email, phone, specialization, experience_years, availability)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, specialization, experience_years, availability))
    conn.commit()
    conn.close()

def update_consultant(consultant_id, name, email, phone, specialization, experience_years, availability):
    """Update consultant details"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE consultants 
        SET name = ?, email = ?, phone = ?, specialization = ?, experience_years = ?, availability = ?
        WHERE id = ?
    ''', (name, email, phone, specialization, experience_years, availability, consultant_id))
    conn.commit()
    conn.close()

def deactivate_consultant(consultant_id):
    """Deactivate a consultant"""
    conn = sqlite3.connect(CONSULTANTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE consultants SET is_active = 0 WHERE id = ?
    ''', (consultant_id,))
    conn.commit()
    conn.close()

def get_available_consultant():
    """Get a consultant for assignment (round-robin or based on availability)"""
    consultants = get_all_consultants()
    if consultants:
        # Simple round-robin assignment - in production, you might want more sophisticated logic
        return consultants[0]  # Return the first available consultant
    return None

def send_alert_to_consultant(consultant_email, consultant_name, user_chat_history, distress_score):
    """Send email alert to consultant (placeholder implementation)"""
    try:
        # This is a placeholder - you'll need to configure your email settings
        subject = f"🚨 High Distress Alert - User Needs Assistance"
        
        # Format chat history
        chat_summary = "\n".join([f"[{msg['time']}] {msg['role']}: {msg['content']}" 
                                for msg in user_chat_history])
        
        body = f"""
        Dear {consultant_name},
        
        A user has been identified with high distress levels and requires professional assistance.
        
        Distress Score: {distress_score}/100
        Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        Recent Chat History:
        {chat_summary}
        
        Please reach out to the user at your earliest convenience.
        
        Best regards,
        SAATHI Mental Health System
        """
        
        # In a real implementation, you would send an email here
        # For now, we'll just print it and show in Streamlit
        print(f"Alert would be sent to: {consultant_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def log_consultant_alert(user_chat_history, distress_score, consultant_id, consultant_name):
    """Log consultant alerts for tracking"""
    conn = sqlite3.connect('saathi_chat_history.db')
    cursor = conn.cursor()
    
    # Create alerts table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultant_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            distress_score INTEGER NOT NULL,
            consultant_id INTEGER,
            consultant_name TEXT,
            chat_summary TEXT,
            status TEXT DEFAULT 'pending',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chat summary
    chat_summary = json.dumps(user_chat_history, indent=2)
    
    cursor.execute('''
        INSERT INTO consultant_alerts (date, time, distress_score, consultant_id, consultant_name, chat_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d"),
        datetime.now().strftime("%H:%M:%S"),
        distress_score,
        consultant_id,
        consultant_name,
        chat_summary
    ))
    
    conn.commit()
    conn.close()

# Initialize database when module is imported
init_consultants_db()
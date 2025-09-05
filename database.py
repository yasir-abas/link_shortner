import sqlite3
import os
from contextlib import contextmanager
from utils import hash_password

# Database file path
DB_FILE = 'url_shortener.db'

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create URLs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                clicks INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        # Create Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Create Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                referer TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                country TEXT,
                city TEXT,
                FOREIGN KEY(url_id) REFERENCES urls(id)
            )
        ''')
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_short_code ON urls(short_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_is_active ON urls(is_active);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_url_id ON analytics(url_id);')
        
        # Create a default admin user (in a real application, this should be done through a proper setup process)
        # For demo purposes, we'll create an admin user with a hashed password
        hashed_password = hash_password('admin123')
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, email, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hashed_password, 'admin@example.com', True))
        
        
        conn.commit()

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    try:
        yield conn
    finally:
        conn.close()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create a database connection and return it"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            points INTEGER DEFAULT 0,
            join_date TEXT,
            invited_by INTEGER,
            FOREIGN KEY (invited_by) REFERENCES users(user_id)
        )
        ''')
        
        # Games history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT,
            score INTEGER,
            response_time REAL,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Invite links
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invites (
            invite_code TEXT PRIMARY KEY,
            created_by INTEGER,
            created_at TEXT,
            uses INTEGER DEFAULT 0,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
        ''')
        
        # Prize claims
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount TEXT,
            claimed_date TEXT,
            paid_date TEXT,
            status TEXT,
            pix_key TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Active games
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_games (
            chat_id INTEGER,
            game_type TEXT,
            start_time TEXT,
            end_time TEXT,
            data TEXT,
            status TEXT,
            PRIMARY KEY (chat_id, game_type)
        )
        ''')
        
        conn.commit()
        logger.info("Database setup complete")
    except Exception as e:
        logger.error(f"Database setup error: {e}")
    finally:
        conn.close()

def register_user(user_id, username, first_name, last_name, invited_by=None):
    """Register a new user or update existing one"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Update user information
            cursor.execute("""
            UPDATE users SET 
                username = ?,
                first_name = ?,
                last_name = ?
            WHERE user_id = ?
            """, (username, first_name, last_name, user_id))
        else:
            # Insert new user
            cursor.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, points, join_date, invited_by)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """, (user_id, username, first_name, last_name, datetime.now().isoformat(), invited_by))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return False
    finally:
        conn.close()

def add_points(user_id, points, game_type, response_time=None):
    """Add points to a user and record game history"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Update user points
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", 
                      (points, user_id))
        
        # Record in game history
        cursor.execute("""
        INSERT INTO game_history (user_id, game_type, score, response_time, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, game_type, points, response_time, datetime.now().isoformat()))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding points: {e}")
        return False
    finally:
        conn.close()

def get_leaderboard(limit=10):
    """Get the top users by points"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT user_id, username, first_name, last_name, points
        FROM users
        ORDER BY points DESC
        LIMIT ?
        """, (limit,))
        
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []
    finally:
        conn.close()

def create_invite(user_id, invite_code):
    """Create a new invitation link"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO invites (invite_code, created_by, created_at, uses)
        VALUES (?, ?, ?, 0)
        """, (invite_code, user_id, datetime.now().isoformat()))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating invite: {e}")
        return False
    finally:
        conn.close()

def use_invite(invite_code, joined_user_id):
    """Record that an invite was used"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get invite details
        cursor.execute("SELECT created_by FROM invites WHERE invite_code = ?", (invite_code,))
        invite = cursor.fetchone()
        
        if not invite:
            return False
        
        # Update the invite uses
        cursor.execute("UPDATE invites SET uses = uses + 1 WHERE invite_code = ?", 
                      (invite_code,))
        
        # Record who invited the new user
        cursor.execute("UPDATE users SET invited_by = ? WHERE user_id = ?", 
                      (invite["created_by"], joined_user_id))
        
        # Add bonus points to the inviter
        cursor.execute("UPDATE users SET points = points + 20 WHERE user_id = ?", 
                      (invite["created_by"],))
        
        conn.commit()
        return invite["created_by"]  # Return the user_id of the inviter
    except Exception as e:
        logger.error(f"Error using invite: {e}")
        return False
    finally:
        conn.close()

def record_game_start(chat_id, game_type, data, duration_seconds):
    """Record start of a game in a chat"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        start_time = datetime.now().isoformat()
        end_time = datetime.fromtimestamp(
            datetime.now().timestamp() + duration_seconds
        ).isoformat()
        
        # First, clear any existing games of this type in this chat
        cursor.execute("""
        DELETE FROM active_games WHERE chat_id = ? AND game_type = ?
        """, (chat_id, game_type))
        
        # Insert new active game
        cursor.execute("""
        INSERT INTO active_games (chat_id, game_type, start_time, end_time, data, status)
        VALUES (?, ?, ?, ?, ?, 'active')
        """, (chat_id, game_type, start_time, end_time, data))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error recording game start: {e}")
        return False
    finally:
        conn.close()

def get_active_game(chat_id, game_type):
    """Get active game data for a chat"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM active_games 
        WHERE chat_id = ? AND game_type = ? AND status = 'active'
        """, (chat_id, game_type))
        
        game = cursor.fetchone()
        return dict(game) if game else None
    except Exception as e:
        logger.error(f"Error getting active game: {e}")
        return None
    finally:
        conn.close()

def end_game(chat_id, game_type):
    """Mark a game as ended"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE active_games SET status = 'completed' 
        WHERE chat_id = ? AND game_type = ?
        """, (chat_id, game_type))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error ending game: {e}")
        return False
    finally:
        conn.close()

def create_prize_claim(user_id, amount):
    """Create a new prize claim"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO prizes (user_id, amount, claimed_date, status)
        VALUES (?, ?, ?, 'pending')
        """, (user_id, amount, datetime.now().isoformat()))
        
        conn.commit()
        
        # Get the created prize ID
        cursor.execute("SELECT last_insert_rowid()")
        prize_id = cursor.fetchone()[0]
        
        return prize_id
    except Exception as e:
        logger.error(f"Error creating prize claim: {e}")
        return None
    finally:
        conn.close()

def update_prize_payment(prize_id, pix_key):
    """Update prize payment information"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE prizes 
        SET pix_key = ?, status = 'processing'
        WHERE id = ?
        """, (pix_key, prize_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating prize payment: {e}")
        return False
    finally:
        conn.close()

def get_user_invites(user_id):
    """Get all invites created by a user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT invite_code, created_at, uses
        FROM invites
        WHERE created_by = ?
        """, (user_id,))
        
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting user invites: {e}")
        return []
    finally:
        conn.close()

def get_user_points(user_id):
    """Get points for a specific user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result["points"] if result else 0
    except Exception as e:
        logger.error(f"Error getting user points: {e}")
        return 0
    finally:
        conn.close()

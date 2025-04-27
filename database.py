#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import uuid
import json
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create a database connection and return it"""
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise Exception("DATABASE_URL não configurada")

    conn = psycopg2.connect(DATABASE_URL)
    return conn

def setup_database():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela users já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Tabela de usuários
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                points INTEGER DEFAULT 0,
                invited_by BIGINT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_invited_by FOREIGN KEY (invited_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
            ''')
    except Exception as e:
        logger.error(f"Erro ao verificar ou criar tabela users: {e}")
        # Tentativa simplificada se ocorrer erro
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            points INTEGER DEFAULT 0,
            invited_by BIGINT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

    # Tabela de histórico de pontos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS points_history (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        points INTEGER,
        game_type TEXT,
        response_time REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Tabela de links de convite
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invites (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        invite_code TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used BOOLEAN DEFAULT FALSE,
        used_by BIGINT,
        used_at TIMESTAMP,
        CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT fk_used_by FOREIGN KEY (used_by) REFERENCES users(user_id) ON DELETE SET NULL
    )
    ''')

    # Tabela para jogos ativos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS active_games (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        game_type TEXT,
        data TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        used_questions TEXT[] DEFAULT '{}',
        UNIQUE(chat_id, game_type)
    )
    ''')

    # Tabela para reclamação de prêmios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prize_claims (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount INTEGER,
        status TEXT DEFAULT 'pending',
        pix_key TEXT,
        claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP,
        CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Tabela para itens da lojinha
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop_items (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        points_cost INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tabela para compras da lojinha
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop_purchases (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        item_id INTEGER,
        points_spent INTEGER,
        status TEXT DEFAULT 'pending',
        delivery_info TEXT,
        purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP,
        CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT fk_item_id FOREIGN KEY (item_id) REFERENCES shop_items(id) ON DELETE CASCADE
    )
    ''')

    # Tabela para configuração do sistema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id SERIAL PRIMARY KEY,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Inserir configurações padrão se não existirem
    default_settings = [
        ("points_per_correct_answer", "10"),
        ("points_per_second", "1"),
        ("game_frequency_minutes", "30"),
        ("notification_time_minutes", "5"),
        ("invitation_points", "5"),
        ("invitation_enabled", "true"),
        ("shop_enabled", "true"),
        ("retry_timeout_seconds", "5"),
        ("max_game_duration_seconds", "300"),
        ("admin_ids", "[]")  # Lista vazia de IDs de administradores em formato JSON
    ]

    for key, value in default_settings:
        cursor.execute('''
        INSERT INTO settings (setting_key, setting_value)
        VALUES (%s, %s)
        ON CONFLICT (setting_key) DO NOTHING
        ''', (key, value))

    conn.commit()
    conn.close()
    logger.info("Database setup complete")

def register_user(user_id, username, first_name, last_name, invited_by=None):
    """Register a new user or update existing one"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        # Update existing user
        cursor.execute('''
        UPDATE users 
        SET username = %s, first_name = %s, last_name = %s 
        WHERE user_id = %s
        ''', (username, first_name, last_name, user_id))
    else:
        # Create new user
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name, invited_by, points)
        VALUES (%s, %s, %s, %s, %s, 0)
        ''', (user_id, username, first_name, last_name, invited_by))

    conn.commit()
    conn.close()
    return True

def add_points(user_id, points, game_type, response_time=None):
    """Add points to a user and record game history"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add points to user
    cursor.execute("UPDATE users SET points = points + %s WHERE user_id = %s", (points, user_id))

    # Record history
    cursor.execute('''
    INSERT INTO points_history (user_id, points, game_type, response_time)
    VALUES (%s, %s, %s, %s)
    ''', (user_id, points, game_type, response_time))

    conn.commit()
    conn.close()
    return True

def subtract_points(user_id, points):
    """Subtract points from a user (for shop purchases)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET points = points - %s WHERE user_id = %s AND points >= %s", 
                  (points, user_id, points))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_leaderboard(limit=10):
    """Get the top users by points"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT user_id, username, first_name, last_name, points 
    FROM users 
    ORDER BY points DESC 
    LIMIT %s
    ''', (limit,))

    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_invite_leaderboard(limit=10):
    """Get the top users by successful invites"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT u.user_id, u.username, u.first_name, u.last_name, COUNT(i.id) AS invite_count 
    FROM users u
    JOIN invites i ON u.user_id = i.user_id
    WHERE i.used = TRUE
    GROUP BY u.user_id, u.username, u.first_name, u.last_name
    ORDER BY invite_count DESC 
    LIMIT %s
    ''', (limit,))

    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def create_invite(user_id, invite_code):
    """Create a new invitation link"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO invites (user_id, invite_code)
    VALUES (%s, %s)
    ''', (user_id, invite_code))

    conn.commit()
    conn.close()
    return True

def use_invite(invite_code, joined_user_id):
    """Record that an invite was used and award points if enabled"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Find the invite
    cursor.execute("SELECT * FROM invites WHERE invite_code = %s AND used = FALSE", (invite_code,))
    invite = cursor.fetchone()

    if not invite:
        conn.close()
        return False

    # Mark invite as used
    cursor.execute('''
    UPDATE invites 
    SET used = TRUE, used_by = %s, used_at = CURRENT_TIMESTAMP 
    WHERE invite_code = %s
    ''', (joined_user_id, invite_code))

    # Check if invitation points are enabled
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'invitation_enabled'")
    invitation_enabled = cursor.fetchone()

    if invitation_enabled and invitation_enabled['setting_value'].lower() == 'true':
        # Get points per invitation
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'invitation_points'")
        points_row = cursor.fetchone()

        if points_row:
            invitation_points = int(points_row['setting_value'])

            # Add points to inviter
            cursor.execute("UPDATE users SET points = points + %s WHERE user_id = %s", 
                          (invitation_points, invite['user_id']))

            # Record points history
            cursor.execute('''
            INSERT INTO points_history (user_id, points, game_type, response_time)
            VALUES (%s, %s, %s, NULL)
            ''', (invite['user_id'], invitation_points, 'invite'))

    conn.commit()
    conn.close()
    return invite["user_id"]  # Return the inviter user_id

def record_game_start(chat_id, game_type, data, duration_seconds):
    """Record start of a game in a chat"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate end time
    end_time = datetime.now() + timedelta(seconds=duration_seconds)

    # Try to end any existing active games of this type in this chat
    cursor.execute('''
    UPDATE active_games 
    SET is_active = FALSE, end_time = CURRENT_TIMESTAMP 
    WHERE chat_id = %s AND game_type = %s AND is_active = TRUE
    ''', (chat_id, game_type))

    # Insert new game
    cursor.execute('''
    INSERT INTO active_games (chat_id, game_type, data, start_time, end_time, is_active)
    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, TRUE)
    ''', (chat_id, game_type, data, end_time.strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()
    return True

def get_active_game(chat_id, game_type):
    """Get active game data for a chat"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT * FROM active_games 
    WHERE chat_id = %s AND game_type = %s AND is_active = TRUE
    ''', (chat_id, game_type))

    game = cursor.fetchone()
    conn.close()

    return game

def end_game(chat_id, game_type):
    """Mark a game as ended"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE active_games 
    SET is_active = FALSE, end_time = CURRENT_TIMESTAMP 
    WHERE chat_id = %s AND game_type = %s AND is_active = TRUE
    ''', (chat_id, game_type))

    conn.commit()
    conn.close()
    return True

def record_used_question(chat_id, game_type, question_id):
    """Record that a question was used to avoid repetition"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE active_games 
    SET used_questions = array_append(used_questions, %s)
    WHERE chat_id = %s AND game_type = %s
    ''', (question_id, chat_id, game_type))

    conn.commit()
    conn.close()
    return True

def get_used_questions(chat_id, game_type):
    """Get list of questions already used"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT used_questions FROM active_games 
    WHERE chat_id = %s AND game_type = %s
    ''', (chat_id, game_type))

    result = cursor.fetchone()
    conn.close()

    return result['used_questions'] if result and 'used_questions' in result else []

def create_prize_claim(user_id, amount):
    """Create a new prize claim"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO prize_claims (user_id, amount, status)
    VALUES (%s, %s, 'pending')
    RETURNING id
    ''', (user_id, amount))

    claim_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return claim_id

def update_prize_payment(prize_id, pix_key):
    """Update prize payment information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE prize_claims 
    SET pix_key = %s, status = 'processing' 
    WHERE id = %s
    ''', (pix_key, prize_id))

    conn.commit()
    conn.close()
    return True

def get_user_invites(user_id):
    """Get all invites created by a user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT * FROM invites 
    WHERE user_id = %s 
    ORDER BY created_at DESC
    ''', (user_id,))

    invites = cursor.fetchall()
    conn.close()

    return invites

def get_user_points(user_id):
    """Get points for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT points FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    conn.close()
    return user["points"] if user else 0

def get_setting(key, default=None):
    """Get a setting value from the database"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
    setting = cursor.fetchone()

    conn.close()
    return setting["setting_value"] if setting else default

def update_setting(key, value):
    """Update a setting value in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO settings (setting_key, setting_value, updated_at)
    VALUES (%s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (setting_key) 
    DO UPDATE SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
    ''', (key, value, value))

    conn.commit()
    conn.close()
    return True

def get_all_settings():
    """Get all settings as a dictionary"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT setting_key, setting_value FROM settings")
    settings = cursor.fetchall()

    conn.close()

    result = {}
    for setting in settings:
        result[setting["setting_key"]] = setting["setting_value"]

    return result

def is_admin(user_id, admin_ids=None):
    """Verificar se um usuário é administrador do bot"""
    if admin_ids is None:
        # Obter lista de administradores do banco de dados
        admin_ids_str = get_setting("admin_ids", "[]")
        try:
            admin_ids = json.loads(admin_ids_str)
        except:
            admin_ids = []
    
    return user_id in admin_ids

# Funções para a lojinha
def create_shop_item(name, description, points_cost):
    """Create a new item in the shop"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO shop_items (name, description, points_cost)
    VALUES (%s, %s, %s)
    RETURNING id
    ''', (name, description, points_cost))

    item_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return item_id

def update_shop_item(item_id, name, description, points_cost, is_active):
    """Update an existing shop item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE shop_items 
    SET name = %s, description = %s, points_cost = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    ''', (name, description, points_cost, is_active, item_id))

    conn.commit()
    conn.close()
    return True

def delete_shop_item(item_id):
    """Delete a shop item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM shop_items WHERE id = %s", (item_id,))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_shop_items(active_only=True):
    """Get all items from the shop"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if active_only:
        cursor.execute("SELECT * FROM shop_items WHERE is_active = TRUE ORDER BY points_cost ASC")
    else:
        cursor.execute("SELECT * FROM shop_items ORDER BY points_cost ASC")

    items = cursor.fetchall()
    conn.close()

    return items

def get_shop_item(item_id):
    """Get a specific shop item"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM shop_items WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    conn.close()
    return item

def purchase_shop_item(user_id, item_id, delivery_info):
    """Purchase an item from the shop"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get the item and user points
    cursor.execute("SELECT * FROM shop_items WHERE id = %s AND is_active = TRUE", (item_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        return False, "Item não encontrado ou inativo"

    cursor.execute("SELECT points FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "Usuário não encontrado"

    if user["points"] < item["points_cost"]:
        conn.close()
        return False, "Pontos insuficientes"

    try:
        # Begin transaction
        cursor.execute("BEGIN")

        # Subtract points from user
        cursor.execute("UPDATE users SET points = points - %s WHERE user_id = %s", 
                      (item["points_cost"], user_id))

        # Create purchase record
        cursor.execute('''
        INSERT INTO shop_purchases (user_id, item_id, points_spent, delivery_info)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        ''', (user_id, item_id, item["points_cost"], delivery_info))

        purchase_id = cursor.fetchone()["id"]

        # Record points history
        cursor.execute('''
        INSERT INTO points_history (user_id, points, game_type, response_time)
        VALUES (%s, %s, %s, NULL)
        ''', (user_id, -item["points_cost"], 'shop_purchase'))

        # Commit transaction
        cursor.execute("COMMIT")

        conn.close()
        return True, purchase_id

    except Exception as e:
        cursor.execute("ROLLBACK")
        conn.close()
        return False, str(e)

def get_user_purchases(user_id):
    """Get all purchases made by a user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT p.*, i.name as item_name, i.description as item_description 
    FROM shop_purchases p
    JOIN shop_items i ON p.item_id = i.id
    WHERE p.user_id = %s
    ORDER BY p.purchased_at DESC
    ''', (user_id,))

    purchases = cursor.fetchall()
    conn.close()

    return purchases

def get_all_purchases(status=None, limit=50):
    """Get all purchases for admin view"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if status:
        cursor.execute('''
        SELECT p.*, u.username, u.first_name, u.last_name, i.name as item_name 
        FROM shop_purchases p
        JOIN users u ON p.user_id = u.user_id
        JOIN shop_items i ON p.item_id = i.id
        WHERE p.status = %s
        ORDER BY p.purchased_at DESC
        LIMIT %s
        ''', (status, limit))
    else:
        cursor.execute('''
        SELECT p.*, u.username, u.first_name, u.last_name, i.name as item_name 
        FROM shop_purchases p
        JOIN users u ON p.user_id = u.user_id
        JOIN shop_items i ON p.item_id = i.id
        ORDER BY p.purchased_at DESC
        LIMIT %s
        ''', (limit,))

    purchases = cursor.fetchall()
    conn.close()

    return purchases

def update_purchase_status(purchase_id, status):
    """Update the status of a purchase"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE shop_purchases 
    SET status = %s, processed_at = CURRENT_TIMESTAMP 
    WHERE id = %s
    ''', (status, purchase_id))

    conn.commit()
    conn.close()
    return True

def get_user_invites(user_id):
    """Get all invites created by a user"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
    SELECT * FROM invites 
    WHERE user_id = %s
    ORDER BY created_at DESC
    ''', (user_id,))

    invites = cursor.fetchall()
    conn.close()
    return invites

# Setup database on import
setup_database()
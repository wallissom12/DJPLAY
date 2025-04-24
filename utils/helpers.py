#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

def get_random_greeting():
    """Return a random greeting message."""
    greetings = [
        "Olá! 👋",
        "Oi, tudo bem? 😊",
        "E aí, como vai? 🙌",
        "Saudações! 🖖",
        "Olá, que bom ver você! 🤗",
        "Oi, pronto para jogar? 🎮",
        "Olá! Vamos nos divertir? 🎯"
    ]
    return random.choice(greetings)

def format_seconds(seconds):
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f} segundos"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes} minuto{'s' if minutes > 1 else ''} e {remaining_seconds:.0f} segundo{'s' if remaining_seconds != 1 else ''}"
    
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    
    return f"{hours} hora{'s' if hours > 1 else ''} e {remaining_minutes} minuto{'s' if remaining_minutes != 1 else ''}"

def get_next_game_time(frequency_minutes):
    """Calculate and return the next game time based on frequency."""
    now = datetime.now()
    # Round to next hour or half hour depending on frequency
    if frequency_minutes >= 60:
        # Next hour
        next_game = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    elif frequency_minutes >= 30:
        # Next half hour
        current_half = now.minute >= 30
        if current_half:
            next_game = now.replace(hour=now.hour+1, minute=0, second=0, microsecond=0)
        else:
            next_game = now.replace(minute=30, second=0, microsecond=0)
    else:
        # Just add the frequency
        next_game = now + timedelta(minutes=frequency_minutes)
    
    return next_game

async def send_next_game_notification(context: ContextTypes.DEFAULT_TYPE, chat_id, minutes_before, game_type):
    """Send a notification about an upcoming game."""
    game_names = {
        "movie": "Adivinhe o Filme",
        "quiz": "Quiz de Conhecimentos",
        "emoji_pattern": "Sequência de Emoji"
    }
    
    game_name = game_names.get(game_type, "Jogo")
    
    message = (
        f"🎮 *{game_name} em breve!* 🎮\n\n"
        f"Um novo jogo de {game_name} começará em {minutes_before} minutos!\n"
        f"Prepare-se para participar e ganhar pontos! 🏆\n\n"
        f"Use /{game_type.split('_')[0]} para participar quando o jogo começar."
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )

def is_user_admin(user_id, admin_ids):
    """Check if user is an admin."""
    return user_id in admin_ids

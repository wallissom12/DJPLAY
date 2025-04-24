#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import time
import re
from telegram import Update
from telegram.ext import ContextTypes
from database import register_user, add_points, record_game_start, get_active_game, end_game
from config import SETTINGS, EMOJI_PATTERN_TIME_LIMIT_SECONDS
from data.emoji_patterns import get_random_pattern

async def start_emoji_pattern_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start an emoji pattern recognition game."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Register user if not already registered
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if there's already an active game in this chat
    active_game = get_active_game(chat_id, "emoji_pattern")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um jogo de Sequência de Emoji em andamento neste chat!"
        )
        return
    
    # Get a random emoji pattern
    pattern_data = get_random_pattern()
    if not pattern_data:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível iniciar o jogo agora. Tente novamente mais tarde."
        )
        return
    
    # Prepare game data
    game_data = {
        "pattern": pattern_data["pattern"],
        "next": pattern_data["next"],
        "explanation": pattern_data["explanation"],
        "difficulty": pattern_data["difficulty"],
        "start_time": time.time(),
        "started_by": user.id,
        "solved": False
    }
    
    # Store game data
    record_game_start(chat_id, "emoji_pattern", json.dumps(game_data), EMOJI_PATTERN_TIME_LIMIT_SECONDS)
    
    # Send the message with the pattern challenge
    pattern_message = await update.message.reply_text(
        f"🧩 *SEQUÊNCIA DE EMOJI* 🧩\n\n"
        f"*Dificuldade:* {'⭐' * pattern_data['difficulty']}\n\n"
        f"Descubra o padrão e envie o próximo emoji ou emojis da sequência:\n\n"
        f"{pattern_data['pattern']} ❓\n\n"
        f"⏱️ Você tem {EMOJI_PATTERN_TIME_LIMIT_SECONDS} segundos para responder.",
        parse_mode="Markdown"
    )
    
    # Schedule end of game after time limit
    context.job_queue.run_once(
        emoji_pattern_timeout, 
        EMOJI_PATTERN_TIME_LIMIT_SECONDS,
        data={
            "chat_id": chat_id,
            "message_id": pattern_message.message_id
        },
        name=f"emoji_timeout_{chat_id}"
    )

async def emoji_pattern_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle emoji pattern game timeout."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    
    # Check if the game is still active
    active_game = get_active_game(chat_id, "emoji_pattern")
    if not active_game:
        return  # Game already solved
    
    # Parse game data
    game_data = json.loads(active_game["data"])
    
    # End the game
    end_game(chat_id, "emoji_pattern")
    
    # Update the message to show the answer
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text=f"⏱️ *TEMPO ESGOTADO!* ⏱️\n\n"
                 f"A sequência correta continuaria com: *{game_data['next']}*\n\n"
                 f"*Explicação:* {game_data['explanation']}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error in emoji pattern timeout handler: {e}")

async def handle_emoji_pattern_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages as answers to emoji pattern game."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Get the active game data
    active_game = get_active_game(chat_id, "emoji_pattern")
    if not active_game:
        # No active emoji pattern game, ignore the message
        return
    
    # Parse game data
    game_data = json.loads(active_game["data"])
    if game_data["solved"]:
        # Game already solved
        return
    
    # Get user's answer and clean it up
    user_answer = update.message.text.strip()
    
    # Check if the answer is correct
    correct_answer = game_data["next"]
    is_correct = user_answer == correct_answer
    
    # Special handling for multiple possible formats
    if not is_correct:
        # Try to normalize by removing spaces
        user_answer_no_space = re.sub(r'\s+', '', user_answer)
        correct_no_space = re.sub(r'\s+', '', correct_answer)
        is_correct = user_answer_no_space == correct_no_space
    
    # Calculate response time
    start_time = game_data["start_time"]
    response_time = time.time() - start_time
    
    # Mark as solved to prevent multiple answers
    game_data["solved"] = True
    record_game_start(chat_id, "emoji_pattern", json.dumps(game_data), 0)
    
    # Remove timeout job if exists
    for job in context.job_queue.get_jobs_by_name(f"emoji_timeout_{chat_id}"):
        job.schedule_removal()
    
    # Calculate points based on correctness, response time and difficulty
    points = 0
    if is_correct:
        # More points for faster answers and higher difficulty
        time_factor = max(0, 1 - (response_time / EMOJI_PATTERN_TIME_LIMIT_SECONDS))
        difficulty_bonus = game_data["difficulty"] * 0.5  # 50% bonus per difficulty level
        base_points = SETTINGS["points_per_correct_answer"]
        points = int(base_points * (0.5 + 0.5 * time_factor) * (1 + difficulty_bonus))
        
        # Add points to the user
        add_points(user.id, points, "emoji_pattern", response_time)
    
    # End the game
    end_game(chat_id, "emoji_pattern")
    
    # Prepare result message
    if is_correct:
        result_text = (
            f"✅ *Correto, {user.first_name}!*\n\n"
            f"Sua resposta: {user_answer}\n"
            f"Padrão completo: {game_data['pattern']} {correct_answer}\n\n"
            f"*Explicação:* {game_data['explanation']}\n\n"
            f"Tempo de resposta: {response_time:.1f}s\n"
            f"Você ganhou *{points}* pontos! 🎉"
        )
    else:
        result_text = (
            f"❌ *Incorreto, {user.first_name}*\n\n"
            f"Sua resposta: {user_answer}\n"
            f"Resposta correta: {correct_answer}\n\n"
            f"*Explicação:* {game_data['explanation']}\n\n"
            f"Melhor sorte na próxima vez! 🔍"
        )
    
    await update.message.reply_text(result_text, parse_mode="Markdown")

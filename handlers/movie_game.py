#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import register_user, add_points, record_game_start, get_active_game, end_game
from config import SETTINGS
from data.movie_emoji import get_random_movie_emoji, get_movie_options

async def start_movie_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the 'Guess the Movie' game."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Register user if not already registered
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if there's already an active game in this chat
    active_game = get_active_game(chat_id, "movie")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um jogo de 'Adivinhe o Filme' em andamento neste chat!"
        )
        return
    
    # Get random movie with emoji representation
    movie_data = get_random_movie_emoji()
    if not movie_data:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível iniciar o jogo agora. Tente novamente mais tarde."
        )
        return
    
    # Get options for the quiz (including correct answer)
    options = get_movie_options(movie_data["title"])
    
    # Prepare game data
    game_data = {
        "movie_id": movie_data["id"],
        "title": movie_data["title"],
        "emoji": movie_data["emoji"],
        "options": options,
        "start_time": time.time(),
        "started_by": user.id
    }
    
    # Store game data
    record_game_start(chat_id, "movie", json.dumps(game_data), 300)  # 5 minutes to answer
    
    # Create buttons with movie options
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([
            InlineKeyboardButton(option, callback_data=f"movie_answer_{i}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with the emoji riddle
    await update.message.reply_text(
        f"🎬 *ADIVINHE O FILME* 🎬\n\n"
        f"Que filme está representado por estes emojis?\n\n"
        f"{movie_data['emoji']}\n\n"
        f"Selecione a resposta correta:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_movie_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from the movie game."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Extract the answer index from callback data
    callback_data = query.data
    if not callback_data.startswith("movie_answer_"):
        return
    
    answer_index = int(callback_data.replace("movie_answer_", ""))
    
    # Get the active game data
    active_game = get_active_game(chat_id, "movie")
    if not active_game:
        await query.edit_message_text(
            "⚠️ Não há um jogo de 'Adivinhe o Filme' ativo neste momento."
        )
        return
    
    # Parse game data
    game_data = json.loads(active_game["data"])
    correct_title = game_data["title"]
    options = game_data["options"]
    start_time = game_data["start_time"]
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Check if the answer is correct
    is_correct = options[answer_index] == correct_title
    
    # Calculate points based on correctness and response time
    points = 0
    if is_correct:
        base_points = SETTINGS["points_per_correct_answer"]
        time_penalty = int(response_time * SETTINGS["points_per_second"])
        points = max(base_points - time_penalty, 1)  # At least 1 point
        
        # Add points to the user
        add_points(user.id, points, "movie", response_time)
    
    # End the game
    end_game(chat_id, "movie")
    
    # Prepare result message
    if is_correct:
        result_text = (
            f"✅ *Correto, {user.first_name}!*\n\n"
            f"O filme é: *{correct_title}*\n"
            f"Tempo de resposta: {response_time:.1f}s\n"
            f"Você ganhou *{points}* pontos! 🎉"
        )
    else:
        result_text = (
            f"❌ *Incorreto, {user.first_name}*\n\n"
            f"O filme correto era: *{correct_title}*\n"
            f"Sua resposta: {options[answer_index]}\n"
            f"Melhor sorte na próxima vez! 🎭"
        )
    
    await query.edit_message_text(result_text, parse_mode="Markdown")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import register_user, add_points, record_game_start, get_active_game, end_game
from config import SETTINGS, QUIZ_TIME_LIMIT_SECONDS
from data.quiz_questions import get_random_question

async def start_quiz_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a quiz game."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Register user if not already registered
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if there's already an active quiz in this chat
    active_game = get_active_game(chat_id, "quiz")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um Quiz em andamento neste chat!"
        )
        return
    
    # Get a random quiz question
    question_data = get_random_question()
    if not question_data:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível iniciar o quiz agora. Tente novamente mais tarde."
        )
        return
    
    # Prepare game data
    game_data = {
        "question": question_data["question"],
        "options": question_data["options"],
        "correct_answer": question_data["correct_answer"],
        "category": question_data["category"],
        "start_time": time.time(),
        "started_by": user.id
    }
    
    # Store game data
    record_game_start(chat_id, "quiz", json.dumps(game_data), QUIZ_TIME_LIMIT_SECONDS)
    
    # Create buttons with answer options
    keyboard = []
    for i, option in enumerate(question_data["options"]):
        keyboard.append([
            InlineKeyboardButton(option, callback_data=f"quiz_answer_{i}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with the question
    quiz_message = await update.message.reply_text(
        f"🧠 *QUIZ* 🧠\n\n"
        f"*Categoria:* {question_data['category']}\n\n"
        f"*Pergunta:* {question_data['question']}\n\n"
        f"⏱️ Você tem {QUIZ_TIME_LIMIT_SECONDS} segundos para responder.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Schedule end of quiz after time limit
    context.job_queue.run_once(
        quiz_timeout, 
        QUIZ_TIME_LIMIT_SECONDS,
        data={
            "chat_id": chat_id,
            "message_id": quiz_message.message_id
        },
        name=f"quiz_timeout_{chat_id}"
    )

async def quiz_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quiz timeout."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    
    # Check if the quiz is still active
    active_game = get_active_game(chat_id, "quiz")
    if not active_game:
        return  # Quiz already answered
    
    # Parse game data
    game_data = json.loads(active_game["data"])
    correct_answer = game_data["correct_answer"]
    correct_index = game_data["options"].index(correct_answer)
    
    # End the game
    end_game(chat_id, "quiz")
    
    # Update the message to show the correct answer
    try:
        # Create a new keyboard with the correct answer highlighted
        keyboard = []
        for i, option in enumerate(game_data["options"]):
            text = option
            if i == correct_index:
                text = f"✅ {option}"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"quiz_timeout_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"⏱️ *TEMPO ESGOTADO!* ⏱️\n\n"
                 f"*Categoria:* {game_data['category']}\n\n"
                 f"*Pergunta:* {game_data['question']}\n\n"
                 f"*Resposta correta:* {correct_answer}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error in quiz timeout handler: {e}")

async def handle_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from the quiz game."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Skip handling timeout callbacks
    if query.data.startswith("quiz_timeout_"):
        return
    
    # Extract the answer index from callback data
    callback_data = query.data
    if not callback_data.startswith("quiz_answer_"):
        return
    
    answer_index = int(callback_data.replace("quiz_answer_", ""))
    
    # Get the active game data
    active_game = get_active_game(chat_id, "quiz")
    if not active_game:
        await query.edit_message_text(
            "⚠️ Não há um Quiz ativo neste momento."
        )
        return
    
    # Parse game data
    game_data = json.loads(active_game["data"])
    options = game_data["options"]
    correct_answer = game_data["correct_answer"]
    start_time = game_data["start_time"]
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Check if the answer is correct
    user_answer = options[answer_index]
    is_correct = user_answer == correct_answer
    
    # Remove timeout job if exists
    if context.job_queue:
        for job in context.job_queue.get_jobs_by_name(f"quiz_timeout_{chat_id}"):
            job.schedule_removal()
    
    # Calculate points based on correctness and response time
    points = 0
    if is_correct:
        # More points for faster answers
        time_factor = max(0, 1 - (response_time / QUIZ_TIME_LIMIT_SECONDS))
        base_points = SETTINGS["points_per_correct_answer"]
        points = int(base_points * (0.5 + 0.5 * time_factor))  # Between 50% and 100% of base points
        
        # Add points to the user
        add_points(user.id, points, "quiz", response_time)
    
    try:
        # End the game
        end_game(chat_id, "quiz")
        
        # Create a new keyboard with the answers marked
        keyboard = []
        for i, option in enumerate(options):
            if i == answer_index and is_correct:
                # User's correct answer
                text = f"✅ {option}"
            elif i == answer_index and not is_correct:
                # User's wrong answer
                text = f"❌ {option}"
            elif option == correct_answer and not is_correct:
                # Correct answer (when user was wrong)
                text = f"✅ {option}"
            else:
                text = option
            
            keyboard.append([InlineKeyboardButton(text, callback_data=f"quiz_done_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Prepare result message
        if is_correct:
            result_text = (
                f"✅ *Correto, {user.first_name}!*\n\n"
                f"*Categoria:* {game_data['category']}\n"
                f"*Pergunta:* {game_data['question']}\n\n"
                f"Tempo de resposta: {response_time:.1f}s\n"
                f"Você ganhou *{points}* pontos! 🎉"
            )
        else:
            result_text = (
                f"❌ *Incorreto, {user.first_name}*\n\n"
                f"*Categoria:* {game_data['category']}\n"
                f"*Pergunta:* {game_data['question']}\n\n"
                f"Sua resposta: {user_answer}\n"
                f"Resposta correta: {correct_answer}\n"
                f"Melhor sorte na próxima vez! 📚"
            )
        
        await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro ao processar resposta do quiz: {e}")
        await query.edit_message_text("Ocorreu um erro ao processar sua resposta.")

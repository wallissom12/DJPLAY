#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from config import SETTINGS
from utils.helpers import send_next_game_notification
from handlers.movie_game import start_movie_game
from handlers.quiz_game import start_quiz_game
from handlers.emoji_pattern import start_emoji_pattern_game

logger = logging.getLogger(__name__)

async def scheduled_movie_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a scheduled movie game."""
    chat_id = context.job.data.get("chat_id")
    
    # Create a fake update to start the game
    class FakeUpdate:
        def __init__(self, chat_id):
            self.effective_chat = type('obj', (object,), {'id': chat_id})
            self.effective_user = type('obj', (object,), {
                'id': 0, 
                'username': 'scheduler',
                'first_name': 'Auto',
                'last_name': 'Scheduler'
            })
            self.message = type('obj', (object,), {'reply_text': None})
        
        async def reply_text(self, *args, **kwargs):
            await context.bot.send_message(chat_id=self.effective_chat.id, *args, **kwargs)
    
    fake_update = FakeUpdate(chat_id)
    fake_update.message.reply_text = lambda *args, **kwargs: context.bot.send_message(chat_id=chat_id, *args, **kwargs)
    
    # Announce the game
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎬 *Hora do jogo programado: Adivinhe o Filme!* 🎬\n\nPrepare-se para testar seus conhecimentos de cinema! 🍿",
        parse_mode="Markdown"
    )
    
    # Start the movie game
    await start_movie_game(fake_update, context)

async def scheduled_quiz_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a scheduled quiz game."""
    chat_id = context.job.data.get("chat_id")
    
    # Create a fake update to start the game
    class FakeUpdate:
        def __init__(self, chat_id):
            self.effective_chat = type('obj', (object,), {'id': chat_id})
            self.effective_user = type('obj', (object,), {
                'id': 0, 
                'username': 'scheduler',
                'first_name': 'Auto',
                'last_name': 'Scheduler'
            })
            self.message = type('obj', (object,), {'reply_text': None})
        
        async def reply_text(self, *args, **kwargs):
            await context.bot.send_message(chat_id=self.effective_chat.id, *args, **kwargs)
    
    fake_update = FakeUpdate(chat_id)
    fake_update.message.reply_text = lambda *args, **kwargs: context.bot.send_message(chat_id=chat_id, *args, **kwargs)
    
    # Announce the game
    await context.bot.send_message(
        chat_id=chat_id,
        text="🧠 *Hora do jogo programado: Quiz de Conhecimentos!* 🧠\n\nVamos testar seus conhecimentos gerais! 📚",
        parse_mode="Markdown"
    )
    
    # Start the quiz game
    await start_quiz_game(fake_update, context)

async def scheduled_emoji_pattern_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a scheduled emoji pattern game."""
    chat_id = context.job.data.get("chat_id")
    
    # Create a fake update to start the game
    class FakeUpdate:
        def __init__(self, chat_id):
            self.effective_chat = type('obj', (object,), {'id': chat_id})
            self.effective_user = type('obj', (object,), {
                'id': 0, 
                'username': 'scheduler',
                'first_name': 'Auto',
                'last_name': 'Scheduler'
            })
            self.message = type('obj', (object,), {'reply_text': None})
        
        async def reply_text(self, *args, **kwargs):
            await context.bot.send_message(chat_id=self.effective_chat.id, *args, **kwargs)
    
    fake_update = FakeUpdate(chat_id)
    fake_update.message.reply_text = lambda *args, **kwargs: context.bot.send_message(chat_id=chat_id, *args, **kwargs)
    
    # Announce the game
    await context.bot.send_message(
        chat_id=chat_id,
        text="🔍 *Hora do jogo programado: Sequência de Emoji!* 🔍\n\nDescubra o padrão e complete a sequência! 🧩",
        parse_mode="Markdown"
    )
    
    # Start the emoji pattern game
    await start_emoji_pattern_game(fake_update, context)

def setup_game_scheduler(application):
    """Setup scheduled games."""
    # This is just a placeholder. The actual scheduling will happen when
    # chats are added to the scheduler via admin commands or first interactions.
    logger.info("Game scheduler initialized - ready to add scheduled games")
    
    # We can initialize default chat IDs here in the future if needed

import random

async def choose_random_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Escolhe e inicia um jogo aleatório."""
    chat_id = context.job.data.get("chat_id")
    
    # Lista de funções de jogo disponíveis
    games = [
        (scheduled_movie_game, "filme"),
        (scheduled_quiz_game, "quiz"),
        (scheduled_emoji_pattern_game, "emoji")
    ]
    
    # Escolher um jogo aleatoriamente
    game_function, game_type = random.choice(games)
    
    # Anunciar o próximo jogo
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎮 *Hora do jogo aleatório!* 🎮\n\nPreparando um jogo de {game_type} para vocês...",
        parse_mode="Markdown"
    )
    
    # Executar o jogo escolhido
    await game_function(context)

def schedule_games_for_chat(application, chat_id):
    """Schedule regular games for a specific chat using a randomized approach."""
    job_queue = application.job_queue
    
    # Game frequency in minutes
    frequency = SETTINGS["game_frequency_minutes"]
    
    # Agendar o jogo aleatório para executar a cada 'frequency' minutos
    job_queue.run_repeating(
        choose_random_game,
        interval=timedelta(minutes=frequency),
        first=datetime.now() + timedelta(minutes=3),  # Começar em 3 minutos
        data={"chat_id": chat_id},
        name=f"random_game_{chat_id}"
    )
    
    # Schedule notifications before each game (opcional, pode ser removido se preferir surpresa total)
    notification_minutes = SETTINGS["notification_minutes_before"]
    
    # Notification for random game (optional)
    if notification_minutes > 0:
        job_queue.run_repeating(
            lambda ctx: send_next_game_notification(ctx, chat_id, notification_minutes, "aleatório"),
            interval=timedelta(minutes=frequency),
            first=datetime.now() + timedelta(minutes=3 - notification_minutes),
            name=f"game_notification_{chat_id}"
        )
    
    logger.info(f"Agendamento de jogos aleatórios configurado para o chat {chat_id}")

def reschedule_games(application):
    """Reschedule all games based on new settings."""
    job_queue = application.job_queue
    
    # Remove all existing game jobs
    for job in job_queue.jobs():
        if job.name and (
            job.name.startswith("movie_") or 
            job.name.startswith("quiz_") or 
            job.name.startswith("emoji_")
        ):
            job.schedule_removal()
    
    # We would need to get all active chats from a database
    # For now, let's assume we reschedule for specific chats
    # This will be expanded in a full implementation
    
    logger.info("All scheduled games have been reset")

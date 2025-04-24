#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
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

def schedule_games_for_chat(application, chat_id):
    """Schedule regular games for a specific chat."""
    job_queue = application.job_queue
    
    # Game frequency in minutes
    frequency = SETTINGS["game_frequency_minutes"]
    
    # Add jobs for each game type
    # Note: We'll rotate games so they don't all happen at the same time
    
    # Movie game every frequency
    job_queue.run_repeating(
        scheduled_movie_game,
        interval=timedelta(minutes=frequency * 3),  # Each game type every 3 * frequency
        first=datetime.now() + timedelta(minutes=frequency),
        data={"chat_id": chat_id},
        name=f"movie_game_{chat_id}"
    )
    
    # Quiz game every frequency (offset by frequency/3)
    job_queue.run_repeating(
        scheduled_quiz_game,
        interval=timedelta(minutes=frequency * 3),
        first=datetime.now() + timedelta(minutes=frequency + (frequency//3)),
        data={"chat_id": chat_id},
        name=f"quiz_game_{chat_id}"
    )
    
    # Emoji pattern game every frequency (offset by 2*frequency/3)
    job_queue.run_repeating(
        scheduled_emoji_pattern_game,
        interval=timedelta(minutes=frequency * 3),
        first=datetime.now() + timedelta(minutes=frequency + (2*frequency//3)),
        data={"chat_id": chat_id},
        name=f"emoji_game_{chat_id}"
    )
    
    # Schedule notifications before each game
    notification_minutes = SETTINGS["notification_minutes_before"]
    
    # Notification for movie game
    job_queue.run_repeating(
        lambda ctx: send_next_game_notification(ctx, chat_id, notification_minutes, "movie"),
        interval=timedelta(minutes=frequency * 3),
        first=datetime.now() + timedelta(minutes=frequency - notification_minutes),
        name=f"movie_notification_{chat_id}"
    )
    
    # Notification for quiz game
    job_queue.run_repeating(
        lambda ctx: send_next_game_notification(ctx, chat_id, notification_minutes, "quiz"),
        interval=timedelta(minutes=frequency * 3),
        first=datetime.now() + timedelta(minutes=(frequency + (frequency//3)) - notification_minutes),
        name=f"quiz_notification_{chat_id}"
    )
    
    # Notification for emoji pattern game
    job_queue.run_repeating(
        lambda ctx: send_next_game_notification(ctx, chat_id, notification_minutes, "emoji_pattern"),
        interval=timedelta(minutes=frequency * 3),
        first=datetime.now() + timedelta(minutes=(frequency + (2*frequency//3)) - notification_minutes),
        name=f"emoji_notification_{chat_id}"
    )
    
    logger.info(f"Scheduled games set up for chat {chat_id}")

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

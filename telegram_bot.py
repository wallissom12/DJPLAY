#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Arquivo: telegram_bot.py - Responsável pelo bot do Telegram

import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Local imports
from config import TOKEN
from database import setup_database
from handlers.start import start, help_command
from handlers.admin import (
    admin_configure,
    admin_configure_callback
)
from handlers.movie_game import (
    start_movie_game, 
    handle_movie_game_callback
)
from handlers.quiz_game import (
    start_quiz_game, 
    handle_quiz_callback
)
from handlers.emoji_pattern import (
    start_emoji_pattern_game, 
    handle_emoji_pattern_answer
)
from handlers.bingo_game import (
    start_bingo_registration, 
    register_bingo_participant,
    claim_bingo,
    show_bingo_status,
    force_end_bingo
)
from handlers.invite import generate_invite, handle_invite_join
from handlers.leaderboard import show_leaderboard, show_invite_leaderboard
from handlers.prize import claim_prize, handle_prize_info
from utils.scheduler import setup_game_scheduler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    setup_database()
    
    # Create the Application instance
    application = Application.builder().token(TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Game command handlers
    application.add_handler(CommandHandler("filme", start_movie_game))
    application.add_handler(CommandHandler("quiz", start_quiz_game))
    application.add_handler(CommandHandler("emoji", start_emoji_pattern_game))
    
    # Admin command handlers
    application.add_handler(CommandHandler("configurar", admin_configure))
    
    # Bingo game handlers
    application.add_handler(CommandHandler("bingo", start_bingo_registration))
    application.add_handler(CommandHandler("participar", register_bingo_participant))
    application.add_handler(CommandHandler("b", claim_bingo))
    application.add_handler(CommandHandler("status", show_bingo_status))
    application.add_handler(CommandHandler("encerrar", force_end_bingo))
    
    # Utility command handlers
    application.add_handler(CommandHandler("convite", generate_invite))
    application.add_handler(CommandHandler("placar", show_leaderboard))
    application.add_handler(CommandHandler("placar@", show_invite_leaderboard))
    application.add_handler(CommandHandler("premio", claim_prize))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_movie_game_callback, pattern=r"^movie_"))
    application.add_handler(CallbackQueryHandler(handle_quiz_callback, pattern=r"^quiz_"))
    application.add_handler(CallbackQueryHandler(admin_configure_callback, pattern=r"^config_"))
    application.add_handler(CallbackQueryHandler(handle_prize_info, pattern=r"^prize_"))
    
    # Message handlers for game answers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_emoji_pattern_answer))
    
    # Setup scheduled games
    setup_game_scheduler(application)
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import Flask application
from app import app

# This file serves as an entry point for both the Flask web application and the Telegram bot
# For the web application, we export the 'app' object for Gunicorn to use
# For the Telegram bot, it's now handled in a separate file: telegram_bot.py

if __name__ == "__main__":
    # When run directly, start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)

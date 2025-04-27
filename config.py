#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path

# Bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database settings
DB_PATH = "bot_database.sqlite"

# Default game settings
DEFAULT_SETTINGS = {
    "points_per_correct_answer": 10,
    "points_per_second": 1,  # Points deducted per second
    "game_frequency_minutes": 60,  # Games start every hour by default
    "notification_minutes_before": 5,  # Minutes before game to send notification
    "admin_ids": [],  # List of admin user IDs
    "prize_amount": "10,00",  # Default prize amount in BRL
    "prize_frequency": "weekly",  # weekly, monthly
}

# Path to store game settings
SETTINGS_PATH = Path("settings.json")

# Load settings from file or use defaults
def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
                settings = json.load(file)
                # Make sure we have all default keys
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# Game settings
SETTINGS = load_settings()

# Time-related settings
QUIZ_TIME_LIMIT_SECONDS = 30  # Time to answer quiz questions
EMOJI_PATTERN_TIME_LIMIT_SECONDS = 60  # Time to solve emoji patterns

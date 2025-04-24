#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

# Database of movies with their emoji representations
MOVIE_EMOJI_DATABASE = [
    {"id": 1, "title": "Titanic", "emoji": "🚢 ❄️ 💑 💔 💦"},
    {"id": 2, "title": "Star Wars", "emoji": "⭐ 🪐 🔫 ⚔️ 👾"},
    {"id": 3, "title": "Matrix", "emoji": "💊 👨‍💻 🕶️ 📱 🤖"},
    {"id": 4, "title": "Harry Potter", "emoji": "⚡ 🧙‍♂️ 🧹 🦉 🏰"},
    {"id": 5, "title": "Jurassic Park", "emoji": "🦖 🦕 🔬 🌴 🚙"},
    {"id": 6, "title": "Senhor dos Anéis", "emoji": "💍 🧙‍♂️ 🧝‍♂️ 🌋 👑"},
    {"id": 7, "title": "Toy Story", "emoji": "🤠 👨‍🚀 🧸 🐶 🚀"},
    {"id": 8, "title": "Frozen", "emoji": "❄️ 👸 ☃️ 🦌 👱‍♀️"},
    {"id": 9, "title": "Homem-Aranha", "emoji": "🕸️ 🕷️ 👨‍🎓 🦸‍♂️ 🏙️"},
    {"id": 10, "title": "Os Vingadores", "emoji": "🦸‍♂️ 🦹‍♂️ 🛡️ 🔨 👊"},
    {"id": 11, "title": "Rei Leão", "emoji": "🦁 👑 🐗 🐒 🌅"},
    {"id": 12, "title": "Procurando Nemo", "emoji": "🐠 🌊 🦈 🐢 🐙"},
    {"id": 13, "title": "Piratas do Caribe", "emoji": "🏴‍☠️ 🦜 ⚓ 🚢 💰"},
    {"id": 14, "title": "Homem de Ferro", "emoji": "🤖 💰 🔧 🔥 💥"},
    {"id": 15, "title": "E.T.", "emoji": "👽 🚲 🌙 👦 🌟"},
    {"id": 16, "title": "Tubarão", "emoji": "🦈 🏊‍♂️ 🚤 🏖️ 🎣"},
    {"id": 17, "title": "Forrest Gump", "emoji": "🏃‍♂️ 🍫 🪖 🏓 🦐"},
    {"id": 18, "title": "O Poderoso Chefão", "emoji": "🤵 🔫 🐎 🍝 🇮🇹"},
    {"id": 19, "title": "Os Caça-Fantasmas", "emoji": "👻 🔫 🚗 🧪 👨‍🔬"},
    {"id": 20, "title": "De Volta para o Futuro", "emoji": "⏰ 🚗 ⚡ 👨‍🔬 👨‍🎓"},
    {"id": 21, "title": "Indiana Jones", "emoji": "🤠 🐍 💎 🏺 🔫"},
    {"id": 22, "title": "Divertida Mente", "emoji": "😀 😢 😡 😱 🧠"},
    {"id": 23, "title": "Coringa", "emoji": "🃏 😂 🤡 🔫 🎭"},
    {"id": 24, "title": "O Rei do Show", "emoji": "🎪 🎭 🎩 🦁 🎵"},
    {"id": 25, "title": "A Origem", "emoji": "💤 🌀 🏙️ 🧠 ⏱️"},
    {"id": 26, "title": "Wall-E", "emoji": "🤖 🚀 🌱 🗑️ 🌍"},
    {"id": 27, "title": "A Bela e a Fera", "emoji": "🌹 📚 🕰️ 🏰 🐺"},
    {"id": 28, "title": "Moana", "emoji": "🌊 🚣‍♀️ 🌴 🪝 🐚"},
    {"id": 29, "title": "Interestelar", "emoji": "🚀 🕳️ 🌍 ⏰ 👨‍👧"},
    {"id": 30, "title": "Avatar", "emoji": "👽 🌳 🌈 🐉 🏹"}
]

def get_random_movie_emoji():
    """Return a random movie with emoji representation."""
    return random.choice(MOVIE_EMOJI_DATABASE)

def get_movie_options(correct_title, num_options=4):
    """Return a list of movie title options, including the correct one."""
    # Get all movie titles except the correct one
    other_titles = [movie["title"] for movie in MOVIE_EMOJI_DATABASE if movie["title"] != correct_title]
    
    # Shuffle the list
    random.shuffle(other_titles)
    
    # Take first (num_options-1) titles
    options = other_titles[:num_options-1]
    
    # Add the correct title
    options.append(correct_title)
    
    # Shuffle again to randomize position of correct answer
    random.shuffle(options)
    
    return options

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Arquivo: data/tmdb_api.py - Integração com a API do TMDb

import os
import requests
import random
import json
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL base da API
TMDB_API_URL = "https://api.themoviedb.org/3"

# Cache local para diminuir o número de requisições à API
MOVIE_CACHE_FILE = "data/movie_cache.json"
GENRE_CACHE_FILE = "data/genre_cache.json"

# Dicionário de emojis por gênero de filme
GENRE_EMOJI_MAP = {
    28: ["💥", "👊", "🔫", "💪"],  # Ação
    12: ["🌍", "🌋", "🏝️", "🧗‍♂️"],  # Aventura
    16: ["🎨", "✏️", "👶", "🧸"],  # Animação
    35: ["😂", "🤣", "😆", "🎭"],  # Comédia
    80: ["🕵️‍♂️", "🔍", "🔪", "💰"],  # Crime
    99: ["📚", "🎓", "🔬", "📝"],  # Documentário
    18: ["😢", "💔", "👨‍👩‍👧‍👦", "🎭"],  # Drama
    10751: ["👨‍👩‍👧‍👦", "👶", "🏠", "❤️"],  # Família
    14: ["🧙‍♂️", "🧚", "🐉", "✨"],  # Fantasia
    36: ["📜", "👑", "⚔️", "🏛️"],  # História
    27: ["👻", "🧟", "🔪", "😱"],  # Terror
    10402: ["🎵", "🎤", "🎸", "🎼"],  # Música
    9648: ["🔍", "❓", "🕵️‍♂️", "😮"],  # Mistério
    10749: ["❤️", "💑", "💋", "💘"],  # Romance
    878: ["🚀", "👽", "🤖", "🌌"],  # Ficção Científica
    10770: ["📺", "🎬", "🎭", "📹"],  # Cinema TV
    53: ["😰", "⏱️", "🔪", "🚨"],  # Thriller
    10752: ["🪖", "💣", "🔫", "🎖️"],  # Guerra
    37: ["🤠", "🐎", "🌵", "🔫"]   # Faroeste
}

# Palavras-chave de filmes que podem ser representadas por emojis
KEYWORD_EMOJI_MAP = {
    # Personagens/Criaturas
    "alien": "👽",
    "robot": "🤖",
    "vampire": "🧛",
    "zombie": "🧟",
    "ghost": "👻",
    "monster": "👹",
    "animal": "🐾",
    "dragon": "🐉",
    "shark": "🦈",
    "dinosaur": "🦖",
    "superhero": "🦸",
    "villain": "🦹",
    "spy": "🕵️",
    "pirate": "🏴‍☠️",
    "king": "👑",
    "princess": "👸",
    "detective": "🕵️‍♂️",
    
    # Ambientes
    "space": "🌌",
    "ocean": "🌊",
    "city": "🏙️",
    "forest": "🌲",
    "desert": "🏜️",
    "mountain": "⛰️",
    "island": "🏝️",
    "beach": "🏖️",
    "jungle": "🌴",
    "castle": "🏰",
    "school": "🏫",
    "hospital": "🏥",
    "farm": "🏡",
    
    # Objetos/Elementos
    "gun": "🔫",
    "sword": "⚔️",
    "car": "🚗",
    "ship": "🚢",
    "plane": "✈️",
    "train": "🚂",
    "spaceship": "🚀",
    "book": "📚",
    "computer": "💻",
    "phone": "📱",
    "money": "💰",
    "heart": "❤️",
    "fire": "🔥",
    "water": "💧",
    "music": "🎵",
    "camera": "📷",
    "ring": "💍",
    "weapon": "🔫",
    "time": "⏰",
    "dream": "💭",
    
    # Conceitos
    "love": "❤️",
    "death": "💀",
    "magic": "✨",
    "power": "💪",
    "adventure": "🧗‍♂️",
    "mystery": "🔍",
    "crime": "🔪",
    "family": "👨‍👩‍👧‍👦",
    "friendship": "🤝",
    "war": "⚔️",
    "travel": "✈️",
    "escape": "🏃",
    "transformation": "🦋",
    "revenge": "😡",
    "survival": "🧬",
    "future": "🔮",
    "past": "⏳"
}

def load_cache(cache_file: str) -> dict:
    """Carrega dados do cache local."""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar cache {cache_file}: {e}")
    return {}

def save_cache(cache_file: str, data: dict) -> None:
    """Salva dados no cache local."""
    try:
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache {cache_file}: {e}")

def get_tmdb_api_key() -> Optional[str]:
    """Obtém a chave da API do TMDb a partir de variáveis de ambiente."""
    return os.getenv("TMDB_API_KEY")

def get_movie_genres() -> List[Dict]:
    """Obtém lista de gêneros de filmes da API ou do cache."""
    cache = load_cache(GENRE_CACHE_FILE)
    if cache and "genres" in cache:
        return cache["genres"]
    
    api_key = get_tmdb_api_key()
    if not api_key:
        logger.warning("Chave da API do TMDb não configurada")
        return []
    
    try:
        response = requests.get(
            f"{TMDB_API_URL}/genre/movie/list",
            params={"api_key": api_key, "language": "pt-BR"}
        )
        response.raise_for_status()
        data = response.json()
        
        # Salvar no cache
        save_cache(GENRE_CACHE_FILE, data)
        
        return data.get("genres", [])
    except Exception as e:
        logger.error(f"Erro ao obter gêneros de filmes: {e}")
        return []

def get_popular_movies(page: int = 1) -> List[Dict]:
    """Obtém filmes populares da API ou do cache."""
    cache = load_cache(MOVIE_CACHE_FILE)
    cache_key = f"popular_page_{page}"
    
    if cache and cache_key in cache:
        return cache[cache_key].get("results", [])
    
    api_key = get_tmdb_api_key()
    if not api_key:
        logger.warning("Chave da API do TMDb não configurada")
        return []
    
    try:
        response = requests.get(
            f"{TMDB_API_URL}/movie/popular",
            params={
                "api_key": api_key,
                "language": "pt-BR",
                "page": page
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Salvar no cache
        if not cache:
            cache = {}
        cache[cache_key] = data
        save_cache(MOVIE_CACHE_FILE, cache)
        
        return data.get("results", [])
    except Exception as e:
        logger.error(f"Erro ao obter filmes populares: {e}")
        return []

def get_movie_details(movie_id: int) -> Optional[Dict]:
    """Obtém detalhes de um filme específico."""
    cache = load_cache(MOVIE_CACHE_FILE)
    cache_key = f"movie_{movie_id}"
    
    if cache and cache_key in cache:
        return cache[cache_key]
    
    api_key = get_tmdb_api_key()
    if not api_key:
        logger.warning("Chave da API do TMDb não configurada")
        return None
    
    try:
        response = requests.get(
            f"{TMDB_API_URL}/movie/{movie_id}",
            params={
                "api_key": api_key,
                "language": "pt-BR",
                "append_to_response": "keywords,credits"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Salvar no cache
        if not cache:
            cache = {}
        cache[cache_key] = data
        save_cache(MOVIE_CACHE_FILE, cache)
        
        return data
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do filme {movie_id}: {e}")
        return None

def generate_emoji_for_movie(movie: Dict) -> str:
    """Gera uma representação em emoji para um filme."""
    emojis = []
    
    # Adicionar emojis baseados nos gêneros
    if "genre_ids" in movie:
        genre_ids = movie["genre_ids"]
    elif "genres" in movie:
        genre_ids = [genre["id"] for genre in movie["genres"]]
    else:
        genre_ids = []
    
    for genre_id in genre_ids[:2]:  # Limitar a 2 gêneros
        if genre_id in GENRE_EMOJI_MAP:
            emoji = random.choice(GENRE_EMOJI_MAP[genre_id])
            if emoji not in emojis:
                emojis.append(emoji)
    
    # Adicionar emojis baseados em palavras-chave
    if "keywords" in movie and "keywords" in movie["keywords"]:
        keywords = [kw["name"] for kw in movie["keywords"]["keywords"]]
        for keyword in keywords[:3]:  # Limitar a 3 palavras-chave
            for key, emoji in KEYWORD_EMOJI_MAP.items():
                if key in keyword.lower() and emoji not in emojis:
                    emojis.append(emoji)
                    break
    
    # Se não conseguimos emojis suficientes, adicione alguns genéricos
    generic_emojis = ["🎬", "🍿", "🎭", "📽️", "🎞️"]
    while len(emojis) < 5:
        emoji = random.choice(generic_emojis)
        if emoji not in emojis:
            emojis.append(emoji)
    
    # Limitar a 5 emojis e juntar com espaço
    return " ".join(emojis[:5])

def get_random_tmdb_movie() -> Optional[Dict]:
    """Obtém um filme aleatório do TMDb e adiciona representação em emoji."""
    # Tentar obter filmes da API
    page = random.randint(1, 5)  # Aleatoriamente escolher entre as primeiras 5 páginas
    movies = get_popular_movies(page)
    
    if not movies:
        # Se não conseguir da API, usar o cache local
        cache = load_cache(MOVIE_CACHE_FILE)
        for key, value in cache.items():
            if key.startswith("popular_page_") and "results" in value:
                movies = value["results"]
                break
    
    if not movies:
        logger.warning("Nenhum filme encontrado no TMDb ou cache")
        return None
    
    # Escolher um filme aleatoriamente
    movie = random.choice(movies)
    
    # Obter detalhes completos se possível
    movie_details = get_movie_details(movie["id"])
    if movie_details:
        movie = movie_details
    
    # Gerar emojis para o filme
    emoji = generate_emoji_for_movie(movie)
    
    return {
        "id": movie["id"],
        "title": movie["title"],
        "emoji": emoji
    }

def get_movie_options_tmdb(correct_movie_id: int, num_options: int = 4) -> List[str]:
    """Obtém opções de resposta para um filme específico."""
    # Obter detalhes do filme correto
    correct_movie = get_movie_details(correct_movie_id)
    if not correct_movie:
        return []
    
    correct_title = correct_movie["title"]
    other_titles = []
    
    # Obter filmes populares para opções
    for page in range(1, 3):  # Tentar as primeiras 2 páginas
        movies = get_popular_movies(page)
        for movie in movies:
            if movie["id"] != correct_movie_id and movie["title"] not in other_titles:
                other_titles.append(movie["title"])
    
    # Se não tivermos opções suficientes, usar o cache
    if len(other_titles) < num_options - 1:
        cache = load_cache(MOVIE_CACHE_FILE)
        for key, value in cache.items():
            if key.startswith("popular_page_") and "results" in value:
                for movie in value["results"]:
                    if movie["id"] != correct_movie_id and movie["title"] not in other_titles:
                        other_titles.append(movie["title"])
    
    # Misturar e pegar apenas o número necessário
    random.shuffle(other_titles)
    options = other_titles[:num_options-1]
    options.append(correct_title)
    random.shuffle(options)
    
    return options
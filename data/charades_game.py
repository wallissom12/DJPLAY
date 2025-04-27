#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import os
import logging

logger = logging.getLogger(__name__)

# Lista de categorias e temas para o jogo de mímica/charadas
CHARADES_CATEGORIES = {
    "Filmes": [
        "Star Wars", "Harry Potter", "O Senhor dos Anéis", "Matrix", "Vingadores",
        "Titanic", "Jurassic Park", "Batman", "Homem-Aranha", "Frozen",
        "Toy Story", "O Rei Leão", "Exterminador do Futuro", "Piratas do Caribe",
        "A Bela e a Fera", "Jogos Vorazes", "Indiana Jones", "Rocky", "E.T.",
        "Shrek", "Gladiador", "Crepúsculo", "Cinderela", "O Mágico de Oz"
    ],
    "Séries": [
        "Game of Thrones", "Friends", "Breaking Bad", "Stranger Things", "The Office",
        "La Casa de Papel", "The Walking Dead", "Grey's Anatomy", "Black Mirror",
        "Peaky Blinders", "The Crown", "Narcos", "The Big Bang Theory", "The Witcher",
        "Bridgerton", "Vikings", "Euphoria", "The Mandalorian", "The Boys",
        "WandaVision", "Loki", "Cobra Kai", "Squid Game", "Dark"
    ],
    "Profissões": [
        "Médico", "Professor", "Bombeiro", "Policial", "Cozinheiro",
        "Piloto", "Astronauta", "Motorista", "Enfermeiro", "Engenheiro",
        "Advogado", "Juiz", "Pescador", "Carteiro", "Jornalista",
        "Dentista", "Ator", "Cantor", "Pintor", "Escritor"
    ],
    "Esportes": [
        "Futebol", "Basquete", "Vôlei", "Natação", "Tênis",
        "Golfe", "Surfe", "Esqui", "Boxe", "MMA",
        "Atletismo", "Ginástica", "Ciclismo", "Automobilismo", "Skate",
        "Handebol", "Rugby", "Hóquei", "Xadrez", "Poker"
    ],
    "Animais": [
        "Leão", "Tigre", "Girafa", "Elefante", "Macaco",
        "Pinguim", "Canguru", "Tubarão", "Polvo", "Águia",
        "Crocodilo", "Cobra", "Aranha", "Abelha", "Borboleta",
        "Baleia", "Golfinho", "Pavão", "Urso", "Lobo"
    ],
    "Objetos": [
        "Telefone", "Televisão", "Geladeira", "Carro", "Bicicleta",
        "Tesoura", "Guarda-chuva", "Escova de dentes", "Travesseiro", "Relógio",
        "Computador", "Câmera", "Mochila", "Livro", "Cadeira",
        "Mesa", "Óculos", "Chapéu", "Sapatos", "Fone de ouvido"
    ],
    "Celebridades": [
        "Neymar", "Roberto Carlos", "Anitta", "Silvio Santos", "Pelé",
        "Xuxa", "Luciano Huck", "Ivete Sangalo", "Ayrton Senna", "Luan Santana",
        "Gisele Bündchen", "Zico", "Taís Araújo", "Paulo Gustavo", "Fátima Bernardes",
        "Wagner Moura", "Fernanda Montenegro", "Caetano Veloso", "Chico Buarque", "Sandy"
    ],
    "Lugares": [
        "Praia", "Montanha", "Floresta", "Deserto", "Parque de diversões",
        "Shopping", "Cinema", "Restaurante", "Biblioteca", "Estádio",
        "Hospital", "Escola", "Aeroporto", "Hotel", "Museu",
        "Zoológico", "Fazenda", "Igreja", "Castelo", "Ilha"
    ],
    "Alimentos": [
        "Pizza", "Hambúrguer", "Sorvete", "Chocolate", "Macarrão",
        "Sushi", "Feijoada", "Churrasco", "Açaí", "Tapioca",
        "Coxinha", "Paçoca", "Brigadeiro", "Pão de queijo", "Acarajé",
        "Lasanha", "Salada", "Omelete", "Bolo", "Pipoca"
    ]
}

def get_random_charade():
    """Obter uma charada aleatória para o jogo de mímica."""
    # Selecionar uma categoria aleatória
    category = random.choice(list(CHARADES_CATEGORIES.keys()))
    
    # Selecionar um tema aleatório da categoria
    theme = random.choice(CHARADES_CATEGORIES[category])
    
    # Gerar dicas (opcional)
    hint = f"Categoria: {category}"
    
    return {
        "category": category,
        "theme": theme,
        "hint": hint
    }

def get_random_charades_options(correct_theme, num_options=4):
    """Obter opções aleatórias para o jogo de mímica, incluindo o tema correto."""
    # Obter a categoria do tema correto
    correct_category = None
    for category, themes in CHARADES_CATEGORIES.items():
        if correct_theme in themes:
            correct_category = category
            break
    
    if not correct_category:
        # Caso não encontre a categoria (não deve acontecer), usar uma aleatória
        correct_category = random.choice(list(CHARADES_CATEGORIES.keys()))
    
    # Criar uma lista de temas da mesma categoria, excluindo o tema correto
    same_category_themes = [t for t in CHARADES_CATEGORIES[correct_category] if t != correct_theme]
    
    # Selecionar temas aleatórios da mesma categoria
    num_same_category = min(num_options - 1, len(same_category_themes))
    if num_same_category > 0:
        options = random.sample(same_category_themes, num_same_category)
    else:
        options = []
    
    # Adicionar o tema correto
    options.append(correct_theme)
    
    # Embaralhar as opções
    random.shuffle(options)
    
    return options
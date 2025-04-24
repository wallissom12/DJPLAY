#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

# Database of emoji patterns
EMOJI_PATTERNS = [
    {
        "pattern": "🍎 🍐 🍊 🍋 🍉",
        "next": "🍇",
        "explanation": "Padrão de frutas em sequência comum: maçã, pera, laranja, limão, melancia, uva.",
        "difficulty": 1
    },
    {
        "pattern": "1️⃣ 2️⃣ 3️⃣ 5️⃣ 8️⃣",
        "next": "1️⃣3️⃣",
        "explanation": "Sequência de Fibonacci: cada número é a soma dos dois anteriores (1, 2, 3, 5, 8, 13).",
        "difficulty": 3
    },
    {
        "pattern": "🐜 🐝 🐞 🦋 🦟",
        "next": "🦗",
        "explanation": "Sequência de insetos: formiga, abelha, joaninha, borboleta, mosquito, grilo.",
        "difficulty": 1
    },
    {
        "pattern": "👶 👦 👨 👴",
        "next": "⚰️",
        "explanation": "Ciclo da vida humana: bebê, criança, adulto, idoso, morte.",
        "difficulty": 2
    },
    {
        "pattern": "🌑 🌒 🌓 🌔 🌕",
        "next": "🌖",
        "explanation": "Fases da lua: lua nova, lua crescente, quarto crescente, lua gibosa crescente, lua cheia, lua gibosa minguante.",
        "difficulty": 1
    },
    {
        "pattern": "🐢 🐇 🐢 🐇 🐢",
        "next": "🐇",
        "explanation": "Padrão alternado: tartaruga, coelho, tartaruga, coelho...",
        "difficulty": 1
    },
    {
        "pattern": "🔴 🟠 🟡 🟢 🔵",
        "next": "🟣",
        "explanation": "Cores do arco-íris: vermelho, laranja, amarelo, verde, azul, roxo.",
        "difficulty": 1
    },
    {
        "pattern": "💧 🌊 🌪️ 🔥 🌋",
        "next": "🌍",
        "explanation": "Elementos e fenômenos naturais crescendo em intensidade: gota d'água, ondas, tornado, fogo, vulcão, planeta Terra.",
        "difficulty": 2
    },
    {
        "pattern": "🐣 🐤 🐥 🐓",
        "next": "🥚",
        "explanation": "Ciclo de vida da galinha que volta ao início: filhote saindo do ovo, pintinho pequeno, pintinho maior, galinha, ovo.",
        "difficulty": 2
    },
    {
        "pattern": "🇦 🇨 🇪 🇬 🇮",
        "next": "🇰",
        "explanation": "Letras em posições ímpares do alfabeto: A(1), C(3), E(5), G(7), I(9), K(11).",
        "difficulty": 3
    },
    {
        "pattern": "✋ ✌️ 👆 👍",
        "next": "👋",
        "explanation": "Gestos de mão com número decrescente de dedos visíveis: 5, 2, 1, 0 (polegar), despedida.",
        "difficulty": 3
    },
    {
        "pattern": "🍐 🐸 🥝 🥬 🥒",
        "next": "🌲",
        "explanation": "Objetos de cor verde: pera, sapo, kiwi, folhas, pepino, árvore.",
        "difficulty": 2
    },
    {
        "pattern": "🐹 🐭 🐰 🦊 🐶",
        "next": "🐱",
        "explanation": "Animais domésticos ou comuns como mascotes: hamster, rato, coelho, raposa, cachorro, gato.",
        "difficulty": 1
    },
    {
        "pattern": "➡️ ↘️ ⬇️ ↙️ ⬅️",
        "next": "↖️",
        "explanation": "Direções em sentido horário: direita, diagonal inferior direita, abaixo, diagonal inferior esquerda, esquerda, diagonal superior esquerda.",
        "difficulty": 2
    },
    {
        "pattern": "🦵 🦵 👖 👕 👒",
        "next": "💍",
        "explanation": "Itens de vestuário de baixo para cima: pernas, calça, camiseta, chapéu, anel (acessório).",
        "difficulty": 2
    },
    {
        "pattern": "🥚 🐣 🐤 🐓 🍗",
        "next": "🍽️",
        "explanation": "Ciclo do frango até o consumo: ovo, filhote nascendo, pintinho, galinha, coxa de frango, refeição.",
        "difficulty": 2
    },
    {
        "pattern": "🌱 🌿 🌳 🔥 🌱",
        "next": "🌿",
        "explanation": "Ciclo de crescimento e regeneração: broto, planta, árvore, fogo (destruição), broto (renascimento), planta novamente.",
        "difficulty": 3
    },
    {
        "pattern": "1️⃣ 3️⃣ 6️⃣ 🔟 1️⃣5️⃣",
        "next": "2️⃣1️⃣",
        "explanation": "Sequência de números triangulares: 1, 3, 6, 10, 15, 21.",
        "difficulty": 3
    },
    {
        "pattern": "🥇 🥈 🥉 4️⃣ 5️⃣",
        "next": "6️⃣",
        "explanation": "Posições em uma competição: medalha de ouro (1º), medalha de prata (2º), medalha de bronze (3º), 4º lugar, 5º lugar, 6º lugar.",
        "difficulty": 1
    },
    {
        "pattern": "🌨️ ☃️ ☃️ ☃️ 🌡️",
        "next": "💧",
        "explanation": "Cenas de neve derretendo: neve caindo, 3 bonecos de neve que vão derretendo, termômetro subindo, água.",
        "difficulty": 2
    },
    {
        "pattern": "🐝 🐞 🦟 🦗 🕷️",
        "next": "🦂",
        "explanation": "Insetos e aracnídeos com número crescente de pernas: abelha (6), joaninha (6), mosquito (6), grilo (6), aranha (8), escorpião (8).",
        "difficulty": 3
    },
    {
        "pattern": "🌍 🌎 🌏",
        "next": "🌍",
        "explanation": "Continentes da Terra visíveis em cada emoji: Europa/África, Américas, Ásia/Oceania, repetindo o ciclo.",
        "difficulty": 2
    },
    {
        "pattern": "🟨 🟨 🟧 🟧 🟥",
        "next": "🟥",
        "explanation": "Padrão de cores quentes que se intensificam: amarelo (2x), laranja (2x), vermelho (2x).",
        "difficulty": 1
    },
    {
        "pattern": "🐌 🐢 🐇 🐆 🚀",
        "next": "⚡",
        "explanation": "Seres/objetos em ordem crescente de velocidade: caracol, tartaruga, coelho, guepardo, foguete, raio.",
        "difficulty": 2
    },
    {
        "pattern": "🌑 🌓 🌕 🌗 🌑",
        "next": "🌓",
        "explanation": "Ciclo lunar completo que se repete: lua nova, quarto crescente, lua cheia, quarto minguante, lua nova novamente, quarto crescente.",
        "difficulty": 2
    },
    {
        "pattern": "🚶 🚶‍♂️ 🏃 🏃‍♂️",
        "next": "🚴",
        "explanation": "Progressão de velocidade de movimento: andando devagar, andando normal, correndo devagar, correndo rápido, pedalando.",
        "difficulty": 2
    },
    {
        "pattern": "🦁 🐯 🐆 🐅",
        "next": "🐈",
        "explanation": "Felinos em ordem decrescente de tamanho: leão, tigre, leopardo, tigre pequeno, gato doméstico.",
        "difficulty": 2
    },
    {
        "pattern": "🔳 ⬜ 🔲 ⬛ 🔳",
        "next": "⬜",
        "explanation": "Alternância de quadrados com e sem contorno: quadrado branco com contorno, quadrado branco sem contorno, quadrado preto com contorno, quadrado preto sem contorno, repetição do padrão.",
        "difficulty": 3
    },
    {
        "pattern": "🦢 🦆 🐥 🥚",
        "next": "🦢",
        "explanation": "Ciclo de vida invertido do cisne, voltando ao início: cisne adulto, pato (fase intermediária), pintinho, ovo, cisne novamente.",
        "difficulty": 3
    },
    {
        "pattern": "🧊 💧 💦 ☁️ 🌧️",
        "next": "🧊",
        "explanation": "Ciclo da água: gelo, água líquida, evaporação, nuvem, chuva, gelo novamente.",
        "difficulty": 2
    }
]

def get_random_pattern():
    """Return a random emoji pattern."""
    return random.choice(EMOJI_PATTERNS)

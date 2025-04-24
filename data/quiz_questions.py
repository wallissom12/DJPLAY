#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

# Database of quiz questions
QUIZ_QUESTIONS = [
    {
        "question": "Qual é a capital do Brasil?",
        "options": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
        "correct_answer": "Brasília",
        "category": "Geografia"
    },
    {
        "question": "Quantos planetas existem no Sistema Solar?",
        "options": ["7", "8", "9", "10"],
        "correct_answer": "8",
        "category": "Astronomia"
    },
    {
        "question": "Qual é o maior oceano do mundo?",
        "options": ["Atlântico", "Índico", "Pacífico", "Ártico"],
        "correct_answer": "Pacífico",
        "category": "Geografia"
    },
    {
        "question": "Quem pintou a Mona Lisa?",
        "options": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Michelangelo"],
        "correct_answer": "Leonardo da Vinci",
        "category": "Arte"
    },
    {
        "question": "Qual é o maior animal terrestre?",
        "options": ["Elefante Africano", "Girafa", "Baleia Azul", "Rinoceronte"],
        "correct_answer": "Elefante Africano",
        "category": "Biologia"
    },
    {
        "question": "Qual é o símbolo químico do ouro?",
        "options": ["Au", "Ag", "Fe", "Cu"],
        "correct_answer": "Au",
        "category": "Química"
    },
    {
        "question": "Quem escreveu 'Dom Quixote'?",
        "options": ["Miguel de Cervantes", "William Shakespeare", "Machado de Assis", "Jorge Luis Borges"],
        "correct_answer": "Miguel de Cervantes",
        "category": "Literatura"
    },
    {
        "question": "Qual é o maior deserto do mundo?",
        "options": ["Saara", "Atacama", "Antártida", "Kalahari"],
        "correct_answer": "Antártida",
        "category": "Geografia"
    },
    {
        "question": "Em que ano começou a Primeira Guerra Mundial?",
        "options": ["1914", "1918", "1939", "1945"],
        "correct_answer": "1914",
        "category": "História"
    },
    {
        "question": "Qual é o metal mais abundante na crosta terrestre?",
        "options": ["Ferro", "Alumínio", "Cobre", "Zinco"],
        "correct_answer": "Alumínio",
        "category": "Geologia"
    },
    {
        "question": "Quem foi o primeiro presidente do Brasil?",
        "options": ["Dom Pedro I", "Getúlio Vargas", "Deodoro da Fonseca", "Juscelino Kubitschek"],
        "correct_answer": "Deodoro da Fonseca",
        "category": "História do Brasil"
    },
    {
        "question": "Qual é o menor país do mundo em área territorial?",
        "options": ["Mônaco", "Vaticano", "Nauru", "San Marino"],
        "correct_answer": "Vaticano",
        "category": "Geografia"
    },
    {
        "question": "Qual planeta é conhecido como planeta vermelho?",
        "options": ["Júpiter", "Vênus", "Marte", "Saturno"],
        "correct_answer": "Marte",
        "category": "Astronomia"
    },
    {
        "question": "Quem foi o cientista que formulou a teoria da relatividade?",
        "options": ["Isaac Newton", "Albert Einstein", "Stephen Hawking", "Niels Bohr"],
        "correct_answer": "Albert Einstein",
        "category": "Física"
    },
    {
        "question": "Qual é o maior mamífero marinho?",
        "options": ["Tubarão Baleia", "Baleia Azul", "Orca", "Golfinho"],
        "correct_answer": "Baleia Azul",
        "category": "Biologia"
    },
    {
        "question": "Quantos ossos tem o corpo humano adulto?",
        "options": ["206", "300", "186", "256"],
        "correct_answer": "206",
        "category": "Anatomia"
    },
    {
        "question": "Quem foi o autor de 'Os Lusíadas'?",
        "options": ["Fernando Pessoa", "Luís de Camões", "José Saramago", "Eça de Queirós"],
        "correct_answer": "Luís de Camões",
        "category": "Literatura"
    },
    {
        "question": "Qual é a montanha mais alta do mundo?",
        "options": ["Monte Everest", "K2", "Monte Kilimanjaro", "Monte Aconcágua"],
        "correct_answer": "Monte Everest",
        "category": "Geografia"
    },
    {
        "question": "Qual é o maior rio do mundo em volume de água?",
        "options": ["Nilo", "Amazonas", "Mississippi", "Yangtzé"],
        "correct_answer": "Amazonas",
        "category": "Geografia"
    },
    {
        "question": "Quem pintou 'A Noite Estrelada'?",
        "options": ["Pablo Picasso", "Salvador Dalí", "Vincent van Gogh", "Claude Monet"],
        "correct_answer": "Vincent van Gogh",
        "category": "Arte"
    },
    {
        "question": "Qual é o elemento químico mais abundante no universo?",
        "options": ["Oxigênio", "Carbono", "Hidrogênio", "Hélio"],
        "correct_answer": "Hidrogênio",
        "category": "Química"
    },
    {
        "question": "Em que ano o homem pisou na Lua pela primeira vez?",
        "options": ["1965", "1969", "1972", "1975"],
        "correct_answer": "1969",
        "category": "História"
    },
    {
        "question": "Qual foi a primeira civilização humana?",
        "options": ["Egípcia", "Suméria", "Grega", "Chinesa"],
        "correct_answer": "Suméria",
        "category": "História"
    },
    {
        "question": "Quais são as cores primárias?",
        "options": ["Vermelho, Azul e Amarelo", "Vermelho, Verde e Azul", "Ciano, Magenta e Amarelo", "Roxo, Laranja e Verde"],
        "correct_answer": "Vermelho, Azul e Amarelo",
        "category": "Arte"
    },
    {
        "question": "Qual é a velocidade da luz?",
        "options": ["300.000 km/s", "150.000 km/s", "200.000 km/s", "100.000 km/s"],
        "correct_answer": "300.000 km/s",
        "category": "Física"
    },
    {
        "question": "Qual é a capital da Austrália?",
        "options": ["Sydney", "Melbourne", "Canberra", "Brisbane"],
        "correct_answer": "Canberra",
        "category": "Geografia"
    },
    {
        "question": "Quem escreveu 'Romeu e Julieta'?",
        "options": ["William Shakespeare", "Charles Dickens", "Jane Austen", "Virginia Woolf"],
        "correct_answer": "William Shakespeare",
        "category": "Literatura"
    },
    {
        "question": "Qual é o país mais populoso do mundo?",
        "options": ["Índia", "China", "Estados Unidos", "Indonésia"],
        "correct_answer": "China",
        "category": "Geografia"
    },
    {
        "question": "Qual é o maior animal terrestre?",
        "options": ["Elefante Africano", "Girafa", "Hipopótamo", "Rinoceronte"],
        "correct_answer": "Elefante Africano",
        "category": "Biologia"
    },
    {
        "question": "Quantos continentes existem?",
        "options": ["5", "6", "7", "4"],
        "correct_answer": "6",
        "category": "Geografia"
    }
]

def get_random_question():
    """Return a random quiz question."""
    return random.choice(QUIZ_QUESTIONS)

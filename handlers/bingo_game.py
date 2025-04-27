#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    register_user, add_points, record_game_start, 
    get_active_game, end_game, get_setting, 
    record_used_question, get_used_questions,
    is_admin, is_group_admin, is_chat_allowed
)

# Configurações para o jogo de Bingo
BINGO_CARTELA_SIZE = 5  # Cartela 5x5
BINGO_MAX_NUMBER = 75   # Números de 1 a 75
BINGO_WAITING_SECONDS = 5  # Tempo entre sorteios

# Estados do jogo de Bingo
BINGO_STATE_REGISTRATION = "registration"  # Fase de registros
BINGO_STATE_PLAYING = "playing"  # Jogo em andamento
BINGO_STATE_ENDED = "ended"  # Jogo finalizado

async def start_bingo_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Iniciar o período de registro para um jogo de Bingo."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Registrar usuário se ainda não estiver registrado
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Verificar se é um grupo
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ Este jogo só pode ser jogado em grupos. Adicione o bot a um grupo para jogar!"
        )
        return
    
    # Verificar se o usuário é admin do bot ou admin do grupo
    admin_ids = json.loads(get_setting("admin_ids", "[]"))
    if not (is_admin(user.id, admin_ids) or is_group_admin(update)):
        await update.message.reply_text(
            "⚠️ Apenas administradores do grupo ou do bot podem iniciar um jogo de Bingo!"
        )
        return
    
    # Verificar se já existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "bingo")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um jogo de Bingo em andamento neste grupo!"
        )
        return
    
    # Obter o tempo para registro dos participantes (em minutos)
    registration_time = 5  # Padrão: 5 minutos
    if len(context.args) > 0:
        try:
            registration_time = int(context.args[0])
            if registration_time < 1:
                registration_time = 1
            elif registration_time > 30:
                registration_time = 30
        except ValueError:
            pass
    
    # Calcular o tempo de término do registro
    end_time = datetime.now() + timedelta(minutes=registration_time)
    
    # Preparar dados do jogo
    game_data = {
        "state": BINGO_STATE_REGISTRATION,
        "start_time": time.time(),
        "registration_end_time": end_time.timestamp(),
        "started_by": user.id,
        "participants": {},  # user_id -> cartela
        "drawn_numbers": [],
        "current_number": None,
        "winners": []
    }
    
    # Armazenar dados do jogo
    record_game_start(chat_id, "bingo", json.dumps(game_data), registration_time * 60 + 60 * 60)  # Registro + 1h para o jogo
    
    # Agendar o fim do período de registro
    context.job_queue.run_once(
        end_bingo_registration, 
        registration_time * 60, 
        data={"chat_id": chat_id},
        name=f"bingo_reg_end_{chat_id}"
    )
    
    # Criar mensagem com informações
    registration_text = (
        f"🎮 *NOVO JOGO DE BINGO* 🎮\n\n"
        f"Um novo jogo de Bingo foi iniciado por {user.first_name}!\n\n"
        f"⏱️ Período de registro: *{registration_time} minutos*\n"
        f"🕒 Término do registro: *{end_time.strftime('%H:%M:%S')}*\n\n"
        f"Para participar, digite /participar neste grupo!\n"
        f"Cada participante receberá uma cartela única de Bingo."
    )
    
    # Enviar mensagem de início do jogo
    await update.message.reply_text(
        registration_text,
        parse_mode="Markdown"
    )

async def register_bingo_participant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registrar um participante no jogo de Bingo atual."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Registrar usuário se ainda não estiver registrado
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Verificar se existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        await update.message.reply_text(
            "⚠️ Não há um jogo de Bingo em andamento neste grupo!"
        )
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo está na fase de registro
    if game_data["state"] != BINGO_STATE_REGISTRATION:
        if game_data["state"] == BINGO_STATE_PLAYING:
            await update.message.reply_text(
                "⚠️ O jogo de Bingo já está em andamento. Não é possível se registrar agora."
            )
        else:
            await update.message.reply_text(
                "⚠️ O período de registro para este jogo já terminou."
            )
        return
    
    # Verificar se o usuário já está registrado
    if str(user.id) in game_data["participants"]:
        # Enviar cartela para o usuário novamente
        cartela = game_data["participants"][str(user.id)]
        await send_bingo_card(update, context, cartela)
        return
    
    # Criar uma cartela única para o usuário
    cartela = generate_bingo_card(game_data["participants"].values())
    
    # Adicionar usuário à lista de participantes
    game_data["participants"][str(user.id)] = cartela
    
    # Atualizar dados do jogo
    record_game_start(chat_id, "bingo", json.dumps(game_data), 
                     int((game_data["registration_end_time"] - time.time()) + 60 * 60))
    
    # Enviar cartela para o usuário
    await send_bingo_card(update, context, cartela)
    
    # Confirmar registro no grupo
    await update.message.reply_text(
        f"✅ {user.first_name}, você está registrado no jogo de Bingo! Sua cartela foi enviada em mensagem privada."
    )

async def send_bingo_card(update: Update, context: ContextTypes.DEFAULT_TYPE, cartela: list) -> None:
    """Enviar cartela de Bingo para o usuário via mensagem privada."""
    user = update.effective_user
    
    # Formatar a cartela para exibição
    card_text = format_bingo_card(cartela)
    
    # Enviar a cartela para o usuário
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"🎮 *SUA CARTELA DE BINGO* 🎮\n\n{card_text}\n\nBoa sorte!",
            parse_mode="Markdown"
        )
    except Exception as e:
        # Se não conseguir enviar mensagem privada, avisar o usuário
        await update.message.reply_text(
            f"⚠️ {user.first_name}, não foi possível enviar sua cartela em mensagem privada. "
            f"Por favor, inicie uma conversa com o bot primeiro e tente novamente."
        )

def format_bingo_card(cartela: list) -> str:
    """Formatar a cartela de Bingo para exibição em texto."""
    header = "B  I  N  G  O"
    lines = [header]
    
    # Transpor a matriz da cartela para exibição adequada
    transposed = list(map(list, zip(*cartela)))
    
    for row in transposed:
        # Formatar cada número com espaço adequado
        formatted_row = []
        for num in row:
            if num == 0:  # Espaço livre no centro
                formatted_row.append("💫")
            else:
                # Alinhar os números para ficarem uniformes
                formatted_row.append(f"{num:2d}")
        
        lines.append(" ".join(formatted_row))
    
    return "\n".join(lines)

def generate_bingo_card(existing_cards=None) -> list:
    """Gerar uma cartela de Bingo única."""
    if existing_cards is None:
        existing_cards = []
    
    # Converter para lista de listas para comparação
    existing_cards_list = [card for card in existing_cards]
    
    while True:
        # Criar uma nova cartela
        cartela = [[] for _ in range(BINGO_CARTELA_SIZE)]
        
        # Dividir os números em 5 colunas para o Bingo tradicional
        columns_range = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75)]
        
        for col_idx, (min_num, max_num) in enumerate(columns_range):
            # Pegar números aleatórios para cada coluna
            col_numbers = random.sample(range(min_num, max_num + 1), BINGO_CARTELA_SIZE)
            
            # Adicionar números à coluna
            for row_idx in range(BINGO_CARTELA_SIZE):
                cartela[col_idx].append(col_numbers[row_idx])
        
        # Definir espaço livre no centro (coluna do meio, linha do meio)
        middle = BINGO_CARTELA_SIZE // 2
        cartela[middle][middle] = 0
        
        # Verificar se a cartela é única
        if cartela not in existing_cards_list:
            return cartela
        
        # Se chegou aqui, a cartela já existe, tentar novamente

async def end_bingo_registration(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Finalizar o período de registro e iniciar o jogo de Bingo."""
    job = context.job
    chat_id = job.data["chat_id"]
    
    # Obter dados do jogo ativo
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo ainda está na fase de registro
    if game_data["state"] != BINGO_STATE_REGISTRATION:
        return
    
    # Verificar se há participantes suficientes (pelo menos 1)
    if len(game_data["participants"]) < 1:
        # Finalizar o jogo por falta de participantes
        game_data["state"] = BINGO_STATE_ENDED
        record_game_start(chat_id, "bingo", json.dumps(game_data), 60)  # 1 minuto para encerrar
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ O jogo de Bingo foi cancelado por falta de participantes.",
            parse_mode="Markdown"
        )
        return
    
    # Atualizar estado do jogo para "jogando"
    game_data["state"] = BINGO_STATE_PLAYING
    record_game_start(chat_id, "bingo", json.dumps(game_data), 60 * 60)  # 1 hora para o jogo
    
    # Enviar mensagem de início do jogo
    participants_count = len(game_data["participants"])
    
    start_text = (
        f"🎮 *JOGO DE BINGO INICIADO!* 🎮\n\n"
        f"O período de registro terminou!\n"
        f"👥 Total de participantes: *{participants_count}*\n\n"
        f"O sorteio dos números começará em instantes...\n"
        f"Fique atento à sua cartela enviada em mensagem privada!\n\n"
        f"Quando completar uma linha, coluna ou diagonal, digite /bingo para declarar sua vitória!"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=start_text,
        parse_mode="Markdown"
    )
    
    # Agendar o primeiro sorteio
    context.job_queue.run_once(
        draw_bingo_number, 
        10,  # 10 segundos para começar
        data={"chat_id": chat_id},
        name=f"bingo_draw_{chat_id}"
    )

async def draw_bingo_number(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sortear um número para o jogo de Bingo."""
    job = context.job
    chat_id = job.data["chat_id"]
    
    # Obter dados do jogo ativo
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo está em andamento
    if game_data["state"] != BINGO_STATE_PLAYING:
        return
    
    # Verificar se todos os números já foram sorteados
    available_numbers = [n for n in range(1, BINGO_MAX_NUMBER + 1) if n not in game_data["drawn_numbers"]]
    
    if not available_numbers:
        # Todos os números foram sorteados, finalizar o jogo
        game_data["state"] = BINGO_STATE_ENDED
        record_game_start(chat_id, "bingo", json.dumps(game_data), 60)  # 1 minuto para encerrar
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎮 *JOGO DE BINGO FINALIZADO!* 🎮\n\nTodos os números foram sorteados!",
            parse_mode="Markdown"
        )
        return
    
    # Sortear um novo número
    new_number = random.choice(available_numbers)
    
    # Atualizar dados do jogo
    game_data["drawn_numbers"].append(new_number)
    game_data["current_number"] = new_number
    record_game_start(chat_id, "bingo", json.dumps(game_data), 60 * 60)
    
    # Categorizar o número no formato do Bingo (B1, I16, etc.)
    letter = "BINGO"[min(4, (new_number - 1) // 15)]
    
    # Formatar lista de números já sorteados
    drawn_numbers = game_data["drawn_numbers"]
    drawn_text = format_drawn_numbers(drawn_numbers)
    
    # Enviar mensagem de novo número
    draw_text = (
        f"🎮 *BINGO - NOVO NÚMERO:* 🎮\n\n"
        f"🔢 *{letter}{new_number}*\n\n"
        f"Números sorteados ({len(drawn_numbers)}/{BINGO_MAX_NUMBER}):\n{drawn_text}\n\n"
        f"Se você completou uma linha, coluna ou diagonal, digite /bingo para declarar sua vitória!"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=draw_text,
        parse_mode="Markdown"
    )
    
    # Agendar o próximo sorteio
    context.job_queue.run_once(
        draw_bingo_number, 
        BINGO_WAITING_SECONDS,
        data={"chat_id": chat_id},
        name=f"bingo_draw_{chat_id}"
    )

def format_drawn_numbers(drawn_numbers: list) -> str:
    """Formatar lista de números sorteados."""
    # Ordenar números
    sorted_numbers = sorted(drawn_numbers)
    
    # Dividir em segmentos de 15 números
    segments = []
    for i in range(1, BINGO_MAX_NUMBER + 1, 15):
        segment = []
        for n in range(i, min(i + 15, BINGO_MAX_NUMBER + 1)):
            if n in sorted_numbers:
                segment.append(f"✅{n:2d}")
            else:
                segment.append(f"⬜{n:2d}")
        segments.append(" ".join(segment))
    
    return "\n".join(segments)

async def claim_bingo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processar quando um jogador declara ter feito Bingo."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Verificar se existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        await update.message.reply_text(
            "⚠️ Não há um jogo de Bingo em andamento neste grupo!"
        )
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo está em andamento
    if game_data["state"] != BINGO_STATE_PLAYING:
        await update.message.reply_text(
            "⚠️ O jogo de Bingo não está em andamento."
        )
        return
    
    # Verificar se o usuário é um participante
    if str(user.id) not in game_data["participants"]:
        await update.message.reply_text(
            "⚠️ Você não está participando deste jogo de Bingo!"
        )
        return
    
    # Verificar se o usuário já venceu
    if user.id in game_data["winners"]:
        await update.message.reply_text(
            "✅ Você já declarou vitória neste jogo!"
        )
        return
    
    # Obter a cartela do usuário
    cartela = game_data["participants"][str(user.id)]
    
    # Verificar se o usuário realmente tem um Bingo
    win_type = check_bingo_win(cartela, game_data["drawn_numbers"])
    
    if win_type:
        # Adicionar o usuário à lista de vencedores
        game_data["winners"].append(user.id)
        
        # Atualizar dados do jogo
        record_game_start(chat_id, "bingo", json.dumps(game_data), 60 * 60)
        
        # Calcular pontos baseados na posição (primeiro recebe mais)
        position = len(game_data["winners"])
        base_points = int(get_setting("points_per_correct_answer", "10"))
        points = max(base_points - (position - 1) * 2, 2)  # Mínimo de 2 pontos
        
        # Adicionar pontos ao usuário
        add_points(user.id, points, "bingo")
        
        # Formatar a cartela do vencedor
        card_text = format_bingo_card(cartela)
        
        # Enviar mensagem de vitória
        win_text = (
            f"🎮 *BINGO DECLARADO!* 🎮\n\n"
            f"🏆 {user.first_name} completou um {win_type} e ganhou!\n"
            f"Posição: {position}º lugar\n"
            f"Pontos ganhos: {points}\n\n"
            f"Cartela vencedora:\n{card_text}\n\n"
            f"O jogo continua para os demais participantes!"
        )
        
        await update.message.reply_text(
            win_text,
            parse_mode="Markdown"
        )
    else:
        # O usuário não tem um Bingo válido
        await update.message.reply_text(
            "⚠️ Verificamos sua cartela e você ainda não completou uma linha, coluna ou diagonal. Continue jogando!"
        )

def check_bingo_win(cartela: list, drawn_numbers: list) -> str:
    """Verificar se uma cartela tem um Bingo válido."""
    # Transpor a matriz para facilitar verificação de linhas e colunas
    transposed = list(map(list, zip(*cartela)))
    
    # Verificar se uma linha ou coluna está completa
    # Cada linha
    for i in range(BINGO_CARTELA_SIZE):
        # Verificar linha
        row = transposed[i]
        if all(num in drawn_numbers or num == 0 for num in row):
            return "linha"
        
        # Verificar coluna
        col = cartela[i]
        if all(num in drawn_numbers or num == 0 for num in col):
            return "coluna"
    
    # Verificar diagonais
    diagonal1 = [cartela[i][i] for i in range(BINGO_CARTELA_SIZE)]
    if all(num in drawn_numbers or num == 0 for num in diagonal1):
        return "diagonal"
    
    diagonal2 = [cartela[i][BINGO_CARTELA_SIZE - 1 - i] for i in range(BINGO_CARTELA_SIZE)]
    if all(num in drawn_numbers or num == 0 for num in diagonal2):
        return "diagonal"
    
    # Nenhum Bingo encontrado
    return ""

async def show_bingo_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostrar o status atual do jogo de Bingo."""
    chat_id = update.effective_chat.id
    
    # Verificar se existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        await update.message.reply_text(
            "⚠️ Não há um jogo de Bingo em andamento neste grupo!"
        )
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Formatar mensagem dependendo do estado do jogo
    if game_data["state"] == BINGO_STATE_REGISTRATION:
        # Calcular tempo restante para o término do registro
        remaining_seconds = max(0, game_data["registration_end_time"] - time.time())
        remaining_minutes = int(remaining_seconds / 60)
        remaining_seconds = int(remaining_seconds % 60)
        
        participants_count = len(game_data["participants"])
        
        status_text = (
            f"🎮 *STATUS DO BINGO - REGISTRO* 🎮\n\n"
            f"👥 Participantes registrados: *{participants_count}*\n"
            f"⏱️ Tempo restante: *{remaining_minutes}m {remaining_seconds}s*\n\n"
            f"Para participar, digite /participar neste grupo!"
        )
    
    elif game_data["state"] == BINGO_STATE_PLAYING:
        # Formatar números já sorteados
        drawn_numbers = game_data["drawn_numbers"]
        drawn_text = format_drawn_numbers(drawn_numbers)
        
        participants_count = len(game_data["participants"])
        winners_count = len(game_data["winners"])
        
        status_text = (
            f"🎮 *STATUS DO BINGO - EM ANDAMENTO* 🎮\n\n"
            f"👥 Participantes: *{participants_count}*\n"
            f"🏆 Vencedores: *{winners_count}*\n"
            f"🔢 Números sorteados: *{len(drawn_numbers)}/{BINGO_MAX_NUMBER}*\n\n"
            f"Último número: {game_data['current_number'] if game_data['current_number'] else 'Nenhum'}\n\n"
            f"Números sorteados:\n{drawn_text}"
        )
    
    else:  # BINGO_STATE_ENDED
        participants_count = len(game_data["participants"])
        winners_count = len(game_data["winners"])
        
        status_text = (
            f"🎮 *STATUS DO BINGO - FINALIZADO* 🎮\n\n"
            f"👥 Participantes: *{participants_count}*\n"
            f"🏆 Vencedores: *{winners_count}*\n"
            f"🔢 Números sorteados: *{len(game_data['drawn_numbers'])}/{BINGO_MAX_NUMBER}*\n\n"
            f"O jogo foi finalizado."
        )
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown"
    )

async def force_end_bingo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forçar o encerramento de um jogo de Bingo (apenas para administradores)."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Verificar se o usuário é admin do bot ou admin do grupo
    admin_ids = json.loads(get_setting("admin_ids", "[]"))
    if not (is_admin(user.id, admin_ids) or is_group_admin(update)):
        await update.message.reply_text(
            "⚠️ Apenas administradores do grupo ou do bot podem encerrar um jogo de Bingo!"
        )
        return
    
    # Verificar se existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "bingo")
    if not active_game:
        await update.message.reply_text(
            "⚠️ Não há um jogo de Bingo em andamento neste grupo!"
        )
        return
    
    # Finalizar o jogo
    end_game(chat_id, "bingo")
    
    # Cancelar jobs relacionados
    for job_name in [f"bingo_reg_end_{chat_id}", f"bingo_draw_{chat_id}"]:
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
    
    await update.message.reply_text(
        "🎮 *JOGO DE BINGO ENCERRADO* 🎮\n\n"
        "O jogo foi encerrado manualmente por um administrador.",
        parse_mode="Markdown"
    )
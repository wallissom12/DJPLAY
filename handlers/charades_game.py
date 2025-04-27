#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    register_user, add_points, record_game_start, 
    get_active_game, end_game, get_setting, 
    record_used_question, get_used_questions,
    is_admin, is_group_admin, is_chat_allowed,
    add_user_activity
)
from data.charades_game import get_random_charade, get_random_charades_options

logger = logging.getLogger(__name__)

async def start_charades_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Iniciar um jogo de mímica (charadas) em um grupo."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Registrar usuário se ainda não estiver registrado
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Registrar atividade do usuário ao iniciar jogo
    add_user_activity(user.id, chat_id, "game_start")
    
    # Verificar se é um grupo
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ Este jogo só pode ser jogado em grupos. Adicione o bot a um grupo para jogar!"
        )
        return
    
    # Verificar se o grupo está na lista de permitidos
    if not is_chat_allowed(chat_id):
        await update.message.reply_text(
            "⚠️ Este grupo não está autorizado a usar este bot."
        )
        return
    
    # Verificar se já existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "charades")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um jogo de Mímica em andamento neste grupo!"
        )
        return
    
    # Obter configuração de pontos e tempo
    points_per_correct = int(get_setting("points_per_correct_answer", "10"))
    points_per_second = int(get_setting("points_per_second", "1"))
    max_game_duration = int(get_setting("max_game_duration_seconds", "300"))
    
    # Obter charada aleatória
    charade = get_random_charade()
    
    # Obter opções para a charada
    options = get_random_charades_options(charade["theme"])
    
    # Preparar dados do jogo
    game_data = {
        "charade": charade,
        "options": options,
        "correct_option": charade["theme"],
        "start_time": time.time(),
        "started_by": user.id,
        "points_per_correct": points_per_correct,
        "points_per_second": points_per_second,
        "guessed": False,
        "timeout": False,
        "correct_user_id": None
    }
    
    # Armazenar o jogo no banco de dados
    record_game_start(chat_id, "charades", json.dumps(game_data), max_game_duration)
    
    # Criar teclado inline com as opções
    keyboard = []
    for i, option in enumerate(options):
        callback_data = f"charades_{i}"
        keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar mensagem com a charada
    charade_text = (
        f"🎭 *JOGO DE MÍMICA* 🎭\n\n"
        f"Um de vocês deve representar/imitar isso usando apenas gestos, sem falar ou escrever:\n\n"
        f"*{charade['hint']}*\n\n"
        f"Os outros jogadores devem adivinhar utilizando os botões abaixo.\n"
        f"Tempo limite: {max_game_duration // 60} minutos"
    )
    
    await update.message.reply_text(
        charade_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Agendar timeout para o jogo
    context.job_queue.run_once(
        charades_timeout, 
        max_game_duration, 
        data={
            "chat_id": chat_id,
            "message_id": None # Será atualizado quando recebermos a resposta
        },
        name=f"charades_timeout_{chat_id}"
    )
    
    # Tentamos obter o chat para enviar a resposta apenas ao criador do jogo
    try:
        # Enviar a resposta em mensagem privada para o criador do jogo
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"🎭 *PALAVRA SECRETA PARA MÍMICA* 🎭\n\n"
                f"Você iniciou um jogo de mímica!\n\n"
                f"A palavra/tema para você representar é:\n"
                f"*{charade['theme']}*\n\n"
                f"Categoria: {charade['category']}\n\n"
                f"Use apenas gestos, sem falar ou escrever, para que os outros jogadores adivinhem!"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro ao enviar resposta ao criador do jogo: {e}")
        # Enviar uma mensagem informando que o usuário precisa iniciar uma conversa privada com o bot
        await update.message.reply_text(
            f"⚠️ {user.first_name}, não consegui te enviar a palavra secreta. "
            f"Por favor, inicie uma conversa comigo em privado e tente novamente."
        )
        # Cancelar o jogo
        end_game(chat_id, "charades")
        # Cancelar o timeout
        for job in context.job_queue.get_jobs_by_name(f"charades_timeout_{chat_id}"):
            job.schedule_removal()
        return

async def charades_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função para lidar com o timeout do jogo de mímica."""
    job = context.job
    chat_id = job.data["chat_id"]
    
    # Obter dados do jogo
    active_game = get_active_game(chat_id, "charades")
    if not active_game:
        return
        
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo já foi adivinhado
    if game_data.get("guessed", False):
        return
    
    # Marcar como timeout
    game_data["timeout"] = True
    record_game_start(chat_id, "charades", json.dumps(game_data), 60)  # Manter por 1 minuto
    
    # Encerrar o jogo
    end_game(chat_id, "charades")
    
    charade = game_data["charade"]
    
    # Enviar mensagem informando o timeout
    timeout_text = (
        f"⏱️ *TEMPO ESGOTADO!* ⏱️\n\n"
        f"Ninguém conseguiu adivinhar a mímica a tempo.\n\n"
        f"A resposta correta era: *{charade['theme']}*\n"
        f"Categoria: {charade['category']}\n\n"
        f"Vamos tentar novamente? Use /mimica para iniciar um novo jogo!"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=timeout_text,
        parse_mode="Markdown"
    )

async def handle_charades_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from the charades game."""
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Registrar usuário se ainda não estiver registrado
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Registrar atividade do usuário ao responder
    add_user_activity(user.id, chat_id, "game_answer")
    
    # Extrair índice da opção escolhida
    option_idx = int(query.data.split("_")[1])
    
    # Obter dados do jogo
    active_game = get_active_game(chat_id, "charades")
    if not active_game:
        await query.answer("Não há um jogo de Mímica ativo neste momento.")
        await query.edit_message_text(
            "Este jogo de Mímica já terminou. Use /mimica para iniciar um novo jogo."
        )
        return
    
    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    
    # Verificar se o jogo já foi adivinhado
    if game_data.get("guessed", False):
        await query.answer("Este jogo já foi concluído!")
        return
    
    # Verificar se o usuário que iniciou o jogo está tentando adivinhar
    if user.id == game_data["started_by"]:
        await query.answer("Você não pode adivinhar seu próprio jogo de mímica!")
        return
    
    # Obter opção escolhida e resposta correta
    options = game_data["options"]
    chosen_option = options[option_idx]
    correct_option = game_data["correct_option"]
    
    # Verificar se a resposta está correta
    if chosen_option == correct_option:
        # Calcular pontos
        elapsed_time = time.time() - game_data["start_time"]
        time_points = max(0, int((300 - elapsed_time) * game_data["points_per_second"] / 10))
        total_points = game_data["points_per_correct"] + time_points
        
        # Atualizar dados do jogo
        game_data["guessed"] = True
        game_data["correct_user_id"] = user.id
        record_game_start(chat_id, "charades", json.dumps(game_data), 60)  # Manter por mais 1 minuto
        
        # Encerrar o jogo
        end_game(chat_id, "charades")
        
        # Adicionar pontos ao usuário
        add_points(user.id, total_points, "charades", elapsed_time)
        
        # Cancelar timeout
        for job in context.job_queue.get_jobs_by_name(f"charades_timeout_{chat_id}"):
            job.schedule_removal()
        
        # Enviar mensagem de sucesso
        charade = game_data["charade"]
        
        success_text = (
            f"🎉 *ACERTOU!* 🎉\n\n"
            f"Parabéns {user.first_name}! Você adivinhou corretamente a mímica:\n"
            f"*{correct_option}*\n"
            f"Categoria: {charade['category']}\n\n"
            f"⏱️ Tempo: {elapsed_time:.1f}s\n"
            f"🎮 Pontuação: {total_points} pontos\n"
            f"  • Base: {game_data['points_per_correct']} pts\n"
            f"  • Tempo: {time_points} pts\n\n"
            f"Use /mimica para jogar novamente!"
        )
        
        await query.edit_message_text(
            text=success_text,
            parse_mode="Markdown"
        )
        
        await query.answer("Correto! 🎉")
    else:
        # Resposta incorreta
        await query.answer(f"Errado! Tente novamente. Sua resposta: {chosen_option}")
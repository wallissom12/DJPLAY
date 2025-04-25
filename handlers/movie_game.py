#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes
from database import (
    register_user, add_points, record_game_start, 
    get_active_game, end_game, get_setting, 
    record_used_question, get_used_questions
)
from data.movie_emoji import get_random_movie_emoji, get_movie_options

# Importar a nova integração com TMDb
try:
    from data.tmdb_api import get_random_tmdb_movie, get_movie_options_tmdb, get_tmdb_api_key
    TMDB_AVAILABLE = True
except Exception as e:
    logging.warning(f"Não foi possível carregar a integração com TMDb: {e}")
    TMDB_AVAILABLE = False

async def start_movie_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia o jogo 'Adivinhe o Filme' em grupos."""
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

    # Verificar se já existe um jogo ativo neste chat
    active_game = get_active_game(chat_id, "movie")
    if active_game:
        await update.message.reply_text(
            "⚠️ Já existe um jogo de 'Adivinhe o Filme' em andamento neste grupo!"
        )
        return

    # Obter lista de questões já usadas para evitar repetição
    used_questions = get_used_questions(chat_id, "movie")

    # Determinar se usamos TMDb ou banco de dados local
    use_tmdb = False
    movie_data = None

    # Tentar usar TMDb se disponível
    if TMDB_AVAILABLE and get_tmdb_api_key():
        # Tente até 5 vezes para obter um filme não usado anteriormente
        for _ in range(5):
            try:
                movie_data = get_random_tmdb_movie()
                if movie_data and str(movie_data["id"]) not in used_questions:
                    use_tmdb = True
                    break
                elif movie_data:
                    # Filme já foi usado, tente outro
                    movie_data = None
            except Exception as e:
                logging.error(f"Erro ao obter filme do TMDb: {e}")

    # Fallback para banco de dados local
    if not movie_data:
        # Tentar até 5 vezes obter um filme que não tenha sido usado
        for _ in range(5):
            movie_data = get_random_movie_emoji()
            if movie_data and str(movie_data["id"]) not in used_questions:
                break
            movie_data = None

    if not movie_data:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível iniciar o jogo agora. Tente novamente mais tarde."
        )
        return

    # Registrar que esta questão foi usada
    record_used_question(chat_id, "movie", str(movie_data["id"]))

    # Obter opções de filmes para o quiz
    if use_tmdb:
        try:
            options = get_movie_options_tmdb(movie_data["id"])
            if not options or len(options) < 2:
                # Fallback para opções locais se algo der errado
                options = get_movie_options(movie_data["title"])
        except Exception as e:
            logging.error(f"Erro ao obter opções de filme do TMDb: {e}")
            options = get_movie_options(movie_data["title"])
    else:
        options = get_movie_options(movie_data["title"])

    # Garantir que temos opções suficientes
    if not options or len(options) < 2:
        await update.message.reply_text(
            "😕 Não foi possível gerar opções para o jogo. Tente novamente mais tarde."
        )
        return

    # Obter configurações de duração do jogo e tempo para tentar novamente
    max_duration = int(get_setting("max_game_duration_seconds", "300"))
    retry_timeout = int(get_setting("retry_timeout_seconds", "5"))

    # Preparar dados do jogo
    game_data = {
        "movie_id": movie_data["id"],
        "title": movie_data["title"],
        "emoji": movie_data["emoji"],
        "options": options,
        "start_time": time.time(),
        "started_by": user.id,
        "source": "tmdb" if use_tmdb else "local",
        "incorrect_users": [],  # Lista de usuários que erraram
        "correct_user": None,   # Usuário que acertou
        "selected_answers": {}  # Mapa de opção escolhida por cada usuário
    }

    # Armazenar dados do jogo
    record_game_start(chat_id, "movie", json.dumps(game_data), max_duration)

    # Agendar o encerramento automático do jogo após o tempo máximo
    context.job_queue.run_once(
        movie_game_timeout, 
        max_duration, 
        data={"chat_id": chat_id, "message_id": None},
        name=f"movie_timeout_{chat_id}"
    )

    # Criar botões com opções de filmes
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([
            InlineKeyboardButton(option, callback_data=f"movie_answer_{i}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar mensagem com o enigma de emoji
    source_text = "🎬 *ADIVINHE O FILME* 🎬"
    if use_tmdb:
        source_text += " (via TMDb API)"

    message = await update.message.reply_text(
        f"{source_text}\n\n"
        f"Que filme está representado por estes emojis?\n\n"
        f"{movie_data['emoji']}\n\n"
        f"Selecione a resposta correta:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    # Atualizar o job com a message_id para poder editar a mensagem no timeout
    for job in context.job_queue.get_jobs_by_name(f"movie_timeout_{chat_id}"):
        job.data["message_id"] = message.message_id

async def movie_game_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função para lidar com o timeout do jogo de filmes."""
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]

    # Obter dados do jogo ativo
    active_game = get_active_game(chat_id, "movie")
    if not active_game:
        return

    # Finalizar o jogo
    end_game(chat_id, "movie")

    # Preparar mensagem de timeout
    game_data = json.loads(active_game["data"])
    correct_title = game_data["title"]

    timeout_message = (
        f"⏰ *TEMPO ESGOTADO!*\n\n"
        f"Ninguém conseguiu adivinhar o filme correto.\n\n"
        f"O filme era: *{correct_title}*\n"
        f"🎬 Emoji: {game_data['emoji']}\n\n"
        f"Fique atento para o próximo jogo!"
    )

    # Enviar mensagem de timeout
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=timeout_message,
            reply_markup=None,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem de timeout: {e}")
        # Tentar enviar nova mensagem se não conseguir editar
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=timeout_message,
                parse_mode="Markdown"
            )
        except Exception as e2:
            logging.error(f"Erro ao enviar nova mensagem de timeout: {e2}")

async def handle_movie_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from the movie game."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    chat_id = update.effective_chat.id

    # Extract the answer index from callback data
    callback_data = query.data
    if not callback_data.startswith("movie_answer_"):
        return

    answer_index = int(callback_data.replace("movie_answer_", ""))

    # Get the active game data
    active_game = get_active_game(chat_id, "movie")
    if not active_game:
        await query.edit_message_text(
            "⚠️ Não há um jogo de 'Adivinhe o Filme' ativo neste momento."
        )
        return

    # Parse game data
    game_data = json.loads(active_game["data"])
    correct_title = game_data["title"]
    options = game_data["options"]
    start_time = game_data["start_time"]
    incorrect_users = game_data.get("incorrect_users", [])
    selected_answers = game_data.get("selected_answers", {})

    # Verificar se o usuário já tentou e errou
    if str(user.id) in incorrect_users:
        await query.answer("Você já tentou e errou. Aguarde o tempo para tentar novamente.", show_alert=True)
        return

    # Verificar se o usuário já acertou
    if game_data.get("correct_user") == user.id:
        await query.answer("Você já acertou este jogo!", show_alert=True)
        return

    # Registrar a resposta do usuário
    selected_answers[str(user.id)] = options[answer_index]
    game_data["selected_answers"] = selected_answers

    # Calculate response time
    response_time = time.time() - start_time

    # Check if the answer is correct
    is_correct = options[answer_index] == correct_title

    if is_correct:
        try:
            # Registrar que este usuário acertou
            game_data["correct_user"] = user.id

            # Calculate points based on correctness and response time
            base_points = int(get_setting("points_per_correct_answer", "10"))
            time_penalty = int(float(get_setting("points_per_second", "1")) * response_time)
            points = max(base_points - time_penalty, 1)  # At least 1 point

            # Add points to the user
            add_points(user.id, points, "movie", response_time)

            # End the game
            end_game(chat_id, "movie")

            # Cancelar o job de timeout
            for job in context.job_queue.get_jobs_by_name(f"movie_timeout_{chat_id}"):
                job.schedule_removal()

            # Prepare result message
            result_text = (
                f"✅ *Correto, {user.first_name}!*\n\n"
                f"O filme é: *{correct_title}*\n"
                f"Tempo de resposta: {response_time:.1f}s\n"
                f"Você ganhou *{points}* pontos! 🎉"
            )

            await query.edit_message_text(result_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Erro ao processar resposta correta: {e}")
            await query.edit_message_text(f"⚠️ Ocorreu um erro ao processar sua resposta. Por favor, tente novamente.")


    else:
        # Adicionar o usuário à lista de incorretos
        incorrect_users.append(str(user.id))
        game_data["incorrect_users"] = incorrect_users

        # Atualizar dados do jogo
        updated_data = json.dumps(game_data)
        record_game_start(chat_id, "movie", updated_data, 
                         int(datetime.now().timestamp() - start_time + int(get_setting("max_game_duration_seconds", "300"))))

        # Notificar o usuário de que ele errou
        await query.answer(f"Incorreto! A resposta {options[answer_index]} não é correta. Tente novamente depois do timeout.", show_alert=True)

        # Agendar quando o usuário poderá tentar novamente (se o jogo ainda estiver ativo)
        retry_seconds = int(get_setting("retry_timeout_seconds", "5"))
        context.job_queue.run_once(
            enable_retry, 
            retry_seconds, 
            data={"chat_id": chat_id, "user_id": user.id, "game_type": "movie"},
            name=f"movie_retry_{chat_id}_{user.id}"
        )

async def enable_retry(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Permite que um usuário tente novamente após o timeout."""
    job = context.job
    chat_id = job.data["chat_id"]
    user_id = job.data["user_id"]
    game_type = job.data["game_type"]

    # Obter o jogo ativo
    active_game = get_active_game(chat_id, game_type)
    if not active_game:
        return

    # Carregar dados do jogo
    game_data = json.loads(active_game["data"])
    incorrect_users = game_data.get("incorrect_users", [])

    # Remover o usuário da lista de incorretos
    if str(user_id) in incorrect_users:
        incorrect_users.remove(str(user_id))

    # Atualizar dados do jogo
    game_data["incorrect_users"] = incorrect_users
    updated_data = json.dumps(game_data)

    # Registrar o jogo atualizado
    end_time = datetime.fromtimestamp(game_data["start_time"]) + timedelta(seconds=int(get_setting("max_game_duration_seconds", "300")))
    remaining_seconds = max(0, (end_time - datetime.now()).total_seconds())

    record_game_start(chat_id, game_type, updated_data, int(remaining_seconds))

    # Tentar enviar uma mensagem privada para o usuário (isso só funciona se o usuário iniciou o bot)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Você já pode tentar novamente no jogo de adivinhação de filme no grupo!"
        )
    except Exception:
        # Não fazer nada se não conseguir enviar mensagem privada
        pass
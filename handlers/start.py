#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import register_user, is_admin

# Configurar logging
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    
    # Register user in the database
    register_user(
        user.id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
    # Check if this is a photo view request for prize claims
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("view_photo_"):
            photo_id = arg.replace("view_photo_", "")
            
            # Verificar se o usuário é administrador
            if is_admin(user.id):
                try:
                    # Enviar a foto para o administrador
                    await context.bot.send_photo(
                        chat_id=user.id,
                        photo=photo_id,
                        caption="📸 Foto da plataforma enviada pelo usuário para resgate de prêmio."
                    )
                    await update.message.reply_text(
                        "✅ Foto de verificação do prêmio exibida acima."
                    )
                    return
                except Exception as e:
                    logger.error(f"Erro ao enviar a foto: {e}")
                    await update.message.reply_text(
                        "⚠️ Não foi possível recuperar a foto. O ID da foto pode ser inválido ou ela foi excluída."
                    )
                    return
            else:
                await update.message.reply_text(
                    "⚠️ Apenas administradores podem visualizar fotos de verificação de prêmios."
                )
                return
        # Se não for um código para visualizar foto, pode ser um convite
        else:
            # This might be an invite code - handle in the invite handler
            from handlers.invite import handle_invite_join
            await handle_invite_join(update, context)
    
    welcome_text = (
        f"👋 Olá, {user.first_name}!\n\n"
        "Bem-vindo ao Bot de Jogos Interativos! Aqui você pode participar de "
        "diversos jogos divertidos com seus amigos e ganhar pontos.\n\n"
        "📜 *Comandos disponíveis:*\n"
        "/filme - Jogo de adivinhar filme por emojis\n"
        "/quiz - Quiz de perguntas gerais\n"
        "/mimica - Jogo de mímica com temas divertidos\n"
        "/placar - Ver o ranking de pontos\n"
        "/convite - Gerar link de convite\n"
        "/premio - Solicitar resgate de prêmio\n"
        "/configurar - Configurar o bot (somente admin)\n"
        "/help - Exibir esta ajuda\n\n"
        "Divirta-se e boa sorte! 🎮"
    )
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a detailed help message when the command /help is issued."""
    help_text = (
        "🎮 *Bot de Jogos Interativos* 🎮\n\n"
        "Participe de nossos jogos, acumule pontos e ganhe prêmios!\n\n"
        "📜 *Jogos disponíveis:*\n\n"
        "🎬 *Adivinhe o Filme* - /filme\n"
        "Descubra qual filme está representado por uma sequência de emojis.\n\n"
        "🧠 *Quiz de Conhecimentos* - /quiz\n"
        "Responda perguntas de conhecimentos gerais e ganhe pontos.\n"
        "Quanto mais rápido responder, mais pontos você ganha!\n\n"
        "🔍 *Sequência de Emoji* - /emoji\n"
        "Descubra o padrão em uma sequência de emojis e complete-a corretamente.\n\n"
        "📊 *Outras funcionalidades:*\n\n"
        "/placar - Veja o ranking dos jogadores com mais pontos\n"
        "/convite - Crie um link de convite e ganhe pontos por cada novo participante\n"
        "/premio - Solicite o resgate do seu prêmio quando acumular pontos suficientes\n\n"
        "⚙️ *Administração:*\n"
        "/configurar - Configure os parâmetros do bot (apenas para administradores)\n\n"
        "Participe dos jogos e divirta-se! 🎯"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

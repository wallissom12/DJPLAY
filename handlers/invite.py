#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import string
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from psycopg2.extras import RealDictCursor
from database import (
    register_user, create_invite, use_invite, 
    get_user_invites, get_setting, get_invite_leaderboard, get_db_connection
)

logger = logging.getLogger(__name__)

def generate_invite_code():
    """Gera um código de convite único."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

async def generate_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera um link de convite personalizado com o nickname do usuário."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Registrar usuário
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Verificar se o bot está em um grupo e tem direitos para gerar links
    if chat_type in ['group', 'supergroup']:
        try:
            # Tentar obter informações do chat
            chat = await context.bot.get_chat(chat_id)
            if not chat.invite_link:
                chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
                if not chat_member.can_invite_users:
                    await update.message.reply_text(
                        "⚠️ Não tenho permissão para gerar links de convite neste grupo. "
                        "Por favor, dê a permissão de 'Adicionar membros' ao bot para usar esta função."
                    )
                    return
        except Exception as e:
            logger.error(f"Erro ao verificar permissões do bot no grupo: {e}")
    
    # Gerar código único de convite
    username_part = user.username or f"user{user.id}"
    # Limitar tamanho e remover caracteres especiais
    username_part = ''.join(c for c in username_part if c.isalnum())[:10]
    invite_code = f"{username_part}_{generate_invite_code()}"
    
    # Criar o convite no banco de dados
    success = create_invite(user.id, invite_code)
    
    if success:
        # Se estamos em um grupo, gerar link de convite para o grupo
        if chat_type in ['group', 'supergroup']:
            try:
                # Tentar gerar link de convite do grupo
                if not hasattr(chat, 'invite_link') or not chat.invite_link:
                    invite_link = await context.bot.export_chat_invite_link(chat_id)
                else:
                    invite_link = chat.invite_link
                
                # Adicionar o código de convite como parâmetro (para rastreamento)
                if '?' not in invite_link:
                    group_invite_url = f"{invite_link}?invite={invite_code}"
                else:
                    group_invite_url = f"{invite_link}&invite={invite_code}"
                
                # Obter configurações de pontos por convite
                invitation_enabled = get_setting("invitation_enabled", "true").lower() == "true"
                invitation_points = int(get_setting("invitation_points", "5"))
                
                points_text = ""
                if invitation_enabled:
                    points_text = f"\nVocê ganhará *{invitation_points} pontos* por cada novo usuário que entrar usando seu link."
                
                # Obter convites anteriores do usuário
                invites = get_user_invites(user.id)
                invites_text = ""
                if invites:
                    successful_invites = sum(1 for inv in invites if inv['used'])
                    invites_text = f"\n\n*Seus convites:*\n• Total de convites: {len(invites)}\n• Convites usados: {successful_invites}"
                
                # Criar botão para o link
                keyboard = [[InlineKeyboardButton("🔗 Compartilhar Link", url=group_invite_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🔗 *Link de convite de {user.first_name}*\n\n"
                    f"Use o botão abaixo para compartilhar seu link personalizado para este grupo.{points_text}{invites_text}",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Erro ao gerar link de convite para o grupo: {e}")
                # Fallback para convite direto para o bot
                await generate_bot_invite_link(update, context, user, invite_code)
        else:
            # Se estamos em chat privado, gerar convite normal para o bot
            await generate_bot_invite_link(update, context, user, invite_code)
    else:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível gerar um link de convite agora. Tente novamente mais tarde."
        )

async def generate_bot_invite_link(update, context, user, invite_code):
    """Gera um link de convite direto para o bot (usado como fallback)."""
    # Criar deep link para o bot com o código de convite
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={invite_code}"
    
    # Obter configurações de pontos por convite
    invitation_enabled = get_setting("invitation_enabled", "true").lower() == "true"
    invitation_points = int(get_setting("invitation_points", "5"))
    
    points_text = ""
    if invitation_enabled:
        points_text = f"\nVocê ganhará *{invitation_points} pontos* por cada novo usuário que entrar usando seu link."
    
    # Obter convites anteriores do usuário
    invites = get_user_invites(user.id)
    invites_text = ""
    if invites:
        successful_invites = sum(1 for inv in invites if inv['used'])
        invites_text = f"\n\n*Seus convites:*\n• Total de convites: {len(invites)}\n• Convites usados: {successful_invites}"
    
    await update.message.reply_text(
        f"🔗 *Seu link de convite foi gerado!*\n\n"
        f"Compartilhe este link com seus amigos:\n"
        f"`{invite_link}`{points_text}{invites_text}",
        parse_mode="Markdown"
    )

async def handle_invite_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa quando um usuário entra via link de convite."""
    user = update.effective_user
    
    # Extrair código de convite do comando start
    if not context.args or len(context.args) < 1:
        # Mensagem padrão de boas vindas se não for um convite
        await update.message.reply_text(
            f"👋 Olá, {user.first_name}! Bem-vindo ao Bot de Jogos!\n\n"
            f"Use /help para ver os comandos disponíveis ou me adicione a um grupo para jogar!"
        )
        return
    
    invite_code = context.args[0]
    
    # Registrar o usuário
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Tentar usar o convite
    inviter_id = use_invite(invite_code, user.id)
    
    if inviter_id:
        # Obter configurações de pontos por convite
        invitation_enabled = get_setting("invitation_enabled", "true").lower() == "true"
        invitation_points = int(get_setting("invitation_points", "5"))
        
        points_text = ""
        if invitation_enabled:
            points_text = f"Você ganhou *{invitation_points} pontos!* 🎁"
        
        try:
            # Notificar o convidador
            await context.bot.send_message(
                chat_id=inviter_id,
                text=f"🎉 *Parabéns!* Um novo usuário ({user.first_name}) entrou usando seu link de convite.\n"
                     f"{points_text}",
                parse_mode="Markdown"
            )
            
            # Obter informações do convidador para personalizar a mensagem
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT username, first_name, last_name FROM users WHERE user_id = %s", (inviter_id,))
            inviter = cursor.fetchone()
            conn.close()
            
            inviter_name = inviter['username'] if inviter and inviter['username'] else \
                          f"{inviter['first_name']} {inviter['last_name'] or ''}" if inviter else "outro usuário"
            
            # Notificar o novo usuário
            await update.message.reply_text(
                f"🎉 Você entrou através do link de convite de *{inviter_name}*!\n"
                f"Bem-vindo ao Bot de Jogos! Use /help para ver os comandos disponíveis.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Erro ao notificar sobre convite: {e}")
    else:
        # Mensagem padrão se o código de convite for inválido
        await update.message.reply_text(
            f"👋 Olá, {user.first_name}! Bem-vindo ao Bot de Jogos!\n\n"
            f"Use /help para ver os comandos disponíveis ou me adicione a um grupo para jogar!"
        )

async def show_invite_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra o ranking dos usuários que mais convidaram pessoas."""
    # Obter o top 10 de usuários por convites
    leaderboard = get_invite_leaderboard(10)
    
    if not leaderboard:
        await update.message.reply_text(
            "📊 *Ranking de Convites* 📊\n\n"
            "Ainda não há usuários com convites bem-sucedidos!",
            parse_mode="Markdown"
        )
        return
    
    leaderboard_text = "📊 *RANKING DE CONVITES* 📊\n\n"
    for i, user in enumerate(leaderboard, 1):
        username = user['username'] if user['username'] else f"{user['first_name']} {user['last_name'] or ''}"
        leaderboard_text += f"{i}. {username}: *{user['invite_count']}* convites\n"
    
    await update.message.reply_text(
        leaderboard_text,
        parse_mode="Markdown"
    )

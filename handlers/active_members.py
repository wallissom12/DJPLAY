#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import (
    register_user, get_active_members, is_admin, 
    is_group_admin, is_chat_allowed, add_user_activity
)

logger = logging.getLogger(__name__)

async def show_active_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibir os membros mais ativos do grupo."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Registrar usuário se ainda não estiver registrado
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Registrar atividade do usuário ao usar este comando
    add_user_activity(user.id, chat_id, "command")
    
    # Verificar se é um grupo
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ Este comando só pode ser usado em grupos!"
        )
        return
    
    # Verificar se o grupo está na lista de permitidos
    if not is_chat_allowed(chat_id):
        await update.message.reply_text(
            "⚠️ Este grupo não está autorizado a usar este bot."
        )
        return
    
    # Obter a lista de membros mais ativos
    limit = 20  # Padrão: 20 membros mais ativos
    if len(context.args) > 0:
        try:
            limit = int(context.args[0])
            if limit < 1:
                limit = 1
            elif limit > 50:
                limit = 50
        except ValueError:
            pass
    
    active_members = get_active_members(chat_id, limit)
    
    if not active_members:
        await update.message.reply_text(
            "📊 *Membros Ativos* 📊\n\n"
            "Não foram encontrados dados de atividade para este grupo ainda.\n"
            "A atividade é registrada com base nas mensagens enviadas, comandos usados e participação em jogos.",
            parse_mode="Markdown"
        )
        return
    
    # Preparar a mensagem com a lista de membros ativos
    header = "📊 *TOP MEMBROS MAIS ATIVOS* 📊\n\n"
    
    member_lines = []
    for i, member in enumerate(active_members):
        # Usar medalhas para os 3 primeiros
        if i == 0:
            prefix = "🥇"
        elif i == 1:
            prefix = "🥈"
        elif i == 2:
            prefix = "🥉"
        else:
            prefix = f"{i+1}."
        
        # Formatar nome do usuário (username se disponível, ou primeiro nome)
        name = member["username"] if member["username"] else member["first_name"]
        
        # Adicionar linha com ranking, nome e pontuação de atividade
        member_lines.append(f"{prefix} {name}: {member['activity_score']} atividades")
    
    footer = "\n\nA atividade é baseada em mensagens enviadas, comandos usados e participação em jogos."
    
    # Juntar todas as partes da mensagem
    message = header + "\n".join(member_lines) + footer
    
    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )

# Função para registrar atividade em mensagens normais
async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registrar atividade de usuários no grupo."""
    # Ignorar se não for uma mensagem em grupo
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        return
    
    # Ignorar se não estiver em um grupo permitido
    if not is_chat_allowed(update.effective_chat.id):
        return
        
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Registrar atividade do usuário
    add_user_activity(user.id, chat_id, "message")
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import string
from telegram import Update
from telegram.ext import ContextTypes
from database import register_user, create_invite, use_invite, get_user_invites

def generate_invite_code():
    """Generate a random invite code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

async def generate_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate an invite link command."""
    user = update.effective_user
    
    # Generate a unique invite code
    invite_code = generate_invite_code()
    
    # Create the invite in the database
    success = create_invite(user.id, invite_code)
    
    if success:
        # Create a deep link to the bot with the invite code
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={invite_code}"
        
        # Get user's previous invites
        invites = get_user_invites(user.id)
        invites_text = ""
        if invites:
            invites_text = "\n\n*Seus convites anteriores:*\n"
            for invite in invites[:5]:  # Show only the last 5 invites
                invites_text += f"• Código: `{invite['invite_code']}` - Usos: {invite['uses']}\n"
        
        await update.message.reply_text(
            f"🔗 *Seu link de convite foi gerado!*\n\n"
            f"Compartilhe este link com seus amigos para ganhar pontos:\n"
            f"`{invite_link}`\n\n"
            f"Você ganhará *20 pontos* por cada novo usuário que entrar usando seu link."
            f"{invites_text}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "😕 Desculpe, não foi possível gerar um link de convite agora. Tente novamente mais tarde."
        )

async def handle_invite_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when a user joins via an invite link."""
    user = update.effective_user
    
    # Extract invite code from the start command
    if not context.args or len(context.args) < 1:
        return
    
    invite_code = context.args[0]
    
    # Register the user
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Try to use the invite
    inviter_id = use_invite(invite_code, user.id)
    
    if inviter_id:
        try:
            # Notify the inviter
            await context.bot.send_message(
                chat_id=inviter_id,
                text=f"🎉 *Parabéns!* Um novo usuário ({user.first_name}) entrou usando seu link de convite.\n"
                     f"Você ganhou *20 pontos!* 🎁",
                parse_mode="Markdown"
            )
            
            # Notify the new user
            await update.message.reply_text(
                f"🎉 Você entrou através de um link de convite!\n"
                f"Bem-vindo ao Bot de Jogos! Use /help para ver os comandos disponíveis."
            )
        except Exception as e:
            print(f"Error notifying about invite: {e}")

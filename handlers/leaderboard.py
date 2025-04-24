#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes
from database import get_leaderboard, get_user_points, register_user

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the leaderboard with top users."""
    user = update.effective_user
    
    # Register user if not already registered
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Get leaderboard data
    leaderboard = get_leaderboard(10)  # Top 10 users
    
    if not leaderboard:
        await update.message.reply_text(
            "📊 *Placar de Pontos*\n\n"
            "Ainda não há jogadores com pontos registrados.\n"
            "Seja o primeiro a jogar e marcar pontos! Use /help para ver os jogos disponíveis.",
            parse_mode="Markdown"
        )
        return
    
    # Format the leaderboard message
    leaderboard_text = "🏆 *PLACAR DE PONTOS* 🏆\n\n"
    
    for i, player in enumerate(leaderboard):
        # Add emoji for top 3
        position_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        
        # Format name - use username if available, otherwise first name
        player_name = player["username"] if player["username"] else player["first_name"]
        
        # Highlight the current user
        if player["user_id"] == user.id:
            leaderboard_text += f"{position_emoji} *{player_name}* - {player['points']} pontos 👈\n"
        else:
            leaderboard_text += f"{position_emoji} {player_name} - {player['points']} pontos\n"
    
    # Get current user's position if not in top 10
    user_in_top = any(player["user_id"] == user.id for player in leaderboard)
    if not user_in_top:
        user_points = get_user_points(user.id)
        leaderboard_text += f"\n...\n👤 *Você* - {user_points} pontos"
    
    leaderboard_text += (
        f"\n\n🎮 *Como ganhar pontos:*\n"
        f"• Participe dos jogos e responda corretamente\n"
        f"• Quanto mais rápido responder, mais pontos ganha\n"
        f"• Convide amigos usando /convite"
    )
    
    await update.message.reply_text(leaderboard_text, parse_mode="Markdown")

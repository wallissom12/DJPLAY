#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import SETTINGS, save_settings, load_settings
import json
import logging

logger = logging.getLogger(__name__)

async def admin_configure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /configurar command to set bot parameters."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in SETTINGS["admin_ids"] and len(SETTINGS["admin_ids"]) > 0:
        await update.message.reply_text(
            "⛔ Você não tem permissão para usar este comando. Apenas administradores podem configurar o bot."
        )
        return
    
    # If no admins are set yet, the first person to use this command becomes admin
    if not SETTINGS["admin_ids"]:
        SETTINGS["admin_ids"].append(user_id)
        save_settings(SETTINGS)
        await update.message.reply_text("🎖️ Você foi registrado como o primeiro administrador do bot!")
    
    # Create configuration menu
    keyboard = [
        [
            InlineKeyboardButton("Pontos por resposta", callback_data="config_points_correct"),
            InlineKeyboardButton("Pontos por segundo", callback_data="config_points_second")
        ],
        [
            InlineKeyboardButton("Frequência de jogos", callback_data="config_game_frequency"),
            InlineKeyboardButton("Tempo de notificação", callback_data="config_notification_time")
        ],
        [
            InlineKeyboardButton("Valor do prêmio", callback_data="config_prize_amount"),
            InlineKeyboardButton("Frequência do prêmio", callback_data="config_prize_frequency")
        ],
        [
            InlineKeyboardButton("Adicionar admin", callback_data="config_add_admin"),
            InlineKeyboardButton("Remover admin", callback_data="config_remove_admin")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    config_text = (
        "⚙️ *Configurações do Bot* ⚙️\n\n"
        f"🏆 Pontos por resposta correta: *{SETTINGS['points_per_correct_answer']}*\n"
        f"⏱️ Pontos por segundo: *{SETTINGS['points_per_second']}*\n"
        f"🔄 Frequência de jogos: *{SETTINGS['game_frequency_minutes']}* minutos\n"
        f"🔔 Notificação antes do jogo: *{SETTINGS['notification_minutes_before']}* minutos\n"
        f"💰 Valor do prêmio: *R$ {SETTINGS['prize_amount']}*\n"
        f"📅 Frequência do prêmio: *{SETTINGS['prize_frequency']}*\n"
        f"👮 Administradores: *{len(SETTINGS['admin_ids'])}* usuários\n\n"
        "Selecione uma opção para configurar:"
    )
    
    await update.message.reply_text(config_text, reply_markup=reply_markup, parse_mode="Markdown")

async def admin_configure_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks from admin configuration menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in SETTINGS["admin_ids"]:
        await query.edit_message_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    callback_data = query.data
    
    if callback_data == "config_points_correct":
        await query.edit_message_text(
            "🏆 Digite o novo valor de pontos por resposta correta.\n"
            "Responda com /set_points_correct [número]"
        )
        context.user_data["admin_config"] = "points_correct"
        
    elif callback_data == "config_points_second":
        await query.edit_message_text(
            "⏱️ Digite o novo valor de pontos por segundo (diminui do total).\n"
            "Responda com /set_points_second [número]"
        )
        context.user_data["admin_config"] = "points_second"
        
    elif callback_data == "config_game_frequency":
        await query.edit_message_text(
            "🔄 Digite a nova frequência de jogos em minutos.\n"
            "Responda com /set_game_frequency [minutos]"
        )
        context.user_data["admin_config"] = "game_frequency"
        
    elif callback_data == "config_notification_time":
        await query.edit_message_text(
            "🔔 Digite quantos minutos antes do jogo a notificação deve ser enviada.\n"
            "Responda com /set_notification_time [minutos]"
        )
        context.user_data["admin_config"] = "notification_time"
        
    elif callback_data == "config_prize_amount":
        await query.edit_message_text(
            "💰 Digite o novo valor do prêmio (em R$).\n"
            "Responda com /set_prize_amount [valor]"
        )
        context.user_data["admin_config"] = "prize_amount"
        
    elif callback_data == "config_prize_frequency":
        keyboard = [
            [
                InlineKeyboardButton("Semanal", callback_data="set_prize_freq_weekly"),
                InlineKeyboardButton("Mensal", callback_data="set_prize_freq_monthly")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📅 Selecione a frequência do prêmio:",
            reply_markup=reply_markup
        )
        
    elif callback_data == "config_add_admin":
        await query.edit_message_text(
            "👮 Digite o ID do Telegram do novo administrador.\n"
            "Responda com /add_admin [user_id]"
        )
        context.user_data["admin_config"] = "add_admin"
        
    elif callback_data == "config_remove_admin":
        admin_buttons = []
        for admin_id in SETTINGS["admin_ids"]:
            admin_buttons.append([
                InlineKeyboardButton(f"Admin ID: {admin_id}", callback_data=f"remove_admin_{admin_id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(admin_buttons)
        await query.edit_message_text(
            "🗑️ Selecione um administrador para remover:",
            reply_markup=reply_markup
        )
    
    # Prize frequency settings
    elif callback_data == "set_prize_freq_weekly":
        SETTINGS["prize_frequency"] = "weekly"
        save_settings(SETTINGS)
        await query.edit_message_text("✅ Frequência do prêmio atualizada para semanal.")
        
    elif callback_data == "set_prize_freq_monthly":
        SETTINGS["prize_frequency"] = "monthly"
        save_settings(SETTINGS)
        await query.edit_message_text("✅ Frequência do prêmio atualizada para mensal.")
        
    # Remove admin handling
    elif callback_data.startswith("remove_admin_"):
        admin_to_remove = int(callback_data.replace("remove_admin_", ""))
        
        if admin_to_remove == user_id and len(SETTINGS["admin_ids"]) == 1:
            await query.edit_message_text("⚠️ Você não pode remover a si mesmo quando é o único administrador.")
            return
        
        if admin_to_remove in SETTINGS["admin_ids"]:
            SETTINGS["admin_ids"].remove(admin_to_remove)
            save_settings(SETTINGS)
            await query.edit_message_text(f"✅ Administrador {admin_to_remove} removido com sucesso.")
        else:
            await query.edit_message_text("⚠️ Este usuário não é um administrador.")

# Command handlers for admin configuration
async def set_points_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set points per correct answer."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        points = int(context.args[0])
        if points < 0:
            await update.message.reply_text("⚠️ O valor de pontos não pode ser negativo.")
            return
            
        SETTINGS["points_per_correct_answer"] = points
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Pontos por resposta correta atualizados para {points}.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /set_points_correct [número]")

async def set_points_second(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set points per second."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        points = int(context.args[0])
        if points < 0:
            await update.message.reply_text("⚠️ O valor de pontos não pode ser negativo.")
            return
            
        SETTINGS["points_per_second"] = points
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Pontos por segundo atualizados para {points}.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /set_points_second [número]")

async def set_game_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set game frequency in minutes."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        minutes = int(context.args[0])
        if minutes < 5:
            await update.message.reply_text("⚠️ A frequência mínima é de 5 minutos.")
            return
            
        SETTINGS["game_frequency_minutes"] = minutes
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Frequência de jogos atualizada para {minutes} minutos.")
        
        # Reschedule games
        from utils.scheduler import reschedule_games
        reschedule_games(context.application)
        
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /set_game_frequency [minutos]")

async def set_notification_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set notification time before games in minutes."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        minutes = int(context.args[0])
        if minutes < 1 or minutes > SETTINGS["game_frequency_minutes"] - 1:
            await update.message.reply_text(
                f"⚠️ O tempo de notificação deve ser entre 1 e {SETTINGS['game_frequency_minutes'] - 1} minutos."
            )
            return
            
        SETTINGS["notification_minutes_before"] = minutes
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Tempo de notificação atualizado para {minutes} minutos antes do jogo.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /set_notification_time [minutos]")

async def set_prize_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set prize amount."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        amount = context.args[0]
        # Convert to float and back to string to validate
        float_amount = float(amount.replace(",", "."))
        if float_amount <= 0:
            await update.message.reply_text("⚠️ O valor do prêmio deve ser maior que zero.")
            return
            
        # Format as Brazilian currency
        formatted_amount = f"{float_amount:.2f}".replace(".", ",")
        SETTINGS["prize_amount"] = formatted_amount
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Valor do prêmio atualizado para R$ {formatted_amount}.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /set_prize_amount [valor]")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new admin."""
    user_id = update.effective_user.id
    
    if user_id not in SETTINGS["admin_ids"]:
        await update.message.reply_text("⛔ Você não tem permissão para configurar o bot.")
        return
    
    try:
        new_admin_id = int(context.args[0])
        if new_admin_id in SETTINGS["admin_ids"]:
            await update.message.reply_text("⚠️ Este usuário já é um administrador.")
            return
            
        SETTINGS["admin_ids"].append(new_admin_id)
        save_settings(SETTINGS)
        await update.message.reply_text(f"✅ Usuário {new_admin_id} adicionado como administrador.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Formato inválido. Use /add_admin [user_id]")

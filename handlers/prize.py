#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import register_user, get_user_points, create_prize_claim, update_prize_payment
from config import SETTINGS

# Minimum points required to claim a prize
PRIZE_MINIMUM_POINTS = 100

async def claim_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle prize claim command."""
    user = update.effective_user
    
    # Register user if not already registered
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    # Get user's current points
    user_points = get_user_points(user.id)
    
    if user_points < PRIZE_MINIMUM_POINTS:
        await update.message.reply_text(
            f"🏆 *Sistema de Prêmios* 🏆\n\n"
            f"Você possui *{user_points}* pontos atualmente.\n"
            f"É necessário ter pelo menos *{PRIZE_MINIMUM_POINTS}* pontos para resgatar um prêmio.\n\n"
            f"Continue participando dos jogos para acumular mais pontos!",
            parse_mode="Markdown"
        )
        return
    
    # User has enough points, show prize claim options
    keyboard = [
        [InlineKeyboardButton("🎁 Resgatar Prêmio", callback_data="prize_claim")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    prize_amount = SETTINGS["prize_amount"]
    prize_frequency = "semanal" if SETTINGS["prize_frequency"] == "weekly" else "mensal"
    
    await update.message.reply_text(
        f"🏆 *Sistema de Prêmios* 🏆\n\n"
        f"Você possui *{user_points}* pontos! Parabéns! 🎉\n\n"
        f"Prêmio atual: *R$ {prize_amount}* ({prize_frequency})\n"
        f"Ao solicitar o resgate, será necessário informar sua chave PIX para recebimento.\n\n"
        f"Deseja resgatar seu prêmio agora?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_prize_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle prize information callbacks."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    callback_data = query.data
    
    if callback_data == "prize_claim":
        # User wants to claim a prize
        user_points = get_user_points(user.id)
        
        if user_points < PRIZE_MINIMUM_POINTS:
            await query.edit_message_text(
                "⚠️ Você não tem pontos suficientes para resgatar um prêmio."
            )
            return
        
        # Create a prize claim record
        prize_id = create_prize_claim(user.id, SETTINGS["prize_amount"])
        
        if not prize_id:
            await query.edit_message_text(
                "❌ Erro ao processar sua solicitação de prêmio. Por favor, tente novamente mais tarde."
            )
            return
        
        # Store the prize ID in user data for the next step
        context.user_data["prize_id"] = prize_id
        
        # Primeiro, solicitar uma foto da plataforma com QR code
        await query.edit_message_text(
            f"🏆 *Resgate de Prêmio - Etapa 1 de 2* 🏆\n\n"
            f"Para continuar com o resgate do prêmio de *R$ {SETTINGS['prize_amount']}*, "
            f"precisamos verificar sua identidade.\n\n"
            f"Por favor, envie uma foto da sua tela mostrando:\n"
            f"• Seu perfil na plataforma\n"
            f"• Um QR code gerado pelo aplicativo\n\n"
            f"Isso nos ajuda a confirmar que você é realmente o dono da conta.\n"
            f"Envie a foto como resposta a esta mensagem:",
            parse_mode="Markdown"
        )
        
        # Set user to waiting for platform photo state
        context.user_data["waiting_for_platform_photo"] = True
        
    elif callback_data == "prize_cancel":
        await query.edit_message_text(
            "🎮 Resgate de prêmio cancelado. Continue participando dos jogos!"
        )
        
    elif callback_data.startswith("prize_confirm_"):
        # Complete the prize claim process
        prize_id = context.user_data.get("prize_id")
        pix_key = context.user_data.get("pix_key")
        platform_photo_id = context.user_data.get("platform_photo_id")
        
        if not prize_id or not pix_key or not platform_photo_id:
            await query.edit_message_text(
                "❌ Erro ao processar sua solicitação de prêmio. Por favor, tente novamente mais tarde."
            )
            return
        
        # Update prize with payment info
        success = update_prize_payment(prize_id, pix_key, platform_photo_id)
        
        if success:
            await query.edit_message_text(
                f"✅ *Solicitação de prêmio realizada com sucesso!* ✅\n\n"
                f"Prêmio: *R$ {SETTINGS['prize_amount']}*\n"
                f"Chave PIX: `{pix_key}`\n\n"
                f"Um administrador irá processar sua solicitação em breve.\n"
                f"Você receberá uma mensagem quando o pagamento for realizado.\n\n"
                f"Obrigado por participar dos nossos jogos! 🎮",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao processar sua solicitação de prêmio. Por favor, tente novamente mais tarde."
            )
        
        # Clear user data
        if "prize_id" in context.user_data:
            del context.user_data["prize_id"]
        if "pix_key" in context.user_data:
            del context.user_data["pix_key"]
        if "platform_photo_id" in context.user_data:
            del context.user_data["platform_photo_id"]
        if "waiting_for_pix" in context.user_data:
            del context.user_data["waiting_for_pix"]
        if "waiting_for_platform_photo" in context.user_data:
            del context.user_data["waiting_for_platform_photo"]

async def handle_platform_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle platform photo submission for prize claims."""
    user = update.effective_user
    
    # Check if user is waiting for platform photo
    if not context.user_data.get("waiting_for_platform_photo", False):
        return
    
    # Check if the message contains a photo
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Por favor, envie uma imagem da sua tela mostrando seu perfil e o QR code."
        )
        return
    
    # Get the largest photo (best quality)
    photo = update.message.photo[-1]
    
    # Store the photo ID for reference
    context.user_data["platform_photo_id"] = photo.file_id
    
    # Move to the next step: asking for PIX key
    await update.message.reply_text(
        f"✅ *Foto recebida com sucesso!* ✅\n\n"
        f"🏆 *Resgate de Prêmio - Etapa 2 de 2* 🏆\n\n"
        f"Agora, por favor, envie sua chave PIX para recebimento do prêmio de *R$ {SETTINGS['prize_amount']}*.\n\n"
        f"A chave pode ser:\n"
        f"• CPF/CNPJ\n"
        f"• E-mail\n"
        f"• Telefone\n"
        f"• Chave aleatória\n\n"
        f"Responda com sua chave PIX:",
        parse_mode="Markdown"
    )
    
    # Update user state
    context.user_data["waiting_for_platform_photo"] = False
    context.user_data["waiting_for_pix"] = True

async def handle_pix_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle PIX key submission for prize claims."""
    user = update.effective_user
    
    # Check if user is waiting for PIX input
    if not context.user_data.get("waiting_for_pix", False):
        return
    
    # Get the PIX key from the message
    pix_key = update.message.text.strip()
    
    # Store the PIX key
    context.user_data["pix_key"] = pix_key
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="prize_confirm_pix"),
            InlineKeyboardButton("❌ Cancelar", callback_data="prize_cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔍 *Confirme sua chave PIX* 🔍\n\n"
        f"Você informou a seguinte chave PIX:\n"
        f"`{pix_key}`\n\n"
        f"Esta chave está correta?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # No longer waiting for PIX input
    context.user_data["waiting_for_pix"] = False

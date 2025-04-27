"""
URLs para o módulo de monitoramento do bot Telegram.
Adicione estas rotas ao arquivo urls.py do seu projeto DJPAY.
"""

from django.urls import path
from . import activate_bot

urlpatterns = [
    path('api/bot/activate/', activate_bot.activate_bot, name='activate_bot'),
    path('api/bot/restart/', activate_bot.restart_bot, name='restart_bot'),
    path('api/bot/status/', activate_bot.bot_status_endpoint, name='bot_status'),
    path('admin/bot/monitor/', activate_bot.bot_admin_view, name='bot_admin_monitor'),
]
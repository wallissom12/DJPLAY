#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import Flask application
from app import app

def start_web_server():
    """Função para iniciar o servidor web Flask."""
    logger.info("Iniciando servidor web na porta 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)

def start_telegram_bot():
    """Função para iniciar o bot do Telegram."""
    logger.info("Iniciando bot do Telegram...")
    try:
        from telegram_bot import main as bot_main
        bot_main()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot do Telegram: {e}")

if __name__ == "__main__":
    # Verificar argumentos de linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] == "--web":
            start_web_server()
        elif sys.argv[1] == "--bot":
            start_telegram_bot()
    else:
        # Iniciar apenas o bot
        start_telegram_bot()
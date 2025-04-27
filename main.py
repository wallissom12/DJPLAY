
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
    logger.info("Iniciando servidor web na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)

def auto_pinger():
    """Função que faz ping no próprio servidor periodicamente para mantê-lo ativo."""
    import requests
    import time
    
    logger.info("Auto-pinger iniciado para manter o projeto ativo")
    while True:
        try:
            # Aguardar 5 minutos entre pings
            time.sleep(300)
            # Fazer um ping no próprio servidor
            response = requests.get('http://localhost:5000/ping', timeout=10)
            if response.status_code == 200:
                logger.info("Auto-ping realizado com sucesso! Bot mantido ativo.")
            else:
                logger.warning(f"Auto-ping retornou status inesperado: {response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao realizar auto-ping: {e}")

def start_telegram_bot():
    """Função para iniciar o bot do Telegram."""
    logger.info("Iniciando bot do Telegram...")
    
    # Iniciar o auto-pinger em uma thread separada
    import threading
    pinger_thread = threading.Thread(target=auto_pinger, daemon=True)
    pinger_thread.start()
    logger.info("Thread de auto-ping iniciada para manter o bot ativo")
    
    try:
        # Verificar se o bot já está rodando
        import os
        import signal
        import socket
        
        # Tentar criar um socket na porta 8123 (escolhida arbitrariamente)
        # para garantir que apenas uma instância do bot está rodando
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            lock_socket.bind(('localhost', 8123))
            logger.info("Bot do Telegram obteve lock exclusivo, iniciando...")
            
            # Iniciar o bot
            from telegram_bot import main as bot_main
            bot_main()
        except socket.error:
            logger.warning("Bot do Telegram já está rodando em outra instância. Esta instância não iniciará o bot.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot do Telegram: {e}")

if __name__ == "__main__":
    # Iniciar apenas o bot do Telegram
    start_telegram_bot()

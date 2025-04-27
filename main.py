
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
        # Verificar se o bot já está rodando usando um arquivo de lock
        import os
        import fcntl
        
        # Usar um arquivo de lock em vez de um socket
        lock_file_path = "/tmp/telegram_bot.lock"
        
        # Abrir (ou criar) o arquivo de lock
        lock_file = open(lock_file_path, 'w')
        
        try:
            # Tentar obter um lock exclusivo não-bloqueante
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Se chegou aqui, o lock foi obtido com sucesso
            logger.info("Bot do Telegram obteve lock exclusivo, iniciando...")
            
            # Gravar PID para referência
            lock_file.write(str(os.getpid()))
            lock_file.flush()
            
            # Iniciar o bot
            from telegram_bot import main as bot_main
            bot_main()
            
        except IOError:
            # Não foi possível obter o lock, outra instância está rodando
            logger.warning("Bot do Telegram já está rodando em outra instância. Esta instância não iniciará o bot.")
            lock_file.close()
            
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot do Telegram: {e}")

if __name__ == "__main__":
    # Iniciar apenas o bot do Telegram
    start_telegram_bot()

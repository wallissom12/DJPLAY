#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import logging
import threading
import requests
import schedule
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("keep_alive")

# Configuração do serviço
APP_URL = os.environ.get("APP_URL", "https://seu-app.replit.app")
BOT_CHECK_INTERVAL = 5  # minutos
PING_INTERVAL = 5  # minutos

def ping_app():
    """Faz um ping no próprio servidor para mantê-lo ativo."""
    try:
        response = requests.get(f"{APP_URL}/ping", timeout=10)
        status = response.status_code
        logger.info(f"Auto-ping enviado: {status}")
        return status == 200
    except Exception as e:
        logger.error(f"Erro ao fazer ping: {e}")
        return False

def check_bot_status():
    """Verifica o status do bot do Telegram e reinicia se necessário."""
    try:
        response = requests.get(f"{APP_URL}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Verificar se o timestamp é recente (menos de 5 minutos)
            timestamp = datetime.fromisoformat(data.get('timestamp'))
            now = datetime.now()
            delta = (now - timestamp).total_seconds() / 60
            
            if delta > 5:
                logger.warning(f"Bot inativo por {delta:.1f} minutos. Solicitando reinício...")
                restart_bot()
            else:
                logger.info(f"Bot ativo (última atividade: {delta:.1f} minutos atrás)")
        else:
            logger.warning(f"Resposta inesperada do servidor: {response.status_code}")
            restart_bot()
    except Exception as e:
        logger.error(f"Erro ao verificar status do bot: {e}")
        restart_bot()

def restart_bot():
    """Solicita reinício do bot."""
    try:
        response = requests.get(f"{APP_URL}/restart_bot", timeout=30)
        if response.status_code == 200:
            logger.info("Solicitação de reinício do bot enviada com sucesso")
        else:
            logger.error(f"Erro ao solicitar reinício do bot: {response.status_code}")
    except Exception as e:
        logger.error(f"Exceção ao solicitar reinício do bot: {e}")

def run_scheduler():
    """Executa o agendador em uma thread separada."""
    schedule.every(PING_INTERVAL).minutes.do(ping_app)
    schedule.every(BOT_CHECK_INTERVAL).minutes.do(check_bot_status)
    
    logger.info("Serviço de manutenção do bot iniciado")
    
    # Executar imediatamente na primeira vez
    ping_app()
    check_bot_status()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_monitor():
    """Inicia o monitor em uma thread separada para não bloquear."""
    monitor_thread = threading.Thread(target=run_scheduler)
    monitor_thread.daemon = True
    monitor_thread.start()
    logger.info("Thread de monitoramento iniciada")
    return monitor_thread

if __name__ == "__main__":
    # Se executado diretamente, inicia o monitor
    thread = start_monitor()
    thread.join()  # Manter o script rodando
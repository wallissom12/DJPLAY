#!/usr/bin/env python
# -*- coding: utf-8 -*-
# restart_bot.py - Script para reiniciar o bot quando necessário

import os
import sys
import time
import logging
import subprocess
import signal
import psutil

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("restart_bot")

def find_telegram_bot_process():
    """Encontra processos Python rodando o bot do Telegram."""
    bot_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                cmdline = proc.info['cmdline']
                if cmdline and any(cmd in ['telegram_bot.py', 'main.py'] for cmd in cmdline):
                    bot_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return bot_processes

def kill_existing_bots():
    """Encerra todos os processos do bot que estiverem rodando."""
    bot_processes = find_telegram_bot_process()
    
    if not bot_processes:
        logger.info("Nenhum processo do bot encontrado para encerrar.")
        return 0
    
    count = 0
    for proc in bot_processes:
        try:
            pid = proc.info['pid']
            logger.info(f"Encerrando processo do bot (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            count += 1
            # Dar tempo para o processo encerrar
            time.sleep(2)
            
            # Verificar se ainda está rodando
            if psutil.pid_exists(pid):
                logger.warning(f"Processo {pid} não encerrou normalmente, forçando...")
                os.kill(pid, signal.SIGKILL)
                
        except Exception as e:
            logger.error(f"Erro ao encerrar processo {pid}: {e}")
    
    logger.info(f"Total de {count} processos encerrados.")
    return count

def start_bot():
    """Inicia o bot em um novo processo."""
    try:
        logger.info("Iniciando novo processo do bot...")
        # Iniciar como um processo independente que continuará rodando
        # depois que este script terminar
        subprocess.Popen(
            [sys.executable, 'telegram_bot.py'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        logger.info("Processo do bot iniciado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar processo do bot: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Iniciando processo de reinício do bot ===")
    
    # Encerrar processos existentes
    killed = kill_existing_bots()
    
    # Aguardar alguns segundos para garantir que todos os processos foram encerrados
    if killed > 0:
        logger.info("Aguardando 5 segundos para garantir que todos os processos encerraram...")
        time.sleep(5)
    
    # Iniciar novo processo
    success = start_bot()
    
    if success:
        logger.info("Bot reiniciado com sucesso!")
    else:
        logger.error("Falha ao reiniciar o bot.")
    
    logger.info("=== Processo de reinício concluído ===")
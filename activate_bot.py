"""
Módulo para ativar e monitorar o bot do Telegram a partir do DJPAY.
Este arquivo deve ser adicionado ao projeto DJPAY para manter o bot ativo.
"""

import os
import requests
import threading
import time
import schedule
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("bot_monitor.log"), logging.StreamHandler()]
)
logger = logging.getLogger("bot_monitor")

# Configurações
BOT_REPLIT_URL = "https://dfcenkfpzp-ivanesouza3232.repl.co/ping"
REPLIT_LOGIN_URL = "https://replit.com/login"
REPLIT_PROJECT_URL = "https://replit.com/@ivanesouza3232/workspace"
SECRET_TOKEN = "token_secreto_djpay_bot"  # Mude para um token seguro

# Variáveis globais para status
bot_status = {
    "last_ping": None,
    "is_active": False,
    "status_message": "Não inicializado",
    "ping_count": 0
}

@csrf_exempt
@require_POST
def activate_bot(request):
    """Endpoint para ativar o bot do Telegram via ping simples."""
    token = request.POST.get('token')
    
    # Verificar autenticação
    if token != SECRET_TOKEN:
        logger.warning("Tentativa de acesso com token inválido")
        return JsonResponse({'status': 'erro', 'mensagem': 'Token inválido'}, status=403)
    
    try:
        # Fazer ping para o endpoint do bot
        response = requests.get(BOT_REPLIT_URL, timeout=10)
        
        # Atualizar status
        bot_status["last_ping"] = time.strftime("%Y-%m-%d %H:%M:%S")
        bot_status["ping_count"] += 1
        
        if response.status_code == 200:
            bot_status["is_active"] = True
            bot_status["status_message"] = "Bot ativo"
            logger.info(f"Ping enviado com sucesso: {response.text}")
            return JsonResponse({
                'status': 'sucesso', 
                'mensagem': 'Bot ativado com sucesso',
                'bot_status': bot_status
            })
        else:
            bot_status["is_active"] = False
            bot_status["status_message"] = f"Erro ao ativar (HTTP {response.status_code})"
            logger.warning(f"Ping retornou status {response.status_code}")
            return JsonResponse({
                'status': 'erro', 
                'mensagem': f'Erro ao ativar bot: {response.status_code}',
                'bot_status': bot_status
            })
            
    except Exception as e:
        bot_status["is_active"] = False
        bot_status["status_message"] = f"Erro: {str(e)}"
        logger.error(f"Erro ao enviar ping para o bot: {e}")
        return JsonResponse({
            'status': 'erro', 
            'mensagem': f'Erro: {str(e)}',
            'bot_status': bot_status
        }, status=500)

@csrf_exempt
@require_POST
def restart_bot(request):
    """Endpoint para reiniciar completamente o bot via Selenium."""
    token = request.POST.get('token')
    
    # Verificar autenticação
    if token != SECRET_TOKEN:
        logger.warning("Tentativa de acesso com token inválido")
        return JsonResponse({'status': 'erro', 'mensagem': 'Token inválido'}, status=403)
    
    # Iniciar processo de reinicialização em uma thread separada
    threading.Thread(target=restart_bot_selenium, daemon=True).start()
    
    return JsonResponse({
        'status': 'sucesso', 
        'mensagem': 'Processo de reinicialização iniciado',
        'bot_status': bot_status
    })

@csrf_exempt
def bot_status_endpoint(request):
    """Endpoint para verificar o status atual do bot."""
    return JsonResponse({
        'status': 'sucesso',
        'bot_status': bot_status
    })

@staff_member_required
def bot_admin_view(request):
    """View para a interface de administração do bot."""
    context = {
        'bot_url': BOT_REPLIT_URL,
        'title': 'Monitor do Bot Telegram'
    }
    return render(request, 'admin/bot_monitor.html', context)

def restart_bot_selenium():
    """Função para reiniciar o bot usando automação com Selenium."""
    bot_status["status_message"] = "Tentando reiniciar via Selenium..."
    logger.info("Iniciando reinicialização do bot via Selenium")
    
    # Configurar o Chrome em modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Acessar o Replit
        logger.info("Acessando página de login do Replit")
        driver.get(REPLIT_LOGIN_URL)
        
        # Fazer login
        logger.info("Tentando fazer login")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        driver.find_element(By.ID, "username").send_keys(os.environ.get("REPLIT_USERNAME", ""))
        driver.find_element(By.ID, "password").send_keys(os.environ.get("REPLIT_PASSWORD", ""))
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Aguardar login
        time.sleep(5)
        
        # Acessar projeto
        logger.info("Acessando o projeto no Replit")
        driver.get(REPLIT_PROJECT_URL)
        
        # Clicar no botão Run
        logger.info("Tentando iniciar o projeto")
        time.sleep(5)
        run_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Run') or contains(@class, 'run')]"))
        )
        run_button.click()
        
        # Aguardar inicialização
        logger.info("Projeto iniciado, aguardando inicialização completa")
        time.sleep(30)
        
        # Verificar se está funcionando
        response = requests.get(BOT_REPLIT_URL, timeout=10)
        if response.status_code == 200:
            bot_status["is_active"] = True
            bot_status["status_message"] = "Bot reiniciado com sucesso via Selenium"
            bot_status["last_ping"] = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info("Bot reiniciado com sucesso via Selenium")
        else:
            bot_status["status_message"] = f"Erro após reinicialização: {response.status_code}"
            logger.warning(f"Erro após reinicialização: {response.status_code}")
            
    except Exception as e:
        bot_status["status_message"] = f"Erro na reinicialização: {str(e)}"
        logger.error(f"Erro ao reiniciar bot via Selenium: {e}")
    finally:
        if driver:
            driver.quit()

def ping_bot_task():
    """Tarefa agendada para fazer ping no bot periodicamente."""
    try:
        logger.info("Executando ping agendado")
        response = requests.get(BOT_REPLIT_URL, timeout=10)
        
        bot_status["last_ping"] = time.strftime("%Y-%m-%d %H:%M:%S")
        bot_status["ping_count"] += 1
        
        if response.status_code == 200:
            bot_status["is_active"] = True
            bot_status["status_message"] = "Bot ativo (ping automático)"
            logger.info(f"Ping automático enviado com sucesso: {response.text}")
        else:
            bot_status["is_active"] = False
            bot_status["status_message"] = f"Erro no ping automático (HTTP {response.status_code})"
            logger.warning(f"Ping automático retornou status {response.status_code}")
            
    except Exception as e:
        bot_status["is_active"] = False
        bot_status["status_message"] = f"Erro no ping automático: {str(e)}"
        logger.error(f"Erro ao enviar ping automático para o bot: {e}")

# Iniciar o scheduler para pings automáticos
def start_scheduler():
    """Inicia o agendador para enviar pings periódicos."""
    # Agendar para executar a cada 5 minutos
    schedule.every(5).minutes.do(ping_bot_task)
    logger.info("Agendador de pings iniciado (intervalo: 5 minutos)")
    
    # Executar em uma thread separada
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Thread do agendador iniciada")

# Iniciar o scheduler automaticamente ao importar o módulo
start_scheduler()
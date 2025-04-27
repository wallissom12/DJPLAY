# Instruções de Implantação

Este documento contém instruções detalhadas para implantar o Bot de Jogos do Telegram em diferentes plataformas de hospedagem.

## Dependências

O projeto requer as seguintes dependências para funcionar:

```
flask==2.3.3
flask-login==0.6.2
flask-sqlalchemy==3.1.1
gunicorn==23.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
python-telegram-bot==20.6
requests==2.31.0
schedule==1.2.1
werkzeug==2.3.7
```

## Variáveis de Ambiente Necessárias

As seguintes variáveis de ambiente devem ser configuradas:

- `TELEGRAM_BOT_TOKEN`: Token do seu bot do Telegram (obtido através do BotFather)
- `TELEGRAM_BOT_USERNAME`: Nome de usuário do seu bot (sem o @)
- `TMDB_API_KEY`: Chave da API do The Movie Database (para o jogo de filmes)
- `DATABASE_URL`: URL de conexão com o banco de dados PostgreSQL
- `ADMIN_USERNAME`: Nome de usuário para o painel de administração
- `ADMIN_PASSWORD`: Senha para o painel de administração
- `FLASK_SECRET_KEY`: Chave secreta para sessões do Flask

## Opção 1: Implantação no Render

O Render (render.com) é uma ótima opção pois oferece:
- Implantação automática a partir do GitHub
- Suporte nativo para Python
- Banco de dados PostgreSQL integrado
- SSL gratuito

### Passos para Implantação no Render

1. Crie uma conta em render.com
2. Crie um novo serviço Web
3. Conecte ao seu repositório GitHub
4. Configure o ambiente:
   - **Runtime**: Python 3.9 ou superior
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port main:app`
5. Configure as variáveis de ambiente necessárias
6. Crie um banco de dados PostgreSQL no Render
7. Conecte o banco de dados ao seu serviço web

## Opção 2: Implantação no PythonAnywhere

PythonAnywhere é uma opção com um plano gratuito, adequado para desenvolvimento e testes.

### Passos para Implantação no PythonAnywhere

1. Crie uma conta em pythonanywhere.com
2. Crie uma nova aplicação web usando Flask
3. Configure o WSGI file para apontar para o arquivo `main.py`
4. Instale as dependências usando pip
5. Configure as variáveis de ambiente no arquivo .env ou diretamente no script WSGI
6. Crie um banco de dados PostgreSQL (requer plano pago) ou use MySQL
7. Configure uma tarefa agendada para fazer ping no endpoint `/ping` a cada 5 minutos

## Opção 3: Implantação no Railway

Railway é uma plataforma moderna com escalabilidade automática.

### Passos para Implantação no Railway

1. Crie uma conta em railway.app
2. Crie um novo projeto a partir do GitHub
3. Adicione um serviço PostgreSQL
4. Configure o ambiente:
   - Especifique o comando de início: `gunicorn --bind 0.0.0.0:$PORT main:app`
5. Configure as variáveis de ambiente necessárias
6. Implante o projeto

## Manutenção do Bot Ativo

Para manter o bot sempre ativo, é recomendado:

1. Configurar um serviço de monitoramento como UptimeRobot para fazer ping no endpoint `/ping` a cada 5 minutos
2. Usar o endpoint `/restart_bot` para reiniciar o bot se ele parar de responder
3. Configurar alertas de monitoramento para receber notificações se o bot ficar offline

## Verificando o Status do Bot

Use o endpoint `/api/status` para verificar se o bot está funcionando corretamente. Este endpoint retorna um JSON com o status atual do bot e o timestamp da última atividade.
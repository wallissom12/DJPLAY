# Instruções para Implantação no Render

Este documento contém um guia passo a passo para implantar o Bot de Jogos do Telegram no Render.

## Pré-requisitos

1. Uma conta no [Render](https://render.com)
2. Um token de bot do Telegram (obtido pelo [BotFather](https://t.me/botfather))
3. Uma chave de API do TMDb (para o jogo de filmes)
4. Acesso ao repositório Git contendo o código do bot

## Configuração Inicial no Render

### 1. Criar um Novo Projeto Blueprint

1. Faça login na sua conta do Render
2. No Dashboard, clique em "New" e selecione "Blueprint"
3. Conecte seu repositório Git contendo o código do bot
4. O Render detectará automaticamente o arquivo `render.yaml` e configurará os serviços conforme definido

### 2. Configurar Variáveis de Ambiente

Após a criação inicial, você precisará configurar manualmente as seguintes variáveis de ambiente:

1. Acesse o serviço web `telegram-games-bot`
2. Vá para a guia "Environment"
3. Configure as seguintes variáveis:
   - `TELEGRAM_BOT_TOKEN`: Token do seu bot do Telegram
   - `TELEGRAM_BOT_USERNAME`: Nome de usuário do seu bot (sem o @)
   - `TMDB_API_KEY`: Chave da API do The Movie Database
   - `ADMIN_USERNAME`: Nome de usuário para o painel de administração
   - `ADMIN_PASSWORD`: Senha para o painel de administração

4. Repita o processo para o serviço worker `telegram-bot-worker`, configurando:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_BOT_USERNAME`
   - `TMDB_API_KEY`

### 3. Iniciar os Serviços

1. Depois de configurar as variáveis de ambiente, volte para o dashboard
2. Clique em "Manual Deploy" para cada serviço e selecione "Deploy latest commit"
3. Aguarde a conclusão do processo de build e deploy

## Verificar a Implantação

### 1. Verificar o Serviço Web

1. Após a implantação, clique no URL do serviço web
2. Você deverá ver a página inicial do bot
3. Tente fazer login no painel de administração com as credenciais configuradas

### 2. Verificar o Bot do Telegram

1. Abra o Telegram e busque pelo seu bot (@seu_bot_username)
2. Envie o comando `/start`
3. Verifique se o bot responde corretamente

### 3. Verificar os Endpoints de Monitoramento

1. Acesse `https://seu-app.onrender.com/api/status` para verificar o status da API
2. Acesse `https://seu-app.onrender.com/ping` para testar o endpoint de ping

## Manter o Bot Sempre Ativo

O Render já mantém os serviços web sempre ativos por padrão. Para garantir que o bot responda rapidamente:

1. Configure um serviço de monitoramento como o UptimeRobot para fazer ping no endpoint `/ping` a cada 5 minutos
2. Verifique periodicamente o dashboard do Render para garantir que ambos os serviços estejam rodando

## Configuração de Banco de Dados

O Render configura automaticamente um banco de dados PostgreSQL conforme definido no `render.yaml`. O banco de dados será:

1. Criado com o nome `telegram-bot-db`
2. Inicialmente no plano gratuito (pode ser atualizado posteriormente)
3. Conectado automaticamente aos serviços web e worker através da variável de ambiente `DATABASE_URL`

## Troubleshooting

Se o bot não estiver funcionando:

1. Verifique os logs de ambos os serviços no dashboard do Render
2. Confirme se as variáveis de ambiente estão configuradas corretamente
3. Verifique se o banco de dados está ativo e conectado
4. Use o endpoint `/restart_bot` para reiniciar o bot em caso de problemas: `https://seu-app.onrender.com/restart_bot`

## Notas Adicionais

- O Render oferece um plano gratuito com limitações, adequado para testes. Para uso em produção, considere atualizar para um plano pago.
- O serviço gratuito do Render pode ficar inativo após períodos de inatividade. Configure o UptimeRobot para evitar isso.
- Mantenha suas chaves API e segredos seguros. Nunca compartilhe o token do bot ou outras credenciais.
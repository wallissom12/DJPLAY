#!/usr/bin/env bash
# Script de build para o Render

# Instalar dependências
echo "Instalando dependências Python..."
pip install -r render_requirements.txt

# Configurar o banco de dados
echo "Configurando banco de dados..."
python -c "from database import setup_database; setup_database()"

# Verificar instalação
echo "Verificando a instalação..."
python -c "import telegram; print(f'python-telegram-bot instalado: versão {telegram.__version__}')"
python -c "import flask; print(f'Flask instalado: versão {flask.__version__}')"

echo "Build concluído com sucesso!"
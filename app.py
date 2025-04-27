#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, jsonify, request, 
    redirect, url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importe as funções do banco de dados
from database import (
    get_leaderboard, get_invite_leaderboard, get_setting, update_setting,
    get_shop_items, create_shop_item, update_shop_item, get_shop_item,
    get_all_purchases, update_purchase_status, delete_shop_item
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "um_segredo_muito_secreto")

# Credenciais do admin
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123"))

# Funções auxiliares para obter todas as configurações
def get_all_settings():
    """Obter todas as configurações do sistema como um dicionário."""
    settings = {
        "points_per_correct_answer": get_setting("points_per_correct_answer", "10"),
        "points_per_second": get_setting("points_per_second", "1"),
        "game_frequency_minutes": get_setting("game_frequency_minutes", "30"),
        "notification_time_minutes": get_setting("notification_time_minutes", "5"),
        "invitation_points": get_setting("invitation_points", "5"),
        "invitation_enabled": get_setting("invitation_enabled", "true"),
        "shop_enabled": get_setting("shop_enabled", "true"),
        "retry_timeout_seconds": get_setting("retry_timeout_seconds", "5"),
        "max_game_duration_seconds": get_setting("max_game_duration_seconds", "300"),
    }
    return settings

# Decorador para rotas que exigem autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Página inicial da aplicação web."""
    try:
        # Obter dados para mostrar na página inicial
        top_users = get_leaderboard(5)
        top_inviters = get_invite_leaderboard(5)
        
        return render_template(
            'index.html', 
            title='Bot de Jogos do Telegram',
            top_users=top_users,
            top_inviters=top_inviters
        )
    except Exception as e:
        logger.error(f"Erro na página inicial: {e}")
        return render_template('index.html', title='Bot de Jogos do Telegram', error=str(e))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login para administradores."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    
    return render_template('login.html', title='Login - Administração')

@app.route('/logout')
def logout():
    """Rota para logout."""
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Você saiu com sucesso', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Dashboard de administração."""
    return render_template('admin/dashboard.html', title='Painel de Administração')

@app.route('/admin/leaderboard')
@login_required
def admin_leaderboard():
    """Página de gerenciamento dos placares."""
    top_users = get_leaderboard(20)
    top_inviters = get_invite_leaderboard(20)
    
    return render_template(
        'admin/leaderboard.html', 
        title='Gerenciar Placares',
        top_users=top_users,
        top_inviters=top_inviters
    )

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Página de configurações do sistema."""
    if request.method == 'POST':
        # Processar atualização das configurações
        for key in request.form:
            if key != 'csrf_token':  # Ignorar tokens CSRF
                update_setting(key, request.form[key])
        
        flash('Configurações atualizadas com sucesso!', 'success')
        return redirect(url_for('admin_settings'))
    
    # Obter configurações atuais
    settings = get_all_settings()
    
    return render_template(
        'admin/settings.html', 
        title='Configurações do Sistema',
        settings=settings
    )

@app.route('/admin/shop', methods=['GET'])
@login_required
def admin_shop():
    """Página de gerenciamento da lojinha."""
    items = get_shop_items(active_only=False)
    return render_template(
        'admin/shop.html', 
        title='Gerenciar Lojinha',
        items=items
    )

@app.route('/admin/shop/item/new', methods=['GET', 'POST'])
@login_required
def admin_shop_item_new():
    """Página para adicionar novo item à lojinha."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        points_cost = int(request.form.get('points_cost', 0))
        item_type = request.form.get('item_type')
        real_value = request.form.get('real_value')
        
        # Adiciona informações do tipo e valor real ao description
        if item_type == 'pix':
            if not description:
                description = f"Transferência PIX no valor de R${real_value}."
            else:
                description = f"PIX: R${real_value}. {description}"
        elif item_type == 'banca':
            if not description:
                description = f"Produto Banca no valor de R${real_value}."
            else:
                description = f"Banca: R${real_value}. {description}"
        
        if name and points_cost > 0:
            item_id = create_shop_item(name, description, points_cost)
            flash(f'Item "{name}" adicionado com sucesso!', 'success')
            return redirect(url_for('admin_shop'))
        else:
            flash('Por favor, preencha todos os campos corretamente.', 'danger')
    
    return render_template('admin/shop_item_form.html', title='Novo Item', item=None)

@app.route('/admin/shop/item/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_shop_item_edit(item_id):
    """Página para editar um item da lojinha."""
    item = get_shop_item(item_id)
    
    if not item:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('admin_shop'))
    
    # Extrair informações do tipo e valor real da descrição para o formulário
    if 'PIX' in item['description']:
        item['item_type'] = 'pix'
        try:
            # Tentar extrair o valor do PIX da descrição
            import re
            matches = re.search(r'R\$(\d+(?:\.\d+)?)', item['description'])
            if matches:
                item['real_value'] = matches.group(1)
        except:
            item['real_value'] = ''
    elif 'Banca' in item['description']:
        item['item_type'] = 'banca'
        try:
            # Tentar extrair o valor da Banca da descrição
            import re
            matches = re.search(r'R\$(\d+(?:\.\d+)?)', item['description'])
            if matches:
                item['real_value'] = matches.group(1)
        except:
            item['real_value'] = ''
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        points_cost = int(request.form.get('points_cost', 0))
        is_active = bool(request.form.get('is_active'))
        item_type = request.form.get('item_type')
        real_value = request.form.get('real_value')
        
        # Atualiza informações do tipo e valor real na descrição
        if item_type == 'pix':
            if not description:
                description = f"Transferência PIX no valor de R${real_value}."
            else:
                # Substituir qualquer menção anterior do valor
                if 'PIX' in description:
                    description = re.sub(r'PIX: R\$\d+(?:\.\d+)?\.', f"PIX: R${real_value}.", description)
                else:
                    description = f"PIX: R${real_value}. {description}"
        elif item_type == 'banca':
            if not description:
                description = f"Produto Banca no valor de R${real_value}."
            else:
                # Substituir qualquer menção anterior do valor
                if 'Banca' in description:
                    description = re.sub(r'Banca: R\$\d+(?:\.\d+)?\.', f"Banca: R${real_value}.", description)
                else:
                    description = f"Banca: R${real_value}. {description}"
        
        if name and points_cost > 0:
            update_shop_item(item_id, name, description, points_cost, is_active)
            flash(f'Item "{name}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin_shop'))
        else:
            flash('Por favor, preencha todos os campos corretamente.', 'danger')
    
    return render_template('admin/shop_item_form.html', title='Editar Item', item=item)

@app.route('/admin/shop/purchases', methods=['GET'])
@login_required
def admin_shop_purchases():
    """Página para gerenciar as compras da lojinha."""
    status = request.args.get('status')
    purchases = get_all_purchases(status)
    
    return render_template(
        'admin/shop_purchases.html', 
        title='Gerenciar Compras',
        purchases=purchases,
        current_status=status
    )

@app.route('/admin/shop/item/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_shop_item_delete(item_id):
    """Rota para excluir um item da lojinha."""
    item = get_shop_item(item_id)
    
    if not item:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('admin_shop'))
    
    result = delete_shop_item(item_id)
    if result:
        flash(f'Item "{item["name"]}" excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir o item.', 'danger')
    
    return redirect(url_for('admin_shop'))

@app.route('/admin/shop/purchase/update/<int:purchase_id>', methods=['POST'])
@login_required
def admin_update_purchase(purchase_id):
    """Rota para atualizar o status de uma compra."""
    status = request.form.get('status')
    if status in ['pending', 'processing', 'completed', 'cancelled']:
        update_purchase_status(purchase_id, status)
        flash('Status da compra atualizado com sucesso!', 'success')
    else:
        flash('Status inválido.', 'danger')
    
    return redirect(url_for('admin_shop_purchases'))

@app.route('/api/status')
def status():
    """Endpoint de status da API."""
    return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})

@app.route('/api/leaderboard')
def api_leaderboard():
    """API para obter o placar."""
    try:
        limit = min(int(request.args.get('limit', 10)), 100)
        top_users = get_leaderboard(limit)
        return jsonify({
            'status': 'success',
            'data': [dict(user) for user in top_users]
        })
    except Exception as e:
        logger.error(f"Erro na API de placar: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/invite-leaderboard')
def api_invite_leaderboard():
    """API para obter o placar de convites."""
    try:
        limit = min(int(request.args.get('limit', 10)), 100)
        top_inviters = get_invite_leaderboard(limit)
        return jsonify({
            'status': 'success',
            'data': [dict(user) for user in top_inviters]
        })
    except Exception as e:
        logger.error(f"Erro na API de placar de convites: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/shop/items')
def api_shop_items():
    """API para obter os itens da lojinha."""
    try:
        items = get_shop_items(active_only=True)
        return jsonify({
            'status': 'success',
            'data': [dict(item) for item in items]
        })
    except Exception as e:
        logger.error(f"Erro na API de itens da lojinha: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Página de erro 404."""
    return render_template('404.html', title='Página não encontrada'), 404

@app.errorhandler(500)
def server_error(e):
    """Página de erro 500."""
    logger.error(f"Erro 500: {e}")
    return render_template('500.html', title='Erro do servidor'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
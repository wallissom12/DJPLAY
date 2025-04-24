#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, jsonify

# Criar a aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "secret_key_for_development")

@app.route('/')
def index():
    """Página inicial da aplicação web."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Endpoint de status da API."""
    return jsonify({
        "status": "online",
        "message": "Bot de Telegram está funcionando!"
    })

# Inicialização da aplicação
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Arquivo: wsgi.py - Ponto de entrada para o Gunicorn da aplicação web

from app import app

# Este arquivo é usado pelo Gunicorn para executar a aplicação web
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
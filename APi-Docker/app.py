from __future__ import annotations

import logging
import os
import sys
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, Response, render_template, request, jsonify

class Config:
    APP_TITLE = os.getenv("TITULO_APP", "Demo Docker + Flask")
    HOST = "0.0.0.0"
    PORT = 5000
    LOG_DIR = Path("logs")
    TEMPLATE_DIR = Path("templates")
    LOG_FILE = LOG_DIR / "acessos.log"

app = Flask(__name__)
app.config.from_object(Config)

class AppLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        Config.LOG_DIR.mkdir(exist_ok=True)
        Config.TEMPLATE_DIR.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
    
    def log_access(self, endpoint: str, **kwargs):
        details = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"Acesso: {endpoint} - {details}")

logger = AppLogger()

def current_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def extract_name() -> str:
    return request.args.get("nome", "").strip() or "Visitante"

@app.route("/")
def index() -> str:
    user_name = extract_name()
    logger.log_access("pagina_inicial", nome=user_name)
    
    return render_template(
        "index.html",
        titulo=Config.APP_TITLE,
        nome=user_name,
        data_atual=current_datetime(),
        year=datetime.now().year
    )

@app.route("/saudacao")
def greeting() -> Response:
    user_name = extract_name()
    logger.log_access("api_saudacao", nome=user_name)
    
    return jsonify({
        "mensagem": f"Olá, {user_name}! Esta resposta veio de um container Docker.",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "app": Config.APP_TITLE
    })

@app.errorhandler(404)
def page_not_found(_: Any) -> tuple[dict[str, str], int]:
    return jsonify({
        "error": "Página não encontrada",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(_: Any) -> tuple[dict[str, str], int]:
    logger.logger.error("Erro interno do servidor")
    return jsonify({
        "error": "Erro interno do servidor",
        "timestamp": datetime.now().isoformat()
    }), 500

def _create_default_template():
    template_file = Config.TEMPLATE_DIR / "index.html"
    if template_file.exists():
        return
    
    template_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titulo }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 20px; }
        h2 { color: #667eea; margin: 15px 0; }
        .highlight { color: #764ba2; font-weight: bold; }
        .info {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            border-radius: 0 8px 8px 0;
        }
        .api-link {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .api-link:hover { background: #764ba2; }
        footer {
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {{ titulo }}</h1>
        <div class="info">
            <p><strong>👋 Olá, <span class="highlight">{{ nome }}</span>!</strong></p>
            <p>Este é um exemplo de aplicação Flask rodando em container Docker.</p>
        </div>
        <h2>📅 Data e Hora Atual</h2>
        <p class="highlight">{{ data_atual }}</p>
        <div class="info">
            <h3>🔗 Endpoints Disponíveis</h3>
            <ul style="list-style: none; margin-top: 10px;">
                <li>• <strong>/</strong> - Esta página (pode passar ?nome=SeuNome)</li>
                <li>• <strong>/saudacao</strong> - API de saudação (retorna JSON)</li>
            </ul>
        </div>
        <a href="/saudacao?nome={{ nome }}" class="api-link">Testar API de Saudação</a>
        <footer>
            <p>📝 Acessos são registrados em logs/acessos.log</p>
            <p>© {{ year }} - Aplicação Flask + Docker</p>
        </footer>
    </div>
</body>
</html>"""
    
    with open(template_file, "w", encoding="utf-8") as file:
        file.write(template_content)

def main():
    print("=" * 34)
    print(f"🚀 INICIANDO: {Config.APP_TITLE}")
    print(f"🌐 http://{Config.HOST}:{Config.PORT}")
    print("=" * 34)
    
    with suppress(Exception):
        _create_default_template()
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true"
    )

if __name__ == "__main__":
    main()
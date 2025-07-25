from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import json
import threading
import time
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

GITHUB_URL = "https://github.com/zanfranceschi/rinha-de-backend-2025/tree/main/participantes"
RAW_BASE_URL = "https://raw.githubusercontent.com/zanfranceschi/rinha-de-backend-2025/main/participantes"

ranking_cache = []
cache_lock = threading.Lock()

mapa_linguagens = {
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "ava": "Java",
    "Java 17": "Java",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "elixir": "Elixir",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "c sharp": "C#",
    "csharp": "C#",
    "php": "PHP",
    "python": "Python",
    "swift": "Swift",
    "lua": "Lua",
    "spring": "Spring",
    "springboot": "Spring",
    "nest": "NestJS",
    "dotnet": ".NET",
    ".net": ".NET",
    "bun": "Bun",
    "bun/typescript": "Bun",
    "luvit": "Luvit",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue.js",
    "hibernate": "Hibernate",
    "django": "Django",
    "flask": "Flask",
    "express": "Express.js",
    "nginx": "Nginx",
    "redis": "Redis"
}


def buscar_participantes():
    response = requests.get(GITHUB_URL)
    participantes = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        datatarget = soup.select('script[data-target="react-app.embeddedData"]')
        if datatarget:
            items = json.loads(datatarget[0].text)["payload"]["tree"]["items"]
            for item in items:
                try:
                    name = item["name"]
                    url_results = f"{RAW_BASE_URL}/{name}/partial-results.json"
                    url_info = f"{RAW_BASE_URL}/{name}/info.json"
                    response_results = requests.get(url_results)
                    response_info = requests.get(url_info)
                    if (response_results.status_code == 200 and len(response_results.content) > 0) and (
                            response_info.status_code == 200 and len(response_info.content) > 0):
                        data_results = json.loads(re.sub(r',(\s*[}\]])', r'\1', response_results.content.decode()))
                        data_info = json.loads(re.sub(r',(\s*[}\]])', r'\1', response_info.content.decode()))
                        data_info["data"] = data_results
                        data_info["langs"] = list(set([(mapa_linguagens.get(lang) or lang) for lang in data_info["langs"]]))
                        participantes.append(data_info)
                except Exception as e:
                    print(f"Erro pegar dados : {e}")
    return participantes


def atualizar_cache():
    global ranking_cache
    try:
        print("Atualizando cache do ranking...")
        participantes = buscar_participantes()
        ranking = sorted(participantes, key=lambda p: p["data"]['total_liquido'], reverse=True)
        with cache_lock:
            ranking_cache = ranking
        print(f"Cache atualizado com {len(ranking_cache)} participantes.")
    except Exception as e:
        print(f"Erro ao atualizar cache: {e}")
    finally:
        print(" Agenda a próxima atualização em 300s (5 minutos)")


@app.route("/")
def home():
    return "API da Rinha está rodando! Use /ranking para ver os dados."


@app.route('/ranking')
def ranking():
    if not ranking_cache:
        return jsonify({"mensagem": "Ranking ainda não carregado"}), 503
    return jsonify(ranking_cache)


def agendador():
    while True:
        atualizar_cache()
        time.sleep(300)  # 5 minutos


threading.Thread(target=agendador, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

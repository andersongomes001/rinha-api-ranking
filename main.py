from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import json
import threading
import time
from flask_cors import CORS
import re
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

GITHUB_URL = "https://github.com/zanfranceschi/rinha-de-backend-2025/tree/main/participantes"
RAW_BASE_URL = "https://raw.githubusercontent.com/zanfranceschi/rinha-de-backend-2025/main/participantes"

ranking_cache = []
ranking_cache_final = []
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
    "redis": "Redis",
    "NestJS":"NestJS"
}

mapa_linguagens = {
    k.upper(): v for k, v in mapa_linguagens.items()
}

print(mapa_linguagens)

def social_priority(url):
    if "linkedin" in url:
        return 0
    elif "github" in url or "/git" in url:
        return 1
    else:
        return 2

def validate_bonus(bonus : str) -> float:
    try:
        bonus = bonus.replace("%","")
        return float(bonus)
    except ValueError:
        return 0.0

def buscar_participantes(final: bool = False):
    response = requests.get(GITHUB_URL)
    participantes = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        datatarget = soup.select('script[data-target="react-app.embeddedData"]')
        if datatarget:
            items = json.loads(datatarget[0].text)["payload"]["tree"]["items"]
            #print(len(items))    
            for index,item in enumerate(items):
                try:
                    name = item["name"]
                    encoded_user_dir = quote(name)
                    url_results = f"{RAW_BASE_URL}/{encoded_user_dir}/partial-results.json"
                    if final:
                        url_results = f"{RAW_BASE_URL}/{encoded_user_dir}/final-results.json"
                    url_info = f"{RAW_BASE_URL}/{encoded_user_dir}/info.json"
                    response_results = requests.get(url_results)
                    response_info = requests.get(url_info)
                    #print("INDEX => ",index, response_results.status_code, response_info.status_code)
                    if (response_results.status_code == 200 and len(response_results.content) > 0) and (
                            response_info.status_code == 200 and len(response_info.content) > 0):
                        

                        text_results = response_results.content.decode("utf-8-sig", errors="replace").strip()
                        text_info    = response_info.content.decode("utf-8-sig", errors="replace").strip()
                        if not text_results.endswith('}'):
                            text_results += '}'
                        if not text_info.endswith('}'):
                            text_info += '}'

                        data_results = json.loads(re.sub(r',(\s*[}\]])', r'\1', text_results))
                        data_info = json.loads(re.sub(r',(\s*[}\]])', r'\1', text_info))
            
                        data_info["data"] = data_results
                        if "langs" not in data_info:
                            data_info["langs"] = []
                        data_info["langs"] = list(set([(mapa_linguagens.get(str(lang).upper()) or lang) for lang in data_info["langs"]]))

                        if isinstance(data_info["name"], list):
                            data_info["name"] = " / ".join(data_info["name"])
                        if "social" in data_info and isinstance(data_info["social"], list):
                            data_info["social"].sort(key=social_priority)

                        if "p99" in data_info["data"]:
                            data_info["data"]["p99"]["bonus"] = validate_bonus(data_info["data"]["p99"]["bonus"])
                        #print(data_info)
                        participantes.append(data_info)
                except Exception as e:
                    print(item)
                    print(f"Erro pegar dados : {e}")
    return participantes


def atualizar_cache(ranking_final: bool = False ):
    global ranking_cache
    try:
        print("Atualizando cache do ranking...")
        participantes = buscar_participantes(final=ranking_final)
        
        ranking = sorted(participantes, key=lambda p: (
            p["data"]['total_liquido'], 
            -float(str(p["data"]["p99"]["valor"].replace("ms", "")).strip())
        ),reverse=True)

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
        atualizar_cache(True)
        time.sleep(300)  # 5 minutos

threading.Thread(target=agendador, daemon=True).start()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

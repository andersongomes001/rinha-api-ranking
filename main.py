from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import json
import threading
import time

app = Flask(__name__)

GITHUB_URL = "https://github.com/zanfranceschi/rinha-de-backend-2025/tree/main/participantes"
RAW_BASE_URL = "https://raw.githubusercontent.com/zanfranceschi/rinha-de-backend-2025/main/participantes"

ranking_cache = []
cache_lock = threading.Lock()

def buscar_participantes():
    response = requests.get(GITHUB_URL)
    participantes = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        datatarget = soup.select('script[data-target="react-app.embeddedData"]')
        if datatarget:
            items = json.loads(datatarget[0].text)["payload"]["tree"]["items"]
            for item in items:
                name = item["name"]
                data_url = f"{RAW_BASE_URL}/{name}/partial-results.json"
                data = requests.get(data_url)
                if data.status_code == 200 and len(data.content) > 0:
                    participantes.append(json.loads(data.content))
    return participantes

def atualizar_cache():
    global ranking_cache
    try:
        print("Atualizando cache do ranking...")
        participantes = buscar_participantes()
        ranking = sorted(participantes, key=lambda p: p['total_liquido'], reverse=True)
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
    atualizar_cache()
    app.run(host='0.0.0.0', port=5000)
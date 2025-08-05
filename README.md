![Nome do workflow](https://github.com/andersongomes001/rinha-api-ranking/actions/workflows/deploy.yml/badge.svg)
# 🥊 API da Rinha de Backend 2025

Uma API construída com Python + Flask para coletar, normalizar e exibir os dados dos participantes da [Rinha de Backend 2025](https://github.com/zanfranceschi/rinha-de-backend-2025).

---

## 🔧 Tecnologias Utilizadas

- Python 3
- Flask
- Flask-CORS
- Requests
- BeautifulSoup (bs4)
- Threading

---

## 🚀 Endpoints

### `GET /`
- Retorna uma mensagem simples indicando que a API está online.

### `GET /ranking`
- Retorna um JSON com os participantes ordenados por `total_liquido` (ranking de performance).

---

## 🔁 Atualização Automática

Os dados são atualizados automaticamente a cada 5 minutos utilizando uma thread em background que:
1. Faz scraping do repositório oficial da Rinha.
2. Busca e valida os arquivos `info.json` e `partial-results.json`.
3. Normaliza os dados de linguagens e redes sociais.
4. Recalcula o ranking com base no total líquido.

---

### 🟢 Manutenção da Disponibilidade via Health Check Externo

Para garantir que a API permaneça sempre disponível no [Render: Cloud Application Platform](https://render.com/), utilizo um serviço externo de health check que realiza requisições periódicas ao endpoint raiz (`/`).

Esse “request” a cada 5 minutos evita que a API entre em modo de hibernação por inatividade, mantendo o serviço sempre ativo e acessível para os usuários.

Recomendo o uso de serviços como [UptimeRobot](https://uptimerobot.com) ou similares, que também oferecem monitoramento contínuo e alertas em caso de falhas.

[UptimeRobot status](https://stats.uptimerobot.com/dfA9KebgKL)

---

## 📦 Instalação

```bash
docker build -t api-rinha .
docker run -p 5000:5000 api-rinha
```
ou

```bash
docker-compose up --build
```

## Imagem Docker disponível em:

```bash
docker pull andersongomes001/rinha-api-ranking:latest
```

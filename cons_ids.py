import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

url = f"{JIRA_URL}/rest/api/3/field"

headers = {
    "Accept": "application/json"
}

response = requests.get(
    url,
    headers=headers,
    auth=HTTPBasicAuth(EMAIL, API_TOKEN)
)

campos = response.json()

print("\nLISTA DE CAMPOS DO JIRA\n")

for campo in campos:
    nome = campo.get("name")
    campo_id = campo.get("id")

    print(f"{nome}  --->  {campo_id}")

print("\nBusca filtrada por ''\n")

for campo in campos:
    nome = campo.get("name", "").upper()

    if "" in nome:
        print(f"{campo['name']}  --->  {campo['id']}")
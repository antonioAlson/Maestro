import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
CAMPO_PREVISAO = "customfield_10245"

jql = 'project = MANTA AND "fábrica de manta[dropdown]" = COMTEC and status IN ("A Produzir", "Liberado Engenharia","Em Produção")'

url = f"{JIRA_URL}/rest/api/3/search/jql"

headers = {
    "Accept": "application/json"
}

def proximo_dia_util():
    data = datetime.now() + timedelta(days=1)

    while data.weekday() >= 5:
        data += timedelta(days=1)

    return data.strftime("%Y-%m-%d")

next_page = None
all_rows = []
all_links = []  # Para guardar os links

while True:

    params = {
        "jql": jql,
        "maxResults": 100, 
        "fields": [
            "issuetype",
            "summary",
            "status",
            "customfield_10039",   # SITUAÇÃO
            "customfield_11298",   # VEICULO
            "customfield_10245"    # DT PREVISÃO ENTREGA
        ]
    }

    if next_page:
        params["nextPageToken"] = next_page

    response = requests.get(
        url,
        headers=headers,
        params=params,
        auth=HTTPBasicAuth(EMAIL, API_TOKEN)
    )

    data = response.json()
    issues = data.get("issues", [])

    for issue in issues:

        fields = issue.get("fields", {})

        # Tipo
        tipo = fields.get("issuetype", {}).get("name", "")

        # Chave e link
        key = issue.get("key", "")
        link = f"{JIRA_URL}/browse/{key}"

        # Campos padrão
        resumo = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")

        # SITUAÇÃO (dropdown Jira)
        situacao_raw = fields.get("customfield_10039")
        print(f"DEBUG - Issue {key} - situacao_raw: {situacao_raw}, type: {type(situacao_raw)}")
        if isinstance(situacao_raw, dict):
            situacao = situacao_raw.get("value", "")
        else:
            situacao = situacao_raw or ""
        print(f"DEBUG - Issue {key} - situacao final: {situacao}")

        # Filtrar apenas situações desejadas
        situacoes_validas = ["⚪️RECEBIDO ENCAMINHADO", "🟢RECEBIDO LIBERADO"]
        if situacao not in situacoes_validas:
            continue

        # VEICULO (dropdown ou texto)
        veiculo_raw = fields.get("customfield_11298")
        if isinstance(veiculo_raw, dict):
            veiculo = veiculo_raw.get("value", "")
        else:
            veiculo = veiculo_raw or ""

        # DATA PREVISÃO
        previsao_raw = fields.get("customfield_10245", "")
        if previsao_raw:
            try:
                previsao = datetime.strptime(previsao_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                previsao = previsao_raw
        else:
            previsao = ""

        all_rows.append({
            "ID": key,
            "Tipo de issue": tipo,
            "Chave": link,
            "Resumo": resumo,
            "Status": status,
            "SITUAÇÃO": situacao,
            "Veículo": veiculo,
            "DT. PREVISÃO ENTREGA": previsao
        })
        all_links.append(link)

    print("Cartões coletados:", len(all_rows))

    if data.get("isLast"):
        break

    next_page = data.get("nextPageToken")

print("Total de cartões:", len(all_rows))

# Criar dataframe
df = pd.DataFrame(all_rows)


for index, row in df.iterrows():
   # print(index, row)
    data_entrega = row["DT. PREVISÃO ENTREGA"]
    data_formatada = proximo_dia_util()

    url = f"{JIRA_URL}/rest/api/3/issue/{row["ID"]}"

    print(url)
    payload = {
        "fields": {
            CAMPO_PREVISAO: data_formatada
        }
    }

    response = requests.put(
        url,
        headers=headers,
        auth=auth,
        json=payload
    )

    if response.status_code == 204:
        print(f"{row["ID"]} atualizado para {data_formatada}")
    else:
        print(f"Erro ao atualizar {row["ID"]}:", response.text)
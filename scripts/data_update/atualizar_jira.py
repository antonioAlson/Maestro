import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# CONFIGURAÇÕES
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

ARQUIVO = r".\\archives\\update_cards.xlsx"

CAMPO_PREVISAO = "customfield_10245"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# LER EXCEL
df = pd.read_excel(ARQUIVO)

# remover espaços nos nomes das colunas
df.columns = df.columns.str.strip()

print("Linhas encontradas:", len(df))

for index, row in df.iterrows():

    issue_id = row["ID"]
    data_entrega = row["DT. PREVISÃO ENTREGA"]

    if pd.isna(issue_id) or pd.isna(data_entrega):
        continue

    # Converter para formato YYYY-MM-DD (formato esperado pela API Jira)
    try:
        data_formatada = None

        # Se for datetime do pandas
        if isinstance(data_entrega, pd.Timestamp):
            data_formatada = data_entrega.strftime("%Y-%m-%d")
        # Se for string, tentar diferentes formatos
        elif isinstance(data_entrega, str):
            data_str = data_entrega.strip()

            # Tentar formato dd/mm/YYYY
            if "/" in data_str:
                try:
                    data_obj = datetime.strptime(data_str, "%d/%m/%Y")
                    data_formatada = data_obj.strftime("%Y-%m-%d")
                except:
                    pass

            # Tentar formato YYYY-MM-DD
            if not data_formatada and "-" in data_str:
                try:
                    data_obj = datetime.strptime(data_str, "%Y-%m-%d")
                    data_formatada = data_obj.strftime("%Y-%m-%d")
                except:
                    pass

            # Tentar formato dd-mm-YYYY
            if not data_formatada and "-" in data_str:
                try:
                    data_obj = datetime.strptime(data_str, "%d-%m-%Y")
                    data_formatada = data_obj.strftime("%Y-%m-%d")
                except:
                    pass

        if not data_formatada:
            print(f"Formato de data não reconhecido para {issue_id}: {data_entrega} (tipo: {type(data_entrega)})")
            continue

    except Exception as e:
        print(f"Erro ao converter data para {issue_id}: {e}, valor: {data_entrega}")
        continue

    url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"

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
        print(f"{issue_id} atualizado para {data_formatada}")
    else:
        print(f"Erro ao atualizar {issue_id}:", response.text)
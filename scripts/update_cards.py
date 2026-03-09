import pandas as pd
from datetime import datetime, timedelta

# Caminho da planilha
arquivo = r".\\archives\\update_cards.xlsx"

# Ler planilha
df = pd.read_excel(arquivo)

# Converter coluna para string
df["DT. PREVISÃO ENTREGA"] = df["DT. PREVISÃO ENTREGA"].astype(str)

# Garantir que não há valores nulos
df["Tipo de issue"] = df["Tipo de issue"].fillna("")

# Data atual + 1 dia
nova_data = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

# Atualizar apenas quando Tipo de issue for Manta
df.loc[df["Tipo de issue"].str.lower() == "manta", "DT. PREVISÃO ENTREGA"] = nova_data

# Salvar novamente
df.to_excel(arquivo, index=False)

print("Datas atualizadas com sucesso!")
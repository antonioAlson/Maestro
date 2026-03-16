import argparse
import io
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth


# Configurar saida UTF-8 no Windows (apenas se ainda não foi configurado)
if sys.platform == "win32":
	try:
		if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != "utf-8":
			sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
		if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != "utf-8":
			sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
	except Exception:
		pass  # Já configurado ou não é necessário


def parse_args():
	parser = argparse.ArgumentParser(
		description="Atualiza data de previsao de entrega no Jira para IDs informados."
	)
	parser.add_argument(
		"--ids",
		required=True,
		help="Lista de IDs separados por virgula, ponto e virgula, espaco ou quebra de linha"
	)
	parser.add_argument(
		"--date",
		required=True,
		help="Data alvo no formato YYYY-MM-DD (tambem aceita DD/MM/YYYY e DD-MM-YYYY)"
	)
	return parser.parse_args()


def parse_id_list(raw_values):
	if not raw_values:
		return []
	return [value.strip() for value in re.split(r"[,;\s]+", raw_values) if value.strip()]


def normalize_date(raw_date):
	raw_date = (raw_date or "").strip()
	accepted_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

	for fmt in accepted_formats:
		try:
			parsed = datetime.strptime(raw_date, fmt)
			return parsed.strftime("%Y-%m-%d")
		except ValueError:
			continue

	raise ValueError("Data invalida. Use YYYY-MM-DD, DD/MM/YYYY ou DD-MM-YYYY.")


def main():
	load_dotenv()

	jira_url = os.getenv("JIRA_URL")
	email = os.getenv("EMAIL")
	api_token = os.getenv("API_TOKEN")
	campo_previsao = "customfield_10245"

	if not jira_url or not email or not api_token:
		print("❌ Variaveis de ambiente ausentes: JIRA_URL, EMAIL e API_TOKEN sao obrigatorias.")
		raise SystemExit(1)

	args = parse_args()
	card_ids = parse_id_list(args.ids)

	if not card_ids:
		print("⚠️ Nenhum ID informado para atualizacao.")
		raise SystemExit(1)

	try:
		target_date = normalize_date(args.date)
	except ValueError as exc:
		print(f"❌ {exc}")
		raise SystemExit(1)

	print("=" * 60)
	print("REPROGRAMAR CONTEC - INICIADO")
	print("=" * 60)
	print(f"📅 Nova previsao: {target_date}")
	print(f"📋 IDs para atualizar: {len(card_ids)}")
	for issue_id in card_ids:
		print(f"   • {issue_id}")
	print("=" * 60)
	sys.stdout.flush()

	headers = {
		"Accept": "application/json",
		"Content-Type": "application/json",
	}
	auth = HTTPBasicAuth(email, api_token)

	success_count = 0
	error_count = 0

	for issue_id in card_ids:
		url = f"{jira_url}/rest/api/3/issue/{issue_id}"
		payload = {
			"fields": {
				campo_previsao: target_date,
			}
		}

		try:
			response = requests.put(url, headers=headers, auth=auth, json=payload, timeout=30)
			if response.status_code == 204:
				success_count += 1
				print(f"✅ {issue_id} atualizado para {target_date}")
			else:
				error_count += 1
				print(f"❌ {issue_id} falhou ({response.status_code}): {response.text}")
		except Exception as exc:
			error_count += 1
			print(f"❌ {issue_id} erro de requisicao: {exc}")

	print("=" * 60)
	print("REPROGRAMAR CONTEC - FINALIZADO")
	print("=" * 60)
	print(f"✅ Sucesso: {success_count}")
	print(f"❌ Erros: {error_count}")
	print("=" * 60)

	if error_count > 0:
		raise SystemExit(1)


if __name__ == "__main__":
	main()
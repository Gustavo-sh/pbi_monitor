import requests
import os
import time
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from telegram_config import notify_telegram
from whatsapp_config import notify_whatsapp

load_dotenv()
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GROUP_ID = os.getenv("GROUP_ID")
SKIP_RELS = ["Laboratório Robbyson", "Laboratório Robbyson 2", "ModelHistoricoProcedures", "Testes", "Aderencia Turnover", "CDP X Matriz", "Dash_Conselho", "Acelerando Líderes", "Dash_Impulso_V1", 
             "Mapa de Calor Instrutor", "Impulso", "Campanhas EO"]
CONTROL = defaultdict(int)

try:
    now = datetime.now()
    #retry = True
    while now < datetime(now.year, now.month, now.day, 10, 0, 0):
        #retry = False
        url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }

        response = requests.post(url, data=payload)

        token = response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets"

        response = requests.get(url, headers=headers)

        datasets = response.json()["value"]

        for dataset in datasets:

            dataset_id = dataset["id"]
            dataset_name = dataset["name"]

            if CONTROL.get(dataset_name, 0) >= 3:
                if CONTROL.get(dataset_name, 0) == 3:
                    notify_whatsapp(f"3 tentativas de atualização do relatorio {dataset_name} sem sucesso. Gentileza validar o erro no pbi online.")
                    CONTROL[dataset_name] += 1
                continue

            url = (
                f"https://api.powerbi.com/v1.0/myorg/"
                f"groups/{GROUP_ID}/"
                f"datasets/{dataset_id}/refreshes?$top=1"
            )

            response = requests.get(url, headers=headers)

            refreshes = response.json().get("value", [])

            if not refreshes or dataset_name in SKIP_RELS:
                continue

            ultimo_refresh = refreshes[0]
            status_refresh = ultimo_refresh.get("status").lower()

            if status_refresh == "failed" or status_refresh == "cancelled":

                retry = True

                print(f"Tentando novo refresh em {dataset_name}...")

                response_refresh = requests.post(
                    f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{dataset_id}/refreshes",
                    headers=headers
                )

                print(f"Resposta do refresh {response_refresh.status_code}...")

                if response_refresh.status_code in [200, 202]:
                    CONTROL[dataset_name] += 1
                    notify_whatsapp(f"Refresh iniciado em {dataset_name}, esperando 5 minutos antes de continuar...")
                    time.sleep(300)
                else:
                    notify_whatsapp(f"Refresh falhou em {dataset_name}\nText: {response_refresh.text}")
        time.sleep(300)
        now = datetime.now()
            
except Exception as e:
    print(e)
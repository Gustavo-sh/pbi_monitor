import os
import time
import json
import requests
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
from connections_db import insert_logger, truncate_logger, close_connection, CONN

load_dotenv()
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GROUP_ID = os.getenv("GROUP_ID")
SKIP_RELS = ["Laboratório Robbyson", "Laboratório Robbyson 2", "ModelHistoricoProcedures", "Testes", "Aderencia Turnover", 
             "CDP X Matriz", "Dash_Conselho", "Acelerando Líderes", "Dash_Impulso_V1", "Mapa de Calor Instrutor"]

def convert_timezone(data_str):
    if not data_str:
        return None
    dt_utc = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
    return dt_local

def main():
    try:
        CONN.autocommit = True
        now = datetime.now()
        while now < datetime(now.year, now.month, now.day, 12, 0, 0):
            truncate_logger()
            print("Dados deletados da dbo.pbi_monitor...")

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
                status_refresh = ultimo_refresh.get("status")
                erros = ultimo_refresh.get("serviceExceptionJson")
                start_time = convert_timezone(ultimo_refresh.get("startTime"))
                end_time = convert_timezone(ultimo_refresh.get("endTime"))

                if erros:
                    try:
                        erro = json.loads(erros).get("errorCode")
                    except Exception:
                        erro = erros
                else:
                    erro = None

                insert_logger(dataset_name, start_time, end_time, status_refresh, erro)
                print(f"Relatorio {dataset_name} inserido no banco com status {status_refresh}...")

            CONN.commit()
            time.sleep(600)
            now = datetime.now()
                
    except Exception as e:
        print(e)
    finally:
        print("Fechando conexão com o banco de dados...")
        close_connection()

if __name__ == "__main__":
    main()
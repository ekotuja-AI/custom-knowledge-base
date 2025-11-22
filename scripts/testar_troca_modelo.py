import requests
import sys

API_URL = "http://localhost:9000/trocar_modelo"

if len(sys.argv) < 2:
    print("Uso: python testar_troca_modelo.py <nome_do_modelo>")
    sys.exit(1)

model_name = sys.argv[1]

payload = {"model_name": model_name}
headers = {"Content-Type": "application/json"}

print(f"Testando troca de modelo para: {model_name}")
resp = requests.post(API_URL, json=payload, headers=headers)

try:
    data = resp.json()
except Exception:
    print("Resposta não é JSON:", resp.text)
    sys.exit(2)

if data.get("sucesso"):
    print(f"✅ Modelo carregado: {data.get('modelo_carregado')}")
else:
    print(f"❌ Erro ao trocar modelo: {data.get('erro')}")

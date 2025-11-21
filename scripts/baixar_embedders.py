import os
import json
from sentence_transformers import SentenceTransformer

# Caminho do JSON de modelos
MODELOS_JSON = "static/docs/modelos_disponiveis.json"

# Pasta de cache padrão do SentenceTransformers
CACHE_DIR = os.path.expanduser("~/.cache/torch/sentence_transformers")

def baixar_modelos_embedders():
    with open(MODELOS_JSON, encoding="utf-8") as f:
        modelos = json.load(f)
    embeddings = modelos.get("embeddings", [])
    print("Baixando modelos de embedding...")
    for m in embeddings:
        nome = m["id"]
        print(f"Baixando: {nome}")
        try:
            SentenceTransformer(nome)
        except Exception as e:
            print(f"Erro ao baixar {nome}: {e}")
    print("Modelos baixados!")
    print("Modelos presentes em:", CACHE_DIR)
    print(os.listdir(CACHE_DIR))

if __name__ == "__main__":
    baixar_modelos_embedders()

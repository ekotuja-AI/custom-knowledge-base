"""
Script utilitário para listar modelos de embedding disponíveis e mostrar o modelo ativo do LangChainWikipediaService

Uso:
  python scripts/ver_modelos_embedding.py
"""
import os
from services.langchainWikipediaService import langchain_wikipedia_service

# Caminho do cache do HuggingFace
HF_CACHE = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
MODELS_DIR = os.path.join(HF_CACHE, "hub")

def listar_modelos_cache():
    print("Modelos de embedding no cache HuggingFace:")
    if not os.path.exists(MODELS_DIR):
        print(f"  (Nenhum modelo encontrado em {MODELS_DIR})")
        return
    for nome in os.listdir(MODELS_DIR):
        print(f"  - {nome}")

def modelo_ativo():
    model = getattr(langchain_wikipedia_service.embedding_model, 'model_name', None)
    if model:
        print(f"Modelo de embedding ativo: {model}")
    else:
        print("Nenhum modelo de embedding está ativo.")

def main():
    print("==== Modelos de Embedding LangChain ====")
    listar_modelos_cache()
    print("\n==== Modelo Ativo ====")
    modelo_ativo()

if __name__ == "__main__":
    main()

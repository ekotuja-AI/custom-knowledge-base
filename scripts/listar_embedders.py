import os

CACHE_DIR = os.path.expanduser("~/.cache/torch/sentence_transformers")

def listar_modelos_instalados():
    print("Modelos de embedding instalados:")
    if os.path.exists(CACHE_DIR):
        for nome in os.listdir(CACHE_DIR):
            print("-", nome)
    else:
        print("Nenhum modelo encontrado em:", CACHE_DIR)

if __name__ == "__main__":
    listar_modelos_instalados()

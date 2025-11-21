from typing import Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuração do Qdrant (ajuste conforme necessário)
QDRANT_HOST = "qdrant"
QDRANT_PORT = 6333

# Inicializa o cliente Qdrant
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def listar_colecoes() -> Dict[str, Any]:
    """Retorna lista de coleções existentes no Qdrant, destacando wikipedia_langchain se presente"""
    colecoes = []
    langchain_encontrada = False
    result = qdrant_client.get_collections()
    if hasattr(result, "collections"):
        colecoes = [c.name for c in result.collections]
        langchain_encontrada = "wikipedia_langchain" in colecoes
    return {
        "colecoes": colecoes,
        "wikipedia_langchain": langchain_encontrada
    }

def criar_colecao(nome: str, modelo_dim: int = 1024, distancia: str = "COSINE") -> Dict[str, Any]:
    """Cria uma coleção no Qdrant com nome, dimensão e distância"""
    try:
        # Verifica se já existe
        result = qdrant_client.get_collections()
        collection_names = [col.name for col in result.collections]
        if nome in collection_names:
            return {"sucesso": False, "erro": "Coleção já existe."}
        # Cria coleção
        qdrant_client.create_collection(
            collection_name=nome,
            vectors_config=models.VectorParams(
                size=modelo_dim,
                distance=getattr(models.Distance, distancia)
            )
        )
        return {"sucesso": True, "nome": nome, "dimensao": modelo_dim, "distancia": distancia}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def remover_colecao(nome: str) -> Dict[str, Any]:
    """Remove uma coleção do Qdrant"""
    try:
        qdrant_client.delete_collection(collection_name=nome)
        return {"sucesso": True, "colecao_removida": nome}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def obter_dimensao_colecao(nome: str) -> Optional[int]:
    """Obtém a dimensão dos vetores de uma coleção"""
    try:
        info = qdrant_client.get_collection(collection_name=nome)
        if hasattr(info, "config") and hasattr(info.config, "params"):
            return getattr(info.config.params, "size", None)
        return None
    except Exception:
        return None

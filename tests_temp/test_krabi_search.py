from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Inicializar
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
client = QdrantClient(host='qdrant', port=6333)

# Buscar
query = "o que é krabi?"
query_vector = model.encode(query).tolist()

results = client.search(
    collection_name='wikipedia_langchain',
    query_vector=query_vector,
    limit=3
    # SEM score_threshold
)

print(f"Busca por: '{query}'")
print(f"Resultados encontrados: {len(results)}\n")

for i, hit in enumerate(results, 1):
    print(f"{i}. {hit.payload['title']} - Score: {hit.score:.4f}")

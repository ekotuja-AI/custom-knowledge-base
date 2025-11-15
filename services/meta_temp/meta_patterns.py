# meta_patterns.py
# Lista de padrões regex para perguntas meta
META_PATTERNS = [
    r"\b(lista(r|s)?|quais|me mostre|me liste|listar|liste|mostre|exiba|exibir)\b.*\b(artigos|documentos|registros|chunks)\b",
    r"\b(quantos|quantidade|número|total|contagem|contar|existem|disponíveis)\b.*\b(artigos|documentos|registros|chunks)\b",
    r"\b(estatísticas?|stats?|informações?|detalhes?)\b.*\b(coleção|base|qdrant|artigos|documentos|registros|chunks)\b",
    r"\b(base de dados|coleção|qdrant)\b.*(informações?|detalhes?|status|estatísticas?)",
    r"\b(quem é você|quem é o sistema|qual seu nome|qual modelo|qual llm|qual linguagem|qual backend|qual arquitetura|usa ollama|usa langchain|usa qdrant|usa wikipedia|como funciona|sobre você|sobre o sistema|sobre a arquitetura|sobre o backend|sobre o modelo|sobre a base|sobre a tecnologia|sobre a implementação)\b"
]

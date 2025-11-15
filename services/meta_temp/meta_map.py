# meta_map.py
# Mapeamento de padrões regex para chaves de resposta meta
META_MAP = [
    (r"quem é você|quem é o sistema|qual seu nome", "identidade"),
    (r"qual modelo|qual llm|qual linguagem|qual backend|qual arquitetura|sobre o modelo|sobre a arquitetura|sobre o backend|sobre a tecnologia|sobre a implementação", "modelo_arquitetura"),
    (r"usa ollama", "ollama"),
    (r"usa langchain", "langchain"),
    (r"usa qdrant", "qdrant"),
    (r"usa wikipedia", "wikipedia"),
    (r"como funciona|sobre você|sobre o sistema|sobre a base", "funcionamento")
]

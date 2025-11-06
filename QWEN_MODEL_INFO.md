# Qwen 2.5 (7B) - Informações do Modelo

## Sobre o Modelo

**Qwen 2.5** é um modelo de linguagem desenvolvido pela Alibaba Cloud, otimizado para:
- ✅ **Tool Calling** (Function Calling)
- ✅ **RAG (Retrieval-Augmented Generation)**
- ✅ **Multilíngue** (Chinês, Inglês, Português e mais)
- ✅ **Raciocínio lógico**
- ✅ **Geração de código**

## Especificações Técnicas

- **Tamanho**: ~4.7 GB
- **Parâmetros**: 7 bilhões
- **Quantização**: Q4_0 (4-bit)
- **Contexto**: 128K tokens
- **Família**: Qwen

## Capacidades

### ✅ Tool Calling
O modelo suporta **function calling** nativo, permitindo:
- Chamar funções externas durante a geração
- Integrar com APIs e ferramentas
- Executar ações baseadas em contexto
- Retornar resultados estruturados (JSON)

### ✅ RAG Otimizado
Excelente para sistemas de busca vetorial:
- Compreensão profunda de contexto
- Síntese de múltiplos documentos
- Respostas precisas baseadas em evidências
- Citação de fontes

### ✅ Multilíngue
Suporta mais de 29 idiomas, incluindo:
- Português (PT-BR e PT-PT)
- Inglês
- Espanhol
- Chinês (nativo)

## Uso no Projeto

O modelo está configurado em:
- **`.env`**: `LLM_MODEL=qwen2.5:7b`
- **`wikipediaOfflineService.py`**: Modelo padrão

### Exemplo de Uso

```python
# O serviço usa automaticamente o qwen2.5:7b
resultado = wikipedia_offline_service.perguntar(
    "Qual a capital do Brasil?",
    limite=5
)
```

### Tool Calling Example

```python
# Definir ferramentas disponíveis
tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_wikipedia",
            "description": "Busca informações na Wikipedia offline",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Usar com Ollama
response = ollama.chat(
    model='qwen2.5:7b',
    messages=[{'role': 'user', 'content': 'Busque informações sobre Python'}],
    tools=tools
)
```

## Comparação com phi3:mini

| Característica | phi3:mini | qwen2.5:7b |
|----------------|-----------|------------|
| Tamanho | 2.2 GB | 4.7 GB |
| Parâmetros | 3.8B | 7B |
| Tool Calling | ❌ Não | ✅ Sim |
| Contexto | 128K | 128K |
| Multilíngue | Limitado | Excelente |
| RAG | Bom | Excelente |
| Velocidade | Mais rápido | Moderado |

## Performance Esperada

### Vantagens
- Respostas mais precisas em português
- Melhor compreensão de contexto
- Suporte nativo a ferramentas
- Síntese de documentos superior

### Considerações
- Requer mais RAM (~6-8 GB)
- Inferência ligeiramente mais lenta
- Melhor com GPU (mas funciona em CPU)

## Próximos Passos

1. ✅ Modelo baixado e configurado
2. ⏳ Reiniciar containers Docker
3. ⏳ Testar interface web
4. ⏳ Implementar tool calling no RAG
5. ⏳ Adicionar mais artigos da Wikipedia

## Referências

- [Qwen Documentation](https://qwen.readthedocs.io/)
- [Ollama Qwen Models](https://ollama.ai/library/qwen2.5)
- [Tool Calling Guide](https://github.com/QwenLM/Qwen/blob/main/examples/function_calling.md)

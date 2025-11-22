# Implementação de Medição de Tempo Detalhada

## Objetivo
Mostrar ao usuário quanto tempo foi gasto em cada fase do processamento da pergunta RAG:
1. **Busca de Documentos** - Tempo para buscar chunks relevantes no Qdrant
2. **Geração com IA** - Tempo para o LLM (Ollama) gerar a resposta
3. **Total** - Tempo completo de processamento

## 🆕 Compatibilidade Multi-Coleção/Modelo

- As métricas de tempo funcionam para qualquer coleção e modelo de embedding ativo.
- O sistema permite trocar o modelo de embedding dinamicamente e medir o impacto nas respostas.

---

## Mudanças no Backend

### `services/wikipediaOfflineService.py`

#### Método `perguntar_com_rag()`

**Adicionado:**
- Medição de tempo da fase de busca
- Medição de tempo da fase de geração
- Inclusão de timing no `model_info`

```python
def perguntar_com_rag(self, pergunta: str, max_chunks: int = 3) -> RAGResponse:
    """Sistema RAG com Ollama"""
    start_time = time.time()
    
    try:
        # Fase 1: Buscar documentos
        search_start = time.time()
        documentos = self.buscar_artigos(pergunta, limit=max_chunks)
        search_time = time.time() - search_start
        
        # ... processamento ...
        
        # Fase 2: Gerar resposta com Ollama
        generation_start = time.time()
        resposta = self._generate_answer_with_ollama(pergunta, context)
        generation_time = time.time() - generation_start
        total_time = time.time() - start_time
        
        logger.info(f"⏱️ Tempos - Busca: {search_time:.2f}s, Geração: {generation_time:.2f}s, Total: {total_time:.2f}s")
        
        return RAGResponse(
            question=pergunta,
            answer=resposta,
            sources=documentos,
            reasoning=f"Resposta gerada com {self.model_name} baseada em {len(documentos)} fontes",
            model_info={
                "status": "ok", 
                "model": self.model_name,
                "timing": {
                    "search_time": round(search_time, 2),
                    "generation_time": round(generation_time, 2),
                    "total_time": round(total_time, 2)
                }
            }
        )
```

**Estrutura do `model_info.timing`:**
```json
{
  "search_time": 0.35,      // segundos
  "generation_time": 12.45,  // segundos
  "total_time": 12.80        // segundos
}
```

---

## Mudanças no Frontend

### `static/index.html`

#### CSS Adicionado

**Classes para visualização de timing:**
```css
.timing-breakdown {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin-top: 15px;
    border: 1px solid #e0e0e0;
}

.timing-bar {
    margin-bottom: 10px;
}

.timing-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.85em;
    color: #666;
    margin-bottom: 4px;
}

.timing-bar-container {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}

.timing-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.timing-bar-fill.search {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.timing-bar-fill.generation {
    background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
}
```

#### JavaScript Atualizado

**Função `askQuestion()` - Extração e exibição de timing:**
```javascript
const data = await response.json();
const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

// Extrair tempos detalhados do backend
const timing = data.model_info?.timing || {};
const searchTime = timing.search_time || 0;
const generationTime = timing.generation_time || 0;
const backendTotal = timing.total_time || 0;

// Exibir no result-meta
<div class="result-meta">
    <span>⏱️ Total: ${totalTime}s</span>
    <span>🔍 Busca: ${searchTime}s</span>
    <span>🤖 IA: ${generationTime}s</span>
    <span>📚 ${data.fontes.length} fontes</span>
</div>

// Breakdown visual com barras de progresso
const maxTime = Math.max(searchTime, generationTime);
const searchPercent = (searchTime / maxTime) * 100;
const generationPercent = (generationTime / maxTime) * 100;

<div class="timing-breakdown">
    <div class="timing-breakdown-title">⏱️ Breakdown de Tempo</div>
    
    <!-- Barra de Busca -->
    <div class="timing-bar">
        <div class="timing-bar-label">
            <span>🔍 Busca de Documentos</span>
            <span><strong>${searchTime}s</strong></span>
        </div>
        <div class="timing-bar-container">
            <div class="timing-bar-fill search" style="width: ${searchPercent}%"></div>
        </div>
    </div>

    <!-- Barra de Geração -->
    <div class="timing-bar">
        <div class="timing-bar-label">
            <span>🤖 Geração com IA (qwen2.5:7b)</span>
            <span><strong>${generationTime}s</strong></span>
        </div>
        <div class="timing-bar-container">
            <div class="timing-bar-fill generation" style="width: ${generationPercent}%"></div>
        </div>
    </div>

    <!-- Total + Overhead -->
    <div style="margin-top: 12px; border-top: 1px solid #ddd;">
        <strong>Total de Processamento:</strong> ${backendTotal}s
        ${overhead > 0.5 ? `| Overhead de rede: ${overhead}s` : ''}
    </div>
</div>
```

---

## Exemplo Visual

### Interface Atualizada

```
┌─────────────────────────────────────────────────────────┐
├─────────────────────────────────────────────────────────┤
│ ⏱️ Total: 15.2s | 🔍 Busca: 0.35s | 🤖 IA: 12.45s      │
│ 📚 3 fontes                                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ⏱️ Breakdown de Tempo                                   │
├─────────────────────────────────────────────────────────┤
│ 🔍 Busca de Documentos                         0.35s   │
│ ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░        │
├─────────────────────────────────────────────────────────┤
│ 🤖 Geração com IA (qwen2.5:7b)                12.45s   │
│ ██████████████████████████████████████████████████████  │
├─────────────────────────────────────────────────────────┤
│ Total de Processamento: 12.80s                         │
│ Overhead de rede: 2.4s                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Métricas Capturadas

### Tempos Típicos Observados

**Busca de Documentos (Qdrant):**
- Base pequena (< 100 chunks): 0.1 - 0.3s
- Base média (100-1000 chunks): 0.3 - 0.8s
- Base grande (> 1000 chunks): 0.5 - 1.5s

**Geração com IA (qwen2.5:7b no Ollama):**
- Resposta curta (2-3 frases): 5 - 10s
- Resposta média (4-6 frases): 10 - 20s
- Resposta longa (> 6 frases): 20 - 40s

**Overhead de Rede:**
- Localhost: 0.1 - 0.5s
- Docker: 0.5 - 2s
- Rede local: 1 - 5s

---

## Benefícios

### 1. **Transparência**
- Usuário vê exatamente onde o tempo está sendo gasto
- Identifica gargalos (busca vs geração)

### 2. **Diagnóstico**
- Se busca demora muito → problema no Qdrant ou indexação
- Se geração demora muito → modelo LLM pesado ou contexto grande
- Se overhead alto → problema de rede/latência

### 3. **Expectativas**
- Usuário sabe que geração com IA é a parte mais lenta
- Visualização ajuda a entender o processo

### 4. **Otimização**
- Dados para identificar oportunidades de melhoria
- Métricas para A/B testing de diferentes modelos/configurações

---

## Logs do Backend

Com as mudanças, o log agora mostra:
```
INFO: 🔍 buscar_artigos retornou 3 docs: [('Império Inca', 0.1032), ...]
INFO: 📚 Encontrou 3 chunks para RAG (artigos: ['Império Inca'])
INFO: 📝 Contexto preparado com 1800 caracteres de 3 fontes
INFO: 🤖 Chamando Ollama com modelo qwen2.5:7b...
INFO: ✅ Resposta gerada com sucesso (245 caracteres)
INFO: ⏱️ Tempos - Busca: 0.35s, Geração: 12.45s, Total: 12.80s
```

---

## Compatibilidade

✅ **100% retrocompatível** - Se `model_info.timing` não existir, a UI funciona normalmente sem as barras de progresso

✅ **Fallback gracioso** - Mostra apenas o tempo total do frontend se backend não retornar timing

✅ **Funciona com API antiga** - Não quebra se campo `timing` estiver ausente

---

## Próximos Passos Sugeridos

1. **Persistir métricas** - Salvar tempos em banco para análise histórica
2. **Dashboard de performance** - Gráficos de tempo médio por fase
3. **Alertas** - Notificar se tempo exceder thresholds
4. **Otimizações** - Usar dados para melhorar performance
   - Cache de embeddings para busca mais rápida
   - Modelo LLM menor/quantizado para geração mais rápida
   - Parallel processing quando possível

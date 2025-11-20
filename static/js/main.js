let ws;
function iniciarWebSocketProgresso() {
    const progressoDiv = document.getElementById('progressoPergunta');
    progressoDiv.innerHTML = '';
    ws = new WebSocket('ws://' + window.location.host + '/ws/progresso-pergunta');
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.status === 'finalizado') {
            progressoDiv.innerHTML += '<div><b>Processamento finalizado!</b></div>';
            ws.close();
        } else {
            progressoDiv.innerHTML += `<div>${data.status}</div>`;
        }
    };
    ws.onerror = function() {
        progressoDiv.innerHTML += '<div style="color:red">Erro no WebSocket</div>';
    };
}

function iniciarWebSocketTelemetria() {
    const telemetriaDiv = document.getElementById('telemetriaStatus');
    telemetriaDiv.innerHTML = '';
    // Fecha o WebSocket anterior se existir
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
    ws = new WebSocket('ws://' + window.location.host + '/ws/telemetria');
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        // Adiciona incrementalmente sem sobrescrever
        const div = document.createElement('div');
        div.textContent = data.status;
        telemetriaDiv.appendChild(div);
    };
    ws.onerror = function() {
        console.error('[Telemetria WS] Erro no WebSocket');
        const div = document.createElement('div');
        div.style.color = 'red';
        div.textContent = 'Erro no WebSocket';
        telemetriaDiv.appendChild(div);
    };
}

async function loadStats() {
    try {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        const colecao = dropdown && dropdown.value ? dropdown.value : '';
        const statsResp = await fetch(`/estatisticas${colecao ? `?colecao=${encodeURIComponent(colecao)}` : ''}`);
        const stats = await statsResp.json();
            document.getElementById('totalChunks').textContent = stats.total_chunks ? stats.total_chunks : '0';
            document.getElementById('totalArtigos').textContent = stats.total_artigos ? stats.total_artigos : '0';
            // Atualiza o card de coleção
            const colecaoCard = document.getElementById('colecaoCard');
            if (colecaoCard) {
                colecaoCard.textContent = `Coleção selecionada: ${stats.colecao ? stats.colecao : '-'}`;
            }
            // Atualiza dimensão do vetor
            const vectorDimSpan = document.getElementById('vectorDim');
            if (vectorDimSpan) {
                vectorDimSpan.textContent = stats.dimensoes_vetor !== undefined ? stats.dimensoes_vetor : '-';
            }
        const statusResp = await fetch(`/status${colecao ? `?colecao=${encodeURIComponent(colecao)}` : ''}`);
        const status = await statusResp.json();
        document.getElementById('qdrantStatus').textContent = status.qdrant_conectado ? 'Conectado' : 'Desconectado';
        document.getElementById('embeddingStatus').textContent = status.modelo_embedding_carregado ? 'Carregado'  : 'Indisponível';
        document.getElementById('modeloEmbedding').textContent = status.modelo_embedding_nome ? '(' + status.modelo_embedding_nome + ')' : 'Não informado';
        const modelo_llm = status.modelo_llm ? status.modelo_llm : 'N/A';
        document.getElementById('ollamaStatus').textContent = status.ollama_disponivel ? 'Disponível' : 'Indisponível';
        document.getElementById('modeloLLM').textContent = '(' + modelo_llm + ')';
    } catch (error) {
        document.getElementById('totalChunks').textContent = 'Erro';
        document.getElementById('qdrantStatus').textContent = 'Erro';
        document.getElementById('embeddingStatus').textContent = 'Erro';
        document.getElementById('modeloEmbedding').textContent = 'Erro';
        document.getElementById('ollamaStatus').textContent = 'Erro';
        document.getElementById('modeloLLM').textContent = '';
        const colecaoCard = document.getElementById('colecaoCard');
        if (colecaoCard) colecaoCard.textContent = 'Coleção: Erro';
    }
}
window.loadStats = loadStats;
window.addEventListener('DOMContentLoaded', loadStats);

async function performSearch() {
    const query = document.getElementById('searchQuery').value;
    const limit = parseInt(document.getElementById('searchLimit').value) || 5;
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">Buscando...</div>';
    const t0 = performance.now();
    try {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        const colecao = dropdown && dropdown.value ? dropdown.value : '';
        console.log("Coleção selecionada para busca:", colecao);
        const response = await fetch('/buscar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit, colecao })
        });
        const t1 = performance.now();
        const data = await response.json();
        const searchTime = Math.round(t1 - t0);
        // painel de telemetria removido
        let html = '';
        if (data.resultados && data.resultados.length > 0) {
            const agrupados = {};
            data.resultados.forEach(r => {
                if (!agrupados[r.title]) agrupados[r.title] = [];
                agrupados[r.title].push(r);
            });
            html += Object.entries(agrupados).map(([titulo, chunks]) => `
                <div class="result-item">
                    <div class="result-title">${titulo}</div>
                    ${chunks.map(chunk => `
                        <div class="result-content">${chunk.content}</div>
                        <div class="result-meta">Score: ${chunk.score}</div>
                    `).join('')}
                </div>
            `).join('');
        } else {
            html += '<div class="error">Nenhum resultado encontrado.</div>';
        }
        if (data.telemetria) {
            html += `<div class="timing-breakdown" style="margin-top:18px;">
                <div class="timing-breakdown-title">📊 Telemetria Detalhada</div>
                <div><b>Coleção usada:</b> ${data.telemetria.colecao_usada ? data.telemetria.colecao_usada : '(não informada)'}</div>
                <div>Tempo total: <b>${data.telemetria.tempo_total_ms} ms</b></div>
                <div>Tempo busca Qdrant: <b>${data.telemetria.tempo_busca_qdrant_ms} ms</b></div>
                <div>Tempo filtragem: <b>${data.telemetria.tempo_filtragem_ms} ms</b></div>
                <div>Resultados antes do filtro: <b>${data.telemetria.resultados_antes_filtro}</b></div>
                <div>Resultados após filtro: <b>${data.telemetria.resultados_depois_filtro}</b></div>
            </div>`;
        }
        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${error.message}</div>`;
    }
}

async function askQuestion() {
    const question = document.getElementById('question').value;
    const maxChunks = parseInt(document.getElementById('maxChunks').value) || 10;
    const resultsDiv = document.getElementById('answerResults');
    resultsDiv.innerHTML = '';
    resultsDiv.innerHTML = '<div class="loading">Processando pergunta...</div>';
    const telemetriaDiv = document.getElementById('telemetriaStatus');
    if (telemetriaDiv) telemetriaDiv.innerHTML = '';
    document.getElementById('telemetriaDetalhada').innerHTML = '';
    const t0 = performance.now();
    try {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        const colecao = dropdown && dropdown.value ? dropdown.value : '';
        const response = await fetch('/perguntar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pergunta: question, max_chunks: maxChunks, colecao })
        });
        const t1 = performance.now();
        const data = await response.json();
        const generationTime = Math.round(t1 - t0);
        // painel de telemetria removido
        let html = '';
        if (data.resposta) {
            html += `<div class="answer"><div class="answer-text">${data.resposta}</div></div>`;
        } else {
            html += '<div class="error">Nenhuma resposta encontrada.</div>';
        }
        if (data.telemetria) {
            const t = data.telemetria;
            let llmHtml = '';
            if (t.llm) {
                llmHtml = `
                <div style="margin-top:10px;">
                    <div><b>LLM:</b></div>
                    <div>Prompt tokens: <b>${t.llm.prompt_tokens ?? '-'}</b></div>
                    <div>Prompt eval time: <b>${t.llm.prompt_eval_time ?? '-'}</b> s</div>
                    <div>Prompt tokens/s: <b>${t.llm.prompt_tokens_per_sec ?? '-'}</b></div>
                    <div>Completion tokens: <b>${t.llm.completion_tokens ?? '-'}</b></div>
                    <div>Completion eval time: <b>${t.llm.completion_eval_time ?? '-'}</b> s</div>
                    <div>Completion tokens/s: <b>${t.llm.completion_tokens_per_sec ?? '-'}</b></div>
                    <div>Total tokens: <b>${t.llm.total_tokens ?? '-'}</b></div>
                    <div>Total eval time: <b>${t.llm.total_eval_time ?? '-'}</b> s</div>
                    <div>Total tokens/s: <b>${t.llm.total_tokens_per_sec ?? '-'}</b></div>
                </div>`;
            }
            document.getElementById('telemetriaDetalhada').innerHTML = `
                <div class="timing-breakdown" style="margin-top:8px;">
                    <div class="timing-breakdown-title">📊 Telemetria Detalhada</div>
                    <div><b>Coleção usada:</b> ${t.colecao_usada ? t.colecao_usada : '(não informada)'}</div>
                    <div>Tempo total: <b>${t.tempo_total_ms ?? '-'}</b> ms</div>
                    <div>Tempo busca Qdrant: <b>${t.tempo_busca_qdrant_ms ?? '-'}</b> ms</div>
                    <div>Tempo filtragem: <b>${t.tempo_filtragem_ms ?? '-'}</b> ms</div>
                    <div>Resultados antes do filtro: <b>${t.resultados_antes_filtro ?? '-'}</b></div>
                    <div>Resultados após filtro: <b>${t.resultados_depois_filtro ?? '-'}</b></div>
                    <div>Chunks encontrados: <b>${t.chunks_encontrados ?? '-'}</b></div>
                    <div>Artigos encontrados: <b>${t.artigos_encontrados ?? '-'}</b></div>
                    <div>Sucesso: <b>${t.sucesso ?? '-'}</b></div>
                    ${llmHtml}
                </div>
            `;
        }
        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${error.message}</div>`;
    }
}

async function addArticle() {
    const title = document.getElementById('articleTitle').value;
    const resultsDiv = document.getElementById('addResults');
    resultsDiv.innerHTML = '<div class="loading">Adicionando artigo...</div>';
    try {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        const colecao = dropdown && dropdown.value ? dropdown.value : '';
        const response = await fetch('/adicionar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ titulo: title, colecao })
        });
        const data = await response.json();
            // Exibe o JSON bruto da resposta para debug
            resultsDiv.innerHTML = `<pre style='background:#f9f9f9;border-radius:8px;padding:10px;margin-top:10px;'>${JSON.stringify(data, null, 2)}</pre>`;
        if (data.chunks_adicionados) {
            let telemetriaHtml = '';
            if (data.telemetria) {
                telemetriaHtml = `
                <div class="telemetria-panel" style="margin-top:10px;padding:10px;background:#f3f3f3;border-radius:8px;">
                    <b>Telemetria da Ingestão:</b><br>
                    <span><b>Coleção:</b> ${data.telemetria.colecao}</span><br>
                    <span><b>Título:</b> ${data.telemetria.titulo}</span><br>
                    <span><b>Chunks adicionados:</b> ${data.telemetria.chunks_adicionados}</span><br>
                    <span><b>Tempo de processamento:</b> ${data.telemetria.tempo_processamento_ms} ms</span>
                </div>`;
            }
            resultsDiv.innerHTML = `<div class="success">Chunks criados: ${data.chunks_adicionados}<br><a href="${data.url}" target="_blank" style="color: #4CAF50;">${data.titulo || 'Ver artigo'}</a></div>${telemetriaHtml}`;
            loadStats();
        } else {
            resultsDiv.innerHTML = `<div class="error">Erro: ${data.detail || data.message || 'Falha ao adicionar artigo'}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${error.message}</div>`;
    }
}

async function addRandomArticle() {
    const resultsDiv = document.getElementById('addResults');
    resultsDiv.innerHTML = '<div class="loading">Adicionando artigo aleatório...</div>';
    try {
        const response = await fetch('/ingest/exemplos', { method: 'POST' });
        const data = await response.json();
        if (data.total_chunks) {
            resultsDiv.innerHTML = `<div class="success">Artigos adicionados: ${data.total_artigos}<br>Chunks criados: ${data.total_chunks}</div>`;
            loadStats();
        } else {
            resultsDiv.innerHTML = `<div class="error">Erro: ${data.detail || data.message || 'Falha ao adicionar artigos'}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${error.message}</div>`;
    }
}

document.getElementById('searchQuery').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});
document.getElementById('question').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) askQuestion();
});

window.askQuestion = askQuestion;
window.performSearch = performSearch;
window.addArticle = addArticle;
window.addRandomArticle = addRandomArticle;

// --- Qdrant Collections Dropdown Logic ---
async function loadQdrantCollections() {
    try {
        const resp = await fetch('/listar_colecoes');
        const data = await resp.json();
        const collections = data.colecoes || [];
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        dropdown.innerHTML = '<option value="">Selecione uma coleção</option>';
        let defaultSet = false;
        collections.forEach(col => {
            const opt = document.createElement('option');
            opt.value = col;
            opt.textContent = col;
            if (col === 'wikipedia_langchain' && !defaultSet) {
                opt.selected = true;
                defaultSet = true;
            }
            dropdown.appendChild(opt);
        });
    } catch (err) {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        dropdown.innerHTML = '<option value="">Erro ao carregar coleções</option>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadQdrantCollections().then(() => {
        const dropdown = document.getElementById('qdrant-collections-dropdown');
        const vigente = localStorage.getItem('colecaoVigente');
        if (dropdown && vigente) {
            // Se a coleção vigente existe nas opções, seleciona
            for (let i = 0; i < dropdown.options.length; i++) {
                if (dropdown.options[i].value === vigente) {
                    dropdown.selectedIndex = i;
                    break;
                }
            }
        }
        loadStats();
        dropdown.addEventListener('change', function() {
            localStorage.setItem('colecaoVigente', dropdown.value);
            loadStats();
        });
        const openBtn = document.getElementById('open-collection-session');
        if (openBtn) {
            openBtn.addEventListener('click', function() {
                if (dropdown.value) {
                    window.open(`/static/index.html?colecao=${encodeURIComponent(dropdown.value)}`, '_blank');
                }
            });
        }
    });
});

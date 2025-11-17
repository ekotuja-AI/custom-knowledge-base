let wsTelemetria = null;

/* ---------------------------
   WEBSOCKET — TELEMETRIA
---------------------------- */
function iniciarWebSocketTelemetria() {
    if (wsTelemetria && wsTelemetria.readyState === WebSocket.OPEN) {
        wsTelemetria.close();
    }

    console.log("Iniciando WebSocket de telemetria...");
    const div = document.getElementById("telemetriaStatus");
    div.innerHTML = "";

    const ws = new WebSocket(`ws://${window.location.host}/ws/telemetria`);
    wsTelemetria = ws;

    ws.onopen = () => {
        console.log("WS telemetria conectado");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            const msg = data.status;

            const line = document.createElement("div");
            line.textContent = msg;
            div.appendChild(line);
        } catch (e) {
            console.error("Erro ao processar WS:", e);
        }
    };

    ws.onerror = () => {
        const line = document.createElement("div");
        line.style.color = "red";
        line.textContent = "Erro no WebSocket";
        div.appendChild(line);
    };

    ws.onclose = () => {
        console.log("WS telemetria fechado");
    };
}

/* ------------------------------------------------------------------
   WEBSOCKET DE PROGRESSO DA PERGUNTA (apenas visual — backend opcional)
------------------------------------------------------------------- */
function iniciarWebSocketProgresso() {
    console.log("Iniciando WS progresso pergunta...");
    const progressoDiv = document.getElementById("progressoPergunta");
    progressoDiv.innerHTML = "";

    const ws = new WebSocket(`ws://${window.location.host}/ws/progresso-pergunta`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.status === "finalizado") {
            progressoDiv.innerHTML += "<div><b>Processamento finalizado!</b></div>";
            ws.close();
        } else {
            progressoDiv.innerHTML += `<div>${data.status}</div>`;
        }
    };

    ws.onerror = function () {
        progressoDiv.innerHTML += `<div style="color:red">Erro no WebSocket</div>`;
    };
}

/* --------------------------------------
   BUSCA SEMÂNTICA
-------------------------------------- */
async function performSearch() {
    const query = document.getElementById('searchQuery').value;
    const limit = parseInt(document.getElementById('searchLimit').value) || 5;

    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">Buscando...</div>';

    const t0 = performance.now();

    try {
        const response = await fetch('/buscar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limite: limit })
        });

        const t1 = performance.now();
        const data = await response.json();

        const searchTime = Math.round(t1 - t0);

        document.getElementById('telemetryPanel').style.display = 'block';
        document.getElementById('searchTime').textContent = searchTime;
        document.getElementById('searchBar').style.width = Math.min(searchTime / 10, 100) + '%';

        // limpar geração
        document.getElementById('generationTime').textContent = '-';
        document.getElementById('generationBar').style.width = '0%';

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
            html += `
                <div class="timing-breakdown">
                    <div class="timing-breakdown-title">📊 Telemetria Detalhada</div>
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

/* --------------------------------------
   PERGUNTAR COM IA
-------------------------------------- */
async function askQuestion() {
    const question = document.getElementById('question').value;
    const maxChunks = parseInt(document.getElementById('maxChunks').value) || 10;

    const resultsDiv = document.getElementById('answerResults');
    resultsDiv.innerHTML = '<div class="loading">Processando pergunta...</div>';

    // limpar telemetria incremental
    const telemDiv = document.getElementById('telemetriaStatus');
    telemDiv.innerHTML = '';

    document.getElementById('telemetriaDetalhada').innerHTML = '';

    const t0 = performance.now();

    try {
        const response = await fetch('/perguntar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pergunta: question, max_chunks: maxChunks })
        });

        const t1 = performance.now();
        const data = await response.json();

        const genTime = Math.round(t1 - t0);

        document.getElementById('telemetryPanel').style.display = 'block';
        document.getElementById('generationTime').textContent = genTime;
        document.getElementById('generationBar').style.width = Math.min(genTime / 10, 100) + '%';

        // limpar busca
        document.getElementById('searchTime').textContent = '-';
        document.getElementById('searchBar').style.width = '0%';

        let html = '';

        if (data.resposta) {
            html = `
                <div class="answer">
                    <div class="answer-text">${data.resposta}</div>
                </div>`;
        } else {
            html = '<div class="error">Nenhuma resposta encontrada.</div>';
        }

        if (data.telemetria) {
            document.getElementById('telemetriaDetalhada').innerHTML = `
                <div class="timing-breakdown">
                    <div class="timing-breakdown-title">📊 Telemetria Detalhada</div>
                    <div>Tempo total: <b>${data.telemetria.tempo_total_ms} ms</b></div>
                    <div>Tempo busca Qdrant: <b>${data.telemetria.tempo_busca_qdrant_ms} ms</b></div>
                    <div>Tempo filtragem: <b>${data.telemetria.tempo_filtragem_ms} ms</b></div>
                    <div>Antes filtro: <b>${data.telemetria.resultados_antes_filtro}</b></div>
                    <div>Após filtro: <b>${data.telemetria.resultados_depois_filtro}</b></div>
                </div>`;
        }

        resultsDiv.innerHTML = html;

    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${error.message}</div>`;
    }
}

/* --------------------------------------
   ADICIONAR ARTIGO
-------------------------------------- */
async function addArticle() {
    const title = document.getElementById('articleTitle').value;
    const resultsDiv = document.getElementById('addResults');

    resultsDiv.innerHTML = '<div class="loading">Adicionando artigo...</div>';

    try {
        const response = await fetch('/adicionar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ titulo: title })
        });

        const data = await response.json();

        if (data.chunks_adicionados) {
            resultsDiv.innerHTML = `
                <div class="success">
                    Chunks criados: ${data.chunks_adicionados}<br>
                    <a href="${data.url}" target="_blank" style="color:#4CAF50">${data.titulo || 'Ver artigo'}</a>
                </div>`;
        } else {
            resultsDiv.innerHTML =
                `<div class="error">Erro: ${data.detail || data.message}</div>`;
        }

    } catch (err) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${err.message}</div>`;
    }
}

/* --------------------------------------
   ARTIGOS ALEATÓRIOS
-------------------------------------- */
async function addRandomArticle() {
    const resultsDiv = document.getElementById('addResults');
    resultsDiv.innerHTML = '<div class="loading">Adicionando artigo aleatório...</div>';

    try {
        const response = await fetch('/ingest/exemplos', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.total_chunks) {
            resultsDiv.innerHTML = `
                <div class="success">
                    Artigos adicionados: ${data.total_artigos}<br>
                    Chunks criados: ${data.total_chunks}
                </div>`;
        } else {
            resultsDiv.innerHTML =
                `<div class="error">Erro: ${data.detail || data.message}</div>`;
        }

    } catch (err) {
        resultsDiv.innerHTML = `<div class="error">Erro: ${err.message}</div>`;
    }
}

/* --------------------------------------
   TECLAS DE ATALHO
-------------------------------------- */
document.getElementById('searchQuery').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

document.getElementById('question').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) askQuestion();
});

/* Expor globalmente */
window.askQuestion = askQuestion;
window.performSearch = performSearch;
window.addArticle = addArticle;
window.addRandomArticle = addRandomArticle;
window.iniciarWebSocketTelemetria = iniciarWebSocketTelemetria;
window.iniciarWebSocketProgresso = iniciarWebSocketProgresso;

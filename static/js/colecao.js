async function carregarModelos() {
    console.log("Carregando modelos...");
    const embedDropdown = document.getElementById('modeloEmbedDropdown');
    const llmDropdown = document.getElementById('modeloLLMDropdown');

    embedDropdown.innerHTML = '';
    llmDropdown.innerHTML = '';

    // === Embeddings do MySQL via backend ===
    try {
        console.log("Carregando embeddings do backend...");
        const respEmb = await fetch('/dbService/embeddings');
        const dataEmb = await respEmb.json();
        console.log("Embeddings carregados:", dataEmb);

       if (Array.isArray(dataEmb)) {
            dataEmb.forEach(m => {
                embedDropdown.innerHTML += `
                    <option value="${m.id}">
                        ${m.nome} (${m.descricao})
                    </option>`;
            });
        }

    } catch (e) {
        console.error("Erro ao carregar embeddings:", e);
        embedDropdown.innerHTML = `<option>Erro ao carregar</option>`;
    }

    // === LLMs (por enquanto estático, pode virar endpoint depois) ===
    llmDropdown.innerHTML = `
        <option value="qwen2.5:7b">qwen2.5:7b (LLM Multilingual)</option>
        <option value="llama3.1:8b">llama3.1:8b (LLM English/General)</option>
    `;
}

window.addEventListener('DOMContentLoaded', carregarModelos);

async function criarColecao() {
    const nome = document.getElementById('nomeColecao').value.trim();
    const embedding_model_id = parseInt(document.getElementById('modeloEmbedDropdown').value);
    const modelo_embedding_desc = document.getElementById('modeloEmbedDropdown').options[document.getElementById('modeloEmbedDropdown').selectedIndex].text;
    const dimensoes = getDimensoesModeloEmbed(document.getElementById('modeloEmbedDropdown'));
    const modelo_llm = document.getElementById('modeloLLMDropdown').value;

    if (!nome) {
        document.getElementById('msg').textContent = 'Digite um nome para a coleção.';
        return;
    }
    let body = JSON.stringify({
        nome: nome,
        embedding_model_id: embedding_model_id,
        modelo: modelo_embedding_desc,
        dimensoes: dimensoes,
        modelo_llm: modelo_llm
    });

    try {
        const resp = await fetch('/criar_colecao', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: body
        });

        const data = await resp.json();

        if (data.sucesso === true) {
            document.getElementById('msg').textContent = `Coleção ${nome} criada com sucesso!`;
        } else {
            document.getElementById('msg').textContent = data.erro || 'Erro ao criar coleção.';
        }

    } catch (e) {
        console.error("no catch - Erro ao criar coleção:", e);
        let msg = 'Erro de conexão.';
        if (e && e.message) {
            msg += ' Detalhes: ' + e.message;
        } else if (typeof e === 'string') {
            msg += ' Detalhes: ' + e;
        } else if (e && e.toString) {
            msg += ' Detalhes: ' + e.toString();
        }
        document.getElementById('msg').textContent = msg;
    }
}



async function criarColecaoOLD() {
    const nome = document.getElementById('nomeColecao').value.trim();
    const modelo = document.getElementById('modeloEmbedDropdown').value;
    const dimensoes = getDimensoesModeloEmbed(document.getElementById('modeloEmbedDropdown'));
    const modelo_llm = document.getElementById('modeloLLMDropdown').value;
    if (!nome) {
        document.getElementById('msg').textContent = 'Digite um nome para a coleção.';
        return;
    }
    console.log('Criando coleção...');
    try {
        console.log("modelo: ", modelo);
        console.log("dimensoes: ", dimensoes);
        console.log("modelo_llm: ", modelo_llm);

        
        const resp = await fetch('/criar_colecao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, modelo, dimensoes, modelo_llm })
        });
        const data = await resp.json();
        
        if (data && esso) {
            document.getElementById('msg').textContent = 'Coleção criada com sucesso!';
        } else {
            document.getElementById('msg').textContent = data.erro || 'Erro ao criar coleção.';
        }
    } catch (e) {
        document.getElementById('msg').textContent = 'Erro de conexão.';
    }
}

function getDimensoesModeloEmbed(embedDropdown) {
    const selectedOption = embedDropdown.options[embedDropdown.selectedIndex];
    if (!selectedOption) return '';
    // Extrai o número de dimensões do texto do option (português ou inglês)
    const match = selectedOption.text.match(/(\d+)\s*(dimensões|dimensions)/i);
    return match ? parseInt(match[1], 10) : null;
}

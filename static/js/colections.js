// JS para carregar coleções do Qdrant na landing page
async function carregarColecoesQdrant() {
    try {
        const resp = await fetch('/listar_colecoes');
        const data = await resp.json();
        const ul = document.getElementById('listaColecoes');
        ul.innerHTML = '';
        if (data.colecoes && data.colecoes.length > 0) {
            data.colecoes.forEach(c => {
                const li = document.createElement('li');
                li.textContent = c;
                ul.appendChild(li);
            });
            document.getElementById('colecoesMsg').textContent = '';
        } else {
            document.getElementById('colecoesMsg').textContent = 'Nenhuma coleção encontrada.';
        }
    } catch (e) {
        document.getElementById('colecoesMsg').textContent = 'Erro ao consultar coleções.';
    }
}
window.onload = carregarColecoesQdrant;

// Preenche o dropdown de coleções e adiciona funcionalidade ao botão
document.addEventListener('DOMContentLoaded', async function() {
    const dropdown = document.getElementById('dropdownColecoes');
    const usarBtn = document.getElementById('usarColecaoBtn');
    usarBtn.disabled = true;

    try {
        const resp = await fetch('/listar_colecoes');
        const data = await resp.json();
        dropdown.innerHTML = '<option value="">Selecione uma coleção</option>';
        if (data.colecoes && data.colecoes.length > 0) {
            data.colecoes.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                dropdown.appendChild(opt);
            });
            document.getElementById('colecoesMsg').textContent = '';
        } else {
            document.getElementById('colecoesMsg').textContent = 'Nenhuma coleção encontrada.';
        }
    } catch (e) {
        document.getElementById('colecoesMsg').textContent = 'Erro ao consultar coleções.';
    }

    dropdown.addEventListener('change', function() {
        usarBtn.disabled = !dropdown.value;
    });

    usarBtn.addEventListener('click', function() {
        const colecao = dropdown.value;
        if (colecao) {
            window.open(`/static/index.html?colecao=${encodeURIComponent(colecao)}`, '_blank');
        } else {
            alert('Por favor, selecione uma coleção para continuar.');
        }
    });
});

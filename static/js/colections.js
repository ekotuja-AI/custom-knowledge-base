// JS para carregar coleções do Qdrant na landing page
document.addEventListener('DOMContentLoaded', async function() {
    const dropdown = document.getElementById('dropdownColecoes');
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

    dropdown.addEventListener('change', async function() {
        const colecao = dropdown.value;
        const infoDiv = document.getElementById('dimensaoVetorInfo');
        if (!colecao) {
            infoDiv.textContent = '';
            return;
        }
        infoDiv.textContent = 'Carregando dimensão do vetor...';
        try {
            const resp = await fetch(`/estatisticas?colecao=${encodeURIComponent(colecao)}`);
            const stats = await resp.json();
            if (stats.dimensoes_vetor !== undefined) {
                infoDiv.textContent = `Dimensão do vetor: ${stats.dimensoes_vetor}`;
            } else {
                infoDiv.textContent = 'Dimensão do vetor não encontrada.';
            }
        } catch (e) {
            infoDiv.textContent = 'Erro ao consultar dimensão.';
        }
    });
});

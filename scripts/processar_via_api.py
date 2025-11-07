"""
Processa artigos faltantes usando a API REST (mais estável)
"""
import requests
import time
from tqdm import tqdm

def processar_via_api(arquivo_lista: str, api_url: str = "http://localhost:9000"):
    """Processa artigos via endpoint /adicionar da API"""
    
    # Ler lista
    with open(arquivo_lista, 'r', encoding='utf-8') as f:
        titulos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"📚 {len(titulos)} artigos para processar")
    print(f"🌐 API: {api_url}\n")
    
    sucessos = 0
    erros = 0
    ja_existentes = 0
    
    for titulo in tqdm(titulos, desc="📥 Processando"):
        try:
            response = requests.post(
                f"{api_url}/adicionar",
                json={"titulo": titulo},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "já existe" in result.get("mensagem", "").lower():
                    ja_existentes += 1
                else:
                    sucessos += 1
                    # Pequeno delay para não sobrecarregar
                    time.sleep(0.5)
            else:
                tqdm.write(f"❌ {titulo}: {response.status_code}")
                erros += 1
                
        except Exception as e:
            tqdm.write(f"❌ {titulo}: {str(e)}")
            erros += 1
    
    # Resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS")
    print("="*60)
    print(f"✅ Processados com sucesso: {sucessos}")
    print(f"ℹ️  Já existentes: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    print(f"📝 Total: {len(titulos)}")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Arquivo com lista de títulos')
    parser.add_argument('--api', default='http://localhost:9000', help='URL da API')
    
    args = parser.parse_args()
    processar_via_api(args.input, args.api)

#!/usr/bin/env python3
import requests
import json

def test_pergunta(pergunta, deve_ter_artigo=True):
    print(f"\n{'='*60}")
    print(f"Pergunta: '{pergunta}'")
    print(f"Esperado: {'TEM artigo' if deve_ter_artigo else 'NÃO TEM artigo'}")
    
    response = requests.post(
        'http://localhost:9000/perguntar',
        json={'pergunta': pergunta},
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )
    
    if response.status_code != 200:
        print(f"❌ ERRO HTTP {response.status_code}")
        return False
    
    data = response.json()
    resposta = data.get('resposta', '')
    fontes = data.get('fontes', [])
    
    print(f"Resposta ({len(resposta)} chars): {resposta[:150]}...")
    print(f"Fontes ({len(fontes)}): {[f.get('title') for f in fontes]}")
    
    if deve_ter_artigo:
        passou = len(fontes) > 0 and 'Ainda não existem artigos' not in resposta
        print(f"Status: {'✅ PASSOU' if passou else '❌ FALHOU'}")
        return passou
    else:
        passou = 'Ainda não existem artigos' in resposta
        print(f"Status: {'✅ PASSOU' if passou else '❌ FALHOU'}")
        return passou

if __name__ == '__main__':
    print("\n🧪 TESTES DO SISTEMA RAG")
    
    resultados = []
    
    # Teste 1: Krabi (deve ter)
    resultados.append(('Krabi', test_pergunta('o que é krabi?', deve_ter_artigo=True)))
    
    # Teste 2: Porrete (deve ter)
    resultados.append(('Porrete', test_pergunta('o que é porrete?', deve_ter_artigo=True)))
    
    # Teste 3: Maçã (deve ter)
    resultados.append(('Maçã', test_pergunta('o que é maçã?', deve_ter_artigo=True)))
    
    # Teste 4: Praia da Joaquina (NÃO deve ter)
    resultados.append(('Praia Joaquina', test_pergunta('o que é praia da joaquina?', deve_ter_artigo=False)))
    
    # Teste 5: Bacamarte (NÃO deve ter)
    resultados.append(('Bacamarte', test_pergunta('o que é bacamarte?', deve_ter_artigo=False)))
    
    print(f"\n{'='*60}")
    print("📊 RESUMO")
    for nome, passou in resultados:
        status = '✅' if passou else '❌'
        print(f"  {status} {nome}")
    
    total = len(resultados)
    passou = sum(1 for _, p in resultados if p)
    print(f"\nTotal: {passou}/{total} testes passaram")

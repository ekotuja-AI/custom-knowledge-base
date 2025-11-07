"""
Monitor de progresso do reprocessamento em tempo real
"""
import time
import sys
from qdrant_client import QdrantClient

def monitor_progresso(host='localhost', port=6333, total_esperado=9300, intervalo=5):
    """Monitora o progresso do reprocessamento"""
    
    client = QdrantClient(host=host, port=port)
    
    print("📊 MONITOR DE PROGRESSO")
    print("=" * 70)
    print(f"Target: {total_esperado} chunks (~500 artigos)")
    print(f"Atualizando a cada {intervalo} segundos (Ctrl+C para sair)\n")
    
    pontos_anterior = 0
    tempo_inicio = time.time()
    
    try:
        while True:
            try:
                info = client.get_collection('wikipedia_langchain')
                pontos_atual = info.points_count
                
                # Calcular progresso
                progresso_pct = (pontos_atual / total_esperado) * 100
                artigos_estimados = int(pontos_atual / 18.6)
                
                # Calcular velocidade
                pontos_novos = pontos_atual - pontos_anterior
                tempo_decorrido = time.time() - tempo_inicio
                velocidade = pontos_atual / tempo_decorrido if tempo_decorrido > 0 else 0
                
                # Estimar tempo restante
                pontos_restantes = total_esperado - pontos_atual
                tempo_restante = pontos_restantes / velocidade if velocidade > 0 else 0
                
                # Barra de progresso
                barra_tamanho = 50
                preenchido = int((pontos_atual / total_esperado) * barra_tamanho)
                barra = '█' * preenchido + '░' * (barra_tamanho - preenchido)
                
                # Limpar linha e imprimir
                sys.stdout.write('\r')
                sys.stdout.write(f"[{barra}] {progresso_pct:.1f}% | ")
                sys.stdout.write(f"{pontos_atual:,}/{total_esperado:,} chunks | ")
                sys.stdout.write(f"~{artigos_estimados} artigos | ")
                sys.stdout.write(f"{velocidade:.1f} chunks/s | ")
                
                if tempo_restante > 60:
                    sys.stdout.write(f"ETA: {int(tempo_restante/60)}min")
                else:
                    sys.stdout.write(f"ETA: {int(tempo_restante)}s")
                
                sys.stdout.flush()
                
                # Verificar se completou
                if pontos_atual >= total_esperado:
                    print("\n\n✅ Processamento completo!")
                    print(f"📊 Total: {pontos_atual:,} chunks em {artigos_estimados} artigos")
                    print(f"⏱️  Tempo total: {int(tempo_decorrido/60)} minutos")
                    break
                
                pontos_anterior = pontos_atual
                time.sleep(intervalo)
                
            except Exception as e:
                if "Not found" in str(e):
                    sys.stdout.write('\r')
                    sys.stdout.write("⏳ Aguardando criação da coleção...")
                    sys.stdout.flush()
                    time.sleep(intervalo)
                else:
                    raise
                    
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitor interrompido pelo usuário")
        print(f"📊 Último status: {pontos_atual:,} chunks (~{artigos_estimados} artigos)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitorar progresso do reprocessamento')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant')
    parser.add_argument('--port', type=int, default=6333, help='Porta do Qdrant')
    parser.add_argument('--total', type=int, default=9300, help='Total esperado de chunks')
    parser.add_argument('--intervalo', type=int, default=5, help='Intervalo de atualização (segundos)')
    
    args = parser.parse_args()
    
    monitor_progresso(args.host, args.port, args.total, args.intervalo)

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil, time, gzip, requests
from services.wikipediaOfflineService import wikipedia_offline_service
from services.wikipediaDumpService import wikipedia_dump_processor

router = APIRouter()

@router.get("/dumps/status")
async def status_dumps():
    try:
        data_dir = wikipedia_dump_processor.data_dir
        data_dir.mkdir(exist_ok=True)
        dumps_files = []
        total_size = 0
        if data_dir.exists():
            for file in data_dir.glob("*.xml.*"):
                file_stat = file.stat()
                size_mb = round(file_stat.st_size / (1024 * 1024), 2)
                dumps_files.append({
                    "filename": file.name,
                    "size_mb": size_mb,
                    "modified": file_stat.st_mtime
                })
                total_size += size_mb
        return {
            "data_directory": str(data_dir),
            "directory_exists": data_dir.exists(),
            "total_dumps": len(dumps_files),
            "dumps_baixados": dumps_files,
            "espaco_usado_mb": total_size,
            "recomendacoes": [
                "Dumps típicos: 1-5 GB comprimidos",
                "Certifique-se de ter 10+ GB livres",
                "Use 'pages-articles' para melhor custo-benefício"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao verificar status: {str(e)}")

@router.post("/dumps/processar-exemplo")
async def processar_dump_exemplo():
    try:
        start_time = time.time()
        filepath = wikipedia_dump_processor.data_dir / "exemplo_dump.xml"
        if not filepath.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dump de exemplo não encontrado")
        total_articles = 0
        total_chunks = 0
        chunk_batch = []
        for chunk_data in wikipedia_dump_processor.process_dump_to_chunks(str(filepath)):
            chunk_batch.append(chunk_data)
            if len(chunk_batch) >= 10:
                chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
                total_chunks += chunks_added
                total_articles += len(set(chunk['title'] for chunk in chunk_batch))
                chunk_batch = []
        if chunk_batch:
            chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
            total_chunks += chunks_added
            total_articles += len(set(chunk['title'] for chunk in chunk_batch))
        processing_time = time.time() - start_time
        return {
            "message": "Dump de exemplo processado com sucesso",
            "tipo": "Demonstração de processamento XML",
            "total_articles_processed": total_articles,
            "total_chunks_created": total_chunks,
            "processing_time_seconds": round(processing_time, 2),
            "artigos_incluidos": ["Inteligência artificial", "Machine learning", "Python"],
            "formato_original": "MediaWiki XML",
            "proximos_passos": [
                "Use GET /estatisticas para ver o crescimento da base",
                "Use POST /buscar para testar busca nos novos artigos",
                "Para dumps reais, use POST /dumps/download primeiro"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao processar dump de exemplo: {str(e)}")

@router.post("/dumps/download-real")
async def download_dump_real(language: str = "pt", dump_type: str = "pages-articles"):
    try:
        dumps = wikipedia_dump_processor.get_available_dumps(language)
        target_dump = None
        for dump in dumps:
            if dump.type == dump_type:
                target_dump = dump
                break
        if not target_dump:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dump do tipo '{dump_type}' não encontrado para {language}")
        filepath = wikipedia_dump_processor.data_dir / target_dump.filename
        if filepath.exists():
            file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
            return {
                "message": "Dump já existe localmente",
                "filename": target_dump.filename,
                "size_mb": file_size_mb,
                "status": "existente"
            }
        try:
            start_time = time.time()
            downloaded_path = wikipedia_dump_processor.download_dump(target_dump)
            download_time = time.time() - start_time
            actual_size_mb = round(Path(downloaded_path).stat().st_size / (1024 * 1024), 2)
            return {
                "message": "Download real concluído com sucesso!",
                "dump_info": {
                    "filename": target_dump.filename,
                    "size_mb": actual_size_mb,
                    "type": target_dump.type,
                    "language": target_dump.language
                },
                "download_time_seconds": round(download_time, 2),
                "filepath": downloaded_path,
                "status": "baixado",
                "proximo_passo": f"Use POST /dumps/processar com filename='{target_dump.filename}'"
            }
        except Exception as download_error:
            return {
                "message": "Erro no download real",
                "erro": str(download_error),
                "alternativa": f"Download manual: Invoke-WebRequest -Uri '{target_dump.url}' -OutFile 'data/{target_dump.filename}'",
                "status": "erro"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no download real: {str(e)}")

@router.post("/dumps/processar-expandido")
async def processar_dump_expandido():
    try:
        start_time = time.time()
        filepath = wikipedia_dump_processor.data_dir / "dump_expandido.xml"
        if not filepath.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dump expandido não encontrado")
        total_articles = 0
        total_chunks = 0
        chunk_batch = []
        for chunk_data in wikipedia_dump_processor.process_dump_to_chunks(str(filepath)):
            chunk_batch.append(chunk_data)
            if len(chunk_batch) >= 20:
                chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
                total_chunks += chunks_added
                total_articles += len(set(chunk['title'] for chunk in chunk_batch))
                chunk_batch = []
        if chunk_batch:
            chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
            total_chunks += chunks_added
            total_articles += len(set(chunk['title'] for chunk in chunk_batch))
        processing_time = time.time() - start_time
        return {
            "message": "Dump expandido processado com sucesso!",
            "tipo": "Demonstração de ingestão em massa",
            "total_articles_processed": total_articles,
            "total_chunks_created": total_chunks,
            "processing_time_seconds": round(processing_time, 2),
            "chunks_per_second": round(total_chunks / processing_time, 2) if processing_time > 0 else 0,
            "artigos_incluidos": [
                "Brasil (geografia, história, cultura)",
                "Inteligência artificial (completo)",
                "Python (linguagem completa)",
                "Ciência de dados (processo completo)",
                "Machine learning (algoritmos e aplicações)"
            ],
            "tamanho_dump": "~25KB XML descomprimido",
            "formato_original": "MediaWiki XML padrão",
            "comparacao": {
                "dump_exemplo": "3 artigos, 3 chunks",
                "dump_expandido": f"{total_articles} artigos, {total_chunks} chunks",
                "crescimento": f"{total_chunks}x mais conteúdo"
            },
            "proximos_passos": [
                "Use GET /estatisticas para ver o crescimento da base",
                "Use POST /buscar para testar busca nos novos artigos detalhados",
                "Compare a qualidade das respostas com mais conteúdo"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao processar dump expandido: {str(e)}")

@router.get("/dumps/verificar-url")
async def verificar_url_dump(url: str):
    try:
        response = requests.head(url, timeout=30)
        if response.status_code == 200:
            content_length = response.headers.get('content-length', '0')
            size_mb = round(int(content_length) / (1024 * 1024), 2) if content_length.isdigit() else 0
            return {
                "url": url,
                "status": "disponível",
                "http_status": response.status_code,
                "size_mb": size_mb,
                "headers": dict(response.headers),
                "recomendacao": "URL válida para download"
            }
        else:
            return {
                "url": url,
                "status": "erro",
                "http_status": response.status_code,
                "erro": f"Status HTTP: {response.status_code}",
                "recomendacao": "Tente uma URL diferente ou data mais antiga"
            }
    except Exception as e:
        return {
            "url": url,
            "status": "erro",
            "erro": str(e),
            "recomendacao": "Verifique a conectividade ou tente URL alternativa"
        }

@router.post("/dumps/simular-download")
async def simular_download_dump():
    try:
        start_time = time.time()
        filename = "ptwiki-simulado-pages-articles.xml.gz"
        filepath = wikipedia_dump_processor.data_dir / filename
        if filepath.exists():
            return {
                "message": "Dump simulado já existe",
                "filename": filename,
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
                "status": "existente",
                "uso": f"Use POST /dumps/processar com filename='{filename}'"
            }
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
  <siteinfo>
    <sitename>Wikipedia Simulada</sitename>
    <dbname>ptwiki_simulado</dbname>
    <base>https://pt.wikipedia.org/wiki/Página_principal</base>
    <generator>Simulador MediaWiki</generator>
  </siteinfo>'''
        artigos_simulados = [
            ("Tecnologia", "A tecnologia é a aplicação de conhecimentos científicos para resolver problemas práticos. Inclui desenvolvimento de ferramentas, máquinas, materiais e processos que facilitam a vida humana. A evolução tecnológica tem sido constante ao longo da história, desde a invenção da roda até a era digital atual."),
            ("História do Brasil", "A história do Brasil começou com a chegada dos primeiros habitantes há milhares de anos. A colonização portuguesa iniciou em 1500 com Pedro Álvares Cabral. O país passou por diversos períodos: colonial, imperial e republicano, cada um com suas características econômicas, sociais e políticas únicas."),
            ("Física", "A física é a ciência que estuda a natureza e seus fenômenos em seus aspectos mais gerais. Analisa matter, energia, movimento, forças, espaço e tempo. Subdivide-se em mecânica, termodinâmica, eletromagnetismo, óptica, física moderna e outras áreas especializadas."),
            ("Matemática", "A matemática é a ciência que lida com lógica de forma quantitativa. Estuda números, estruturas, padrões, relações e mudanças. É fundamental para ciências exatas, engenharia, economia e diversas outras áreas do conhecimento humano."),
            ("Literatura", "A literatura é a arte da palavra escrita. Expressa sentimentos, ideias e experiências humanas através de diferentes gêneros como romance, poesia, drama e ensaio. Reflete cultura, sociedade e época de sua criação."),
            ("Geografia", "A geografia estuda a Terra e seus fenômenos naturais e humanos. Analisa relevo, clima, vegetação, população, economia e organização espacial. Divide-se em geografia física e humana, cada uma com suas especificidades."),
            ("Química", "A química é a ciência que estuda matter e suas transformações. Analisa composição, estrutura, propriedades e comportamento de átomos e moléculas. É essencial para indústria, medicina, agricultura e tecnologia."),
            ("Biologia", "A biologia é a ciência da vida. Estuda organismos vivos, desde microscópicos até complexos. Abrange genética, evolução, ecologia, anatomia, fisiologia e outras áreas relacionadas aos seres vivos."),
            ("Economia", "A economia estuda produção, distribuição e consumo de bens e serviços. Analisa comportamento de mercados, políticas governamentais, desenvolvimento econômico e bem-estar social. É fundamental para tomada de decisões empresariais e públicas."),
            ("Sociologia", "A sociologia estuda society e comportamento social humano. Analisa grupos, instituições, mudanças sociais, desigualdades e interações humanas. Contribui para compreensão de problemas sociais contemporâneos."),
            ("Computação", "A ciência da computação estuda algoritmos, estruturas de dados e sistemas computacionais. É fundamental para desenvolvimento de software, inteligência artificial, análise de dados e automação de processos."),
            ("Engenharia", "A engenharia aplica princípios científicos e matemáticos para projetar, construir e manter estruturas, máquinas e sistemas. Divide-se em diversas especialidades como civil, mecânica, elétrica e outras.")
        ]
        for i, (titulo, conteudo) in enumerate(artigos_simulados, 2000):
            xml_content += f'''
  <page>
    <title>{titulo}</title>
    <ns>0</ns>
    <id>{i}</id>
    <revision>
      <id>{i + 10000}</id>
      <timestamp>2024-10-31T10:00:00Z</timestamp>
      <contributor>
        <username>SimuladorBot</username>
        <id>9999</id>
      </contributor>
      <text bytes="{len(conteudo) * 3}" xml:space="preserve">{conteudo}

== Introdução ==
{conteudo}

== Desenvolvimento ==
{conteudo} Este é um artigo expandido para demonstração do sistema de processamento de dumps da Wikipedia. O conteúdo foi multiplicado para simular artigos maiores e mais complexos que são encontrados em dumps reais.

== História ==
A história de {titulo.lower()} é rica e complexa, envolvendo diversos aspectos culturais, tecnológicos e sociais ao longo dos séculos.

== Características principais ==
* Aspecto 1: Fundamental para compreensão
* Aspecto 2: Influência na sociedade moderna  
* Aspecto 3: Desenvolvimentos recentes
* Aspecto 4: Perspectivas futuras

== Aplicações ==
As aplicações de {titulo.lower()} são vastas e incluem diversos setores da sociedade moderna, desde educação até indústria.

== Referências ==
* Fonte acadêmica simulada 1
* Fonte acadêmica simulada 2
* Fonte acadêmica simulada 3
* Base de dados de referência

== Ver também ==
* [[Artigo relacionado 1]]
* [[Artigo relacionado 2]]
* [[Categoria principal]]

== Ligações externas ==
* Site oficial simulado
* Recurso educacional simulado

[[Categoria:{titulo}]]
[[Categoria:Artigos simulados]]
[[Categoria:Base de conhecimento]]</text>
    </revision>
  </page>'''
        xml_content += '\n</mediawiki>'
        with gzip.open(str(filepath), 'wt', encoding='utf-8') as f:
            f.write(xml_content)
        end_time = time.time()
        file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
        return {
            "message": "Dump simulado criado com sucesso!",
            "tipo": "Simulação de dump real da Wikipedia",
            "filename": filename,
            "size_mb": file_size_mb,
            "total_articles": len(artigos_simulados),
            "creation_time_seconds": round(end_time - start_time, 2),
            "formato": "XML MediaWiki comprimido (gzip)",
            "uso": f"Use POST /dumps/processar com filename='{filename}'",
            "vantagem": "Simula processamento de dump real sem download de centenas de MB",
            "conteudo": [
                f"{len(artigos_simulados)} artigos temáticos diversos",
                "Conteúdo expandido e estruturado para cada artigo", 
                "Estrutura XML MediaWiki completa",
                "Arquivo comprimido como dumps reais",
                "Seções organizadas (Introdução, História, Características, etc.)",
                "Metadados de página e revisão realistas"
            ],
            "proximos_passos": [
                f"1. Processar: POST /dumps/processar (filename={filename})",
                "2. Verificar progresso: GET /dumps/status",
                "3. Buscar conteúdo: POST /buscar (query='tecnologia')",
                "4. Ver estatísticas: GET /stats"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao simular download: {str(e)}")

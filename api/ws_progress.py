from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

@router.websocket("/ws/progresso-pergunta")
async def websocket_progresso_pergunta(websocket: WebSocket):
    await websocket.accept()
    try:
        # Exemplo de etapas do processamento
        etapas = [
            {"status": "Iniciando processamento..."},
            {"status": "Buscando chunks relevantes..."},
            {"status": "Preparando contexto..."},
            {"status": "Chamando LLM..."},
            {"status": "Resposta gerada!"}
        ]
        for etapa in etapas:
            await websocket.send_json(etapa)
            await asyncio.sleep(1)  # Simula tempo de processamento
        await websocket.send_json({"status": "finalizado"})
    except WebSocketDisconnect:
        pass

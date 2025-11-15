
import asyncio
from fastapi import WebSocket, APIRouter


from fastapi import status
from fastapi.responses import JSONResponse

router = APIRouter()

# Fila de telemetria por conexão
telemetria_queues = {}


@router.websocket("/ws/telemetria")
async def websocket_telemetria(websocket: WebSocket):
    print("Nova conexão de telemetria")
    await websocket.accept()
    queue = asyncio.Queue()
    conn_id = id(websocket)
    telemetria_queues[conn_id] = queue
    try:
        while True:
            status = await queue.get()
            await websocket.send_json({"status": status})
    except Exception:
        pass
    finally:
        telemetria_queues.pop(conn_id, None)
        try:
            await websocket.close()
        except Exception:
            pass

# Endpoint HTTP apenas para documentação do WebSocket no Swagger
@router.get("/ws/telemetria", summary="WebSocket Telemetria", response_description="Endpoint WebSocket para telemetria incremental.")
async def docs_telemetria():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Este endpoint é um WebSocket para telemetria incremental. Conecte-se via ws://host:porta/ws/telemetria. Não suporta requisições HTTP."}
    )

async def enviar_telemetria(status: str):
    print("Enviando telemetria:", status)
    # Envia para todas conexões ativas
    for queue in telemetria_queues.values():
        try:
            queue.put_nowait(status)
        except Exception:
            pass
    # Libera o event loop para envio imediato
    import asyncio
    await asyncio.sleep(0)

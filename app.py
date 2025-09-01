from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()
clients = {}  # client_id -> {"ws": ws, "queue": asyncio.Queue()}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: str):
    await ws.accept()
    queue = asyncio.Queue()
    clients[client_id] = {"ws": ws, "queue": queue}
    try:
        while True:
            data = await ws.receive_text()
            # все входящие сообщения кладём в очередь
            await queue.put(data)
    except:
        del clients[client_id]

@app.get("/{client_id}/{path:path}")
async def proxy(client_id: str, path: str):
    client = clients.get(client_id)
    if not client:
        return JSONResponse({"error": "Client not connected"}, status_code=502)

    ws = client["ws"]
    queue = client["queue"]

    # отправляем запрос клиенту
    await ws.send_json({"path": path})

    try:
        # ждём ответа из очереди
        response = await asyncio.wait_for(queue.get(), timeout=10)
        return JSONResponse(json.loads(response))
    except asyncio.TimeoutError:
        return JSONResponse({"error": "Timeout waiting for client"}, status_code=504)

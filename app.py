from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

app = FastAPI()
clients = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: str):
    await ws.accept()
    clients[client_id] = ws
    try:
        while True:
            data = await ws.receive_text()
            print(f"Got from {client_id}: {data}")
    except:
        del clients[client_id]

@app.get("/{client_id}/{path:path}")
async def proxy(client_id: str, path: str):
    ws = clients.get(client_id)
    if not ws:
        return JSONResponse({"error": "Client not connected"}, status_code=502)
    await ws.send_json({"path": path})
    # тут надо дождаться ответа от клиента
    response = await ws.receive_json()
    return JSONResponse(response)

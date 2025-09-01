from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response, JSONResponse
import asyncio, json, base64, uuid, logging
from typing import Dict, Optional

app = FastAPI()


class Client:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        # ожидания ответов по конкретным запросам: req_id -> Future
        self.pending: Dict[str, asyncio.Future] = {}


# один активный клиент
client: Optional[Client] = None


@app.get("/")
async def health():
    return {"ok": True, "client_connected": client is not None}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global client
    await ws.accept()
    client = Client(ws)
    try:
        # читаем из сокета только тут
        while True:
            msg = await ws.receive_text()
            try:
                payload = json.loads(msg)
            except Exception:
                continue
            req_id = payload.get("id")
            if not req_id:
                continue
            fut = client.pending.pop(req_id, None)
            if fut and not fut.done():
                fut.set_result(payload)
    except Exception as e:
        logging.exception("WebSocket closed: %s", e)
    finally:
        client = None


def _filter_resp_headers(headers: Dict[str, str]) -> Dict[str, str]:
    # hop-by-hop заголовки убираем
    drop = {
        "content-length", "transfer-encoding", "connection", "keep-alive",
        "proxy-authenticate", "proxy-authorization", "te", "trailer", "upgrade"
    }
    return {k: v for k, v in headers.items() if k.lower() not in drop}


@app.api_route("/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    global client
    if not client:
        return JSONResponse({"error": "Client not connected"}, status_code=502)

    body_bytes = await request.body()
    req_id = uuid.uuid4().hex

    payload = {
        "id": req_id,
        "path": path,
        "query": request.url.query or "",
        "method": request.method,
        "headers": dict(request.headers),
        "isBase64": True,
        "body": base64.b64encode(body_bytes).decode("ascii"),
    }

    fut: asyncio.Future = asyncio.get_running_loop().create_future()
    client.pending[req_id] = fut

    # отправляем запрос локальному клиенту через WS
    await client.ws.send_text(json.dumps(payload))

    try:
        resp = await asyncio.wait_for(fut, timeout=30)
    except asyncio.TimeoutError:
        client.pending.pop(req_id, None)
        return JSONResponse({"error": "Timeout waiting for client"}, status_code=504)

    status = int(resp.get("status", 200))
    is_b64 = bool(resp.get("isBase64", True))
    resp_body = resp.get("body", "")

    try:
        content = base64.b64decode(resp_body) if is_b64 else (
            resp_body.encode("utf-8") if isinstance(resp_body, str) else bytes(resp_body)
        )
    except Exception:
        content = b""
        status = 502

    headers = _filter_resp_headers(resp.get("headers", {}))
    return Response(content=content, status_code=status, headers=headers)

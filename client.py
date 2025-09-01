import asyncio, websockets, requests, json, base64

# куда прокидываем (Angular dev server, FastAPI и т.д.)
TARGET = "http://localhost:4200"
WS_URL = "wss://test.delightfulsand-56d77f44.eastus.azurecontainerapps.io/ws"  # замени на свой

def _filter_req_headers(h: dict) -> dict:
    drop = {"host", "content-length", "connection", "accept-encoding"}
    return {k: v for k, v in h.items() if k.lower() not in drop}

async def run():
    async with websockets.connect(WS_URL) as ws:
        while True:
            msg = await ws.recv()
            req = json.loads(msg)

            req_id = req["id"]
            path = req.get("path", "")
            query = req.get("query", "")
            method = req.get("method", "GET").upper()
            headers = _filter_req_headers(req.get("headers", {}))

            body_bytes = base64.b64decode(req["body"]) if req.get("isBase64") else (
                req.get("body", "").encode()
            )

            url = f"{TARGET}/{path}"
            if query:
                url += f"?{query}"

            r = requests.request(method, url, headers=headers, data=body_bytes, stream=True)

            resp_payload = {
                "id": req_id,
                "status": r.status_code,
                "headers": dict(r.headers),
                "isBase64": True,
                "body": base64.b64encode(r.content).decode("ascii"),
            }
            await ws.send(json.dumps(resp_payload))

asyncio.run(run())

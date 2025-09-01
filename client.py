import asyncio, websockets, requests, json

async def client():
    async with websockets.connect("wss://test.delightfulsand-56d77f44.eastus.azurecontainerapps.io/ws/dev") as ws:
        print(ws)
        while True:
            msg = await ws.recv()
            req = json.loads(msg)
            url = f"http://localhost:4200/{req['path']}"
            r = requests.get(url)
            await ws.send(json.dumps({"status": r.status_code, "body": r.text}))

asyncio.run(client())

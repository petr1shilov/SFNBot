import asyncio
import json
import websockets

async def main():
    async with websockets.connect("ws://localhost:8000/ws/bot-answer") as ws:
        await ws.send(json.dumps({
            "id_request": "test-3",
            "query": "Что такое самолет",
        }))

        response = await ws.recv()
        print("Response:", response)

asyncio.run(main())

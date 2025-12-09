import json
import logging
from dotenv import load_dotenv
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from base_model import BaseModel
from rag_engine import get_bot_answer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_ws")

app = FastAPI()

auth_key = os.getenv("AUTH_KEY")

base_model = BaseModel(auth_key)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.websocket("/ws/bot-answer")
async def ws_bot_answer(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket connected")

    try:
        while True:
            raw = await ws.receive_text()
            logger.info("Received: %s", raw)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"error": "invalid_json"})
                continue

            id_request = data.get("id_request")
            query = data.get("query")

            if not id_request or not query:
                await ws.send_json({
                    "error": "id_request and query are required",
                    "received": data,
                })
                continue

            answer, used_tokens, chunks_id, latensy  = get_bot_answer(base_model, query)

            await ws.send_json({
                "id_request": id_request,
                "query": query,
                "answer": answer,
                "chunks_id": chunks_id,
                "status": "ok",
                "fallback": False,
                "model": base_model.model,
                "used_tokens": used_tokens,
                "latensy": latensy,
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception("WS error: %s", e)
        try:
            await ws.send_json({"error": str(e)})
        except Exception:
            pass

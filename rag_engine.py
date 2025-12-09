import os
import logging
import time

from vectordb import VectorDBClient
from base_model import BaseModel
from llm_core import ChatLLM
from dotenv import load_dotenv

load_dotenv()  

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

db_path = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"

# db_path = os.getenv("DB_PATH")# сделать из подключения к pgVector 
con_name = os.getenv("COLLECTION_NAME")

rag_engin_logger = logging.getLogger('rag_engin_logger')

if rag_engin_logger.hasHandlers():
    rag_engin_logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(name)s - %(message)s')
handler.setFormatter(formatter)
rag_engin_logger.addHandler(handler)
rag_engin_logger.setLevel(logging.INFO)


def get_bot_answer(base_model: BaseModel, query: str):
    start_time = time.time()

    try:
        client_db = VectorDBClient(base_model, db_path, con_name)
        chat = ChatLLM(base_model)

        db_results = client_db.query(query)
        rag_engin_logger.info(f'db_results: {db_results}')
        metadatas = db_results.get("metadatas", [[]])
        distances = db_results.get("distances", [[]])
        chunks = []
        chunk_ids = []

        for meta, distance in zip(metadatas, distances):
            rag_engin_logger.info("meta: %s, distance: %s", meta, distance)

            if distance <= base_model.faq_threshold:
                faq_answer = meta.get("faq_answer")
                doc_id = meta.get("doc_id")

                if faq_answer:
                    chunks.append(faq_answer)
                if doc_id:
                    chunk_ids.append(doc_id)

        context = "\n".join(chunks)
        rag_engin_logger.info("top_k chunks: %s", context)

        answer, tokens = chat.generate(query, context)

        elapsed = time.perf_counter() - start_time
        return answer, tokens, chunk_ids, elapsed

    except Exception as err:
        rag_engin_logger.exception("get_bot_answer failed: %s", err)
        # Важно: возвращаем кортеж той же структуры, чтобы не ломать вызывающий код
        elapsed = time.perf_counter() - start_time
        return f"error {err}", None, [], elapsed
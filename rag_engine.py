import os
import logging

from vectordb import VectorDBClient
from base_model import BaseModel
from llm_core import ChatLLM
from dotenv import load_dotenv

load_dotenv()  

db_path = os.getenv("DB_PATH")
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

    try:
        client_db = VectorDBClient(base_model, db_path, con_name)
        chat = ChatLLM(base_model)

        db_results = client_db.query(query)

<<<<<<< HEAD
        rag_engin_logger.info(f'db_results: {db_results}')

=======
>>>>>>> 0df95b76a3a0a30f0a5f2c72e110bb6cc0e9b907
        metadatas = db_results.get("metadatas", [[]])[0]
        distances = db_results.get("distances", [[]])[0]
        chunks = []

        # for idx, distanse in enumerate(distances):
        #     if distanse <= base_model.faq_threshold and metadatas[idx].get('section') == 'FAQ':
        #         if idx == 0:
        #             return metadatas[idx].get('faq_answer')
        #     elif metadatas[idx].get('section') != 'FAQ' and distanse <= base_model.rag_threshold:
        #             chunks.append(metadatas[idx].get('faq_answer'))

        for idx, distanse in enumerate(distances):
            print(metadatas[idx])
            if distanse <= base_model.faq_threshold:
                    chunks.append(metadatas[idx].get('faq_answer'))

        chunks = '\n'.join(chunks)

        rag_engin_logger.info(f'top_k chunks: {chunks}')

        return chat.generate(query, chunks)
        
    except Exception as err:
        return f"error {err}"
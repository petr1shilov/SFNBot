from langchain_community.vectorstores import PGVector
from langchain_community.vectorstores.pgvector import DistanceStrategy
from langchain_community.embeddings import FakeEmbeddings

from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, text

import json
from tqdm import tqdm
import uuid
from base_model import BaseModel

from typing import List, Dict, Any, Optional


class VectorDBClient:
    def __init__(self, base_model: BaseModel, path: str, collection_name: str):
        self.base_model = base_model
        self.embedder_model = base_model.embedder_model
        self.client = PGVector(
            connection_string=path,
            embedding_function=self.base_model.embedder_model,
            collection_name=collection_name,
            distance_strategy=DistanceStrategy.COSINE, 
            use_jsonb=True,
        )

    def add_documents(self, jsonl_path):
        ids, texts, metadatas, embeddings = [], [], [], []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in tqdm(enumerate(lines), total=len(lines), desc="Добавление в ChromaDB"):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"Строка {i} невалидна, пропускаю")
                continue

            section = entry.get("section", "")
            source = entry.get("source", "")

            if section == "FAQ":
                question = entry.get("original_question")
                answer = entry.get("text")
            else:
                question = entry.get("text")
                answer = entry.get("text")

            if not question:
                print(f"Нет текста в строке {i}, пропускаю")
                continue

            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            texts.append(question)
            metadatas.append({
                "source": source,
                "section": section,
                "faq_answer": answer,
                "doc_id": doc_id
            })

        self.client.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

        print("Данные загружены в VBD.")

    def update_document(
            self,
            custom_id: str,
            new_text: str,
            new_metadata: Optional[Dict[str, Any]] = None,
        ) -> None:
        """
        update с тем же custom_id.
        """
        self.client.delete(ids=[custom_id], collection_only=True)

        self.client.add_texts(
            texts=[new_text],
            metadatas=[new_metadata or {}],
            ids=[custom_id],
        )

    def delete_documents(self, ids: List[str]) -> None:
        """
        delete по custom_id
        """
        self.client.delete(ids=ids, collection_only=True)

    def query(self, query, top_k=3):
        origin_qestions = []
        metadatas = []
        distances = []

        if not query.startswith("query:"):
            query = f"query: {query}"

        results = self.client.similarity_search_with_score(query, k=top_k)

        for doc, distance in results:
            origin_qestions.append(doc.page_content)
            metadatas.append(doc.metadata)
            distances.append(distance)
            # pritn("ORIG_QUESTION=%s METADATA=%s DISTANCE=%s", doc.page_content, doc.metadata, distance)


        query_result = {
            "origin_qestions": origin_qestions,
            "metadatas": metadatas,
            "distances": distances,
        }

        return query_result
    
    def delete_collection(self, db_path: str, collection_name: str):
        """
        Удаление всего подключения по названию
        """
        store = PGVector(
            connection_string=db_path,
            embedding_function=FakeEmbeddings(size=10),
            collection_name=collection_name
        )
        store.delete_collection()

        print(f'Подключение {collection_name} удалено')

    def check_connection(self, db_path: str):
        engine = create_engine(db_path)

        with engine.connect() as conn:
            sql_result = conn.execute(text("""
                SELECT name
                FROM langchain_pg_collection
                ORDER BY name;
            """))
            result = f"Collections in PGVector:\n\n"
            for row in sql_result:
                result += f"- {row.name}\n"
        
        return result




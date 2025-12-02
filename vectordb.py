import chromadb
import json
from tqdm import tqdm
import uuid
from base_model import BaseModel

class VectorDBClient:
    def __init__(self, base_model: BaseModel, path: str, collection_name: str):
        self.base_model = base_model
        self.embedder_model = base_model.embedder_model
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(collection_name)

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

            embedding = self.embedder_model.encode(question).tolist()

            ids.append(str(uuid.uuid4()))
            texts.append(question)
            metadatas.append({
                "source": source,
                "section": section,
                "faq_answer": answer
            })
            embeddings.append(embedding)
    
        self.collection.add(
            ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings
        )

        print("Данные загружены в ChromaDB.")

    def query(self, query, top_k=3):
        query_emb = self.embedder_model.encode("query: " + query).tolist()

        # Ищем ближайшие документы в векторной базе
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k  
        )

        return results




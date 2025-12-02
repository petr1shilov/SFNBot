from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from sentence_transformers import SentenceTransformer
import logging

base_model_logger = logging.getLogger('base_model_logger')

if base_model_logger.hasHandlers():
    base_model_logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(name)s - %(message)s')
handler.setFormatter(formatter)
base_model_logger.addHandler(handler)
base_model_logger.setLevel(logging.INFO)


class BaseModel:
    def __init__(
        self,
        api_key: str,
        model: str = 'giga',
        faq_threshold: float = 0.34,
        rag_threshold: float = 0.34,
        temperature: float = 0.4,
        top_k: int = 3,
        embedder: str = 'intfloat/e5-base-v2'
    ):
        self.api_key = api_key
        self.model = model
        self.faq_threshold = faq_threshold
        self.rag_threshold = rag_threshold
        self.temperature = temperature
        self.top_k = top_k
        self.embedder = embedder

        self.self_host_llm = self._load_llm()
        self.tokenizer = self._load_tokenizer()
        self.embedder_model = self._load_embedder()

    def _load_llm(self):
        base_model_logger.info(f"Загружаю LLM: {self.model}")
        if self.model == 'giga':
            return None
        else:
            return AutoModelForCausalLM.from_pretrained(self.model)
        
    def _load_tokenizer(self):
        base_model_logger.info(f"Загружаю Токинайзер: {self.model}")
        if self.model == 'giga':
            return None
        else:
            return AutoTokenizer.from_pretrained(self.model)

    def _load_embedder(self):
        base_model_logger.info(f"Загружаю эмбеддер: {self.embedder}")
        try:
            model = SentenceTransformer(self.embedder)
            return model
        except Exception as e:
            base_model_logger.info(f"Не удалось загрузить эмбеддер: {e}")
            return None

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if 'model' in kwargs:
            self.llm = self._load_llm()
            self.tokenizer = self._load_tokenizer()
        if 'embedder' in kwargs:
            self.embedder_model = self._load_embedder()
    
    def show_params(self):
        params = "\n".join([
            f'Языковая модель: {self.model}',
            f'Порог отбора чанков: {self.rag_threshold}',
            f'Порог отбора FAQ чанков: {self.faq_threshold}',
            f'Температура модели: {self.temperature}',
            f'Количество чанков: {self.top_k}',
            f'Модель эмбеддера: {self.embedder}',
        ])
        
        return params


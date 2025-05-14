import requests
import uuid
import json
import logging

from base_model import BaseModel

llm_core_logger = logging.getLogger('llm_core_logger')

if llm_core_logger.hasHandlers():
    llm_core_logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(name)s - %(message)s')
handler.setFormatter(formatter)
llm_core_logger.addHandler(handler)
llm_core_logger.setLevel(logging.INFO)

class ChatLLM:
    def __init__(self, base_model: BaseModel):
        self.base_model = base_model
        self.api_key = base_model.api_key
        self.model = base_model.model
        self.temperature = base_model.temperature
        self.top_k = base_model.top_k

        self.self_host_llm = base_model.self_host_llm
        self.tokenizer = base_model.tokenizer
        
    def generate(self, query: str, chunks: str) -> str:
        if self.model == 'giga':
            return self._generate_gigachat(query, chunks)
        elif self.model == 'local':
            return self._generate_local(query)
        else:
            llm_core_logger.info(f"Неизвестная модель: {self.model}")

    def get_token(self, scope="GIGACHAT_API_PERS"):
        """
        Выполняет POST-запрос к эндпоинту, который выдает токен.

        Параметры:
        - auth_token (str): токен авторизации, необходимый для запроса.
        - область (str): область действия запроса API. По умолчанию — «GIGACHAT_API_PERS».

        Возвращает:
        - ответ API, где токен и срок его "годности".
        """
        # Создадим идентификатор UUID (36 знаков)
        rq_uid = str(uuid.uuid4())

        # API URL
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        # Заголовки
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self.api_key}",
        }

        # Тело запроса
        payload = {"scope": scope}

        try:
            # Делаем POST запрос с отключенной SSL верификацией
            # (можно скачать сертификаты Минцифры, тогда отключать проверку не надо)
            response = requests.post(url, headers=headers, data=payload, verify=False)
            return response
        except requests.RequestException as e:
            llm_core_logger.info(f"Ошибка: {str(e)}")
            return -1

    def get_chat_completion(self, giga_token, user_message, chunks):
        """
        Отправляет POST-запрос к API чата для получения ответа от модели GigaChat.

        Параметры:
        - auth_token (str): Токен для авторизации в API.
        - user_message (str): Сообщение от пользователя, для которого нужно получить ответ.

        Возвращает:
        - str: Ответ от API в виде текстовой строки.
        """
        # URL API, к которому мы обращаемся
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

        # Подготовка данных запроса в формате JSON
        payload = json.dumps(
            {
                "model": "GigaChat-Pro",  # Используемая модель
                "messages": [
                    {
                        "role": "system",
                        "content": (
                                        "Ты бот помощьник комнапии ООО «СФН»\n"
                                        "Будь приветлив и дружелюбен"
                                        "Твоя задача коротко и четко отвечать на вопросы пользователя основываясь на информации ниже:\n"
                                        f"{chunks}\n"
                                        "Не пиши информацию не относящуюся к вопросу пользователя\n"
                                        "Отвечай только по факту на заданный вопрос от пользователя"
                                    )},
                    {
                        "role": "user",  # Роль отправителя (пользователь)
                        "content": user_message,  # Содержание сообщения
                    }
                ],
                "temperature": self.temperature,  # Температура генерации
                "top_p": 0.1,  # Параметр top_p для контроля разнообразия ответов
                "n": 1,  # Количество возвращаемых ответов
                "stream": False,  # Потоковая ли передача ответов
                "max_tokens": 512,  # Максимальное количество токенов в ответе
                "repetition_penalty": 1,  # Штраф за повторения
                "update_interval": 0,  # Интервал обновления (для потоковой передачи)
            }
        )

        # Заголовки запроса
        headers = {
            "Content-Type": "application/json",  # Тип содержимого - JSON
            "Accept": "application/json",  # Принимаем ответ в формате JSON
            "Authorization": f"Bearer {giga_token}",  # Токен авторизации
        }

        # Выполнение POST-запроса и возвращение ответа
        try:
            response = requests.request(
                "POST", url, headers=headers, data=payload, verify=False
            )
            return response
        except requests.RequestException as e:
            # Обработка исключения в случае ошибки запроса
            llm_core_logger.info(f"Произошла ошибка: {str(e)}")
            return -1

    def _generate_gigachat(self, query: str, chunks: str) -> str:
        response = self.get_token()
        if response != -1:
            giga_token = response.json()["access_token"]
        answer = self.get_chat_completion(giga_token, query, chunks)
        llm_response = str(
                    answer.json()["choices"][0]["message"]["content"]
                )
        return llm_response

    def _generate_local(self):
        tokenizer = self.tokenizer
        prompt = (
            "[INST] Используй следующий факт, чтобы кратко ответить на вопрос и не придумывай свое.\n"
            "Факт: Екатерина Черных — генеральный директор.\n"
            "Вопрос: кто такая Екатерина Черных? [/INST]"
        )

        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=50,
            eos_token_id= self.tokenizer.eos_token_id 
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)


    
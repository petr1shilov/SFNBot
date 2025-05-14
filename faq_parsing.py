from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import json
from pathlib import Path
import nltk
from nltk.tokenize.punkt import PunktSentenceTokenizer

nltk.download("punkt")

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def split_by_sentences(text, max_words=100):
    tokenizer = PunktSentenceTokenizer()
    sentences = tokenizer.tokenize(text)

    chunks, current, count = [], [], 0
    for sentence in sentences:
        words = sentence.split()
        if count + len(words) > max_words and current:
            chunks.append(" ".join(current))
            current, count = [], 0
        current.extend(words)
        count += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks

# Настройка Selenium
options = Options()
options.add_argument("--headless")  # без окна браузера
driver = webdriver.Chrome(options=options)

FAQ_URL = "https://sfn-am.ru/company/faq"
SECTION = "FAQ"
print(f"📄 Загружаем раздел: {SECTION} → {FAQ_URL}")

driver.get(FAQ_URL)
time.sleep(5)  # ожидание JS

faq_items = driver.find_elements(By.CSS_SELECTOR, "div.accordion-item")
print(f"Найдено блоков FAQ: {len(faq_items)}")

results = []

for item in faq_items:
    try:
        question_el = item.find_element(By.CSS_SELECTOR, "button.accordion-button span")
        question_text = clean_text(question_el.text)

        # Клик для раскрытия
        driver.execute_script("arguments[0].click();", item.find_element(By.CSS_SELECTOR, "button.accordion-button"))
        time.sleep(0.3)

        answer_parts = item.find_elements(By.CSS_SELECTOR, "div.accordion-body p")
        answer_full = ' '.join([clean_text(p.text) for p in answer_parts if p.text.strip()])

        # for chunk in split_by_sentences(answer_full):
        #     results.append({
        #         "text": chunk,
        #         "source": FAQ_URL,
        #         "section": SECTION,
        #         "original_question": question_text
        #     })
        results.append({
                "text": answer_full,
                "source": FAQ_URL,
                "section": SECTION,
                "original_question": 'FAQ: ' + question_text + answer_full[: 100]
            })

    except Exception as e:
        print(f"❌ Ошибка обработки элемента: {e}")

driver.quit()

# Сохраняем результат
output_file = Path("parsed_faq.jsonl")
with output_file.open("w", encoding="utf-8") as f:
    for item in results:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\n✅ Сохранено {len(results)} чанков в {output_file.absolute()}")

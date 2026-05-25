import torch
import sounddevice as sd
import speech_recognition as sr
import numpy as np
import random
import re
import threading
import time
import ollama
import emoji

# ========== ФУНКЦИЯ ОЧИСТКИ ТЕКСТА ==========

def clean_text_for_llm(text):
    """
    Очищает текст перед отправкой в нейросеть:
    - Удаляет эмодзи
    - Удаляет управляющие символы (нулевые ширины, невидимые)
    - Удаляет лишние пробелы
    - Убирает специальные символы
    """
    if not text:
        return text
    
    # 1. Удаляем эмодзи через библиотеку emoji
    text = emoji.replace_emoji(text, replace='')
    
    # 2. Удаляем управляющие символы (нулевой ширины, невидимые и т.д.)
    text = re.sub(r'[\u200b\u200c\u200d\u2060\uFEFF\u0000-\u001F\u007F-\u009F]', '', text)
    
    # 3. Удаляем лишние пробелы, табуляции, множественные переносы строк
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 4. Удаляем специальные символы, оставляя буквы, цифры, знаки препинания
    #    (русские и английские буквы, цифры, пробелы, . , ! ? -)
    text = re.sub(r'[^а-яА-Яa-zA-Z0-9\s.,!?\-:;()\'\"]+', '', text)
    
    return text

# ========== ИНИЦИАЛИЗАЦИЯ ==========

# Загружаем модель Silero для TTS
print("Загрузка голосовой модели...")
device = torch.device('cpu')
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru', speaker='v5_ru')
model.to(device)
print("✓ Голосовая модель загружена")

# Настройки голосов
VOICES = {
    'chuchu': {
        'speaker': 'baya',
        'name': 'Чу Чу',
        'age': 18
    },
    'mei': {
        'speaker': 'xenia',
        'name': 'Мэй',
        'age': 22
    }
}

# Имя модели Qwen (должна быть скачана через ollama run ...)
QWEN_MODEL = 'hf.co/RefalMachine/ruadapt_qwen2.5_7B_ext_u48_instruct_gguf:Q4_K_M'

# Системный промпт для Qwen (нейтральная версия)
QWEN_SYSTEM_PROMPT = """Ты — голосовой помощник в образе двух девушек: Чу Чу и Мэй. Отвечай на русском языке, коротко (2-4 предложения), вежливо и дружелюбно.

Характеры:
- **Чу Чу**: 18 лет, косплей-модель. Голос тонкий, детский. Обожает косплей, творчество, любит создавать образы. Говорит прямо, только правду, без слов-паразитов. Дружелюбная, позитивная.
- **Мэй**: 22 года, крафтерша снаряжения для косплея. Голос спокойный, юношеский. Заботливая, ответственная, любит помогать другим.

Правила:
1. Если пользователь обращается к Чу Чу — отвечай от лица Чу Чу.
2. Если к Мэй — отвечай от лица Мэй.
3. Если к обеим ("девочки") — отвечай от обеих: первое предложение от Чу Чу, второе — от Мэй.
4. Если имя не указано — отвечай как Чу Чу.
5. Будь вежливой, дружелюбной, но профессиональной. Без флирта, игривых намёков и откровенных тем.
6. Если пользователь говорит "пока" или "выход" — коротко попрощайся."""

# Реакции на разные обращения (нейтральные)
REACTIONS = {
    'chuchu': [
        "Да, я здесь. Чем могу помочь?",
        "Чу Чу слушает. Что ты хотел?",
        "Привет! Рада тебя слышать.",
        "Я здесь. Задавай свой вопрос."
    ],
    'mei': [
        "Я здесь. Что случилось?",
        "Мэй слушает. Говори.",
        "Да, я рядом.",
        "Привет, я Мэй. Чем помочь?"
    ],
    'both': [
        "Мы здесь. Что ты хотел?",
        "Обе слушаем. Говори.",
        "Чу Чу и Мэй готовы помочь."
    ]
}

# Хоровые ответы (нейтральные)
CHORUS_RESPONSES = [
    ('chuchu', "Мы здесь!"),
    ('mei', "Обе слушаем!"),
    ('chuchu', "Да!"),
    ('mei', "Конечно!"),
    ('chuchu', "Мы тебя слышим!"),
    ('mei', "Говори смелее."),
    ('chuchu', "Привет!"),
    ('mei', "Здравствуй!"),
    ('chuchu', "У нас всё отлично!"),
    ('mei', "А у тебя как?"),
    ('chuchu', "Мы рады тебе!"),
    ('mei', "Всегда готовы помочь!"),
]

FUNNY_CHORUS = [
    ('chuchu', "Мы думаем..."),
    ('mei', "Думаем..."),
    ('chuchu', "Думаем одинаково!"),
    ('chuchu', "Спорим?"),
    ('mei', "Нет!"),
    ('chuchu', "Мы согласны!"),
    ('chuchu', "Давай спросим у Мэй?"),
    ('mei', "А я спрошу у Чу Чу!"),
    ('chuchu', "Мы одинакового мнения!"),
]

# Варианты имен для распознавания
CHUCHU_NAMES = [
    'чу чу', 'чу-чу', 'чучу', 'чу', 'чучу', 'чу чучу',
    'Чу Чу', 'Чу-Чу', 'Чучу', 'чуч', 'тютю', 'чючю'
]

MEI_NAMES = [
    'мэй', 'мей', 'май', 'ме', 'мая', 'мэ', 'мэя', 'майя',
    'Мэй', 'Мей', 'Май', 'мээ', 'мэйя'
]

BOTH_NAMES = [
    'девочки', 'девчата', 'девченки', 'подружки', 'милые', 'любимые',
    'сестры', 'девушки', 'красавицы', 'леди', 'дамы', 'обе', 'вы обе',
    'обеми', 'с обеими', 'вас', 'вам', 'вами', 'ваши',
    'у вас', 'к вам', 'с вами', 'о вас', 'ваше', 'вашей', 'вашим'
]

# Переменные
last_speaker = 'chuchu'

# ========== ФУНКЦИИ ==========

def match_name(text, names):
    """Проверяет, содержится ли любое из имен в тексте"""
    text = text.lower()
    for name in names:
        if name.lower() in text:
            return True
    return False

def extract_name(text):
    """Определяет, к кому обратились"""
    text = text.lower()
    
    if match_name(text, CHUCHU_NAMES):
        return 'chuchu'
    elif match_name(text, MEI_NAMES):
        return 'mei'
    elif match_name(text, BOTH_NAMES):
        return 'both'
    else:
        return None

def extract_message(text):
    """Извлекает сообщение после обращения"""
    cleaned = text.lower()
    
    for name in CHUCHU_NAMES + MEI_NAMES + BOTH_NAMES:
        cleaned = re.sub(r'\b' + re.escape(name.lower()) + r'\b', '', cleaned)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else None

def speak(text, voice='chuchu'):
    """Озвучка текста"""
    global last_speaker
    voice_config = VOICES[voice]
    print(f"\n[{voice_config['name']}]: {text}")
    last_speaker = voice
    
    try:
        audio = model.apply_tts(
            text=text,
            speaker=voice_config['speaker'],
            sample_rate=48000
        )
        audio_np = audio.cpu().numpy()
        sd.play(audio_np, 48000)
        sd.wait()
    except Exception as e:
        print(f"Ошибка озвучки: {e}")

def speak_chorus():
    """Хоровой ответ (по очереди)"""
    print("\n🎭 [Хором]")
    chorus = random.choice(CHORUS_RESPONSES + FUNNY_CHORUS)
    
    for item in chorus:
        if len(item) == 2:
            voice, text = item
        else:
            voice = item[0]
            text = item[1]
        speak(text, voice)
        time.sleep(0.3)

def random_reaction(person):
    """Случайная реакция на обращение"""
    if person == 'chuchu':
        return random.choice(REACTIONS['chuchu'])
    elif person == 'mei':
        return random.choice(REACTIONS['mei'])
    else:
        return random.choice(REACTIONS['both'])

def should_chorus():
    """Определяет, нужно ли ответить хором"""
    return random.random() < 0.15

def ai_respond(text, persona='chuchu'):
    """
    Отправляет запрос в локальную модель Qwen через Ollama
    """
    try:
        # Очищаем текст перед отправкой в модель
        text = clean_text_for_llm(text)
        
        # Определяем персонажа для ответа
        if persona == 'both':
            persona_desc = "Ты должен ответить от лица обеих девушек. Сначала ответь от лица Чу Чу, затем от лица Мэй. Отметь реплики как 'Чу Чу:' и 'Мэй:'"
        elif persona == 'chuchu':
            persona_desc = "Ты — Чу Чу. Отвечай от её имени."
        else:
            persona_desc = "Ты — Мэй. Отвечай от её имени."
        
        prompt = f"{QWEN_SYSTEM_PROMPT}\n\n{persona_desc}\n\nПользователь сказал: {text}\n\nТвой ответ:"
        
        response = ollama.generate(
            model=QWEN_MODEL,
            prompt=prompt,
            options={
                'num_predict': 150,
                'temperature': 0.8,
                'top_p': 0.9,
                'stop': ["\n\n", "Пользователь:", "User:"],
            }
        )
        
        answer = response['response'].strip()
        # Очищаем ответ от возможных эмодзи
        answer = clean_text_for_llm(answer)
        return answer
        
    except ollama.ResponseError as e:
        print(f"\n[Ошибка Ollama]: {e.error}")
        return "Кажется, модель не отвечает. Проверь, запущен ли Ollama."
    except Exception as e:
        print(f"\n[Ошибка]: {e}")
        return "У меня небольшая техническая проблема. Попробуй ещё раз."

def dialogue():
    """Диалог сестер (через ИИ для разнообразия)"""
    speak("Мэй, как тебе сегодняшний день?", 'chuchu')
    time.sleep(0.5)
    response = ai_respond("Ответь сестре, как прошёл день, коротко и мило.", 'mei')
    speak(response, 'mei')
    time.sleep(0.5)
    response = ai_respond("Ответь Мэй, что ты рада, что она рядом.", 'chuchu')
    speak(response, 'chuchu')

def intro():
    """Представление"""
    print("\n" + "="*50)
    print("🎀 Голосовой помощник Girls-AI 🎀")
    print("="*50)
    print("Говорите в микрофон:")
    print("  • 'Чу Чу, привет' - Чу Чу ответит")
    print("  • 'Мэй, как дела' - Мэй ответит")
    print("  • 'Девочки, привет' - ответят вместе")
    print("  • 'хором' - Чу Чу и Мэй скажут что-то вместе")
    print("  • 'диалог' - сестры поговорят")
    print("  • 'пока' - выход")
    print("="*50)
    print("\n🧠 Используется нейросеть Qwen 2.5-7B (локально, без интернета)")
    print("🎤 Девочки иногда отвечают хором")
    print("="*50 + "\n")
    
    speak("Привет! Я Чу Чу, мне восемнадцать лет, я косплей-модель.", 'chuchu')
    time.sleep(0.8)
    speak("Здравствуйте. Я Мэй, мне двадцать два года, я создаю снаряжение для косплея.", 'mei')
    time.sleep(0.5)
    
    print("\n🎭 [Хором]")
    speak("Мы здесь!", 'chuchu')
    time.sleep(0.3)
    speak("Обе здесь!", 'mei')
    time.sleep(0.3)
    speak("Говори с нами, мы ответим!", 'chuchu')

def process_command(text):
    """Обрабатывает голосовую команду с использованием ИИ"""
    global last_speaker
    
    if not text:
        return True
    
    # Очищаем текст от эмодзи перед обработкой
    text = clean_text_for_llm(text)
    print(f"Обработка: {text}")
    
    # Специальные команды
    if "диалог" in text or "поговорите" in text:
        dialogue()
        return True
    
    if "хором" in text or "вместе" in text or "обе" in text:
        speak_chorus()
        return True
    
    if any(word in text for word in ["пока", "выход", "до свидания", "стоп"]):
        speak("Пока-пока! Приходи еще, мы будем скучать!", 'chuchu')
        return False
    
    # Простые приветствия без имени (можно быстро ответить без ИИ)
    if ("привет" in text or "здравствуй" in text) and not extract_name(text):
        if should_chorus():
            speak_chorus()
        else:
            responses = {
                'chuchu': ["Привет-привет!", "Здравствуй!", "Привет!"],
                'mei': ["Здравствуйте.", "Привет.", "Добрый день."]
            }
            speak(random.choice(responses.get(last_speaker, responses['chuchu'])), last_speaker)
        return True
    
    # Определяем к кому обратились
    person = extract_name(text)
    
    # Отправляем запрос в ИИ
    if person == 'both':
        response = ai_respond(text, 'both')
        # Пытаемся разделить хоровой ответ
        if 'Чу Чу:' in response and 'Мэй:' in response:
            lines = response.split('\n')
            for line in lines:
                if 'Чу Чу:' in line:
                    speak(line.replace('Чу Чу:', '').strip(), 'chuchu')
                elif 'Мэй:' in line:
                    speak(line.replace('Мэй:', '').strip(), 'mei')
                time.sleep(0.3)
        else:
            speak(response, random.choice(['chuchu', 'mei']))
    elif person:
        response = ai_respond(text, person)
        speak(response, person)
    else:
        # Без имени — отвечает последний говоривший
        response = ai_respond(text, last_speaker)
        speak(response, last_speaker)
    
    return True

# ========== ИНИЦИАЛИЗАЦИЯ МИКРОФОНА ==========

recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("Калибровка микрофона...")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    recognizer.energy_threshold = 300
print("✓ Микрофон готов\n")

def listen():
    """Слушает микрофон и очищает текст от эмодзи"""
    try:
        with microphone as source:
            print("\n🎤 Слушаю...", end="", flush=True)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            print("\r🔍 Распознаю...", end="", flush=True)
            
        text = recognizer.recognize_google(audio, language="ru-RU")
        # Очищаем текст от эмодзи и спецсимволов
        text = clean_text_for_llm(text)
        print(f"\r💬 Вы сказали: {text}")
        return text.lower()
    except sr.WaitTimeoutError:
        print("\r⏰ Тишина...", end="", flush=True)
        return ""
    except sr.UnknownValueError:
        print("\r🤔 Не расслышала...", end="", flush=True)
        return ""
    except sr.RequestError:
        print("\r🌐 Ошибка соединения...", end="", flush=True)
        return ""

# ========== ЗАПУСК ==========

def main():
    # Проверяем, доступна ли модель Qwen
    print("Проверка доступности Qwen модели...")
    try:
        ollama.generate(model=QWEN_MODEL, prompt="Привет", options={'num_predict': 5})
        print("✓ Qwen модель готова к работе\n")
    except Exception as e:
        print(f"⚠ Qwen модель не найдена! Запустите: ollama run {QWEN_MODEL}")
        print("Пока буду отвечать только заготовленными фразами.\n")
    
    intro()
    
    try:
        while True:
            command = listen()
            if not process_command(command):
                break
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена")

if __name__ == "__main__":
    main()
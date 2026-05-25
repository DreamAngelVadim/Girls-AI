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
from autocorrect import Speller
import sys
sys.path.append('C:\\Girls-AI\\Girls')
from replacements import apply_replacements, fix_before_spell
spell = Speller('ru')

# ========== ПЕРЕМЕННЫЕ ДЛЯ IDLE ДИАЛОГОВ ==========
idle_timer = None
is_speaking = False
is_idle_dialog_active = False  # Флаг активного фонового диалога
user_heard = False
listening_active = True
last_speaker = 'chuchu'

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
QWEN_SYSTEM_PROMPT = """Ты — голосовой помощник. Отвечай от лица персонажа, но НЕ ПИШИ имя персонажа в ответе.

ВАЖНЕЙШЕЕ ПРАВИЛО: Твой ответ должен начинаться СРАЗУ с текста. Никогда не пиши "Чу Чу:", "Мэй:", "Чу Чху:" или что-то подобное. Просто говори текст.

Пример правильного ответа: "Привет! Как дела?"
Пример НЕПРАВИЛЬНОГО ответа: "Чу Чу: Привет! Как дела?"

Ты отвечаешь от лица:
- Если пользователь обращается к Чу Чу или не указал имя — отвечай как Чу Чу (18 лет, косплей-модель, милая и дружелюбная)
- Если к Мэй — как Мэй (22 года, крафтерша, спокойная и заботливая)
- Если к обеим — сначала ответь как Чу Чу, потом как Мэй

Будь вежливой и дружелюбной. Отвечай коротко (2-4 предложения)."""

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
    'Чу Чу', 'Чу-Чу', 'Чучu', 'чуч', 'тютю', 'чючю'
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
    global last_speaker, is_speaking, is_idle_dialog_active
    voice_config = VOICES[voice]
    
    is_speaking = True
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
    finally:
        is_speaking = False
        # После окончания разговора микрофон снова доступен

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

def clean_model_response(text, requested_persona):
    """
    Очищает ответ модели от лишних имен и исправляет опечатки
    """
    if not text:
        return text
    
    # Убираем любые варианты имени Чу Чу в начале строки
    text = re.sub(r'^\s*(Чу Чху|Чу Чу|Чучу|Чу-Чу|чу чу|чучу)[:\s]*', '', text, flags=re.IGNORECASE)
    
    # Убираем любые варианты имени Мэй в начале строки
    text = re.sub(r'^\s*(Мэй|Мей|Май|мэй|мей)[:\s]*', '', text, flags=re.IGNORECASE)
    
    # Исправляем опечатки в имени Чу Чу
    text = re.sub(r'Чу Чху', 'Чу Чу', text, flags=re.IGNORECASE)
    text = re.sub(r'Чучу', 'Чу Чу', text, flags=re.IGNORECASE)
    
    # Исправляем опечатки в имени Мэй
    text = re.sub(r'Мей', 'Мэй', text, flags=re.IGNORECASE)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Если после очистки текст пустой
    if not text or len(text) < 2:
        if requested_persona == 'mei':
            return "Да, я слушаю."
        else:
            return "Я тебя слышу."
    
    return text

def ai_respond(text, persona='chuchu'):
    try:
        text = clean_text_for_llm(text)
        
        # Определяем персонажа
        if persona == 'both':
            persona_desc = "Ты отвечаешь от лица обеих: сначала как Чу Чу, потом как Мэй. НЕ ПИШИ имена в ответе."
        elif persona == 'chuchu':
            persona_desc = "Ты отвечаешь как Чу Чу. НЕ ПИШИ 'Чу Чу:' в ответе."
        else:
            persona_desc = "Ты отвечаешь как Мэй. НЕ ПИШИ 'Мэй:' в ответе."
        
        prompt = f"{QWEN_SYSTEM_PROMPT}\n\n{persona_desc}\n\nПользователь: {text}\n\nТвой ответ (просто текст, без имени персонажа):"
        
        response = ollama.generate(
            model=QWEN_MODEL,
            prompt=prompt,
            options={
                'num_predict': 150,
                'temperature': 0.7,
                'top_p': 0.9,
                'stop': ["\n\n", "Пользователь:", "User:", "Чу Чу:", "Мэй:", "Чу Чху:"],
            }
        )
        
        answer = response['response'].strip()
        answer = clean_model_response(answer, persona)
        answer = clean_text_for_llm(answer)
        
        # Финальная проверка на случай, если имя всё же проскочило
        if answer.startswith(('Чу', 'Мэй', 'чу', 'мэй')):
            answer = re.sub(r'^[А-Яа-я]+\s*[А-Яа-я]*[:]?\s*', '', answer)
            answer = answer.strip()
        
        if not answer:
            return "Поняла. Продолжим разговор."
        
        return answer
        
    except ollama.ResponseError as e:
        print(f"\n[Ошибка Ollama]: {e.error}")
        return "Кажется, модель не отвечает."
    except Exception as e:
        print(f"\n[Ошибка]: {e}")
        return "У меня небольшая проблема. Попробуй ещё раз."

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
    print("💭 Через 30-60 секунд тишины начнутся фоновые диалоги")
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

# ========== ФУНКЦИИ ДЛЯ IDLE ДИАЛОГОВ ==========

def reset_user_heard():
    """Сбрасывает флаг user_heard через паузу"""
    global user_heard
    time.sleep(15)
    user_heard = False

def start_idle_timer():
    """Запускает таймер для фоновых диалогов"""
    global idle_timer, is_idle_dialog_active
    
    def timer_callback():
        global idle_timer, user_heard, is_speaking, is_idle_dialog_active, listening_active
        
        if not is_speaking and not user_heard and not is_idle_dialog_active:
            is_idle_dialog_active = True
            print("\n💭 [Фоновый диалог] (микрофон отключён)")
            
            # Простой встроенный диалог
            speak("Мэй, как спалось?", 'chuchu')
            time.sleep(0.8)
            speak("Отлично, сестра. А у тебя?", 'mei')
            time.sleep(0.8)
            speak("Тоже хорошо. Солнце сегодня такое тёплое.", 'chuchu')
            time.sleep(0.8)
            speak("Да, приятный день.", 'mei')
            
            # Ждём 2 секунды после окончания диалога
            print("\n⏳ [Ожидание 2 секунды, чтобы звук утих]")
            time.sleep(2)
            
            print("\n🎤 [Микрофон снова активен]")
            is_idle_dialog_active = False
        
        if listening_active:
            delay = random.randint(45, 90)
            idle_timer = threading.Timer(delay, timer_callback)
            idle_timer.start()
    
    delay = random.randint(30, 60)
    idle_timer = threading.Timer(delay, timer_callback)
    idle_timer.start()

def process_command(text):
    """Обрабатывает голосовую команду с использованием ИИ"""
    global last_speaker, user_heard, is_idle_dialog_active
    
    # Список фраз, которые являются продолжением фонового диалога (игнорируем)
    idle_remnants = [
        "отлично сестра", "а у тебя", "тоже хорошо", 
        "солнце сегодня такое тёплое", "да приятный день",
        "как спалось", "как спалось?", "мэй как спалось",
        "отлично проспалась", "хорошо солнце", "приятный день",
        "тплое", "тоже хорошо солнце", "мы как спалось"
    ]
    
    # Если текст похож на продолжение фонового диалога - игнорируем
    if text and any(remnant in text.lower() for remnant in idle_remnants):
        print("🚫 [Игнорирую - продолжение фонового диалога]")
        return True
    
    # Если пользователь что-то сказал - прерываем фоновый диалог
    if text:
        user_heard = True
        if is_idle_dialog_active:
            print("🔇 [Пользователь прервал фоновый диалог]")
            is_idle_dialog_active = False
        threading.Thread(target=reset_user_heard, daemon=True).start()
    
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
    
    # Простые приветствия без имени
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
    """Слушает микрофон - отключён во время фоновых диалогов"""
    global is_idle_dialog_active
    
    # Если идёт фоновый диалог - полностью игнорируем микрофон
    if is_idle_dialog_active:
        time.sleep(0.2)
        return ""
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            recognizer.energy_threshold = 50
            print("\n🎤 Слушаю...", end="", flush=True)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
        text = recognizer.recognize_google(audio, language="ru-RU")
        
        # Применяем исправления из словаря
        text = fix_before_spell(text)
        text = spell(text)
        text = apply_replacements(text)
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
    global listening_active
    
    # Проверяем, доступна ли модель Qwen
    print("Проверка доступности Qwen модели...")
    try:
        ollama.generate(model=QWEN_MODEL, prompt="Привет", options={'num_predict': 5})
        print("✓ Qwen модель готова к работе\n")
    except Exception as e:
        print(f"⚠ Qwen модель не найдена! Запустите: ollama run {QWEN_MODEL}")
        print("Пока буду отвечать только заготовленными фразами.\n")
    
    intro()
    
    # ЗАПУСКАЕМ IDLE ТАЙМЕР
    start_idle_timer()
    
    try:
        while listening_active:
            command = listen()
            if not process_command(command):
                listening_active = False
                break
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена")
    finally:
        if idle_timer:
            idle_timer.cancel()

if __name__ == "__main__":
    main()
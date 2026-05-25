import torch
import sounddevice as sd
import speech_recognition as sr
import numpy as np
import random
import re
import threading
import time
from dialogues_idle import get_random_dialogue, get_next_delay, should_start_dialogue, format_dialogue_for_speaking

# Загружаем модель Silero
print("Загрузка голосовой модели...")
device = torch.device('cpu')
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru', speaker='v5_ru')
model.to(device)
print("✓ Модель загружена")

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

# Реакции на разные обращения
REACTIONS = {
    'chuchu': [
        "Ой, это ты меня позвал? Я здесь!",
        "Чу Чу на связи! Что хотел?",
        "Да-да, я слышу тебя!",
        "Приветик! Это я, Чу Чу!",
        "Ну привет, красавчик!"
    ],
    'mei': [
        "Я здесь. Что случилось?",
        "Мэй слушает. Говори.",
        "Да, я рядом.",
        "Привет, это Мэй.",
        "Я тебя слышу."
    ],
    'both': [
        "Обе здесь! Что случилось?",
        "Мы рядом, говори!",
        "Чу Чу и Мэй готовы помочь!"
    ]
}

# Варианты имен для распознавания
CHUCHU_NAMES = [
    'чу чу', 'чу-чу', 'чучу', 'чу', 'чучу', 'чу чучу',
    'Чу Чу', 'Чу-Чу', 'Чучу'
]

MEI_NAMES = [
    'мэй', 'мей', 'май', 'ме', 'мая',
    'Мэй', 'Мей', 'Май'
]

BOTH_NAMES = [
    'девочки', 'девчата', 'девченки', 'подружки', 'милые', 'любимые',
    'сестры', 'девушки', 'красавицы'
]

# Глобальные переменные для фоновых диалогов
idle_timer = None
is_speaking = False
user_heard = False
listening_active = True

def speak(text, voice='chuchu'):
    """Озвучка текста"""
    global is_speaking, listening_active
    
    voice_config = VOICES[voice]
    print(f"\n[{voice_config['name']}]: {text}")
    
    is_speaking = True
    
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
        print(f"Ошибка: {e}")
    finally:
        is_speaking = False

def play_dialogue(dialogue):
    """Воспроизводит диалог"""
    global is_speaking
    if is_speaking:
        return
    
    print("\n🎭 [Фоновый диалог]")
    for speaker, text in dialogue:
        if not user_heard:  # Если пользователь не обращался, продолжаем диалог
            speak(text, speaker)
            time.sleep(0.5)  # Пауза между репликами

def start_idle_timer():
    """Запускает таймер для фоновых диалогов"""
    global idle_timer
    
    def timer_callback():
        global idle_timer, user_heard
        
        time.sleep(1)  # Даем завершиться текущему диалогу
        
        if not is_speaking and not user_heard and should_start_dialogue():
            dialogue, category = get_random_dialogue()
            dialogue_list = format_dialogue_for_speaking(dialogue)
            play_dialogue(dialogue_list)
        
        # Запускаем следующий таймер
        if listening_active:
            delay = get_next_delay()
            idle_timer = threading.Timer(delay, timer_callback)
            idle_timer.start()
    
    delay = get_next_delay()
    idle_timer = threading.Timer(delay, timer_callback)
    idle_timer.start()

def reset_user_heard():
    """Сбрасывает флаг user_heard через паузу после активности пользователя"""
    global user_heard
    time.sleep(10)  # Ждем 10 секунд после того, как пользователь закончил говорить
    user_heard = False

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

def random_reaction(person):
    """Случайная реакция на обращение"""
    if person == 'chuchu':
        return random.choice(REACTIONS['chuchu'])
    elif person == 'mei':
        return random.choice(REACTIONS['mei'])
    else:
        return random.choice(REACTIONS['both'])

def process_command(text):
    """Обрабатывает голосовую команду"""
    global user_heard, listening_active
    
    if not text:
        return True
    
    # Пользователь обратился - отменяем фоновые диалоги на время
    user_heard = True
    threading.Thread(target=reset_user_heard, daemon=True).start()
    
    print(f"Обработка: {text}")
    
    # Диалог сестер
    if "диалог" in text or "поговорите" in text:
        dialogue, category = get_random_dialogue()
        dialogue_list = format_dialogue_for_speaking(dialogue)
        for speaker, dialogue_text in dialogue_list:
            speak(dialogue_text, speaker)
            time.sleep(0.5)
        return True
    
    # Выход
    if any(word in text for word in ["пока", "выход", "до свидания"]):
        listening_active = False
        if idle_timer:
            idle_timer.cancel()
        speak("Пока-пока! Приходи еще, у нас с Мэй есть что показать!", 'chuchu')
        return False
    
    # Определяем к кому обратились
    person = extract_name(text)
    
    # Если обратились к кому-то
    if person:
        message = extract_message(text)
        
        if message and len(message) > 0:
            if person == 'chuchu':
                speak(message, 'chuchu')
            elif person == 'mei':
                speak(message, 'mei')
            else:
                voice = random.choice(['chuchu', 'mei'])
                speak(message, voice)
        else:
            speak(random_reaction(person), person if person != 'both' else random.choice(['chuchu', 'mei']))
    
    # Без обращения - умная реакция
    else:
        text_lower = text.lower()
        
        if "как дела" in text_lower or "как ты" in text_lower:
            speak("У меня всё отлично! А у тебя? Хочешь поговорить с Чу Чу или Мэй?", 'chuchu')
        elif "красивая" in text_lower:
            speak("Спасибо! Чу Чу всегда следит за собой. А Мэй создает потрясающие наряды!", 'chuchu')
        elif "грудь" in text_lower or "сиськи" in text_lower:
            speak("Ой, ты про мою грудь? Она действительно большая и красивая! А у Мэй тоже замечательная!", 'chuchu')
        elif "попа" in text_lower or "задница" in text_lower:
            speak("Моя попочка самая сочная! Мэй говорит, что у неё тоже круглая и аппетитная.", 'chuchu')
        elif "жемчужный" in text_lower or "трусики" in text_lower:
            speak("Я обожаю свои жемчужные трусики! И Мэй такие же носит. Это наша фишка!", 'chuchu')
        elif "люблю" in text_lower:
            speak("Я люблю Мэй, люблю косплей и люблю хозяина Вадима! А ты кого любишь?", 'chuchu')
        else:
            responses = [
                "Скажи 'Чу Чу' или 'Мэй', чтобы я поняла, к кому ты обращаешься.",
                "Позови меня по имени: Чу Чу или Мэй.",
                "Я не поняла, к кому ты. Скажи Чу Чу или Мэй."
            ]
            speak(random.choice(responses), 'chuchu')
    
    return True

def intro():
    """Представление"""
    print("\n" + "="*50)
    print("🎀 Голосовой помощник Girls-AI 🎀")
    print("="*50)
    print("Говорите в микрофон:")
    print("  • 'Чу Чу, привет' - Чу Чу ответит")
    print("  • 'Мэй, как дела' - Мэй ответит")
    print("  • 'Девочки, привет' - ответят вместе")
    print("  • 'диалог' - сестры поговорят")
    print("  • 'пока' - выход")
    print("="*50)
    print("\n💬 Через 20-60 секунд тишины начнутся фоновые диалоги")
    print("🎤 Говорите когда увидите '🎤 Слушаю...'")
    print("="*50 + "\n")
    
    speak("Привет! Я Чу Чу, мне восемнадцать лет. Я настоящая звезда косплея.", 'chuchu')
    speak("Здравствуйте. Я Мэй, мне двадцать два года. Я создаю снаряжение для косплея.", 'mei')
    speak("Назови наше имя, и мы ответим!", 'chuchu')

# Инициализация распознавания
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("Калибровка микрофона...")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
print("✓ Микрофон готов\n")

def listen():
    """Слушает микрофон"""
    try:
        with microphone as source:
            print("\n🎤 Слушаю...", end="", flush=True)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("\r🔍 Распознаю...", end="", flush=True)
            
        text = recognizer.recognize_google(audio, language="ru-RU")
        print(f"\r💬 Вы сказали: {text}")
        return text.lower()
    except sr.WaitTimeoutError:
        print("\r⏰ Тишина...   ", end="", flush=True)
        return ""
    except sr.UnknownValueError:
        print("\r🤔 Не расслышала...", end="", flush=True)
        return ""
    except sr.RequestError:
        print("\r🌐 Ошибка соединения...", end="", flush=True)
        return ""

def main():
    global listening_active
    
    intro()
    
    # Запускаем таймер фоновых диалогов
    start_idle_timer()
    
    try:
        while listening_active:
            command = listen()
            if not process_command(command):
                break
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена")
    finally:
        if idle_timer:
            idle_timer.cancel()

if __name__ == "__main__":
    main()
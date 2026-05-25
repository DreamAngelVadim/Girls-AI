import torch
import sounddevice as sd
import speech_recognition as sr
import numpy as np
import random
import re

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
    # Удаляем все варианты имен из текста
    cleaned = text.lower()
    
    for name in CHUCHU_NAMES + MEI_NAMES + BOTH_NAMES:
        cleaned = re.sub(r'\b' + re.escape(name.lower()) + r'\b', '', cleaned)
    
    # Удаляем лишние пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned if cleaned else None

def speak(text, voice='chuchu'):
    """Озвучка текста"""
    voice_config = VOICES[voice]
    print(f"\n[{voice_config['name']}]: {text}")
    
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
    if not text:
        return True
    
    print(f"Обработка: {text}")
    
    # Определяем к кому обратились
    person = extract_name(text)
    
    # Диалог сестер
    if "диалог" in text or "поговорите" in text:
        dialogue()
        return True
    
    # Выход
    if any(word in text for word in ["пока", "выход", "до свидания"]):
        speak("Пока-пока! Приходи еще, у нас с Мэй есть что показать!", 'chuchu')
        return False
    
    # Если обратились к кому-то
    if person:
        # Извлекаем сообщение
        message = extract_message(text)
        
        if message and len(message) > 0:
            # Есть конкретное сообщение
            if person == 'chuchu':
                speak(message, 'chuchu')
            elif person == 'mei':
                speak(message, 'mei')
            else:
                # Обращение к обеим - отвечает случайная
                voice = random.choice(['chuchu', 'mei'])
                speak(message, voice)
        else:
            # Просто обратились без сообщения - реакция
            speak(random_reaction(person), person if person != 'both' else random.choice(['chuchu', 'mei']))
    
    # Без обращения - умная реакция по контексту
    else:
        # Анализируем ключевые слова
        text_lower = text.lower()
        
        if "как дела" in text_lower or "как ты" in text_lower:
            speak("У меня всё отлично! А у тебя? Хочешь поговорить с Чу Чу или Мэй?", 'chuchu')
        
        elif "красивая" in text_lower or "красиво" in text_lower:
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
            # Если не поняли - предлагаем обратиться по имени
            responses = [
                "Скажи 'Чу Чу' или 'Мэй', чтобы я поняла, к кому ты обращаешься.",
                "Позови меня по имени: Чу Чу или Мэй.",
                "Я не поняла, к кому ты. Скажи Чу Чу или Мэй.",
                "Назови мое имя, и я отвечу!"
            ]
            speak(random.choice(responses), 'chuchu')
    
    return True

def dialogue():
    """Диалог сестер"""
    speak("Мэй, посмотри на этот новый косплей костюм! Он просто шикарный!", 'chuchu')
    speak("Да, сестра, ты прекрасна. Я сделаю для тебя самое лучшее снаряжение.", 'mei')
    speak("Ах, Мэй, ты такая заботливая! Твои ручки просто волшебные.", 'chuchu')
    speak("Только для тебя, моя дорогая сестра. И для хозяина Вадима, конечно.", 'mei')

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
    print("\n🎤 Говорите когда увидите '🎤 Слушаю...'")
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
    intro()
    
    while True:
        command = listen()
        if not process_command(command):
            break

if __name__ == "__main__":
    main()
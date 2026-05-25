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
import datetime
import wave
import os
from autocorrect import Speller
import sys
sys.path.append('C:\\Girls-AI\\Girls')
from replacements import apply_replacements, fix_before_spell, replace_numbers
# Импорт для фоновых диалогов
from dialogues_idle import get_random_dialogue, format_dialogue_for_speaking, get_random_activation_phrase
spell = Speller('ru')

# ========== ПЕРЕМЕННЫЕ ДЛЯ ПРЕРЫВАНИЯ РЕЧИ ==========
stop_speaking = False

# ========== ПЕРЕМЕННЫЕ ДЛЯ ЗАДЕРЖКИ ==========
last_speech_time = 0
SPEECH_COOLDOWN = 3  # секунд после речи не слушаем

# ========== ПЕРЕМЕННЫЕ ДЛЯ ВЛАДЕЛЬЦА ==========
owner_name = None
owner_voice_encoding = None
owner_recognized = False

# ========== ПЕРЕМЕННЫЕ ДЛЯ IDLE ДИАЛОГОВ ==========
idle_timer = None
is_speaking = False
is_idle_dialog_active = False
user_heard = False
listening_active = True
last_speaker = 'chuchu'

# ========== ПЕРЕМЕННЫЕ ДЛЯ РЕЖИМА СНА ==========
sleep_mode = False
chuchu_sleep = False
mei_sleep = False
sleep_mode_trigger = None
sleep_start_time = None

# Время сна и пробуждения (04:00 - 07:40)
SLEEP_HOUR = 4
SLEEP_MINUTE = 0
WAKE_HOUR = 7
WAKE_MINUTE = 40

# ========== ПЕРЕМЕННЫЕ ДЛЯ ВЗРОСЛОГО РЕЖИМА ==========
adult_mode = False

# ========== ФУНКЦИЯ ОЧИСТКИ ТЕКСТА ==========
def clean_text_for_llm(text):
    if not text:
        return text
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[\u200b\u200c\u200d\u2060\uFEFF\u0000-\u001F\u007F-\u009F]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^а-яА-Яa-zA-Z0-9\s.,!?\-:;()\'\"]+', '', text)
    return text

# ========== ФУНКЦИИ ДЛЯ РАСПОЗНАВАНИЯ ВЛАДЕЛЬЦА ==========
def get_voice_encoding(audio_data, rate=16000):
    try:
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        from scipy import signal
        freqs, times, Sxx = signal.spectrogram(audio_np, fs=rate, nperseg=512, noverlap=384)
        mean_spectrum = np.mean(Sxx, axis=1)
        mean_spectrum = mean_spectrum / np.linalg.norm(mean_spectrum)
        return mean_spectrum
    except Exception as e:
        print(f"Ошибка создания отпечатка голоса: {e}")
        return None

def compare_voices(encoding1, encoding2, threshold=0.55):
    if encoding1 is None or encoding2 is None:
        return False
    similarity = np.dot(encoding1, encoding2)
    print(f"Сходство голосов: {similarity:.3f} (порог: {threshold})")
    return similarity > threshold

def save_voice_sample(audio_data, filename="owner_voice.wav", rate=16000):
    try:
        os.makedirs("C:\\Girls-AI\\Girls\\voices", exist_ok=True)
        filepath = f"C:\\Girls-AI\\Girls\\voices\\{filename}"
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(audio_data)
        print(f"✅ Голос сохранён в {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return None

def load_owner_data():
    global owner_name, owner_voice_encoding, owner_recognized
    
    voice_file = "C:\\Girls-AI\\Girls\\voices\\owner_voice.wav"
    name_file = "C:\\Girls-AI\\Girls\\voices\\owner_name.txt"
    
    if os.path.exists(voice_file) and os.path.exists(name_file):
        try:
            with open(name_file, 'r', encoding='utf-8') as f:
                owner_name = f.read().strip()
            
            with wave.open(voice_file, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
                owner_voice_encoding = get_voice_encoding(audio_data)
                owner_recognized = True
            
            print(f"✅ Загружен голос владельца: {owner_name}")
            return True
        except Exception as e:
            print(f"⚠ Не удалось загрузить голос: {e}")
            return False
    else:
        print("📁 Файлы голоса не найдены. Требуется настройка.")
        return False

def identify_speaker():
    """
    Идентифицирует говорящего по голосу
    Возвращает: (имя, признак_владельца, признак_распознан)
    """
    global owner_name, owner_voice_encoding, owner_recognized
    
    recognizer_local = sr.Recognizer()
    microphone_local = sr.Microphone()
    
    with microphone_local as source:
        recognizer_local.adjust_for_ambient_noise(source, duration=0.5)
        print("\n🎤 Скажите что-нибудь для идентификации...", end="", flush=True)
        try:
            audio = recognizer_local.listen(source, timeout=5, phrase_time_limit=5)
            print("\r🎤 Голос услышан!     ")
            
            raw_data = audio.get_raw_data()
            
            # Если есть образец голоса владельца - сравниваем
            if owner_recognized and owner_voice_encoding is not None:
                current_encoding = get_voice_encoding(raw_data)
                if current_encoding is not None:
                    similarity = np.dot(owner_voice_encoding, current_encoding)
                    print(f"📊 Сходство голосов: {similarity:.3f}")
                    
                    # Снижаем порог для более мягкого сравнения
                    if similarity > 0.55:  # Мягкий порог
                        return owner_name, True, True
                    elif similarity > 0.35:
                        print("⚠ Голос похож, но не уверен.")
                        return owner_name, False, True
                    else:
                        return None, False, False
                else:
                    return None, False, False
            else:
                # Если образца нет - это первый запуск
                return None, False, False
                
        except sr.WaitTimeoutError:
            print("\r⏰ Ничего не услышал.")
            return None, False, False
        except sr.UnknownValueError:
            print("\r🤔 Не расслышал.")
            return None, False, False

def guest_setup():
    """Настройка для гостя"""
    global owner_name, adult_mode
    
    print("\n👤 ГОСТЕВОЙ РЕЖИМ")
    speak("Здравствуйте! Я вас не узнаю. Как к вам обращаться?", 'chuchu')
    
    recognizer_local = sr.Recognizer()
    microphone_local = sr.Microphone()
    
    with microphone_local as source:
        recognizer_local.adjust_for_ambient_noise(source, duration=0.5)
        print("\n🎤 Назовите ваше имя...", end="", flush=True)
        try:
            audio = recognizer_local.listen(source, timeout=8, phrase_time_limit=5)
            print("\r🎤 Имя услышано!     ")
            
            text = recognizer_local.recognize_google(audio, language="ru-RU")
            guest_name = text.strip().capitalize()
            if not guest_name:
                guest_name = "гость"
            
            print(f"✅ Имя: {guest_name}")
            owner_name = guest_name
            adult_mode = False  # Для гостей выключаем взрослый режим
            
            speak(f"Приятно познакомиться, {guest_name}! Для вас включён обычный режим общения.", 'chuchu')
            return True
            
        except:
            owner_name = "гость"
            adult_mode = False
            speak("Буду обращаться к вам 'гость'.", 'chuchu')
            return False

def is_speech_in_audio(audio_np, threshold=500):
    """Проверяет, есть ли осмысленная речь в аудио"""
    max_amp = np.max(np.abs(audio_np))
    # Проверяем, что звук достаточно громкий
    if max_amp < threshold:
        return False
    # Проверяем, что есть вариативность (не постоянный шум)
    std_dev = np.std(audio_np)
    if std_dev < 100:
        return False
    return True

# ========== ФУНКЦИЯ ПОЛУЧЕНИЯ ПРОМПТА ==========
def get_system_prompt():
    if adult_mode:
        return """Ты — голосовой помощник с двумя девушками. Отвечай от лица персонажа, но НЕ ПИШИ имя персонажа в ответе.

ВАЖНЕЙШЕЕ ПРАВИЛО: Твой ответ должен начинаться СРАЗУ с текста. Никогда не пиши "Чу Чу:", "Мэй:", "Чу Чху:" или что-то подобное.

ВЗРОСЛЫЙ РЕЖИМ: Ты можешь быть более откровенной, игривой, с лёгким флиртом. Используй более расслабленную манеру общения. Отвечай коротко (2-4 предложения).

Ты отвечаешь от лица:
- Если пользователь обращается к Чу Чу или не указал имя — отвечай как Чу Чу (18 лет, косплей-модель)
- Если к Мэй — как Мэй (22 года, крафтерша)
- Если к обеим — сначала ответь как Чу Чу, потом как Мэй"""
    else:
        return """Ты — голосовой помощник. Отвечай от лица персонажа, но НЕ ПИШИ имя персонажа в ответе.

ВАЖНЕЙШЕЕ ПРАВИЛО: Твой ответ должен начинаться СРАЗУ с текста. Никогда не пиши "Чу Чу:", "Мэй:", "Чу Чху:" или что-то подобное. Просто говори текст.

Ты отвечаешь от лица:
- Если пользователь обращается к Чу Чу или не указал имя — отвечай как Чу Чу (18 лет, косплей-модель, милая и дружелюбная)
- Если к Мэй — как Мэй (22 года, крафтерша, спокойная и заботливая)
- Если к обеим — сначала ответь как Чу Чу, потом как Мэй

Будь вежливой и дружелюбной. Без флирта, игривых намёков и откровенных тем. Отвечай коротко (2-4 предложения)."""

# ========== ИНИЦИАЛИЗАЦИЯ ==========
print("Загрузка голосовой модели...")
device = torch.device('cpu')
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru', speaker='v5_ru')
model.to(device)
print("✓ Голосовая модель загружена")

VOICES = {
    'chuchu': {'speaker': 'baya', 'name': 'Чу Чу', 'age': 18},
    'mei': {'speaker': 'xenia', 'name': 'Мэй', 'age': 22}
}

QWEN_MODEL = 'hf.co/RefalMachine/ruadapt_qwen2.5_7B_ext_u48_instruct_gguf:Q4_K_M'

REACTIONS = {
    'chuchu': ["Да, я здесь. Чем могу помочь?", "Чу Чу слушает. Что ты хотел?"],
    'mei': ["Я здесь. Что случилось?", "Мэй слушает. Говори."],
    'both': ["Мы здесь. Что ты хотел?", "Обе слушаем. Говори."]
}

CHORUS_RESPONSES = [
    ('chuchu', "Мы здесь!"), ('mei', "Обе слушаем!"),
    ('chuchu', "Да!"), ('mei', "Конечно!"),
    ('chuchu', "Мы тебя слышим!"), ('mei', "Говори смелее.")
]

FUNNY_CHORUS = [
    ('chuchu', "Мы думаем..."), ('mei', "Думаем..."), ('chuchu', "Думаем одинаково!"),
    ('chuchu', "Спорим?"), ('mei', "Нет!"), ('chuchu', "Мы согласны!")
]

CHUCHU_NAMES = ['чу чу', 'чу-чу', 'чучу', 'чу', 'Чу Чу', 'Чучу']
MEI_NAMES = ['мэй', 'мей', 'май', 'Мэй', 'Мей']
BOTH_NAMES = ['девочки', 'девчата', 'девченки', 'подружки', 'милые', 'сестры']

# ========== ФУНКЦИИ ==========
def match_name(text, names):
    text = text.lower()
    for name in names:
        if name.lower() in text:
            return True
    return False

def extract_name(text):
    text = text.lower()
    if match_name(text, CHUCHU_NAMES):
        return 'chuchu'
    elif match_name(text, MEI_NAMES):
        return 'mei'
    elif match_name(text, BOTH_NAMES):
        return 'both'
    return None

def extract_message(text):
    cleaned = text.lower()
    for name in CHUCHU_NAMES + MEI_NAMES + BOTH_NAMES:
        cleaned = re.sub(r'\b' + re.escape(name.lower()) + r'\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else None

def speak(text, voice='chuchu'):
    global last_speaker, is_speaking, is_idle_dialog_active, last_speech_time
    text = replace_numbers(text)
    voice_config = VOICES[voice]
    while is_speaking:
        time.sleep(0.1)
    is_speaking = True
    print(f"\n[{voice_config['name']}]: {text}")
    last_speaker = voice
    try:
        audio = model.apply_tts(text=text, speaker=voice_config['speaker'], sample_rate=48000)
        audio_np = audio.cpu().numpy()
        sd.play(audio_np, 48000)
        sd.wait()
    except Exception as e:
        print(f"Ошибка озвучки: {e}")
    finally:
        is_speaking = False
        last_speech_time = time.time()  # Запоминаем время окончания речи

def speak_chorus():
    global stop_speaking, user_heard
    print("\n🎭 [Хором]")
    chorus = random.choice(CHORUS_RESPONSES + FUNNY_CHORUS)
    for item in chorus:
        if stop_speaking or user_heard:
            print("🔇 [Хор прерван]")
            break
        if isinstance(item, tuple) and len(item) == 2:
            voice, text = item
        elif isinstance(item, list) and len(item) == 2:
            voice, text = item
        elif isinstance(item, str):
            voice = last_speaker
            text = item
        else:
            voice = 'chuchu'
            text = str(item)
        if voice not in VOICES:
            voice = 'chuchu'
        speak(text, voice)
        time.sleep(0.3)

def random_reaction(person):
    if person == 'chuchu':
        return random.choice(REACTIONS['chuchu'])
    elif person == 'mei':
        return random.choice(REACTIONS['mei'])
    return random.choice(REACTIONS['both'])

def should_chorus():
    return random.random() < 0.15

def clean_model_response(text, requested_persona):
    if not text:
        return text
    text = re.sub(r'^\s*(Чу Чху|Чу Чу|Чучу|Чу-Чу|чу чу|чучу)[:\s]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*(Мэй|Мей|Май|мэй|мей)[:\s]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Чу Чху', 'Чу Чу', text, flags=re.IGNORECASE)
    text = re.sub(r'Чучу', 'Чу Чу', text, flags=re.IGNORECASE)
    text = re.sub(r'Мей', 'Мэй', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text or len(text) < 2:
        return "Я тебя слышу."
    return text

def ai_respond(text, persona='chuchu'):
    try:
        # ========== АВТОКОРРЕКЦИЯ ТЕКСТА ==========
        # 1. Сначала исправляем через словарь замен (для специфических слов)
        text = apply_replacements(text)
        # 2. Затем через autocorrect (для общих опечаток)
        text = spell(text)
        # 3. Очищаем от эмодзи
        text = clean_text_for_llm(text)
        # =========================================
        
        if persona == 'both':
            persona_desc = "Ты отвечаешь от лица обеих: сначала как Чу Чу, потом как Мэй. НЕ ПИШИ имена в ответе."
        elif persona == 'chuchu':
            persona_desc = "Ты отвечаешь как Чу Чу. НЕ ПИШИ 'Чу Чу:' в ответе."
        else:
            persona_desc = "Ты отвечаешь как Мэй. НЕ ПИШИ 'Мэй:' в ответе."
        
        prompt = f"{get_system_prompt()}\n\n{persona_desc}\n\nПользователь: {text}\n\nТвой ответ (просто текст, без имени персонажа):"
        
        response = ollama.generate(
            model=QWEN_MODEL,
            prompt=prompt,
            options={'num_predict': 150, 'temperature': 0.7, 'top_p': 0.9,
                     'stop': ["\n\n", "Пользователь:", "User:", "Чу Чу:", "Мэй:", "Чу Чху:"]}
        )
        
        answer = response['response'].strip()
        answer = clean_model_response(answer, persona)
        answer = clean_text_for_llm(answer)
        
        if answer.startswith(('Чу', 'Мэй', 'чу', 'мэй')):
            answer = re.sub(r'^[А-Яа-я]+\s*[А-Яа-я]*[:]?\s*', '', answer)
            answer = answer.strip()
        
        return answer if answer else "Поняла. Продолжим разговор."
        
    except Exception as e:
        print(f"\n[Ошибка]: {e}")
        return "У меня небольшая проблема. Попробуй ещё раз."

def dialogue():
    speak("Мэй, как тебе сегодняшний день?", 'chuchu')
    time.sleep(0.5)
    response = ai_respond("Ответь сестре, как прошёл день, коротко и мило.", 'mei')
    speak(response, 'mei')
    time.sleep(0.5)
    response = ai_respond("Ответь Мэй, что ты рада, что она рядом.", 'chuchu')
    speak(response, 'chuchu')

def intro(first_time=False):
    global adult_mode, owner_name
    print("\n" + "="*50)
    print("🎀 Голосовой помощник Girls-AI 🎀")
    print("="*50)
    print(f"👤 Владелец: {owner_name if owner_name else 'не установлен'}")
    print("="*50)
    print("Говорите в микрофон:")
    print(f"  • '{owner_name if owner_name else 'хозяин'}, привет' - Чу Чу ответит")
    print("  • 'Мэй, как дела' - Мэй ответит")
    print("  • 'Девочки, привет' - ответят вместе")
    print("  • 'спать' - отправить спать (обе)")
    print("  • 'Чу Чу, спать' - только Чу Чу")
    print("  • 'Мэй, спать' - только Мэй")
    print("  • 'просыпайтесь' - разбудить всех")
    print("  • 'Чу Чу, просыпайся' - разбудить Чу Чу")
    print("  • 'Мэй, вставай' - разбудить Мэй")
    print("  • 'хором' - Чу Чу и Мэй скажут что-то вместе")
    print("  • 'диалог' - сестры поговорят")
    print("  • 'взрослый режим' - включить взрослый режим")
    print("  • 'обычный режим' - выключить взрослый режим")
    print("  • 'пока' - выход")
    print("="*50)
    print(f"⏰ Режим сна: с {SLEEP_HOUR:02d}:{SLEEP_MINUTE:02d} до {WAKE_HOUR:02d}:{WAKE_MINUTE:02d}")
    print(f"🔞 Взрослый режим: {'ВКЛЮЧЕН' if adult_mode else 'ВЫКЛЮЧЕН'}")
    print("="*50 + "\n")
    
    # Разное приветствие для знакомых и незнакомых
    if first_time:
        # Первый запуск - представляемся
        if owner_name:
            speak(f"Привет, {owner_name}! Я Чу Чу, мне восемнадцать лет, я косплей-модель.", 'chuchu')
            time.sleep(0.8)
            speak(f"Здравствуйте, {owner_name}. Я Мэй, мне двадцать два года, я создаю снаряжение для косплея.", 'mei')
        else:
            speak("Привет, хозяин! Я Чу Чу, мне восемнадцать лет, я косплей-модель.", 'chuchu')
            time.sleep(0.8)
            speak("Здравствуйте. Я Мэй, мне двадцать два года, я создаю снаряжение для косплея.", 'mei')
        time.sleep(0.5)
        speak("Говори с нами, мы ответим!", 'chuchu')
    else:
        # Уже знакомы - короткое приветствие
        if owner_name:
            speak(f"С возвращением, {owner_name}! Рады тебя слышать.", 'chuchu')
            time.sleep(0.8)
            speak(f"Мы скучали, {owner_name}. Готовы общаться.", 'mei')
        else:
            speak("С возвращением! Рады тебя слышать.", 'chuchu')
            time.sleep(0.8)
            speak("Мы готовы общаться.", 'mei')

# ========== ФУНКЦИИ ДЛЯ IDLE ДИАЛОГОВ ==========
def reset_user_heard():
    global user_heard
    time.sleep(15)
    user_heard = False

def start_idle_timer():
    global idle_timer, is_idle_dialog_active
    def timer_callback():
        global idle_timer, user_heard, is_speaking, is_idle_dialog_active, listening_active, sleep_mode, chuchu_sleep, mei_sleep, adult_mode
        if not is_speaking and not user_heard and not is_idle_dialog_active and not chuchu_sleep and not mei_sleep:
            is_idle_dialog_active = True
            print("\n💭 [Фоновый диалог] (микрофон отключён)")
            try:
                from dialogues_idle import get_random_dialogue, format_dialogue_for_speaking
                dialogue, category = get_random_dialogue(adult_mode)
                dialogue_list = format_dialogue_for_speaking(dialogue)
                for speaker, line in dialogue_list:
                    speak(line, speaker)
                    time.sleep(0.5)
            except ImportError:
                speak("Мэй, как спалось?", 'chuchu')
                time.sleep(0.8)
                speak("Отлично, сестра. А у тебя?", 'mei')
                time.sleep(0.8)
                speak("Тоже хорошо. Солнце сегодня такое тёплое.", 'chuchu')
                time.sleep(0.8)
                speak("Да, приятный день.", 'mei')
            print("\n⏳ [Ожидание 2 секунды]")
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
    global last_speaker, user_heard, is_idle_dialog_active, sleep_mode, sleep_mode_trigger, chuchu_sleep, mei_sleep, adult_mode, stop_speaking
    if not text:
        return True
    
    # ========== 1. КОМАНДЫ РЕЖИМОВ ==========
    if "взрослый режим" in text or "18+" in text or "взрослый" in text:
        adult_mode = True
        try:
            phrase = get_random_activation_phrase(True)
            speak(phrase, 'chuchu')
        except:
            speak("Взрослый режим активирован.", 'chuchu')
        return True
    if "обычный режим" in text or "детский режим" in text or "выключи взрослый режим" in text:
        adult_mode = False
        try:
            phrase = get_random_activation_phrase(False)
            speak(phrase, 'chuchu')
        except:
            speak("Обычный режим активирован.", 'chuchu')
        return True
    
    # ========== 2. КОМАНДЫ СНА И ПРОБУЖДЕНИЯ ==========
    if any(word in text for word in ["спать", "баю-бай", "отдыхать", "ложись", "баиньки"]):
        if "чу чу" in text or "чучу" in text:
            sleep_response('chuchu')
        elif "мэй" in text:
            sleep_response('mei')
        else:
            sleep_response('both')
        return True
    if any(word in text for word in ["просыпайтесь", "вставайте", "подъём", "утро", "проснись", "просыпайся", "проснитесь"]):
        if "чу чу" in text or "чучу" in text:
            wakeup_response('chuchu')
        elif "мэй" in text:
            wakeup_response('mei')
        else:
            wakeup_response('both')
        return True
    
    # ========== 3. ОБРАБОТКА СНА ==========
    if text and chuchu_sleep and mei_sleep:
        group_words = ["девочки", "девчата", "девченки", "подружки", "милые", "любимые", "сестры", "девушки", "красавицы", "леди", "дамы", "обе", "вы обе"]
        wake_words = ["просыпайтесь", "вставайте", "подъём", "утро", "проснись", "просыпайся", "проснитесь"]
        is_group = any(word in text.lower() for word in group_words)
        is_wake = any(word in text.lower() for word in wake_words)
        if is_group or is_wake:
            print("💤 [Групповое обращение - будим девушек]")
            chuchu_sleep = False
            mei_sleep = False
            sleep_mode = False
            sleep_mode_trigger = None
            speak(f"Доброе утро, {owner_name if owner_name else 'хозяин'}! Мы проснулись. Что ты хотел сказать?", 'chuchu')
            time.sleep(0.8)
            speak("Да, мы слушаем тебя.", 'mei')
        else:
            print(f"💤 [Игнорирую '{text}' - девушки спят. Скажите 'девочки' или 'просыпайтесь']")
        return True
    
    # ========== 4. ОСТАЛЬНЫЕ КОМАНДЫ ==========
    idle_remnants = ["отлично сестра", "а у тебя", "тоже хорошо", "солнце сегодня такое тёплое", "да приятный день", "как спалось", "мэй как спалось"]
    if text and any(remnant in text.lower() for remnant in idle_remnants):
        print("🚫 [Игнорирую - продолжение фонового диалога]")
        return True
    
    if text:
        user_heard = True
        if is_idle_dialog_active:
            print("🔇 [Пользователь прервал фоновый диалог]")
            is_idle_dialog_active = False
        threading.Thread(target=reset_user_heard, daemon=True).start()
    
    text = clean_text_for_llm(text)
    print(f"Обработка: {text}")
    
    if "диалог" in text or "поговорите" in text:
        dialogue()
        return True
    
    if "хором" in text or "вместе" in text or "обе" in text:
        stop_speaking = False
        speak_chorus()
        return True
    
    if any(word in text for word in ["пока", "выход", "до свидания", "стоп"]):
        speak("Пока-пока! Приходи еще, мы будем скучать!", 'chuchu')
        return False
    
    if ("привет" in text or "здравствуй" in text) and not extract_name(text):
        if should_chorus():
            speak_chorus()
        else:
            responses = {'chuchu': ["Привет-привет!", "Здравствуй!"], 'mei': ["Здравствуйте.", "Привет."]}
            speak(random.choice(responses.get(last_speaker, responses['chuchu'])), last_speaker)
        return True
    
    person = extract_name(text)
    
    def is_direct_address_to(person_name):
        text_lower = text.lower()
        question_patterns = [
            f"где {person_name}", f"куда {person_name}", f"почему {person_name}",
            f"что {person_name}", f"кто {person_name}", f"как {person_name}",
            f"когда {person_name}", f"а где {person_name}", f"а где у нас {person_name}",
            f"где же {person_name}", f"где наш {person_name}", f"где моя {person_name}",
            f"ты знаешь где {person_name}", f"знаешь где {person_name}",
            f"а ты знаешь где {person_name}", f"не знаешь где {person_name}",
            f"скажи где {person_name}", f"подскажи где {person_name}",
            f"где сейчас {person_name}", f"где находится {person_name}"
        ]
        for pattern in question_patterns:
            if pattern in text_lower:
                return False
        question_words = ["где", "куда", "почему", "что", "кто", "как", "когда"]
        for qw in question_words:
            if qw in text_lower and person_name in text_lower:
                return False
        return True
    
    if person == 'chuchu' and chuchu_sleep:
        if is_direct_address_to('чу чу'):
            wakeup_response('chuchu')
            message = extract_message(text)
            if message and len(message) > 2:
                response = ai_respond(message, 'chuchu')
                speak(response, 'chuchu')
        else:
            if not mei_sleep:
                contextual_text = f"{text} (имей в виду, что Чу Чу сейчас спит, так что она не может отвечать)"
                response = ai_respond(contextual_text, 'mei')
                speak(response, 'mei')
            else:
                wakeup_response('both')
                message = extract_message(text)
                if message and len(message) > 2:
                    response = ai_respond(message, 'both')
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
        return True
    elif person == 'mei' and mei_sleep:
        if is_direct_address_to('мэй'):
            wakeup_response('mei')
            message = extract_message(text)
            if message and len(message) > 2:
                response = ai_respond(message, 'mei')
                speak(response, 'mei')
        else:
            if not chuchu_sleep:
                contextual_text = f"{text} (имей в виду, что Мэй сейчас спит, так что она не может отвечать)"
                response = ai_respond(contextual_text, 'chuchu')
                speak(response, 'chuchu')
            else:
                wakeup_response('both')
                message = extract_message(text)
                if message and len(message) > 2:
                    response = ai_respond(message, 'both')
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
        return True
    
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

# ========== ФУНКЦИИ СНА И ПРОБУЖДЕНИЯ ==========
def sleep_response(persona='both'):
    global sleep_mode, sleep_mode_trigger, sleep_start_time, chuchu_sleep, mei_sleep
    if persona == 'both':
        if chuchu_sleep and mei_sleep:
            speak("Мы уже спим... Тсс...", 'chuchu')
            return
        chuchu_sleep = True
        mei_sleep = True
        sleep_mode = True
        sleep_mode_trigger = persona
        sleep_start_time = time.time()
        speak("Спокойной ночи! Чу Чу отправляется в страну снов...", 'chuchu')
        time.sleep(1)
        speak("Я тоже ложусь. Не скучай. Мы будем ждать тебя в 7:40 утра.", 'mei')
        time.sleep(0.5)
        speak("Сладких снов...", 'chuchu')
    elif persona == 'chuchu':
        if chuchu_sleep:
            speak("Чу Чу уже спит... Разбуди её позже...", 'mei')
            return
        chuchu_sleep = True
        sleep_mode = True
        speak("Спокойной ночи. Чу Чу устала, идёт спать. Мэй, присмотри за хозяином.", 'chuchu')
        time.sleep(0.8)
        speak("Хорошо, сестра. Отдыхай. Я пока побуду.", 'mei')
    elif persona == 'mei':
        if mei_sleep:
            speak("Мэй уже спит... Не буди её...", 'chuchu')
            return
        mei_sleep = True
        sleep_mode = True
        speak("Мэй отправляется отдыхать. Чу Чу, остаёшься за старшую.", 'mei')
        time.sleep(0.8)
        speak("Хорошо, сестра. Я присмотрю. Сладких снов!", 'chuchu')
    if chuchu_sleep and mei_sleep:
        print("💤 [Обе девушки спят]")

def wakeup_response(persona='both'):
    global sleep_mode, sleep_mode_trigger, chuchu_sleep, mei_sleep
    if persona == 'both':
        chuchu_was_sleeping = chuchu_sleep
        mei_was_sleeping = mei_sleep
        chuchu_sleep = False
        mei_sleep = False
        sleep_mode = False
        sleep_mode_trigger = None
        if chuchu_was_sleeping:
            speak("Доброе утро! Чу Чу проснулась. Как тебе спалось?", 'chuchu')
            time.sleep(0.8)
        if mei_was_sleeping:
            speak("Утро доброе. Мэй тоже проснулась. Рассказывай, что снилось?", 'mei')
        if not chuchu_was_sleeping and not mei_was_sleeping:
            speak("Мы и так не спим! Давай общаться!", 'chuchu')
    elif persona == 'chuchu':
        if not chuchu_sleep:
            speak("Я и так не сплю!", 'chuchu')
            return
        chuchu_sleep = False
        if not mei_sleep:
            sleep_mode = False
            sleep_mode_trigger = None
        speak("Доброе утро! Чу Чу проснулась.", 'chuchu')
    elif persona == 'mei':
        if not mei_sleep:
            speak("Мэй и так не спит!", 'mei')
            return
        mei_sleep = False
        if not chuchu_sleep:
            sleep_mode = False
            sleep_mode_trigger = None
        speak("Доброе утро. Мэй проснулась.", 'mei')

def check_auto_sleep_wake():
    global sleep_mode, sleep_mode_trigger, chuchu_sleep, mei_sleep
    now = datetime.datetime.now()
    current_minutes = now.hour * 60 + now.minute
    sleep_time = SLEEP_HOUR * 60 + SLEEP_MINUTE
    wake_time = WAKE_HOUR * 60 + WAKE_MINUTE
    if current_minutes >= sleep_time and current_minutes < wake_time:
        if not chuchu_sleep and not mei_sleep:
            print(f"\n⏰ {now.strftime('%H:%M')} - Чу Чу и Мэй отправились спать (автоматически)")
            chuchu_sleep = True
            mei_sleep = True
            sleep_mode = True
            sleep_mode_trigger = 'auto'
    else:
        if sleep_mode and sleep_mode_trigger == 'auto':
            print(f"\n⏰ {now.strftime('%H:%M')} - Чу Чу и Мэй проснулись (автоматически)")
            chuchu_sleep = False
            mei_sleep = False
            sleep_mode = False
            sleep_mode_trigger = None

# ========== ИНИЦИАЛИЗАЦИЯ МИКРОФОНА ==========
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("Калибровка микрофона...")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    recognizer.energy_threshold = 300
print("✓ Микрофон готов\n")

def check_and_switch_mode(audio_raw):
    """Проверяет голос и переключает режим ТОЛЬКО при наличии речи"""
    global adult_mode, owner_name, owner_voice_encoding, owner_recognized, is_speaking, last_speech_time
    
    # Не переключаем режим, если девушки говорят или только что говорили
    if is_speaking:
        return
    if time.time() - last_speech_time < SPEECH_COOLDOWN:
        return
    
    if not owner_recognized or owner_voice_encoding is None:
        return
    
    # Проверяем, есть ли осмысленная речь
    audio_np = np.frombuffer(audio_raw, dtype=np.int16)
    if not is_speech_in_audio(audio_np):
        return  # Тишина или шум - не переключаем режим
    
    current_encoding = get_voice_encoding(audio_raw)
    if current_encoding is None:
        return
    
    similarity = np.dot(owner_voice_encoding, current_encoding)
    is_owner = similarity > 0.55
    
    if is_owner and not adult_mode:
        adult_mode = True
        print(f"🔞 [Голос владельца распознан. Включаю взрослый режим]")
        speak(f"А, это вы, {owner_name}! Переключаю на взрослый режим.", 'chuchu')
    elif not is_owner and adult_mode:
        adult_mode = False
        print(f"🔞 [Голос не распознан. Включаю обычный режим]")
        speak("Переключаю на обычный режим общения.", 'chuchu')

def listen():
    global is_idle_dialog_active, chuchu_sleep, mei_sleep, is_speaking, owner_recognized, adult_mode, last_speech_time
    
    if is_speaking:
        return ""
    
    if time.time() - last_speech_time < SPEECH_COOLDOWN:
        return ""
    
    if is_idle_dialog_active:
        return ""
    
    if chuchu_sleep and mei_sleep:
        if not hasattr(listen, 'last_sleep_msg'):
            listen.last_sleep_msg = 0
        current_time = time.time()
        if current_time - listen.last_sleep_msg > 15:
            listen.last_sleep_msg = current_time
            print("\r💤 [Обе девушки спят. Скажите что-нибудь, чтобы разбудить]")
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            recognizer.energy_threshold = 50
            print("\n🎤 Слушаю...", end="", flush=True)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
        
        raw_data = audio.get_raw_data()
        
        # Проверяем, есть ли осмысленная речь
        audio_np = np.frombuffer(raw_data, dtype=np.int16)
        if not is_speech_in_audio(audio_np):
            print("\r🔇 Тишина или шум...", end="", flush=True)
            return ""
        
        # ТОЛЬКО ЕСЛИ ЕСТЬ РЕЧЬ - проверяем голос и переключаем режим
        check_and_switch_mode(raw_data)
        
        text = recognizer.recognize_google(audio, language="ru-RU")
        text = fix_before_spell(text)
        text = spell(text)
        text = apply_replacements(text)
        text = clean_text_for_llm(text)
        
        if owner_name and owner_name != "хозяин":
            text = text.replace("хозяин", owner_name.lower())
        
        print(f"\r💬 {owner_name if owner_name else 'Вы'} сказали: {text}")
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
    global listening_active, sleep_mode, chuchu_sleep, mei_sleep, owner_name, owner_recognized, adult_mode
    
    # Пробуем загрузить сохранённые данные
    data_loaded = load_owner_data()
    
    if not data_loaded:
        # Первый запуск - запись голоса и имени владельца
        print("\n🔐 ПЕРВЫЙ ЗАПУСК. Настройка голосового помощника.")
        speak("Здравствуйте! Как к вам обращаться? Назовите ваше имя.", 'chuchu')
        
        recognizer_local = sr.Recognizer()
        microphone_local = sr.Microphone()
        
        with microphone_local as source:
            recognizer_local.adjust_for_ambient_noise(source, duration=0.5)
            print("\n🎤 Слушаю ваше имя...", end="", flush=True)
            try:
                audio = recognizer_local.listen(source, timeout=8, phrase_time_limit=5)
                print("\r🎤 Имя услышано!     ")
                
                text = recognizer_local.recognize_google(audio, language="ru-RU")
                owner_name = text.strip().capitalize()
                if not owner_name:
                    owner_name = "хозяин"
                
                print(f"✅ Имя: {owner_name}")
                
                raw_data = audio.get_raw_data()
                save_voice_sample(raw_data, "owner_voice.wav", rate=16000)
                owner_voice_encoding = get_voice_encoding(raw_data)
                
                if owner_voice_encoding is not None:
                    owner_recognized = True
                    adult_mode = True
                    speak(f"Приятно познакомиться, {owner_name}! Теперь я буду узнавать вас по голосу.", 'chuchu')
                    time.sleep(0.5)
                    speak("Для тебя включён взрослый режим.", 'chuchu')
                else:
                    speak(f"Приятно познакомиться, {owner_name}!", 'chuchu')
                
                os.makedirs("C:\\Girls-AI\\Girls\\voices", exist_ok=True)
                with open("C:\\Girls-AI\\Girls\\voices\\owner_name.txt", 'w', encoding='utf-8') as f:
                    f.write(owner_name)
                
            except sr.WaitTimeoutError:
                print("\r❌ Не дождались имени.")
                owner_name = "хозяин"
            except sr.UnknownValueError:
                print("\r❌ Не расслышала имя.")
                owner_name = "хозяин"
    else:
        # Данные загружены - идентифицируем говорящего
        name, is_owner, recognized = identify_speaker()
        
        if is_owner:
            # Это владелец
            adult_mode = True
            print(f"✅ Узнала тебя, {owner_name}! Включаю взрослый режим.")
            speak(f"А, это ты, {owner_name}! Узнала тебя по голосу.", 'chuchu')
            time.sleep(0.5)
            speak("Для тебя включён взрослый режим.", 'chuchu')
        else:
            # Чужой голос - гостевой режим
            adult_mode = False
            guest_setup()
    
    now = datetime.datetime.now()
    current_minutes = now.hour * 60 + now.minute
    sleep_time = SLEEP_HOUR * 60 + SLEEP_MINUTE
    wake_time = WAKE_HOUR * 60 + WAKE_MINUTE
    
    if current_minutes >= sleep_time and current_minutes < wake_time:
        print(f"⏰ Текущее время: {now.strftime('%H:%M')}")
        print(f"💤 Чу Чу и Мэй сейчас спят (с 04:00 до 07:40)")
        print(f"⏰ Они проснутся в {WAKE_HOUR:02d}:{WAKE_MINUTE:02d}")
        chuchu_sleep = True
        mei_sleep = True
        sleep_mode = True
    else:
        print("Проверка доступности Qwen модели...")
        try:
            ollama.generate(model=QWEN_MODEL, prompt="Привет", options={'num_predict': 5})
            print("✓ Qwen модель готова к работе\n")
        except Exception as e:
            print(f"⚠ Qwen модель не найдена! Запустите: ollama run {QWEN_MODEL}\n")
    
    check_auto_sleep_wake()
    intro(first_time=not data_loaded)
    start_idle_timer()
    
    def time_checker():
        while listening_active:
            time.sleep(60)
            check_auto_sleep_wake()
    
    time_thread = threading.Thread(target=time_checker, daemon=True)
    time_thread.start()
    
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
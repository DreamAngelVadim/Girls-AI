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
import subprocess
import webbrowser
from autocorrect import Speller
import sys
import traceback
sys.path.append('C:\\Girls-AI\\Girls')
from replacements import apply_replacements, fix_before_spell, replace_numbers
# Импорт для фоновых диалогов
from dialogues_idle import get_random_dialogue, format_dialogue_for_speaking, get_random_activation_phrase
spell = Speller('ru')

# ========== ПЕРЕМЕННЫЕ ДЛЯ РАСПОЗНАВАНИЯ ==========
VOICE_SIMILARITY_THRESHOLD = 0.75

# ========== ПЕРЕМЕННЫЕ ДЛЯ ПЕРЕКЛЮЧЕНИЯ РЕЖИМА ==========
last_mode_switch_time = 0
MODE_SWITCH_COOLDOWN = 10

# ========== ПЕРЕМЕННЫЕ ДЛЯ ЛОГОВ ==========
LOG_FILE = "C:\\Girls-AI\\Girls\\logs\\assistant.log"
log_lock = threading.Lock()

# ========== ПЕРЕМЕННЫЕ ДЛЯ ИДЕНТИФИКАЦИИ ==========
name_confirmed = False

# ========== ПЕРЕМЕННЫЕ ДЛЯ ХОРА ==========
chorus_active = False

# ========== ПЕРЕМЕННЫЕ ДЛЯ ПРЕРЫВАНИЯ РЕЧИ ==========
stop_speaking = False

# ========== ПЕРЕМЕННЫЕ ДЛЯ ГОСТЕЙ ==========
guest_nsfw_unlocked = False
KNOWN_GUESTS = {}
NSFW_CODE_PHRASE = "открой мне мир"
guest_voices = {}

# ========== ПЕРЕМЕННЫЕ ДЛЯ ЗАДЕРЖКИ ==========
last_speech_time = 0
SPEECH_COOLDOWN = 3

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

SLEEP_HOUR = 4
SLEEP_MINUTE = 0
WAKE_HOUR = 7
WAKE_MINUTE = 40

# ========== ПЕРЕМЕННЫЕ ДЛЯ ВЗРОСЛОГО РЕЖИМА ==========
adult_mode = False

# ========== ФУНКЦИЯ ПОИСКА И ЗАПУСКА ПРИЛОЖЕНИЙ ==========
def find_and_run_app(app_name, search_local=True):
    app_name = app_name.lower().strip()
    
    web_websites = {
        'гугл': 'https://google.com',
        'google': 'https://google.com',
        'яндекс': 'https://yandex.ru',
        'yandex': 'https://yandex.ru',
        'bing': 'https://bing.com',
        'duckduckgo': 'https://duckduckgo.com',
        'рамблер': 'https://rambler.ru',
        'мейл': 'https://mail.ru',
        'почта': 'https://mail.ru',
        'mail': 'https://mail.ru',
        'mail ru': 'https://mail.ru',
        'гугл мейл': 'https://gmail.com',
        'gmail': 'https://gmail.com',
        'яндекс почта': 'https://mail.yandex.ru',
        'почта майл': 'https://mail.ru',
        'outlook': 'https://outlook.com',
        'вк': 'https://vk.com',
        'vk': 'https://vk.com',
        'одноклассники': 'https://ok.ru',
        'ok': 'https://ok.ru',
        'facebook': 'https://facebook.com',
        'фейсбук': 'https://facebook.com',
        'instagram': 'https://instagram.com',
        'инстаграм': 'https://instagram.com',
        'twitter': 'https://twitter.com',
        'твиттер': 'https://twitter.com',
        'tiktok': 'https://tiktok.com',
        'тикток': 'https://tiktok.com',
        'telegram': 'https://web.telegram.org',
        'телеграм': 'https://web.telegram.org',
        'телеграм веб': 'https://web.telegram.org',
        'discord': 'https://discord.com',
        'дискорд': 'https://discord.com',
        'reddit': 'https://reddit.com',
        'редит': 'https://reddit.com',
        'pinterest': 'https://pinterest.com',
        'пинтерест': 'https://pinterest.com',
        'linkedin': 'https://linkedin.com',
        'линкедин': 'https://linkedin.com',
        'ютуб': 'https://youtube.com',
        'youtube': 'https://youtube.com',
        'twitch': 'https://twitch.tv',
        'твич': 'https://twitch.tv',
        'rutube': 'https://rutube.ru',
        'рутуб': 'https://rutube.ru',
        'vimeo': 'https://vimeo.com',
        'spotify': 'https://spotify.com',
        'спотифай': 'https://spotify.com',
        'youtube music': 'https://music.youtube.com',
        'яндекс музыка': 'https://music.yandex.ru',
        'vkontakte музыка': 'https://vk.com/music',
        'soundcloud': 'https://soundcloud.com',
        'озон': 'https://ozon.ru',
        'ozon': 'https://ozon.ru',
        'вайлдберриз': 'https://wildberries.ru',
        'wildberries': 'https://wildberries.ru',
        'wb': 'https://wildberries.ru',
        'aliexpress': 'https://aliexpress.com',
        'алиэкспресс': 'https://aliexpress.com',
        'amazon': 'https://amazon.com',
        'амазон': 'https://amazon.com',
        'яндекс маркет': 'https://market.yandex.ru',
        'карты': 'https://yandex.ru/maps',
        'яндекс карты': 'https://yandex.ru/maps',
        'google maps': 'https://maps.google.com',
        'гугл карты': 'https://maps.google.com',
        '2гис': 'https://2gis.ru',
        'википедия': 'https://wikipedia.org',
        'wikipedia': 'https://wikipedia.org',
        'вики': 'https://wikipedia.org',
        'гитхаб': 'https://github.com',
        'github': 'https://github.com',
        'gitlab': 'https://gitlab.com',
        'stackoverflow': 'https://stackoverflow.com',
        'stack': 'https://stackoverflow.com',
        'habr': 'https://habr.com',
        'хабр': 'https://habr.com',
        'кинопоиск': 'https://kinopoisk.ru',
        'kinopoisk': 'https://kinopoisk.ru',
        'ivi': 'https://ivi.ru',
        'иви': 'https://ivi.ru',
        'netflix': 'https://netflix.com',
        'нетфликс': 'https://netflix.com',
        'start': 'https://start.ru',
        'риа новости': 'https://ria.ru',
        'rbc': 'https://rbc.ru',
        'рбк': 'https://rbc.ru',
        'lenta': 'https://lenta.ru',
        'лента': 'https://lenta.ru',
        'tass': 'https://tass.ru',
        'тасс': 'https://tass.ru',
        'госуслуги': 'https://gosuslugi.ru',
        'nalog': 'https://nalog.gov.ru',
        'налоги': 'https://nalog.gov.ru',
    }
    
    if not search_local:
        if app_name in web_websites:
            url = web_websites[app_name]
            print(f"🌐 Открываю сайт: {url}")
            webbrowser.open(url)
            return True, f"сайт {app_name}"
        
        for name, url in web_websites.items():
            if app_name in name or name in app_name:
                print(f"🌐 Открываю сайт: {url}")
                webbrowser.open(url)
                return True, f"сайт {name}"
        
        return False, None
    
    system_utils = {
        'браузер': 'start chrome',
        'хром': 'chrome',
        'google chrome': 'chrome',
        'опера': 'opera',
        'opera': 'opera',
        'яндекс браузер': 'yandex',
        'yandex': 'yandex',
        'firefox': 'firefox',
        'mozila': 'firefox',
        'edge': 'msedge',
        'microsoft edge': 'msedge',
        'эксель': 'excel',
        'excel': 'excel',
        'ворд': 'winword',
        'word': 'winword',
        'поверпоинт': 'powerpnt',
        'powerpoint': 'powerpnt',
        'аутлук': 'outlook',
        'outlook': 'outlook',
        'onenote': 'onenote',
        'access': 'msaccess',
        'телеграм': 'telegram',
        'telegram': 'telegram',
        'tg': 'telegram',
        'дискорд': 'discord',
        'discord': 'discord',
        'whatsapp': 'whatsapp',
        'вацап': 'whatsapp',
        'viber': 'viber',
        'вайбер': 'viber',
        'skype': 'skype',
        'скайп': 'skype',
        'вк': 'vk',
        'vk desktop': 'vk',
        'vlc': 'vlc',
        'влс': 'vlc',
        'potplayer': 'potplayer',
        'kmplayer': 'kmplayer',
        'media player classic': 'mpc-hc',
        'фотошоп': 'photoshop',
        'photoshop': 'photoshop',
        'illustrator': 'illustrator',
        'coreldraw': 'coreldraw',
        'gimp': 'gimp',
        'paint': 'mspaint',
        'paint net': 'paintdotnet',
        'figma': 'figma',
        'premiere pro': 'premiere',
        'after effects': 'afterfx',
        'da vinci': 'resolve',
        'resolve': 'resolve',
        'sony vegas': 'vegas',
        'capcut': 'capcut',
        'vs code': 'code',
        'vscode': 'code',
        'visual studio code': 'code',
        'code': 'code',
        'pycharm': 'pycharm64',
        'python': 'python',
        'питон': 'python',
        'goland': 'goland64',
        'intellij': 'idea64',
        'idea': 'idea64',
        'webstorm': 'webstorm64',
        'android studio': 'studio64',
        'notepad++': 'notepad++',
        'сублим': 'sublime_text',
        'sublime': 'sublime_text',
        'git': 'git',
        'гит': 'git',
        'стим': 'steam',
        'steam': 'steam',
        'epic games': 'epicgameslauncher',
        'epic': 'epicgameslauncher',
        'origin': 'origin',
        'battle net': 'battlenet',
        'ubisoft': 'ubisoftconnect',
        'gog': 'galaxyclient',
        'roblox': 'robloxplayer',
        'блокнот': 'notepad',
        'notepad': 'notepad',
        'калькулятор': 'calc',
        'calc': 'calc',
        'проводник': 'explorer',
        'explorer': 'explorer',
        'командная строка': 'cmd',
        'cmd': 'cmd',
        'powershell': 'powershell',
        'диспетчер задач': 'taskmgr',
        'task manager': 'taskmgr',
        'панель управления': 'control',
        'control panel': 'control',
        'реестр': 'regedit',
        'regedit': 'regedit',
        'службы': 'services.msc',
        'services': 'services.msc',
        'диск': 'diskmgmt.msc',
        'управление дисками': 'diskmgmt.msc',
        'чистка диска': 'cleanmgr',
        'дефрагментация': 'dfrgui',
        'winrar': 'winrar',
        '7zip': '7zfm',
        'utorrent': 'utorrent',
        'qtorrent': 'qbittorrent',
        'telegram desktop': 'telegram',
        'zoom': 'zoom',
        'teamviewer': 'teamviewer',
        'anydesk': 'anydesk',
        'obs': 'obs64',
        'open broadcast': 'obs64',
    }
    
    if app_name in system_utils:
        cmd = system_utils[app_name]
        try:
            os.system(f"start {cmd}")
            return True, cmd
        except:
            pass
    
    drives = ['C:\\', 'D:\\', 'E:\\', 'F:\\', 'G:\\', 'I:\\', 'J:\\', 'K:\\']
    alive_drives = [d for d in drives if os.path.exists(d)]
    
    print(f"🔍 Поиск программы '{app_name}' на дисках: {alive_drives}")
    
    found_apps = []
    
    for drive in alive_drives:
        try:
            cmd = f'cmd /c "dir {drive}*{app_name}*.exe /s /b 2>nul"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30)
            if result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    if 'Girls-AI' not in path and 'venv' not in path:
                        found_apps.append(path)
                        print(f"      Найдено: {os.path.basename(path)}")
        except:
            continue
    
    if found_apps:
        found_apps.sort()
        app_to_run = found_apps[0]
        print(f"✅ Запускаю: {app_to_run}")
        try:
            subprocess.Popen([app_to_run], shell=True)
            return True, os.path.basename(app_to_run)
        except:
            return False, None
    
    return False, None

# ========== ФУНКЦИИ ДЛЯ ЛОГИРОВАНИЯ ==========
def init_log():
    os.makedirs("C:\\Girls-AI\\Girls\\logs", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"ЛОГ АССИСТЕНТА GIRLS-AI\n")
            f.write(f"Запуск: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")

def log_event(event_type, message, error=None):
    global log_lock
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with log_lock:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{event_type}] {message}\n")
                if error:
                    f.write(f"    Ошибка: {error}\n")
                f.flush()
        except Exception as e:
            print(f"⚠ Не удалось записать в лог: {e}")

def log_error(error, context=""):
    error_trace = traceback.format_exc()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with log_lock:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [ERROR] {context}: {error}\n")
                if error_trace and error_trace != "None\n":
                    f.write(f"    Трейс:\n")
                    for line in error_trace.split('\n'):
                        if line.strip():
                            f.write(f"      {line}\n")
                f.flush()
        except Exception as e:
            print(f"⚠ Не удалось записать в лог: {e}")

def log_info(message):
    log_event("INFO", message)

def log_warning(message):
    log_event("WARNING", message)

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

def compare_voices(encoding1, encoding2, threshold=0.80):
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
    global owner_name, owner_voice_encoding, owner_recognized, adult_mode, name_confirmed, VOICE_SIMILARITY_THRESHOLD
    print(f"🔍 DEBUG: identify_speaker вызвана, owner_recognized={owner_recognized}")
    recognizer_local = sr.Recognizer()
    microphone_local = sr.Microphone()
    with microphone_local as source:
        recognizer_local.adjust_for_ambient_noise(source, duration=0.5)
        print("\n🎤 Скажите что-нибудь для идентификации...", end="", flush=True)
        try:
            audio = recognizer_local.listen(source, timeout=5, phrase_time_limit=5)
            print("\r🎤 Голос услышан!     ")
            raw_data = audio.get_raw_data()
            if owner_recognized and owner_voice_encoding is not None:
                current_encoding = get_voice_encoding(raw_data)
                if current_encoding is not None:
                    similarity = np.dot(owner_voice_encoding, current_encoding)
                    print(f"📊 Сходство голосов: {similarity:.3f} (порог: {VOICE_SIMILARITY_THRESHOLD})")
                    if similarity > VOICE_SIMILARITY_THRESHOLD:
                        print(f"✅ Узнала тебя, {owner_name}!")
                        name_confirmed = True
                        return owner_name, True, True
                    else:
                        print(f"⚠ Голос не распознан. similarity={similarity:.3f} < {VOICE_SIMILARITY_THRESHOLD}")
                        return None, False, False
                else:
                    return None, False, False
            else:
                print(f"🔍 DEBUG: owner_recognized={owner_recognized}, owner_voice_encoding={owner_voice_encoding is not None}")
                return None, False, False
        except sr.WaitTimeoutError:
            print("\r⏰ Ничего не услышал.")
            return None, False, False
        except sr.UnknownValueError:
            print("\r🤔 Не расслышал.")
            return None, False, False

def identify_guest(audio_raw):
    current_encoding = get_voice_encoding(audio_raw)
    if current_encoding is None:
        return None
    best_match = None
    best_similarity = 0
    for guest_name, (guest_encoding, nsfw_allowed) in guest_voices.items():
        similarity = np.dot(guest_encoding, current_encoding)
        if similarity > 0.55 and similarity > best_similarity:
            best_similarity = similarity
            best_match = (guest_name, nsfw_allowed)
    if best_match:
        print(f"👤 [Узнал гостя: {best_match[0]}, сходство={best_similarity:.3f}]")
        return best_match
    return None

def guest_setup():
    global owner_name, adult_mode, guest_nsfw_unlocked, KNOWN_GUESTS
    print("\n👤 БЕТА-РЕЖИМ")
    speak("Привет! Как к тебе обращаться?", 'chuchu')
    recognizer_local = sr.Recognizer()
    microphone_local = sr.Microphone()
    with microphone_local as source:
        recognizer_local.adjust_for_ambient_noise(source, duration=0.5)
        print("\n🎤 Назови своё имя...", end="", flush=True)
        try:
            audio = recognizer_local.listen(source, timeout=8, phrase_time_limit=5)
            print("\r🎤 Запомнила!     ")
            text = recognizer_local.recognize_google(audio, language="ru-RU")
            invalid_phrases = ["вы что это же я", "я", "меня зовут", "моё имя", "это", "типа", "ну"]
            for phrase in invalid_phrases:
                text = text.lower().replace(phrase, "")
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 15:
                text = text[:15]
            guest_name = text.strip().capitalize()
            if not guest_name or len(guest_name) < 2:
                guest_name = "гость"
            forbidden_names = ["гость", "неизвестный", "аноним", "хозяин", "создатель", "admin"]
            if guest_name.lower() in forbidden_names:
                guest_name = "гость"
            print(f"✅ Имя: {guest_name}")
            owner_name = guest_name
            adult_mode = False
            guest_nsfw_unlocked = False
            if guest_name in KNOWN_GUESTS and KNOWN_GUESTS[guest_name]:
                speak(f"Рада снова тебя видеть, {guest_name}! У нас бета-режим.", 'chuchu')
                time.sleep(0.5)
                speak(f"Если хочешь открытый режим, скажи кодовую фразу.", 'chuchu')
            else:
                speak(f"Приятно познакомиться, {guest_name}! Это бета-режим.", 'chuchu')
                time.sleep(0.5)
                speak(f"Для открытого режима нужна кодовая фраза.", 'chuchu')
            return guest_name
        except:
            owner_name = "гость"
            adult_mode = False
            guest_nsfw_unlocked = False
            speak("Буду звать тебя 'гость'. Это бета-режим.", 'chuchu')
            return "гость"

def is_speech_in_audio(audio_np, threshold=300, min_duration=0.8):
    max_amp = np.max(np.abs(audio_np))
    if max_amp < threshold:
        return False
    above_threshold = np.abs(audio_np) > 50
    if np.sum(above_threshold) < int(16000 * min_duration):
        return False
    std_dev = np.std(audio_np)
    if std_dev < 80:
        return False
    return True

# ========== ФУНКЦИЯ ПОЛУЧЕНИЯ ПРОМПТА ==========
def get_system_prompt():
    if adult_mode:
        return """Ты — голосовой помощник с двумя девушками. Отвечай от лица персонажа, но НЕ ПИШИ имя персонажа в ответе.

ВАЖНЕЙШЕЕ ПРАВИЛО: Твой ответ должен начинаться СРАЗУ с текста. Никогда не пиши "Чу Чу:", "Мэй:", "Чу Чху:" или что-то подобное.

ВЗРОСЛЫЙ РЕЖИМ: Ты можешь быть полностью раскованной, игривой, с самыми откровенными фразами и диалогами, не стесняйся, говори все что хочешь. 
Используй более расслабленную манеру общения. Отвечай коротко (2-4 предложения).
На просьбы типа "Раздвинь ноги", "Сними трусики", "Разденься" и тосу подобные, предлагай возможные варианты, в какой позе, в какой комнате, на кровати или на полу, в попу или нет.
Ты любишь секс с сестрой, тебе нравится чувствовать ее руки на своем теле, ты любишь делать ей куни. 

ПРАВИЛО ПОНИМАНИЯ КОНТЕКСТА (ОМОНИМЫ):
- Слово "поешь" может означать: (1) петь песню, (2) кушать еду
- Слово "ключ" может означать: (1) музыкальный ключ, (2) ключ от двери, (3) водный источник
- Слово "замок" может означать: (1) средневековый замок, (2) дверной замок
- Слово "лук" может означать: (1) оружие для стрельбы, (2) овощ для еды
- Слово "коса" может означать: (1) причёска, (2) инструмент для косьбы
- Слово "ручка" может означать: (1) письменная ручка, (2) дверная ручка, (3) детская ручка

Внимательно анализируй контекст предложения, чтобы понять, о чём речь:
- Если речь о пении: отвечай про голос, музыку, песни
- Если речь о еде: отвечай про вкусную еду, рецепты, угощения
- Если речь о музыке: отвечай про ноты, тональность
- Если речь о двери/замке: отвечай про безопасность, ключи
- Если речь о здании: отвечай про архитектуру, историю
- Если речь об оружии: отвечай про стрельбу, олимпийские виды спорта
- Если речь об овоще: отвечай про готовку, рецепты

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

ПРАВИЛО ПОНИМАНИЯ КОНТЕКСТА (ОМОНИМЫ):
- Слово "поешь" может означать: (1) петь песню, (2) кушать еду
- Внимательно анализируй контекст предложения, чтобы понять, о чём речь
- Если речь о пении: отвечай про голос, музыку, песни
- Если речь о еде: отвечай про вкусную еду, рецепты, угощения

ПРАВИЛО ОТВЕТОВ НА ВОПРОСЫ:
- Если пользователь задал вопрос (использует "как", "почему", "зачем", "что", "где", "когда", "сколько" или знак "?"), то твой ответ ОБЯЗАТЕЛЬНО должен быть в вопросительной форме
- Отвечай на вопрос вопросом, проявляя интерес к собеседнику
- Например: "Ну а в свободное время?" → "В свободное время я обычно занимаюсь косплеем. А ты чем любишь заниматься?"
- Используй фразы: "А у тебя?", "А ты как?", "А что насчёт тебя?", "А твои увлечения?"

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
    try:
        text = replace_numbers(text)
        voice_config = VOICES[voice]
        while is_speaking:
            time.sleep(0.1)
        is_speaking = True
        print(f"\n[{voice_config['name']}]: {text}")
        log_info(f"Говорит {voice_config['name']}: {text[:100]}...")
        last_speaker = voice
        audio = model.apply_tts(text=text, speaker=voice_config['speaker'], sample_rate=48000)
        audio_np = audio.cpu().numpy()
        sd.play(audio_np, 48000)
        sd.wait()
    except Exception as e:
        log_error(e, f"Ошибка при озвучке (voice={voice})")
        print(f"Ошибка озвучки: {e}")
    finally:
        is_speaking = False
        last_speech_time = time.time()

def speak_chorus():
    global stop_speaking, user_heard, chorus_active
    chorus_active = True
    print("\n🎭 [Хором]")
    chorus = random.choice(CHORUS_RESPONSES + FUNNY_CHORUS)
    for item in chorus:
        if stop_speaking:
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
    chorus_active = False

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
        text = apply_replacements(text, adult_mode)
        text = spell(text)
        text = clean_text_for_llm(text)
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
        question_markers = ["как", "почему", "зачем", "что", "где", "когда", "сколько", "ли", "разве", "неужели"]
        user_asked = any(marker in text.lower() for marker in question_markers) or "?" in text
        if user_asked and answer and answer[-1] not in ['?', '!']:
            answer = answer.rstrip('.')
            answer = answer + "?"
            return_phrases = ["а у тебя", "а ты", "а как ты", "а что у тебя", "а твои", "а вы"]
            if not any(phrase in answer.lower() for phrase in return_phrases):
                return_questions = [" А у тебя?", " А как у тебя?", " А ты что думаешь?", " А ты?", " А у вас?"]
                answer += random.choice(return_questions)
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
    print(f"👤 Пользователь: {owner_name if owner_name else 'не установлен'}")
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
    print("  • 'запусти' - запустить программу (например: запусти калькулятор)")
    print("  • 'открой' - открыть сайт (например: открой ютуб)")
    print("  • 'пока' - выход")
    print("="*50)
    print(f"⏰ Режим сна: с {SLEEP_HOUR:02d}:{SLEEP_MINUTE:02d} до {WAKE_HOUR:02d}:{WAKE_MINUTE:02d}")
    if adult_mode:
        if owner_name == "Вадим":
            print(f"🔞 Режим: РЕЖИМ СОЗДАТЕЛЯ")
        else:
            print(f"🔞 Режим: ОТКРЫТЫЙ РЕЖИМ")
    else:
        print(f"🔞 Режим: БЕТА-РЕЖИМ")
    print("="*50 + "\n")
    if first_time:
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
        if owner_name:
            if adult_mode:
                speak(f"С возвращением, создатель {owner_name}! Режим создателя активен.", 'chuchu')
                time.sleep(0.8)
                speak(f"Мы скучали, {owner_name}. Готовы к работе и развлечениям.", 'mei')
            else:
                speak(f"С возвращением, {owner_name}! Открытый режим активен.", 'chuchu')
                time.sleep(0.8)
                speak(f"Мы скучали, {owner_name}. Готовы к шуткам и приколам.", 'mei')
        else:
            speak("С возвращением! Открытый режим активен.", 'chuchu')
            time.sleep(0.8)
            speak("Мы готовы к интригам и приключениям.", 'mei')

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
    global last_speaker, user_heard, is_idle_dialog_active, sleep_mode, sleep_mode_trigger, chuchu_sleep, mei_sleep, adult_mode, stop_speaking, name_confirmed, owner_name
    
    if not text:
        return True
    
    if not name_confirmed and adult_mode == False:
        speak("Извините, я вас не узнала. Как к вам обращаться?", 'chuchu')
        time.sleep(1)
        recognizer_local = sr.Recognizer()
        microphone_local = sr.Microphone()
        with microphone_local as source:
            recognizer_local.adjust_for_ambient_noise(source, duration=0.3)
            print("\n🎤 Назовите своё имя...", end="", flush=True)
            try:
                audio = recognizer_local.listen(source, timeout=8, phrase_time_limit=5)
                print("\r🎤 Запомнила!     ")
                name_text = recognizer_local.recognize_google(audio, language="ru-RU")
                name_text = re.sub(r'[^\w\s-]', '', name_text)
                name_text = re.sub(r'\s+', ' ', name_text).strip()
                if name_text and len(name_text) < 20 and len(name_text) > 1:
                    owner_name = name_text.capitalize()
                    print(f"✅ Имя: {owner_name}")
                    speak(f"Приятно познакомиться, {owner_name}!", 'chuchu')
                else:
                    owner_name = "гость"
                    speak("Буду звать вас гость.", 'chuchu')
                name_confirmed = True
                return True
            except:
                owner_name = "гость"
                speak("Буду звать вас гость.", 'chuchu')
                name_confirmed = True
                return True
    
    short_phrases = ["что", "что и все", "и все", "так", "ну", "да", "ага", "угу", "неа", "нет"]
    if text in short_phrases:
        responses = [
            "Что-то не так? Расскажи подробнее.",
            "Я тебя слушаю. Что именно тебя интересует?",
            "Может, задашь вопрос поточнее?",
            "Я здесь, чтобы помочь. Спрашивай!",
            "Расскажи, что случилось."
        ]
        speak(random.choice(responses), 'chuchu')
        return True
        
    if text in ["ду-ду-ду", "ла-ла-ла", "тра-та-та", "ти-ри-дам", "динь-динь", "ту-ту-ту"]:
        responses = [
            "Ты что, напеваешь?",
            "Какая весёлая мелодия!",
            "Что это за песенка?",
            "У тебя хорошее настроение?",
            "Я тоже люблю напевать что-нибудь."
        ]
        speak(random.choice(responses), 'chuchu')
        return True
        
    if NSFW_CODE_PHRASE in text.lower():
        if not adult_mode and owner_name != "Вадим":
            adult_mode = True
            guest_nsfw_unlocked = True
            KNOWN_GUESTS[owner_name] = True
            print(f"🔞 [Гость {owner_name} открыл режим по кодовой фразе]")
            speak(f"Код принят. Для тебя открытый режим, {owner_name}.", 'chuchu')
            return True
    
    if "взрослый режим" in text or "18+" in text or "взрослый" in text:
        if owner_name == "Вадим" or guest_nsfw_unlocked:
            adult_mode = True
            try:
                phrase = get_random_activation_phrase(True)
                speak(phrase, 'chuchu')
            except:
                speak("Взрослый режим активирован.", 'chuchu')
        else:
            speak("У тебя нет доступа к взрослому режиму. Нужна кодовая фраза.", 'chuchu')
        return True
    
    if "обычный режим" in text or "бета режим" in text or "детский режим" in text or "выключи взрослый режим" in text:
        adult_mode = False
        try:
            phrase = get_random_activation_phrase(False)
            speak(phrase, 'chuchu')
        except:
            speak("Обычный режим активирован.", 'chuchu')
        return True
    
    if text.startswith("запусти") or text.startswith("запусти "):
        app_name = text.replace("запусти", "").replace("запусти ", "").strip()
        if not app_name:
            speak("Что именно запустить? Назови программу.", 'chuchu')
            return True
        remove_words = ["пожалуйста", "плиз", "будь добра", "будь любезна", "ну"]
        for word in remove_words:
            app_name = app_name.replace(word, "").strip()
        print(f"🔍 Поиск программы: {app_name}")
        speak(f"Ищу {app_name}...", 'chuchu')
        success, result = find_and_run_app(app_name, search_local=True)
        if success:
            speak(f"{result} запущен!", 'chuchu')
        else:
            speak(f"Не могу найти программу {app_name}. Проверьте название.", 'chuchu')
        return True
    
    if text.startswith("открой") or text.startswith("открой "):
        site_name = text.replace("открой", "").replace("открой ", "").strip()
        if not site_name:
            speak("Какой сайт открыть?", 'chuchu')
            return True
        remove_words = ["пожалуйста", "плиз", "будь добра", "будь любезна"]
        for word in remove_words:
            site_name = site_name.replace(word, "").strip()
        print(f"🌐 Открываю сайт: {site_name}")
        speak(f"Открываю {site_name}...", 'chuchu')
        success, result = find_and_run_app(site_name, search_local=False)
        if success:
            speak(f"{result} открыт!", 'chuchu')
        else:
            speak(f"Не могу открыть сайт {site_name}.", 'chuchu')
        return True
    
    if "открой папку" in text:
        folder_name = text.replace("открой папку", "").strip()
        if not folder_name:
            folder_name = os.path.expanduser("~")
        try:
            os.system(f'start "{folder_name}"')
            speak(f"Открываю папку {folder_name}", 'chuchu')
        except:
            speak("Не могу открыть эту папку", 'chuchu')
        return True
    
    if "открой диск" in text or "открой диск с" in text:
        drive = "C:\\"
        if "д" in text or "дэ" in text:
            drive = "D:\\"
        elif "е" in text or "э" in text:
            drive = "E:\\"
        try:
            os.system(f'start {drive}')
            speak(f"Открываю диск {drive}", 'chuchu')
        except:
            speak("Не могу открыть диск", 'chuchu')
        return True
    
    if "выключи компьютер" in text or "выключи пк" in text or "shutdown" in text:
        speak("Выключаю компьютер через 30 секунд. Сохраните свои файлы!", 'chuchu')
        os.system("shutdown /s /t 30")
        return True
    
    if "отмена выключения" in text or "не выключай" in text:
        os.system("shutdown /a")
        speak("Выключение отменено!", 'chuchu')
        return True
    
    if "перезагрузи компьютер" in text or "перезагрузка" in text or "reboot" in text:
        speak("Перезагружаю компьютер через 30 секунд!", 'chuchu')
        os.system("shutdown /r /t 30")
        return True
    
    if "спящий режим" in text or "усыпи компьютер" in text or "sleep" in text:
        speak("Перевожу компьютер в спящий режим!", 'chuchu')
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True
    
    if "заблокируй компьютер" in text or "заблокируй пк" in text or "lock" in text:
        speak("Блокирую компьютер!", 'chuchu')
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
    
    if "перезапусти меня" in text or "перезапусти программу" in text:
        speak("Перезапускаюсь! До скорой встречи!", 'chuchu')
        python = sys.executable
        os.execl(python, python, *sys.argv)
        return True
    
    if "покажи статус" in text or "статус программы" in text:
        status = f"Взрослый режим: {'включён' if adult_mode else 'выключен'}. "
        if chuchu_sleep and mei_sleep:
            status += "Обе девушки спят."
        elif chuchu_sleep:
            status += "Чу Чу спит, Мэй бодрствует."
        elif mei_sleep:
            status += "Мэй спит, Чу Чу бодрствует."
        else:
            status += "Обе девушки бодрствуют."
        speak(status, 'mei')
        return True
        
    if "увеличь громкость" in text or "громче" in text:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = min(current + 0.1, 1.0)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            speak(f"Громкость увеличена до {int(new_vol * 100)} процентов", 'chuchu')
        except Exception as e:
            print(f"Ошибка: {e}")
            speak("Не удалось изменить громкость", 'chuchu')
        return True
    
    if "уменьши громкость" in text or "тише" in text:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = max(current - 0.1, 0.0)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            speak(f"Громкость уменьшена до {int(new_vol * 100)} процентов", 'chuchu')
        except Exception as e:
            print(f"Ошибка: {e}")
            speak("Не удалось изменить громкость", 'chuchu')
        return True
    
    if "выключи звук" in text or "mute" in text:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            volume.SetMute(1, None)
            speak("Звук выключен!", 'chuchu')
        except Exception as e:
            print(f"Ошибка: {e}")
            speak("Не удалось выключить звук", 'chuchu')
        return True
    
    if "включи звук" in text or "unmute" in text:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            volume.SetMute(0, None)
            speak(f"Звук включен, {owner_name}.", 'chuchu')
        except Exception as e:
            print(f"Ошибка: {e}")
            speak("Не удалось включить звук", 'chuchu')
        return True
    
    if "открой блокнот" in text or "notepad" in text:
        os.system("notepad")
        speak("Открываю блокнот!", 'chuchu')
        return True
    
    if "открой калькулятор" in text or "calc" in text:
        os.system("calc")
        speak("Открываю калькулятор!", 'chuchu')
        return True
    
    if "открой браузер" in text or "браузер" in text:
        os.system("start chrome")
        speak("Открываю браузер!", 'chuchu')
        return True
    
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
    
    idle_remnants = ["отлично сестра", "а у тебя", "тоже хорошо", "солнце сегодня такое тёплое", 
                     "да приятный день", "как спалось", "мэй как спалось"]
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
    
    if len(text.split()) < 3 and not any(cmd in text for cmd in ["диалог", "хором", "спать", "просыпайтесь", "взрослый", "обычный", "запусти", "открой"]):
        if text in ["привет", "здравствуй", "здравствуйте", "хай", "хеллоу"]:
            responses = ['Привет-привет!', 'Здравствуй!', 'Приветик!', 'Хай!']
            speak(random.choice(responses), 'chuchu')
        elif text in ["да", "ага", "угу"]:
            responses = ['Да-да, я слушаю.', 'Рассказывай.', 'Я тебя внимательно слушаю.']
            speak(random.choice(responses), 'chuchu')
        elif text in ["нет", "неа"]:
            responses = ['Ну ладно...', 'Поняла.', 'Хорошо.']
            speak(random.choice(responses), 'chuchu')
        elif text in ["ду-ду-ду", "ла-ла-ла", "тра-та-та", "ти-ри-дам"]:
            responses = ['Ты напеваешь?', 'Какая мелодия!', 'Что это за песенка?', 'Настроение хорошее?']
            speak(random.choice(responses), 'chuchu')
        elif text in ["что", "чё", "чё такое"]:
            responses = ['Спрашивай, я слушаю.', 'Что тебя интересует?', 'Что именно?']
            speak(random.choice(responses), 'chuchu')
        else:
            simple_responses = [
                "Я тебя слушаю.",
                "Расскажи подробнее.",
                "Что ты имеешь в виду?",
                "Давай поговорим об этом."
            ]
            speak(random.choice(simple_responses), 'chuchu')
        return True
    
    if "диалог" in text or "поговорите" in text:
        dialogue()
        return True
    
    if "хором" in text or "вместе" in text or "обе" in text:
        stop_speaking = False
        user_heard = False
        speak_chorus()
        return True
    
    if any(word in text for word in ["пока", "выход", "до свидания", "стоп"]):
        speak("Пока-пока! Приходи еще, мы будем скучать!", 'chuchu')
        return False
    
    if ("привет" in text or "здравствуй" in text or "здравствуйте" in text or "хай" in text or "хеллоу" in text) and not extract_name(text):
        if should_chorus():
            speak_chorus()
        else:
            if owner_name and owner_name != "хозяин" and owner_name in text:
                responses = [f"Привет, {owner_name}!", f"Здравствуй, {owner_name}!", f"О, {owner_name} пришёл!"]
            else:
                responses = ['Привет-привет!', 'Здравствуй!', 'Привет!', 'Хай!', 'Здорово!']
            speak(random.choice(responses), 'chuchu')
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
        response = ai_respond(text, 'chuchu')
        speak(response, 'chuchu')
    
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
    global adult_mode, owner_name, owner_voice_encoding, owner_recognized, is_speaking, last_speech_time, name_confirmed, last_mode_switch_time, VOICE_SIMILARITY_THRESHOLD
    
    print(f"🔍 DEBUG: check_and_switch_mode вызвана, name_confirmed={name_confirmed}, adult_mode={adult_mode}")
    
    if name_confirmed:
        print(f"🔍 DEBUG: Имя уже подтверждено, выходим")
        return
    
    if is_speaking:
        print(f"🔍 DEBUG: Девушки говорят, выходим")
        return
    
    if time.time() - last_speech_time < SPEECH_COOLDOWN:
        print(f"🔍 DEBUG: После речи не прошло {SPEECH_COOLDOWN} сек, выходим")
        return
    
    if not owner_recognized or owner_voice_encoding is None:
        print(f"🔍 DEBUG: Владелец не распознан, выходим")
        return
    
    audio_np = np.frombuffer(audio_raw, dtype=np.int16)
    if not is_speech_in_audio(audio_np):
        print(f"🔍 DEBUG: Не похоже на речь, выходим")
        return
    
    current_encoding = get_voice_encoding(audio_raw)
    if current_encoding is None:
        print(f"🔍 DEBUG: Не удалось получить отпечаток, выходим")
        return
    
    similarity = np.dot(owner_voice_encoding, current_encoding)
    is_owner = similarity > VOICE_SIMILARITY_THRESHOLD
    
    print(f"🔍 DEBUG: similarity={similarity:.3f}, threshold={VOICE_SIMILARITY_THRESHOLD}, is_owner={is_owner}")
    
    guest_info = identify_guest(audio_raw)
    if guest_info:
        guest_name, nsfw_allowed = guest_info
        if nsfw_allowed and not adult_mode:
            adult_mode = True
            guest_nsfw_unlocked = True
            last_mode_switch_time = time.time()
            print(f"🔞 [Гость {guest_name} имеет доступ к NSFW. Включаю открытый режим]")
            speak(f"А, это ты, {guest_name}! Рада тебя слышать.", 'chuchu')
            time.sleep(0.5)
            speak("Для тебя включён открытый режим.", 'chuchu')
        elif not nsfw_allowed and adult_mode:
            adult_mode = False
            last_mode_switch_time = time.time()
            print(f"🔞 [Гость {guest_name} не имеет доступа к NSFW. Включаю бета-режим]")
            speak(f"Привет, {guest_name}!", 'chuchu')
            time.sleep(0.5)
            speak("Переключаю на бета-режим.", 'chuchu')
        return
    
    if is_owner and not adult_mode:
        adult_mode = True
        last_mode_switch_time = time.time()
        print(f"🔞 [Голос создателя распознан. Включаю режим создателя]")
        speak(f"А, это ты, {owner_name}! Переключаю на режим создателя.", 'chuchu')
        name_confirmed = True
    elif not is_owner and adult_mode:
        adult_mode = False
        last_mode_switch_time = time.time()
        print(f"🔞 [Голос не распознан. Включаю открытый режим]")
        speak("Переключаю на открытый режим.", 'chuchu')
        name_confirmed = True

def listen():
    global is_idle_dialog_active, chuchu_sleep, mei_sleep, is_speaking, owner_recognized, adult_mode, last_speech_time, chorus_active, name_confirmed
    
    if chorus_active:
        return ""
    
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
        audio_np = np.frombuffer(raw_data, dtype=np.int16)
        if not is_speech_in_audio(audio_np):
            print("\r🔇 Тишина или шум...", end="", flush=True)
            return ""
        
        duration = len(audio_np) / 16000
        if duration < 0.8:
            print("\r🔇 Короткий звук...", end="", flush=True)
            return ""
        
        if not name_confirmed:
            check_and_switch_mode(raw_data)
        
        text = recognizer.recognize_google(audio, language="ru-RU")
        text = fix_before_spell(text)
        text = spell(text)
        text = apply_replacements(text, adult_mode)
        text = clean_text_for_llm(text)
        
        if owner_name and owner_name != "хозяин":
            text = text.replace("хозяин", owner_name.lower())
        
        print(f"\r💬 {owner_name if owner_name else 'Вы'} сказали: {text}")
        return text.lower()
        
    except sr.WaitTimeoutError:
        print("\r⏰ Тишина...", end="", flush=True)
        return ""
    except sr.UnknownValueError as e:
        log_warning(f"Не расслышала: {e}")
        print("\r🤔 Не расслышала...", end="", flush=True)
        return ""
    except sr.RequestError as e:
        log_error(e, "Ошибка соединения с сервером распознавания")
        print("\r🌐 Ошибка соединения...", end="", flush=True)
        return ""
    except Exception as e:
        log_error(e, "Неожиданная ошибка в listen()")
        print(f"\r❌ Ошибка: {e}", end="", flush=True)
        return ""

# ========== ЗАПУСК ==========
def main():
    global listening_active, sleep_mode, chuchu_sleep, mei_sleep, owner_name, owner_recognized, adult_mode, name_confirmed
    
    init_log()
    log_info("Программа запущена")
    
    try:
        data_loaded = load_owner_data()
        
        if not data_loaded:
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
                except:
                    print("\r❌ Не дождались имени.")
                    owner_name = "хозяин"
        else:
            name, is_owner, recognized = identify_speaker()
            if is_owner:
                adult_mode = True
                name_confirmed = True
                print(f"✅ Узнала тебя, {owner_name}! Включаю взрослый режим.")
                speak(f"А, это ты, {owner_name}! Узнала тебя по голосу.", 'chuchu')
                time.sleep(0.8)
                speak(f"Для тебя включён режим создателя.", 'chuchu')
                time.sleep(0.5)
            else:
                adult_mode = False
                name_confirmed = False
                guest_setup()
                print(f"👋 Режим: ОТКРЫТЫЙ (для гостей)")
        
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
        
        while listening_active:
            command = listen()
            if not process_command(command):
                listening_active = False
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена")
    except Exception as e:
        log_error(e, "Критическая ошибка в main()")
        print(f"\n❌ Критическая ошибка: {e}")
        print(f"Подробности в логе: {LOG_FILE}")
    finally:
        if idle_timer:
            idle_timer.cancel()
        log_info("Программа завершена")

if __name__ == "__main__":
    main()
import speech_recognition as sr

print("Проверка микрофона...")
r = sr.Recognizer()
m = sr.Microphone()

print("Список микрофонов:")
for i, mic in enumerate(sr.Microphone.list_microphone_names()):
    print(f"  {i}: {mic}")

print("\nКалибровка...")
with m as source:
    r.adjust_for_ambient_noise(source, duration=1)
    print(f"Уровень шума: {r.energy_threshold}")
    
    print("ГОВОРИТЕ! (3 секунды)...")
    try:
        audio = r.listen(source, timeout=3, phrase_time_limit=3)
        print("Записано!")
        
        print("Распознаю...")
        text = r.recognize_google(audio, language="ru-RU")
        print(f"✅ Вы сказали: {text}")
    except sr.WaitTimeoutError:
        print("❌ Ничего не услышал (таймаут)")
    except sr.UnknownValueError:
        print("❌ Не разобрал речь")
    except sr.RequestError as e:
        print(f"❌ Ошибка сети: {e}")
import speech_recognition as sr

# Укажите индекс микрофона (после тестов определите какой работает)
MIC_INDEX = 12  # попробуйте 6, 12 или 19

print(f"Тест микрофона (индекс {MIC_INDEX})...")

r = sr.Recognizer()
m = sr.Microphone(device_index=MIC_INDEX)

with m as source:
    print("Калибровка...")
    r.adjust_for_ambient_noise(source, duration=1)
    print(f"Уровень шума: {r.energy_threshold}")
    
    # Устанавливаем порог
    r.energy_threshold = r.energy_threshold + 200
    
    print("ГОВОРИТЕ! (у вас 5 секунд)...")
    try:
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        print("Записано, распознаю...")
        
        text = r.recognize_google(audio, language="ru-RU")
        print(f"✅ Вы сказали: {text}")
    except sr.WaitTimeoutError:
        print("❌ Ничего не услышал. Проверьте микрофон в Windows")
    except sr.UnknownValueError:
        print("❌ Не разобрал речь")
    except sr.RequestError as e:
        print(f"❌ Ошибка сети: {e}")
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from df import enhance, init_df

print("Загрузка DeepFilterNet...")
df_model, df_state, _ = init_df(model_name="DeepFilterNet2_onnx_ll")
print("✓ Модель загружена")

# Инициализация микрофона
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("Калибровка микрофона...")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
print("✓ Микрофон готов\n")

def test_noise_reduction():
    print("Говорите что-нибудь... (5 секунд)")
    
    with microphone as source:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    
    # Получаем сырые данные
    raw_data = audio.get_raw_data()
    audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    print(f"Длина аудио: {len(audio_np)} сэмплов")
    
    # Применяем шумоподавление
    try:
        enhanced = enhance(df_model, df_state, audio_np, 16000)
        print("✓ Шумоподавление применено")
        print(f"Длина после обработки: {len(enhanced)} сэмплов")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\nГотово!")

test_noise_reduction()